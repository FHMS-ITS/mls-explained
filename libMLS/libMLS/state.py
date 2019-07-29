import copy

from dataclasses import dataclass
from typing import Optional, List

from libMLS.libMLS.cipher_suite import CipherSuite
from libMLS.libMLS.tree_node import TreeNode
from libMLS.libMLS.messages import WelcomeInfoMessage, AddMessage
from libMLS.libMLS.tree import Tree


@dataclass
class GroupContext:
    group_id: bytes
    epoch: int
    tree_hash: bytes
    confirmed_transcript_hash: bytes

    def __eq__(self, other):
        if not isinstance(other, GroupContext):
            return False

        return self.group_id == other.group_id and \
               self.epoch == other.epoch and \
               self.confirmed_transcript_hash == other.confirmed_transcript_hash and \
               self.tree_hash == other.tree_hash


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

    def add(self, user_init_key: bytes, user_credential: bytes) -> (WelcomeInfoMessage, AddMessage):
        welcome: WelcomeInfoMessage = WelcomeInfoMessage()
        welcome.epoch = self._context.epoch
        welcome.group_id = self._context.group_id
        welcome.init_secret = b'0'
        welcome.interim_transcript_hash = b'0'
        welcome.tree = copy.deepcopy(self._tree.get_nodes())
        welcome.key = b'0'
        welcome.nounce = b'0'

        # self._tree.add_leaf(TreeNode(user_init_key, None, user_credential))

        # todo: support insert in the middle of a group
        add: AddMessage = AddMessage(index=self._tree.get_num_leaves(),
                                     init_key=user_init_key,
                                     welcome_info_hash=b'0')

        return welcome, add

    def process_add(self, add_message: AddMessage) -> None:
        # todo: validate stuff
        self._tree.add_leaf(TreeNode(add_message.init_key, None, None))
