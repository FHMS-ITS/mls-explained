import string

from libMLS.libMLS.local_key_store_mock import LocalKeyStoreMock
from libMLS.libMLS.messages import WelcomeInfoMessage, AddMessage, UpdateMessage
from libMLS.libMLS.state import State
from libMLS.libMLS.group_context import GroupContext
from libMLS.libMLS.x25519_cipher_suite import X25519CipherSuite


class Session:

    def __init__(self, state: State, key_store: LocalKeyStoreMock, user_name: string):
        self._state: State = state
        self._key_store = key_store
        self._user_name = user_name

    @classmethod
    def from_welcome(cls, welcome: WelcomeInfoMessage, key_store: LocalKeyStoreMock, user_name: string) -> 'Session':
        context: GroupContext = GroupContext(
            group_id=welcome.group_id,
            epoch=welcome.epoch,
            tree_hash=b'0',
            # todo: interim_transcript_hash aus welcome bedenken
            confirmed_transcript_hash=b'0'
        )

        state = State.from_existing(cipher_suite=X25519CipherSuite(), context=context, nodes=welcome.tree)
        return cls(state, key_store, user_name)

    # todo: Use user_credentials
    @classmethod
    def from_empty(cls, key_store: LocalKeyStoreMock, user_name: string) -> 'Session':

        empty_context: GroupContext = GroupContext(
            group_id=b'0',
            epoch=0,
            tree_hash=b'0',
            confirmed_transcript_hash=b'0'
        )

        public_key: bytes = key_store.fetch_init_key(user_name=user_name)

        state = State.from_empty(
            cipher_suite=X25519CipherSuite(),
            context=empty_context,
            leaf_public=public_key,
            leaf_secret=key_store.get_private_key(public_key))

        return cls(state, key_store, user_name)

    def get_state(self) -> State:
        return self._state

    def add_member(self, user_name: string, user_credentials: bytes) -> (WelcomeInfoMessage, AddMessage):
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

        user_init_key: bytes = self._key_store.fetch_init_key(user_name=user_name)

        if user_init_key is None:
            raise RuntimeError()

        # todo: Verify Keys and Cipher Suite support
        return self._state.add(user_init_key, user_credentials)

        # todo: encrypt welcome message
        # todo: encrypt add message

    def process_add(self, add_message: AddMessage) -> None:

        private_key = self._key_store.get_private_key(add_message.init_key)

        self._state.process_add(add_message=add_message, private_key=private_key)

    def update(self, leaf_index: int) -> UpdateMessage:
        # TODO: ACTHUNG ACHTUNG RESEQUENCING
        # DIESE METHODE IST NICHT RESEQUENCING SICHER
        # Gegensätzlich zum RFC müssten wir auch das leaf secret mit versenden, damit wir im resequencing fall
        # nicht unseren tree borken. Gerade erstzen wir das leaf secret sofort, wenn die update nachricht dann
        # resequenced wird ist der updatende client raus. MLSpp von cisco hat das gleiche problem.

        return self._state.update(leaf_index)

    def process_update(self, leaf_index: int, update_message: UpdateMessage) -> None:
        self._state.process_update(leaf_index=leaf_index, message=update_message)
