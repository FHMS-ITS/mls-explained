from math import ceil
from typing import List, Optional

from libMLS.tree_node import TreeNode
from .tree_math import parent, level, root, left, right, is_leaf
from .cipher_suite import CipherSuite
from .tree_node import LeafNodeHashInput, LeafNodeInfo, ParentNodeHashInput


class Tree:
    """
    RFC Section 5.2 Ratchet Tree Nodes
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-5.2

    A particular instance of a ratchet tree is based on the following
    cryptographic primitives, defined by the ciphersuite in use:

        o  An HPKE ciphersuite, which specifies a Key Encapsulation Method
           (KEM), an AEAD encryption scheme, and a hash function
        o  A Derive-Key-Pair function that produces an asymmetric key pair
           for the specified KEM from a symmetric secret, using the specified
           hash function.
    """

    def __init__(self, cipher_suite: CipherSuite, nodes: Optional[List[Optional[TreeNode]]] = None):
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

    def deep_eq(self, other) -> bool:
        if not self == other:
            return False

        for node, index in self._nodes:
            if not node.deep_eq(other.get_node(index)):
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

    def get_root(self) -> Optional[TreeNode]:
        if self._nodes is None:
            return None

        return self._nodes[self.get_root_index()]

    def get_root_index(self):
        return root(self.get_num_leaves())

    def get_nodes(self) -> List[Optional[TreeNode]]:
        return self._nodes

    def set_node(self, node_index: int, node: Optional[TreeNode]):
        self._nodes[node_index] = node

    def add_leaf(self, node: TreeNode, leaf_index: Optional[int] = None) -> None:
        """
        Appends a ratchetTreeNode to the ratchetTree
        @todo: ignores blank tree leaves at the moment (could occur after user removal). These should be populated first
        @todo: path hash
        :param node: the ratchetTreeNode which should be added to the ratchetTree
        :param leaf_index: index where the leaf should be added
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
        """
        RFC Section 5.2 Ratchet Tree Nodes
        https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-5.2

        A node in the tree may also be _blank_, indicating that no value is present at that node.

        This is a helper function, that blanks a path from a node to the root node

        :param node_index: index of the ratchetTreeNode which path should be blanked
        """
        current_index = node_index
        last_index = node_index

        while True:
            current_index = parent(current_index, self.get_num_leaves())

            if current_index == last_index:
                break

            self._nodes[current_index] = None
            last_index = current_index

    def get_tree_hash(self) -> bytes:
        """
        RFC Section 6.3 Tree Hashes
        https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-6.3

        To allow group members to verify that they agree on the cryptographic
        state of the group, this section defines a scheme for generating a
        hash value that represents the contents of the group's ratchet tree
        and the members' credentials.

        :return: treeHash
        """
        return self._get_node_hash(node_index=self.get_root_index())

    def _get_node_hash(self, node_index: int) -> bytes:
        """
        The hash of a node is determined in get_leaf_hash if the node is a leaf
        or else in get_intermediate_hash if the node has children

        :param node_index: index of the ratchetTreeNode that should be hashed
        :return: hash of ratchetTreeNode
        """
        if is_leaf(node_index):
            return self._get_leaf_hash(node_index)
        return self._get_intermediate_hash(node_index)

    def _get_leaf_hash(self, node_index) -> bytes:
        """
        RFC Section 6.3 Tree Hashes
        https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-6.3

        The hash of a leaf node is the hash of a "LeafNodeHashInput" object.

        :param node_index: index of the ratchetTreeNode that should be hashed
        :return: hash of ratchetTreeNode
        """
        if self._nodes[node_index]:
            node_info = LeafNodeInfo(self._nodes[node_index].get_public_key(),
                                     self._nodes[node_index].get_credentials())
        else:
            node_info = None

        hash_input = LeafNodeHashInput(node_info)

        node_hash = self.cipher_suite.get_hash()
        node_hash.update(bytes(hash_input))
        return node_hash.finalize()

    def _get_intermediate_hash(self, node_index: int) -> bytes:
        """
        RFC Section 6.3 Tree Hashes
        https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-6.3

        Likewise, the hash of a parent node (including the root) is the hash
        of a "ParentNodeHashInput" struct.

        :param node_index: index of the ratchetTreeNode that should be hashed
        :return: hash of ratchetTreeNode
        """
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
