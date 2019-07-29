from math import ceil
from typing import List, Optional

from libMLS.libMLS.tree_node import TreeNode
from .tree_math import parent


class Tree:

    def __init__(self, nodes: Optional[List[Optional[TreeNode]]] = None):

        if nodes is None:
            self._nodes: List[Optional[TreeNode]] = []
        else:
            self._nodes = nodes

    def __eq__(self, other):
        if not isinstance(other, Tree):
            return False

        if len(other._nodes) != len(self._nodes):
            return False

        # a tree is equal to another tree, if each node ist equal
        for node_index in range(len(self._nodes)):
            if self._nodes[node_index] != other._nodes[node_index]:
                return False

        return True

    def get_num_leaves(self) -> int:
        if len(self._nodes) == 0:
            return 0

        return int(ceil(len(self._nodes) / 2))

    def get_num_nodes(self) -> int:
        return len(self._nodes)

    def get_node(self, index) -> Optional[TreeNode]:

        if index < 0 or index >= len(self._nodes):
            raise IndexError()

        return self._nodes[index]

    def get_nodes(self) -> List[Optional[TreeNode]]:
        return self._nodes

    def add_leaf(self, node: TreeNode, leaf_index: Optional[int] = None) -> None:
        """
        Appends a node to the ratched tree
        @todo: ignores blank tree leaves at the moment (could occur after user removal). These should be populated first
        @todo: path hash
        :param node:
        :return:
        """

        if leaf_index is None:
            leaf_index = self.get_num_leaves()

        node_index = leaf_index*2
        for i in range(node_index-self.get_num_nodes()):
            self._nodes.append(None)

        self._nodes.append(node)

        # blank path to root
        self._blank_path(len(self._nodes) - 1)

    def _blank_path(self, node_index: int) -> None:

        current_index = node_index
        last_index = node_index

        while True:
            current_index = parent(current_index, self.get_num_leaves())

            if current_index == last_index:
                break

            self._nodes[current_index] = None
            last_index = current_index
