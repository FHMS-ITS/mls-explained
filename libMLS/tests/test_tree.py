from libMLS.libMLS.tree_node import TreeNode
from libMLS.libMLS.tree import Tree
from libMLS.libMLS.x25519_cipher_suite import X25519CipherSuite


def test_node_can_be_added_to_empty_tree():
    tree: Tree = Tree(cipher_suite=X25519CipherSuite())

    assert tree.get_num_nodes() == 0
    tree.add_leaf(TreeNode(b'public', None, b'A'))

    assert tree.get_num_nodes() == 1
    assert tree.get_num_leaves() == 1


def test_add_node_blanks_path():
    tree: Tree = Tree(cipher_suite=X25519CipherSuite())
    tree.add_leaf(TreeNode(b'publicA', None, b'A'))
    tree.add_leaf(TreeNode(b'publicB', None, b'B'))

    assert tree.get_num_nodes() == 3
    assert tree.get_node(1) is None

    tree.add_leaf(TreeNode(b'publicC', None, b'C'))
    assert tree.get_node(3) is None


def test_get_leaf_count():
    tree: Tree = Tree(cipher_suite=X25519CipherSuite())

    for should_be in range(11):
        assert tree.get_num_leaves() == should_be
        tree.add_leaf(TreeNode(b'public', None, b'node'))


def test_get_hash_one_node():
    tree: Tree = Tree(cipher_suite=X25519CipherSuite())

    assert tree.get_num_nodes() == 0
    tree.add_leaf(TreeNode(b'public', None, b'A'))

    assert tree.get_num_nodes() == 1
    assert tree.get_num_leaves() == 1

    assert tree.get_tree_hash() == \
           b'\xa7^V&\xc2\x80\xcdW\x9dfB\xc4\xb0\t\xd8\xc0\xc9\x87s\n\xb4\xd97\xf7$:\x83\xa1\xe7=\xcb\\'


def test_tree_hash_changes_when_adding_nodes():
    tree: Tree = Tree(cipher_suite=X25519CipherSuite())

    assert tree.get_num_nodes() == 0
    tree.add_leaf(TreeNode(b'public', None, b'A'))

    assert tree.get_num_nodes() == 1
    assert tree.get_num_leaves() == 1

    assert tree.get_tree_hash() == \
           b'\xa7^V&\xc2\x80\xcdW\x9dfB\xc4\xb0\t\xd8\xc0\xc9\x87s\n\xb4\xd97\xf7$:\x83\xa1\xe7=\xcb\\'

    tree.add_leaf(TreeNode(b'public', None, b'B'))
    assert tree.get_tree_hash() == \
           b'\xdb"\xb4H\x94\x10\xff\x17gY\x0c\n\xa2!\xeb\x10BT^\x97\x0b\x0bcfJ\xc9\xb0-\x98\xfe\xd2\x90'

    tree.add_leaf(TreeNode(b'public', None, b'C'))
    assert tree.get_tree_hash() == \
           b'.\xe2\xa3\x865\xdd\xc87\xf1xk/\x88VK)\x03\xc0\\\xda\x1ey_\\2\xd3y\xd2\xae\xdb\xc7Y'


def test_trees_have_different_hashes_when_content_different():
    tree1: Tree = Tree(cipher_suite=X25519CipherSuite())
    tree2: Tree = Tree(cipher_suite=X25519CipherSuite())

    tree1.add_leaf(TreeNode(b'public', None, b'A'))
    tree2.add_leaf(TreeNode(b'public_key', None, b'A'))

    assert tree1.get_tree_hash() != tree2.get_tree_hash()

    tree1.add_leaf(TreeNode(b'public', None, b'B'))
    tree2.add_leaf(TreeNode(b'public', None, b'B'))

    assert tree1.get_tree_hash() != tree2.get_tree_hash()


def test_tree_hash_with_blank_leaf():
    tree: Tree = Tree(cipher_suite=X25519CipherSuite())

    assert tree.get_num_nodes() == 0

    tree.add_leaf(TreeNode(b'publicA', None, b'A'))
    tree.add_leaf(None)

    assert tree.get_tree_hash() == \
           b'O4X\x84\xf4\xda\xed/\x94\xfd\x1e\xb9\xe5\xea\xf2?\xcd\x8a\x10\x1b~_\xf6L\xff\xa7\xf2\xbe%\x1d\xd9\xe1'


def test_tree_hash_with_blank_intermediate():
    tree: Tree = Tree(cipher_suite=X25519CipherSuite())

    assert tree.get_num_nodes() == 0

    tree.add_leaf(TreeNode(b'public', None, b'A'))
    tree.add_leaf(None)
    tree.add_leaf(TreeNode(b'public', None, b'B'))

    tree.set_node(2, None)

    assert tree.get_tree_hash() == \
           b't}\xf5\x07\x80_\xfdu\x1d\xdd\xbf\xb8d~\xe0\xca,\xa2\xbe\xactl\x02\xc8\xb4\xf4]]\x91\xb1C~'
