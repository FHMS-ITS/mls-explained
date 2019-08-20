# The largest power of 2 less than n.Equivalent to:
# int(math.floor(math.log(x, 2)))
from typing import List


def log2(number: int):
    if number == 0:
        return 0

    k = 0
    while (number >> k) > 0:
        k += 1
    return k - 1


def level(node_index: int):
    """
    The level of a node in the tree.  Leaves are level 0, their
    parents are level 1, etc.  If a node's children are at different
    level, then its level is the max level of its children plus one.
    :param node_index:
    :return:
    """
    if node_index & 0x01 == 0:
        return 0

    k = 0
    while ((node_index >> k) & 0x01) == 1:
        k += 1
    return k


def node_width(num_leaves: int):
    """
    The number of nodes needed to represent a tree with n leaves
    :param num_leaves:
    :return:
    """
    return 2 * (num_leaves - 1) + 1


def root(num_nodes: int) -> int:
    """
    The index of the root node of a tree with n leaves
    :param num_nodes:
    :return:
    """
    width = node_width(num_nodes)
    return (1 << log2(width)) - 1


def left(node_index: int) -> int:
    """
    The left child of an intermediate node.  Note that because the
    tree is left-balanced, there is no dependency on the size of the
    tree.  The child of a leaf node is itself.
    :param node_index:
    :return:
    """
    node_level = level(node_index)
    if node_level == 0:
        return node_index

    return node_index ^ (0x01 << (node_level - 1))


def right(node_index: int, num_leaves: int) -> int:
    """
    The right child of an intermediate node.  Depends on the size of
    the tree because the straightforward calculation can take you
    beyond the edge of the tree.  The child of a leaf node is itself.
    :param node_index:
    :param num_leaves:
    :return:
    """
    node_level = level(node_index)
    if node_level == 0:
        return node_index

    right_index = node_index ^ (0x03 << (node_level - 1))
    while right_index >= node_width(num_leaves):
        right_index = left(right_index)
    return right_index


def parent_step(node_index: int):
    """
    The immediate parent of a node.  May be beyond the right edge of
    the tree.
    :param node_index:
    :return:
    """
    node_level = level(node_index)
    # pylint: disable=invalid-name
    b = (node_index >> (node_level + 1)) & 0x01
    return (node_index | (1 << node_level)) ^ (b << (node_level + 1))


def parent(node_index: int, num_nodes: int):
    """
    The parent of a node.  As with the right child calculation, have
    to walk back until the parent is within the range of the tree.
    :param node_index:
    :param num_nodes:
    :return:
    """
    if node_index == root(num_nodes):
        return node_index

    parent_index = parent_step(node_index)
    while parent_index >= node_width(num_nodes):
        parent_index = parent_step(parent_index)
    return parent_index


def sibling(node_index: int, num_nodes: int):
    """
    The other child of the node's parent.  Root's sibling is itself.
    :param node_index:
    :param num_nodes:
    :return:
    """
    parent_index = parent(node_index, num_nodes)
    if node_index < parent_index:
        return right(parent_index, num_nodes)
    if node_index > parent_index:
        return left(parent_index)

    return parent_index


def direct_path(node_index: int, num_nodes: int) -> List[int]:
    """
    The direct path of a node, ordered from the root
    down, not including the root or the terminal node
    :param node_index:
    :param num_nodes:
    :return:
    """
    path = []
    parent_index = parent(node_index, num_nodes)
    root_index = root(num_nodes)
    while parent_index != root_index:
        path.append(parent_index)
        parent_index = parent(parent_index, num_nodes)
    return path


def copath(nodex_index, num_leaves):
    """
    The copath of the node is the siblings of the nodes on its direct
    path (including the node itself)
    :param nodex_index:
    :param num_leaves:
    :return:
    """
    path = direct_path(nodex_index, num_leaves)
    if nodex_index != sibling(nodex_index, num_leaves):
        path.append(nodex_index)

    return [sibling(y, num_leaves) for y in path]


def frontier(num_leaves: int):
    """
    Frontier is is the list of full subtrees, from left to right.  A
    balance binary tree with n leaves has a full subtree for every
    power of two where n has a bit set, with the largest subtrees
    furthest to the left.  For example, a tree with 11 leaves has full
    subtrees of size 8, 2, and 1.
    :param num_leaves:
    :return:
    """
    # pylint: disable=invalid-name
    st = [1 << k for k in range(log2(num_leaves) + 1) if num_leaves & (1 << k) != 0]
    st = reversed(st)

    base = 0
    # pylint: disable=invalid-name
    f = []
    for size in st:
        f.append(root(size) + base)
        base += 2 * size
    return f


def leaves(num_nodes: int):
    """
    Leaves are in even-numbered nodes
    :param num_nodes:
    :return:
    """
    return [2 * i for i in range(num_nodes)]


def number_of_leaves(num_nodes: int):
    return len(list(range(0, num_nodes, 2)))


def is_leaf(node_index: int):
    """
    Checks if given node is a leaf
    :param node_index:
    :return:
    """
    return node_index % 2 == 0


def resolve(tree: List, node_index: int, num_leaves: int) -> List[int]:
    """
    The resolution of a node is the collection of non-blank
    descendants of this node.  Here the tree is represented by a list
    of nodes, where blank nodes are represented by None
    :param tree:
    :param node_index:
    :param num_leaves:
    :return:
    """
    if tree[node_index] is not None:
        return [node_index]

    if level(node_index) == 0:
        return []
    left_nodes = resolve(tree, left(node_index), num_leaves)
    right_nodes = resolve(tree, right(node_index, num_leaves), num_leaves)
    return left_nodes + right_nodes
