import os

import copy

from typing import Optional, List

from libMLS.libMLS.cipher_suite import CipherSuite
from libMLS.libMLS.crypto import hkdf_expand_label
from libMLS.libMLS.group_context import GroupContext
from libMLS.libMLS.tree_math import parent, direct_path, sibling, copath, resolve
from libMLS.libMLS.tree_node import TreeNode
from libMLS.libMLS.messages import WelcomeInfoMessage, AddMessage, UpdateMessage, DirectPathNode, HPKECiphertext
from libMLS.libMLS.tree import Tree


class State:

    def __init__(
            self,
            cipher_suite: CipherSuite,
            tree: Tree,
            context: GroupContext
    ):
        """

        :param cipher_suite:
        """
        # todo: Credentials, private key
        self._cipher_suite: CipherSuite = cipher_suite
        self._init_secret: int = 0  # todo: 0 is probably a bad init secret
        self._tree = tree
        self._context = context

    @classmethod
    def from_existing(cls, cipher_suite: CipherSuite, context: GroupContext,
                      nodes: List[Optional[TreeNode]]) -> 'State':
        tree: Tree = Tree(nodes=nodes)
        return cls(cipher_suite=cipher_suite, tree=tree, context=context)

    @classmethod
    def from_empty(cls, cipher_suite: CipherSuite, context: GroupContext, leaf_secret: bytes) -> 'State':
        tree: Tree = Tree()
        tree.add_leaf(TreeNode(leaf_secret, None, None))

        return cls(tree=tree, cipher_suite=cipher_suite, context=context)

    def get_tree(self) -> Tree:
        return self._tree

    def get_group_context(self) -> GroupContext:
        return self._context

    # todo: user user_credential
    # pylint: disable=unused-argument
    def add(self, user_init_key: bytes, user_credential: bytes) -> (WelcomeInfoMessage, AddMessage):
        welcome: WelcomeInfoMessage = WelcomeInfoMessage()
        welcome.epoch = self._context.epoch
        welcome.group_id = self._context.group_id
        welcome.init_secret = b'0'
        welcome.interim_transcript_hash = b'0'
        welcome.tree = copy.deepcopy(self._tree.get_nodes())  # todo: remove private keys
        welcome.key = b'0'
        welcome.nounce = b'0'

        # self._tree.add_leaf(TreeNode(user_init_key, None, user_credential))

        # todo: support insert in the middle of a group
        # Pylint currently has a problem with dataclasses
        # pylint: disable=unexpected-keyword-arg
        add: AddMessage = AddMessage(index=self._tree.get_num_leaves(),
                                     init_key=user_init_key,
                                     welcome_info_hash=b'0')

        return welcome, add

    def process_add(self, add_message: AddMessage) -> None:
        # todo: validate stuff
        self._tree.add_leaf(TreeNode(add_message.init_key, None, None))

    def update(self, leaf_index: int) -> UpdateMessage:
        # TODO: ACTHUNG ACHTUNG RESEQUENCING
        # DIESE METHODE IST NICHT RESEQUENCING SICHER
        # Gegensätzlich zum RFC müssten wir auch das leaf secret mit versenden, damit wir im resequencing fall
        # nicht unseren tree borken. Gerade erstzen wir das leaf secret sofort, wenn die update nachricht dann
        # resequenced wird ist der updatende client raus. MLSpp von cisco hat das gleiche problem.

        # current_node: TreeNode = self._tree.get_nodes(leaf_index * 2)

        nodes_in_copath = copath(leaf_index, self._tree.get_num_leaves())
        nodes_out: List[DirectPathNode] = []
        path_secret = os.urandom(16)
        # todo: get hash len
        hash_length = 32
        node_secret = hkdf_expand_label(secret=path_secret, context=self._context, label=b"node",
                                        cipher_suite=self._cipher_suite, length=hash_length)

        self._tree.set_node(leaf_index * 2, TreeNode.from_node_secret(node_secret=node_secret,
                                                                      cipher_suite=self._cipher_suite))
        # Pylint currently has a problem with dataclasses
        # pylint: disable=unexpected-keyword-arg
        nodes_out.append(DirectPathNode(public_key=self._tree.get_node(leaf_index).get_public_key(),
                                        encrypted_path_secret=[]))

        for conode_index in nodes_in_copath:
            node_index = parent(conode_index, self._tree.get_num_leaves())

            path_secret = hkdf_expand_label(secret=path_secret, context=self._context, label=b"path",
                                            cipher_suite=self._cipher_suite, length=hash_length)

            node_secret = hkdf_expand_label(secret=path_secret, context=self._context, label=b"node",
                                            cipher_suite=self._cipher_suite, length=hash_length)

            self._tree.set_node(node_index=node_index,
                                node=TreeNode.from_node_secret(node_secret=node_secret,
                                                               cipher_suite=self._cipher_suite))

            # encrypt the path secrect for the nodes in the copath
            resolution: List[int] = resolve(self._tree.get_nodes(), conode_index, self._tree.get_num_nodes())
            ciphers: List[HPKECiphertext] = []
            # todo: This loop must be updated with Issue !6
            # https://git.fh-muenster.de/masterprojekt-mls/implementation/issues/6
            # pylint: disable=unused-variable
            for resolution_node_index in resolution:
                # Pylint currently has a problem with dataclasses
                # pylint: disable=unexpected-keyword-arg
                ciphers.append(HPKECiphertext(ephemeral_key=b'0', cipher_text=path_secret))

            # todo: SetupBaseI aus HPKE nutzen https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-9.3
            # todo: Path secret verschlüsseln
            # Pylint currently has a problem with dataclasses
            # pylint: disable=unexpected-keyword-arg
            nodes_out.append(DirectPathNode(public_key=self._tree.get_node(node_index).get_public_key(),
                                            encrypted_path_secret=ciphers))

        return UpdateMessage(direct_path=nodes_out)

    def process_update(self, leaf_index: int, message: UpdateMessage) -> None:

        # todo: more sanity checks
        if len(direct_path(leaf_index * 2, self._tree.get_num_leaves())) != len(message.direct_path):
            raise RuntimeError()

        if message.direct_path[0].encrypted_path_secret is not None:
            raise RuntimeError()

        # overwrite leaf
        self._tree.set_node(leaf_index * 2, TreeNode(message.direct_path[0].public_key, None, None))

        last_node_index = leaf_index * 2
        for entry in message.direct_path[1:]:
            current_node_index = parent(last_node_index, self._tree.get_num_leaves())
            private_key = None

            current_node_sibling_index = sibling(current_node_index, self._tree.get_num_leaves())
            current_node_sibling_resolution = resolve(self._tree.get_nodes(), current_node_sibling_index,
                                                      self._tree.get_num_leaves())

            for resolution_node_index in current_node_sibling_resolution:
                resolution_node = self._tree.get_node(resolution_node_index)
                if not resolution_node.has_private_key():
                    continue

                #todo: decrypt secret here, as soon as it is encrypted

                private_key = entry.encrypted_path_secret[0]

            self._tree.set_node(leaf_index * 2, TreeNode(entry.public_key, private_key, None))
