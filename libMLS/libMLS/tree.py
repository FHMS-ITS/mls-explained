from math import ceil
from typing import List, Optional
from .tree_math import parent

from libMLS.libMLS.abstract_tree_node import AbstractTreeNode


class Tree:

    def __init__(self):
        self._nodes: List[Optional[AbstractTreeNode]] = []

    def get_num_leaves(self) -> int:
        if len(self._nodes) == 0:
            return 0

        return int(ceil(len(self._nodes) / 2))

    def get_num_nodes(self) -> int:
        return len(self._nodes)

    def get_node(self, index) -> Optional[AbstractTreeNode]:

        if index < 0 or index >= len(self._nodes):
            raise IndexError()

        return self._nodes[index]

    def add_leaf(self, node: AbstractTreeNode) -> None:
        """
        Appends a node to the ratched tree
        @todo: ignores blank tree leaves at the moment (could occur after user removal). These should be populated first
        @todo: path hash
        :param node:
        :return:
        """

        if len(self._nodes) != 0:
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
