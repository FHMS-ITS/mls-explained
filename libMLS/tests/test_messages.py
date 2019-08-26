import os

from libMLS.libMLS.messages import UpdateMessage, DirectPathNode, HPKECiphertext


def test_update_message():
    # pylint: disable=too-many-function-args
    direct_path_node0 = DirectPathNode(os.urandom(32), [])

    # pylint: disable=too-many-function-args
    encrypted_messages11 = HPKECiphertext(b'a' * 32, b'j' * 32)
    # pylint: disable=too-many-function-args
    encrypted_messages12 = HPKECiphertext(os.urandom(32), b'b' * 64)
    # pylint: disable=too-many-function-args
    encrypted_messages13 = HPKECiphertext(os.urandom(32), b'c' * 32)
    # pylint: disable=too-many-function-args
    direct_path_node1 = DirectPathNode(os.urandom(32),
                                       [encrypted_messages11, encrypted_messages12, encrypted_messages13])

    # pylint: disable=too-many-function-args
    encrypted_messages21 = HPKECiphertext(os.urandom(32), b'6' * 64)
    # pylint: disable=too-many-function-args
    direct_path_node2 = DirectPathNode(os.urandom(32), [encrypted_messages21])

    # pylint: disable=too-many-function-args
    encrypted_messages31 = HPKECiphertext(os.urandom(32), b'a' * 128)
    # pylint: disable=too-many-function-args
    encrypted_messages32 = HPKECiphertext(os.urandom(32), b'b' * 256)
    # pylint: disable=too-many-function-args
    encrypted_messages33 = HPKECiphertext(os.urandom(32), b'c' * 512)
    # pylint: disable=too-many-function-args
    encrypted_messages34 = HPKECiphertext(os.urandom(32), b'd' * 1024)
    # pylint: disable=too-many-function-args
    direct_path_node3 = DirectPathNode(os.urandom(32),
                                       [encrypted_messages31, encrypted_messages32, encrypted_messages33,
                                        encrypted_messages34])

    # pylint: disable=too-many-function-args
    direct_path = [direct_path_node0, direct_path_node1, direct_path_node2, direct_path_node3]
    # pylint: disable=too-many-function-args
    message = UpdateMessage(direct_path)

    assert HPKECiphertext.from_bytes(encrypted_messages11.pack()) == encrypted_messages11
    assert DirectPathNode.from_bytes(direct_path_node1.pack()) == direct_path_node1

    assert UpdateMessage.from_bytes(message.pack()) == message
