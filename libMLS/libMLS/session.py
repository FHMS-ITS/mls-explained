import os

from libMLS.libMLS.messages import WelcomeInfoMessage, AddMessage, UpdateMessage
from libMLS.libMLS.state import State, GroupContext
from libMLS.libMLS.x25519_cipher_suite import X25519CipherSuite


class Session:

    def __init__(self, state: State):
        self._state: State = state

    @classmethod
    def from_welcome(cls, welcome: WelcomeInfoMessage) -> 'Session':
        context: GroupContext = GroupContext(
            group_id=welcome.group_id,
            epoch=welcome.epoch,
            tree_hash=b'0',
            confirmed_transcript_hash=b'0'
        )

        state = State.from_existing(cipher_suite=X25519CipherSuite(), context=context, nodes=welcome.tree)
        return cls(state)

    @classmethod
    def from_empty(cls, user_init_key: bytes, user_credentials: bytes) -> 'Session':
        empty_context: GroupContext = GroupContext(
            group_id=b'0',
            epoch=0,
            tree_hash=b'0',
            confirmed_transcript_hash=b'0'
        )
        state = State.from_empty(cipher_suite=X25519CipherSuite(), context=empty_context, leaf_secret=user_init_key)
        return cls(state)

    def get_state(self) -> State:
        return self._state

    def add_member(self, user_init_key: bytes, user_credential: bytes) -> (WelcomeInfoMessage, AddMessage):
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
        return self._state.add(user_init_key, user_credential)

        # todo: Build encrypt welcome message
        # todo: Build encrypt add message

    def process_add(self, add_message: AddMessage) -> None:
        self._state.process_add(add_message=add_message)

    def update(self, leaf_index: int) -> UpdateMessage:
        # TODO: ACTHUNG ACHTUNG RESEQUENCING
        # DIESE METHODE IST NICHT RESEQUENCING SICHER
        # Gegensätzlich zum RFC müssten wir auch das leaf secret mit versenden, damit wir im resequencing fall
        # nicht unseren tree borken. Gerade erstzen wir das leaf secret sofort, wenn die update nachricht dann
        # resequenced wird ist der updatende client raus. MLSpp von cisco hat das gleiche problem.

        return self._state.update(leaf_index)

    def process_update(self, update_message: UpdateMessage) -> None:
        pass
