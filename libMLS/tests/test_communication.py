from libMLS.libMLS.session import Session


def test_session_can_be_created_from_welcome():
    # setup session
    alice_session = Session.from_empty(b'0', b'0')
    welcome, add = alice_session.add_member(b'1', b'1')
    bob_session = Session.from_welcome(welcome)

    # assert add message correctly created
    assert add.index == 1 and add.init_key == b'1'

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

"""
test todo: 
If "index < n" and the leaf node at position "index" is
   not blank, then the recipient MUST reject the Add as malformed.
"""
