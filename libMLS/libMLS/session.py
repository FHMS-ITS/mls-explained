from libMLS.libMLS.data_tree_node import DataTreeNode
from libMLS.libMLS.tree import Tree


class Session:

    def __init__(self):
        self._tree = Tree()

    def add_member(self, user_init_key: bytes, user_credential: bytes):
        self._tree.add_leaf(DataTreeNode(user_init_key, None, user_credential))



