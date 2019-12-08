# pylint: disable=unexpected-keyword-arg,too-many-function-args
import os

import pytest

from libMLS.libMLS.messages import UpdateMessage, DirectPathNode, HPKECiphertext, WelcomeInfoMessage, AddMessage, \
    MLSCiphertext, ContentType, MLSPlaintext, MLSPlaintextHandshake, GroupOperation, GroupOperationType
from libMLS.libMLS.tree_node import TreeNode


def test_update_message():
    direct_path_node0 = DirectPathNode(os.urandom(32), [])

    encrypted_messages11 = HPKECiphertext(b'a' * 32, b'j' * 32)

    encrypted_messages12 = HPKECiphertext(os.urandom(32), b'b' * 64)

    encrypted_messages13 = HPKECiphertext(os.urandom(32), b'c' * 32)

    direct_path_node1 = DirectPathNode(os.urandom(32),
                                       [encrypted_messages11, encrypted_messages12, encrypted_messages13])

    encrypted_messages21 = HPKECiphertext(os.urandom(32), b'6' * 64)

    direct_path_node2 = DirectPathNode(os.urandom(32), [encrypted_messages21])

    encrypted_messages31 = HPKECiphertext(os.urandom(32), b'a' * 128)

    encrypted_messages32 = HPKECiphertext(os.urandom(32), b'b' * 256)

    encrypted_messages33 = HPKECiphertext(os.urandom(32), b'c' * 512)

    encrypted_messages34 = HPKECiphertext(os.urandom(32), b'd' * 1024)

    direct_path_node3 = DirectPathNode(os.urandom(32),
                                       [encrypted_messages31, encrypted_messages32, encrypted_messages33,
                                        encrypted_messages34])

    direct_path = [direct_path_node0, direct_path_node1, direct_path_node2, direct_path_node3]

    message = UpdateMessage(direct_path)

    assert HPKECiphertext.from_bytes(encrypted_messages11.pack()) == encrypted_messages11
    assert DirectPathNode.from_bytes(direct_path_node1.pack()) == direct_path_node1

    assert UpdateMessage.from_bytes(message.pack()) == message


def test_tree_node():
    cases = [
        TreeNode(public_key=b'a' * 32),
        TreeNode(public_key=b'b' * 32, private_key=b'b' * 32),
        TreeNode(public_key=b'c' * 32, credentials=b'c' * 32),
        TreeNode(public_key=b'd' * 32, private_key=b'd' * 32, credentials=b'd' * 32),
    ]

    for case in cases:
        assert case == TreeNode.from_bytes(case.pack())


def test_welcome_info_message():
    # pylint: disable=unexpected-keyword-arg
    message = WelcomeInfoMessage(
        protocol_version=b'13377331',
        group_id=b'00000001',
        epoch=42,
        tree=[],
        interim_transcript_hash=b'a' * 32,
        init_secret=b'b' * 32,
        key=b'c' * 32,
        nounce=b'd' * 32
    )

    assert WelcomeInfoMessage.from_bytes(message.pack()) == message

    tree = [
        TreeNode(public_key=b'a' * 32),
        TreeNode(public_key=b'b' * 32, private_key=b'b' * 32),
        TreeNode(public_key=b'c' * 32, credentials=b'c' * 32)
    ]

    message.tree = tree
    assert WelcomeInfoMessage.from_bytes(message.pack()) == message


@pytest.mark.dependency(name="test_add_message")
def test_add_message():
    # pylint: disable=unexpected-keyword-arg
    message = AddMessage(index=1337, init_key=os.urandom(32), welcome_info_hash=os.urandom(32))

    assert AddMessage.from_bytes(message.pack()) == message


def test_ciphertext_message():
    # pylint: disable=unexpected-keyword-arg
    message = MLSCiphertext(
        group_id=b'helloworld',
        epoch=1337,
        content_type=ContentType.HANDSHAKE,
        sender_data_nounce=b'steffensoddemann',
        encrypted_sender_data=b'mepmep',
        ciphertext=b'topsecrit'
    )

    assert MLSCiphertext.from_bytes(message.pack()) == message


@pytest.mark.dependency(name="test_plaintext_message", depends=[test_add_message])
def test_plaintext_message():
    add_message = AddMessage(index=1337, init_key=os.urandom(32), welcome_info_hash=os.urandom(32))
    group_op = GroupOperation(msg_type=GroupOperationType.ADD, operation=add_message)
    handshake = MLSPlaintextHandshake(confirmation=12, group_operation=group_op)

    message = MLSPlaintext(
        group_id=b'helloworld',
        epoch=1337,
        content_type=ContentType.HANDSHAKE,
        sender=42,
        signature=b'steffensoddemann',
        content=handshake
    )

    assert MLSPlaintext.from_bytes(message.pack()) == message
