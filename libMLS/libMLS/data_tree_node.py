from typing import Optional

from libMLS.libMLS.abstract_tree_node import AbstractTreeNode


class DataTreeNode(AbstractTreeNode):

    def __init__(self, public_key: bytes, private_key: Optional[bytes] = None, credential: Optional[bytes] = None):
        super().__init__()
        self._public_key: bytes = public_key
        self._private_key: Optional[bytes] = private_key
        self._credential: Optional[bytes] = credential
