from libMLS.libMLS.data_tree_node import DataTreeNode
from libMLS.libMLS.state import State
from libMLS.libMLS.x25519_cipher_suite import X25519CipherSuite


class Session:

    def __init__(self, user_init_key: bytes, user_crendtials: bytes):
        self._state = State(X25519CipherSuite(), user_init_key, user_crendtials)

    def add_member(self, user_init_key: bytes, user_credential: bytes):
        """
        From draft-ietf-mls-protocol-07:
        In order to add a new member to the group, an existing member of the
        group must take two actions:
        1.  Send a Welcome message to the new member
        2.  Send an Add message to the group (including the new member)
        :param user_init_key:
        :param user_credential:
        :return:
        """
        # todo: Verify Keys and Cipher Suite support
        self._state.add(user_init_key, user_credential)

        # todo: Build welcome message
        # todo: Build add message
