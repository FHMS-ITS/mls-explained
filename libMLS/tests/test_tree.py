from libMLS.libMLS.data_tree_node import DataTreeNode
from libMLS.libMLS.tree import Tree


def test_node_can_be_added_to_empty_tree():
    tree: Tree = Tree()

    assert tree.get_num_nodes() == 0
    tree.add_leaf(DataTreeNode(b'public', None, b'A'))

    assert tree.get_num_nodes() == 1
    assert tree.get_num_leaves() == 1


def test_add_node_blanks_path():
    tree: Tree = Tree()
    tree.add_leaf(DataTreeNode(b'publicA', None, b'A'))
    tree.add_leaf(DataTreeNode(b'publicB', None, b'B'))

    assert tree.get_num_nodes() == 3
    assert tree.get_node(1) is None

    tree.add_leaf(DataTreeNode(b'publicC', None, b'C'))
    assert tree.get_node(3) is None
