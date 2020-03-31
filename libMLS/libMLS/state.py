import os

from typing import Optional, List, Dict

from libMLS.cipher_suite import CipherSuite
from libMLS.crypto import hkdf_expand_label
from libMLS.group_context import GroupContext
from libMLS.key_schedule import KeySchedule, advance_epoch
from libMLS.tree_math import parent, direct_path, sibling, copath, resolve
from libMLS.tree_node import TreeNode
from libMLS.messages import WelcomeInfoMessage, AddMessage, UpdateMessage, DirectPathNode, HPKECiphertext
from libMLS.tree import Tree
from libMLS.x25519_cipher_suite import X25519CipherSuite


class State:
    """
    RFC Section 6.4 Group State
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-6.4

    When a new member is added to the group, an existing member of the
    group provides the new member with a Welcome message.  The Welcome
    message provides the information the new member needs to initialize
    its GroupContext.

    Different group operations will have different effects on the group
    state.  These effects are described in their respective subsections
    of Section 9.  The following rules apply to all operations:

    o  The "group_id" field is constant

    o  The "epoch" field increments by one for each GroupOperation that
      is processed

    o  The "tree_hash" is updated to represent the current tree and
      credentials

    o  The "confirmed_transcript_hash" is updated with the data for an
      MLSPlaintext message encoding a group operation in two parts:

    struct {
        opaque group_id<0..255>;
        uint32 epoch;
        uint32 sender;
        ContentType content_type = handshake;
        GroupOperation operation;
    } MLSPlaintextOpContent;

    struct {
        opaque confirmation<0..255>;
        opaque signature<0..2^16-1>;
    } MLSPlaintextOpAuthData;

    confirmed_transcript_hash_[n] =
       Hash(interim_transcript_hash_[n-1] ||
            MLSPlaintextOpContent_[n]);

    interim_transcript_hash_[n] =
       Hash(confirmed_transcript_hash_[n] ||
            MLSPlaintextOpAuthData_[n]);

    This structure incorporates everything in an MLSPlaintext up to the
    confirmation field in the transcript that is included in that
    confirmation field (via the GroupContext).  The confirmation and
    signature fields are then included in the transcript for the next
    operation.  The interim transcript hash is passed to new members in
    the WelcomeInfo struct, and enables existing members to incorporate a
    handshake message into the transcript without having to store the
    whole MLSPlaintextOpAuthData structure.

    When a new one-member group is created (which requires no
    GroupOperation), the "interim_transcript_hash" field is set to the
    zero-length octet string.
    """

    def __init__(
            self,
            cipher_suite: CipherSuite,
            tree: Tree,
            context: GroupContext
    ):

        # todo: Credentials, private key
        self._cipher_suite: CipherSuite = cipher_suite
        self._tree = tree
        self._context = context
        self._key_schedule = KeySchedule(self._cipher_suite)

    @classmethod
    def from_existing(cls, cipher_suite: CipherSuite, context: GroupContext,
                      nodes: List[Optional[TreeNode]]) -> 'State':
        tree: Tree = Tree(nodes=nodes, cipher_suite=X25519CipherSuite())
        return cls(cipher_suite=cipher_suite, tree=tree, context=context)

    @classmethod
    def from_empty(cls, cipher_suite: CipherSuite, context: GroupContext, leaf_public: bytes,
                   leaf_secret: bytes) -> 'State':
        tree: Tree = Tree(cipher_suite=X25519CipherSuite())
        tree.add_leaf(TreeNode(leaf_public, leaf_secret, None))

        return cls(tree=tree, cipher_suite=cipher_suite, context=context)

    def get_tree(self) -> Tree:
        return self._tree

    def get_group_context(self) -> GroupContext:
        return self._context

    def get_key_schedule(self) -> KeySchedule:
        return self._key_schedule

    # todo: user user_credential
    # pylint: disable=unused-argument
    def add(self, user_init_key: bytes, user_credential: bytes) -> (WelcomeInfoMessage, AddMessage):
        """
        RFC Section 9.2 Add
        https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-9.2

        In order to add a new member to the group, an existing member of the
        group must take two actions:

        1.  Send a Welcome message to the new member
        2.  Send an Add message to the group (including the new member)

        The Welcome message contains the information that the new member
        needs to initialize a GroupContext object that can be updated to the
        current state using the Add message.  This information is encrypted
        for the new member using HPKE.  The recipient key pair for the HPKE
        encryption is the one included in the indicated ClientInitKey,
        corresponding to the indicated ciphersuite.  The "add_key_nonce"
        field contains the key and nonce used to encrypt the corresponding
        Add message; if it is not encrypted, then this field MUST be set to
        the null optional value.

        A group member generates this message(Add) by requesting a ClientInitKey
        from the directory for the user to be added, and encoding it into an
        Add message.

        :param user_init_key: the init_key of the user
        :param user_credential: the user credentials
        :return: WelcomeInfoMessage and AddMessage
        """
        # pylint: disable=unexpected-keyword-arg
        welcome: WelcomeInfoMessage = WelcomeInfoMessage(
            epoch=self._context.epoch,
            group_id=self._context.group_id,
            init_secret=self._key_schedule.get_init_secret(),
            interim_transcript_hash=bytes(bytearray(b'\x00') * self._cipher_suite.get_hash_length()),
            key=b'0',
            nounce=b'0',
            tree=[],
            protocol_version=b'0'
        )

        # strip private keys
        for node in self._tree.get_nodes():
            welcome.tree.append(TreeNode(node.get_public_key(), None, None) if node is not None else None)

        # todo: support insert in the middle of a group
        # Pylint currently has a problem with dataclasses
        # pylint: disable=unexpected-keyword-arg
        add: AddMessage = AddMessage(index=self._tree.get_num_leaves(),
                                     init_key=user_init_key,
                                     welcome_info_hash=b'0')

        return welcome, add

    def process_add(self, add_message: AddMessage, private_key=Optional[bytes]) -> None:
        """
        RFC Section 9.2 Add
        https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-9.2

        A group member generates this message by requesting a ClientInitKey
        from the directory for the user to be added, and encoding it into an
        Add message.

        The client joining the group processes Welcome and Add messages
        together as follows:

        o  Prepare a new GroupContext object based on the Welcome message
        o  Process the Add message as an existing member would

        An existing member receiving a Add message first verifies the
        signature on the message, then updates its state as follows:

        o  If the "index" value is equal to the size of the group, increment
          the size of the group, and extend the tree accordingly

        o  Verify the signature on the included ClientInitKey; if the
          signature verification fails, abort

        o  Generate a WelcomeInfo object describing the state prior to the
          add, and verify that its hash is the same as the value of the
          "welcome_info_hash" field

        o  Update the ratchet tree by setting to blank all nodes in the
          direct path of the new node

        o  Set the leaf node in the tree at position "index" to a new node
          containing the public key from the ClientInitKey in the Add
          corresponding to the ciphersuite in use, as well as the credential
          under which the ClientInitKey was signed

        The "update_secret" resulting from this change is an all-zero octet
        string of length Hash.length.

        After processing an Add message, the new member SHOULD send an Update
        immediately to update its key.  This will help to limit the tree
        structure degrading into subtrees, and thus maintain the protocol's
        efficiency.
        :param add_message:
        :param private_key:
        :return:
        """
        # todo: validate stuff
        self._tree.add_leaf(TreeNode(add_message.init_key, private_key, None))

        advance_epoch(self._context, self._key_schedule,
                      bytes(bytearray(b'\x00') * self._cipher_suite.get_hash_length()))

    def update(self, leaf_index: int) -> UpdateMessage:
        """
        RFC Section 9.3 Update
        https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-9.3

        The sender of an Update message creates it in the following way:

        o  Generate a fresh leaf key pair
        o  Compute its direct path in the current ratchet tree

        The "update_secret" resulting from this change is the
        "path_secret[i+1]" derived from the "path_secret[i]" associated to
        the root node.

        :param leaf_index: leaf to update
        :return: UpdateMessage
        """

        # TODO: ACHTUNG ACHTUNG RESEQUENCING
        # DIESE METHODE IST NICHT RESEQUENCING SICHER
        # Gegensätzlich zum RFC müssten wir auch das leaf secret mit versenden, damit wir im resequencing fall
        # nicht unseren tree borken. Gerade erstzen wir das leaf secret sofort, wenn die update nachricht dann
        # resequenced wird ist der updatende client raus. MLSpp von cisco hat das gleiche problem.

        nodes_in_copath = copath(leaf_index * 2, self._tree.get_num_leaves())
        nodes_out: List[DirectPathNode] = []
        # Corresponds to X=path_secret[0]
        path_secret = os.urandom(16)
        # todo: get hash len
        node_secret = hkdf_expand_label(secret=path_secret,
                                        context=self._context,
                                        label=b"node",
                                        cipher_suite=self._cipher_suite)

        self._tree.set_node(node_index=leaf_index * 2, node=TreeNode.from_node_secret(node_secret=node_secret,
                                                                                      cipher_suite=self._cipher_suite))

        # pylint: disable=unexpected-keyword-arg
        nodes_out.append(DirectPathNode(public_key=self._tree.get_node(leaf_index * 2).get_public_key(),
                                        encrypted_path_secret=[]))

        last_path_secret = None
        for conode_index in nodes_in_copath:
            node_index = parent(conode_index, self._tree.get_num_leaves())

            path_secret = hkdf_expand_label(secret=path_secret, context=self._context, label=b"path",
                                            cipher_suite=self._cipher_suite)
            last_path_secret = path_secret

            node_secret = hkdf_expand_label(secret=path_secret, context=self._context, label=b"node",
                                            cipher_suite=self._cipher_suite)

            self._tree.set_node(node_index=node_index,
                                node=TreeNode.from_node_secret(node_secret=node_secret,
                                                               cipher_suite=self._cipher_suite))

            # encrypt the path secret for the nodes in the copath
            resolution: List[int] = resolve(self._tree.get_nodes(), conode_index, self._tree.get_num_leaves())
            ciphers: List[HPKECiphertext] = []
            # todo: This loop must be updated with Issue !6
            # https://git.fh-muenster.de/masterprojekt-mls/implementation/issues/6
            # pylint: disable=unused-variable
            for resolution_node_index in resolution:
                # pylint: disable=unexpected-keyword-arg
                ciphers.append(HPKECiphertext(ephemeral_key=b'0', cipher_text=path_secret))

            # todo: SetupBaseI aus HPKE nutzen https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-9.3
            # todo: Path secret verschlüsseln
            # pylint: disable=unexpected-keyword-arg
            nodes_out.append(DirectPathNode(public_key=self._tree.get_node(node_index).get_public_key(),
                                            encrypted_path_secret=ciphers))

        if len(nodes_in_copath) == 0 and self._tree.get_num_leaves() == 1:
            last_path_secret = path_secret

        if last_path_secret is None:
            raise ValueError()

        advance_epoch(self._context, self._key_schedule, last_path_secret)
        return UpdateMessage(direct_path=nodes_out)

    # pylint: disable=too-many-locals
    def process_update(self, leaf_index: int, message: UpdateMessage) -> None:
        """
        RFC Section 5.5 Synchronizing Views of the Tree
        https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-5.5

        The recipient of an update processes it with the following steps:

        1.  Compute the updated path secrets.

        o Identify a node in the direct path for which the local member
          is in the subtree of the non-updated child.
        o Identify a node in the resolution of the copath node for which
          this node has a private key.
        o Decrypt the path secret for the parent of the copath node
          using the private key from the resolution node.
        o Derive path secrets for ancestors of that node using the
          algorithm described above.
        o The recipient SHOULD verify that the received public keys
          agree with the public keys derived from the new node_secret
          values.

        2.  Merge the updated path secrets into the tree.

        o Replace the public keys for nodes on the direct path with the
          received public keys.
        o For nodes where an updated path secret was computed in step 1,
          compute the corresponding node secret and node key pair and
          replace the values stored at the node with the computed
          values.
        o For all updated nodes, set the list of unmerged leaves to the
          empty list.

        :param leaf_index: leaf node that got updated
        :param message: received updateMessage
        """

        # todo: more sanity checks
        len_local_path = len(direct_path(leaf_index * 2, self._tree.get_num_leaves()))
        len_received_path = len(message.direct_path)
        # the direct path does not include the root or the target node, so we have to add 2 to the expected count
        if len_local_path + 2 != len_received_path:
            raise RuntimeError(
                f"Len of direct path to target leaf is {len_local_path} vs received path of len {len_received_path}")

        if message.direct_path[0].encrypted_path_secret:
            raise RuntimeError()

        # We do not update the tree immediately, as we may need the old secrets to unpack further nodes. We rather
        # store them and apply them after unpacking all nodes.
        nodes_to_update: Dict[int, TreeNode] = {
            leaf_index * 2: TreeNode(message.direct_path[0].public_key, None, None)
        }

        last_node_index = leaf_index * 2
        last_path_secret = None
        for entry in message.direct_path[1:]:
            current_node_index = parent(last_node_index, self._tree.get_num_leaves())

            last_node_sibling_index = sibling(current_node_index, self._tree.get_num_leaves())
            last_node_sibling_resolution = resolve(self._tree.get_nodes(), last_node_sibling_index,
                                                   self._tree.get_num_leaves())

            computed_node: TreeNode = TreeNode(entry.public_key, None, None)
            for resolution_node_index in last_node_sibling_resolution:
                resolution_node = self._tree.get_node(resolution_node_index)
                if not resolution_node.has_private_key():
                    continue

                # todo: decrypt secret here, as soon as it is encrypted
                path_secret: Optional[bytes] = entry.encrypted_path_secret[0].cipher_text
                last_path_secret = path_secret

                node_secret = hkdf_expand_label(secret=path_secret, context=self._context, label=b"node",
                                                cipher_suite=self._cipher_suite)

                computed_node = TreeNode.from_node_secret(
                    node_secret=node_secret,
                    cipher_suite=self._cipher_suite)

                if computed_node.get_public_key() != entry.public_key:
                    raise RuntimeError("Received path secret does not match the received public key.")

                break

            nodes_to_update[current_node_index] = computed_node
            last_node_index = current_node_index

        # apply new nodes
        for index, node in nodes_to_update.items():
            self._tree.set_node(index, node)

        advance_epoch(self._context, self._key_schedule, last_path_secret)
