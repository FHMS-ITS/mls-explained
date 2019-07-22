from libMLS.libMLS.cipher_suite import CipherSuite
from libMLS.libMLS.data_tree_node import DataTreeNode
from libMLS.libMLS.tree import Tree


class State:

    def __init__(
            self,
            cipher_suite: CipherSuite,
            leaf_secret: bytes,
            credentials: bytes
    ):
        """

        :param cipher_suite:
        """
        # todo: Credentials, private key
        self._epoch: int = 0
        self._cipher_suite: CipherSuite = cipher_suite
        self._init_secret: int = 0  # todo: 0 is probably a bad init secret
        self._tree: Tree = Tree()
        self._tree.add_leaf(DataTreeNode(leaf_secret, None, credentials))

    def add(self, user_init_key: bytes, user_credential: bytes):
        self._tree.add_leaf(DataTreeNode(user_init_key, None, user_credential))

