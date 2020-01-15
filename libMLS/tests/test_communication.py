import pytest
from libMLS.abstract_application_handler import AbstractApplicationHandler

from libMLS.local_key_store_mock import LocalKeyStoreMock
from libMLS.messages import UpdateMessage, WelcomeInfoMessage, AddMessage
from libMLS.session import Session


def test_key_store_mock_works():
    alice_store = LocalKeyStoreMock('alice')
    alice_store.register_keypair(b'0', b'0')

    bob_store = LocalKeyStoreMock('bob')
    bob_store.register_keypair(b'1', b'1')

    assert bob_store.fetch_init_key('alice') == b'0'
    assert bob_store.get_private_key(b'1') == b'1'


def test_session_can_be_created_from_welcome():
    """
    test todo:
    If "index < n" and the leaf node at position "index" is
       not blank, then the recipient MUST reject the Add as malformed.
    """

    # init user keys
    alice_store = LocalKeyStoreMock('alice')
    alice_store.register_keypair(b'0', b'0')

    bob_store = LocalKeyStoreMock('bob')
    bob_store.register_keypair(b'1', b'1')

    # setup session
    alice_session = Session.from_empty(alice_store, 'alice', 'test')
    welcome, add = alice_session.add_member('bob', b'1')
    bob_session = Session.from_welcome(welcome, bob_store, 'bob')

    # assert add message correctly created
    assert add.index == 1 and add.init_key == b'1'
    # assert bob did not get alice's private key
    for node in welcome.tree:
        assert node.get_private_key() is None

    alice_state = alice_session.get_state()
    bob_state = bob_session.get_state()

    # assert that alice session only contains herself before processing the add
    assert alice_state.get_tree().get_num_nodes() == 1 and alice_state.get_tree().get_num_leaves() == 1
    # assert that bob received the pre-add session tree
    assert alice_state.get_tree() == bob_state.get_tree()

    # assert both group context are equal
    assert alice_state.get_group_context() == bob_state.get_group_context()

    # process adds
    alice_session.process_add(add_message=add)
    bob_session.process_add(add_message=add)

    # assert that both sessions have the same state after adds
    assert alice_state.get_tree().get_num_nodes() == 3 and alice_state.get_tree().get_num_leaves() == 2
    assert bob_state.get_tree().get_num_nodes() == 3 and bob_state.get_tree().get_num_leaves() == 2
    assert alice_state.get_tree() == bob_state.get_tree()

    # compare key schedule secrets
    assert alice_session.get_state().get_key_schedule().get_epoch_secret() == \
           bob_session.get_state().get_key_schedule().get_epoch_secret()


@pytest.mark.dependency(name="test_update_message")
def test_update_message():
    # init user keys
    alice_store = LocalKeyStoreMock('alice')
    alice_store.register_keypair(b'0', b'0')

    bob_store = LocalKeyStoreMock('bob')
    bob_store.register_keypair(b'1', b'1')

    # setup session
    alice_session = Session.from_empty(alice_store, 'alice', 'test')
    welcome, add = alice_session.add_member('bob', b'1')
    bob_session = Session.from_welcome(welcome, bob_store, 'bob')

    alice_session.process_add(add_message=add)
    bob_session.process_add(add_message=add)

    update: UpdateMessage = alice_session.update()

    # assert that this update contains two nodes: The leaf and the root node
    assert len(update.direct_path) == 2

    # assert that the leaf node (node[0]) does not contain an encrypted path secret
    assert update.direct_path[0].encrypted_path_secret == [], "leaf node must not contain an encrypted path secret"
    # assert that the root node (node[1] contains one encrypted path secret for bob
    assert len(update.direct_path[1].encrypted_path_secret) == 1

    bob_session.process_update(0, update)

    alice_tree = alice_session.get_state().get_tree()
    bob_tree = bob_session.get_state().get_tree()

    # assert that the public keys of the nodes are equal
    assert alice_tree == bob_tree

    # assert that the new, shared secret has been distributed
    assert alice_tree.get_node(1).get_private_key() == bob_tree.get_node(1).get_private_key()

    # but make sure that bob does not know alice's private key
    assert bob_tree.get_node(0).get_private_key() is None

    # compare tree hashses
    assert alice_tree.get_tree_hash() == bob_tree.get_tree_hash()

    # compare key schedule secrets
    assert alice_session.get_state().get_key_schedule().get_epoch_secret() == \
           bob_session.get_state().get_key_schedule().get_epoch_secret()


@pytest.mark.dependency(depends=["test_update_message"])
def test_update_message_serialized():
    # init user keys
    alice_store = LocalKeyStoreMock('alice')
    alice_store.register_keypair(b'0', b'0')

    bob_store = LocalKeyStoreMock('bob')
    bob_store.register_keypair(b'1', b'1')

    # setup session
    alice_session = Session.from_empty(alice_store, 'alice', 'test')
    welcome, add = alice_session.add_member('bob', b'1')

    welcome = WelcomeInfoMessage.from_bytes(welcome.pack())
    add = AddMessage.from_bytes(add.pack())
    bob_session = Session.from_welcome(welcome, bob_store, 'bob')

    alice_session.process_add(add_message=add)
    bob_session.process_add(add_message=add)

    update: UpdateMessage = alice_session.update()
    update = UpdateMessage.from_bytes(update.pack())

    # assert that this update contains two nodes: The leaf and the root node
    assert len(update.direct_path) == 2

    # assert that the leaf node (node[0]) does not contain an encrypted path secret
    assert update.direct_path[0].encrypted_path_secret == [], "leaf node must not contain an encrypted path secret"
    # assert that the root node (node[1] contains one encrypted path secret for bob
    assert len(update.direct_path[1].encrypted_path_secret) == 1

    bob_session.process_update(0, update)

    alice_tree = alice_session.get_state().get_tree()
    bob_tree = bob_session.get_state().get_tree()

    # assert that the public keys of the nodes are equal
    assert alice_tree == bob_tree

    # assert that the new, shared secret has been distributed
    assert alice_tree.get_node(1).get_private_key() == bob_tree.get_node(1).get_private_key()

    # but make sure that bob does not know alice's private key
    assert bob_tree.get_node(0).get_private_key() is None


class StubHandler(AbstractApplicationHandler):

    def on_application_message(self, application_data: bytes):
        pass

    def on_group_welcome(self, session):
        pass

    def on_group_member_added(self, group_id: bytes):
        pass


@pytest.mark.dependency(depends=["test_session_can_be_created_from_welcome"])
def test_handshake_processing():
    alice_store = LocalKeyStoreMock('alice')
    alice_store.register_keypair(b'0', b'0')

    bob_store = LocalKeyStoreMock('bob')
    bob_store.register_keypair(b'1', b'1')

    # setup session
    alice_session = Session.from_empty(alice_store, 'alice', 'test')
    welcome, add = alice_session.add_member('bob', b'1')

    welcome = WelcomeInfoMessage.from_bytes(welcome.pack())

    encrypted_add = alice_session.encrypt_handshake_message(add)
    bob_session = Session.from_welcome(welcome, bob_store, 'bob')
    bob_session.process_message(encrypted_add, StubHandler())
    alice_session.process_message(encrypted_add, StubHandler())

    # assert that both sessions have the same state after adds
    assert alice_session.get_state().get_tree().get_num_nodes() == 3
    assert bob_session.get_state().get_tree().get_num_nodes() == 3
