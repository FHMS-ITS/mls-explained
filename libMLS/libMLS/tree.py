from math import ceil
from typing import List, Optional

from libMLS.libMLS.tree_node import TreeNode
from .tree_math import parent, level, root, left, right, is_leaf
from .cipher_suite import CipherSuite
from .tree_node import LeafNodeHashInput, LeafNodeInfo, ParentNodeHashInput
from .x25519_cipher_suite import X25519CipherSuite

class Tree:

    def __init__(self, cipher_suite: CipherSuite = X25519CipherSuite(), nodes: Optional[List[Optional[TreeNode]]] = None):
        self.cipher_suite = cipher_suite

        if nodes is None:
            self._nodes: List[Optional[TreeNode]] = []
        else:
            self._nodes = nodes

    def __eq__(self, other):
        if not isinstance(other, Tree):
            return False

        if other.get_num_nodes() != len(self._nodes):
            return False

        # a tree is equal to another tree, if each node ist equal
        for node_index in range(len(self._nodes)):
            if self._nodes[node_index] != other.get_node(node_index):
                return False

        return True

    def get_num_leaves(self) -> int:
        if not self._nodes:
            return 0

        return int(ceil(len(self._nodes) / 2))

    def get_num_nodes(self) -> int:
        return len(self._nodes)

    def get_node(self, index) -> Optional[TreeNode]:

        if index < 0 or index >= len(self._nodes):
            raise IndexError()

        return self._nodes[index]

    def get_root(self) -> TreeNode:
        if self._nodes is None:
            return None

        return root(self.get_num_leaves())

    def get_nodes(self) -> List[Optional[TreeNode]]:
        return self._nodes

    def set_node(self, node_index: int, node: Optional[TreeNode]):
        self._nodes[node_index] = node

    def add_leaf(self, node: TreeNode, leaf_index: Optional[int] = None) -> None:
        """
        Appends a node to the ratched tree
        @todo: ignores blank tree leaves at the moment (could occur after user removal). These should be populated first
        @todo: path hash
        :param node:
        :param leaf_index:
        :return:
        """

        if leaf_index is None:
            leaf_index = self.get_num_leaves()

        node_index = leaf_index * 2
        # pylint: disable=unused-variable
        for i in range(node_index - self.get_num_nodes()):
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

    def get_tree_hash(self):
        if self.get_root() is None:
            raise IndexError()

        return self._get_node_hash(node_index=self.get_root())

    def _get_node_hash(self, node_index):
        if is_leaf(node_index):
            return self._get_leaf_hash(node_index)
        return self._get_intermediate_hash(node_index)

    def _get_leaf_hash(self, node_index):

        if self._nodes[node_index]:
            node_info = LeafNodeInfo(self._nodes[node_index].get_public_key(),
                                     self._nodes[node_index].get_credentials())
        else:
            node_info = None

        hash_input = LeafNodeHashInput(node_info)

        node_hash = self.cipher_suite.get_hash()
        node_hash.update(bytes(hash_input))
        return node_hash.finalize()

    def _get_intermediate_hash(self, node_index):
        left_node = left(node_index)
        right_node = right(node_index, self.get_num_leaves())

        if self._nodes[node_index]:
            hash_input = ParentNodeHashInput(self._nodes[node_index].get_public_key(),
                                             self._get_node_hash(left_node),
                                             self._get_node_hash(right_node))
        else:
            hash_input = ParentNodeHashInput(None,
                                             self._get_node_hash(left_node),
                                             self._get_node_hash(right_node))

        node_hash = self.cipher_suite.get_hash()
        node_hash.update(bytes(hash_input))
        return node_hash.finalize()

    def __str__(self):

        out_string: str = 'Tree:\n'
        for node_index in range(len(self._nodes)):
            out_string += f'[{node_index}] ' + ('\t' * level(node_index)) + str(self._nodes[node_index]) + '\n'

        return out_string
