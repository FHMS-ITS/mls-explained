import string
from typing import Optional

from libMLS.libMLS.abstract_application_handler import AbstractApplicationHandler
from libMLS.libMLS.local_key_store_mock import LocalKeyStoreMock
from libMLS.libMLS.messages import WelcomeInfoMessage, AddMessage, UpdateMessage, MLSCiphertext, ContentType, \
    MLSSenderData, MLSPlaintext, MLSPlaintextApplicationData, MLSPlaintextHandshake, GroupOperation
from libMLS.libMLS.state import State
from libMLS.libMLS.group_context import GroupContext
from libMLS.libMLS.x25519_cipher_suite import X25519CipherSuite


class Session:

    def __init__(self, state: State, key_store: LocalKeyStoreMock, user_name: string, user_index: Optional[int]):
        self._state: State = state
        self._key_store = key_store
        self._user_name = user_name
        self._user_index: Optional[int] = user_index

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
        state.get_key_schedule().set_init_secret(welcome.init_secret)
        return cls(state, key_store, user_name, user_index=None)

    # todo: Use user_credentials
    @classmethod
    def from_empty(cls, key_store: LocalKeyStoreMock, user_name: string, group_name: string) -> 'Session':

        empty_context: GroupContext = GroupContext(
            group_id=group_name.encode('ascii'),
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

        return cls(state, key_store, user_name, user_index=0)

    def get_state(self) -> State:
        return self._state

    def add_member(self, user_name: string, user_credentials: bytes) -> (WelcomeInfoMessage, AddMessage):
        """
        From draft-ietf-mls-protocol-07:
        In order to add a new member to the group, an existing member of the
        group must take two actions:
        1.  Send a Welcome message to the new member
        2.  Send an Add message to the group (including the new member)
        :param user_credentials:
        :param user_name:
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

        if private_key is not None:
            # we possess the private key for this given init_key
            if self._user_index is not None:
                # if we are not new to the group ( i.e. already know our index), this cant be right
                raise RuntimeError()
            self._user_index = add_message.index

        self._state.process_add(add_message=add_message, private_key=private_key)

    def update(self) -> UpdateMessage:
        # TODO: ACTHUNG ACHTUNG RESEQUENCING
        # DIESE METHODE IST NICHT RESEQUENCING SICHER
        # Gegensätzlich zum RFC müssten wir auch das leaf secret mit versenden, damit wir im resequencing fall
        # nicht unseren tree borken. Gerade erstzen wir das leaf secret sofort, wenn die update nachricht dann
        # resequenced wird ist der updatende client raus. MLSpp von cisco hat das gleiche problem.

        return self._state.update(self._user_index)

    def process_update(self, leaf_index: int, update_message: UpdateMessage) -> None:
        # todo: We still do not know which leaf to update with this add message
        self._state.process_update(leaf_index=leaf_index, message=update_message)

    def encrypt_application_message(self, message: str) -> MLSCiphertext:

        # pylint: disable=unexpected-keyword-arg
        sender_data = MLSSenderData(sender=self._user_index, generation=0)

        # pylint: disable=unexpected-keyword-arg
        out = MLSCiphertext(
            group_id=self._state.get_group_context().group_id,
            epoch=self._state.get_group_context().epoch,
            content_type=ContentType.APPLICATION,
            sender_data_nounce=b'0',
            encrypted_sender_data=sender_data.pack(),
            ciphertext=message.encode('UTF-8')
        )

        return out

    def encrypt_handshake_message(self, group_op: GroupOperation) -> MLSCiphertext:

        # todo: confirmation
        # pylint: disable=unexpected-keyword-arg
        handshake = MLSPlaintextHandshake(confirmation=0, group_operation=group_op)

        # pylint: disable=unexpected-keyword-arg
        plaintext = MLSPlaintext(
            group_id=self._state.get_group_context().group_id,
            epoch=self._state.get_group_context().epoch,
            content_type=ContentType.HANDSHAKE,
            sender=self._user_index,
            signature=b'0',
            content=handshake
        )

        # todo: encrypt stuff
        # pylint: disable=unexpected-keyword-arg
        encrypted = MLSCiphertext(
            content_type=ContentType.HANDSHAKE,
            group_id=plaintext.group_id,
            epoch=plaintext.epoch,
            sender_data_nounce=b'0',
            encrypted_sender_data=b'0',
            ciphertext=handshake.pack()
        )

        return encrypted

    def _process_handshake(self, message: MLSCiphertext, handler: AbstractApplicationHandler) -> None:
        # todo: Usually, this would have to be decrypted right here
        plain = MLSPlaintext.from_bytes(message.ciphertext)

        if not plain.verify_metadata_from_cipher(message):
            raise RuntimeError()

        if not isinstance(plain.content, MLSPlaintextHandshake):
            raise RuntimeError()

        # todo: We most certainly have to perform more checks here
        operation: GroupOperation = plain.content.group_operation

        if isinstance(operation.operation, AddMessage):
            self.process_add(operation.operation)
            handler.on_group_member_added(plain.group_id)
        elif isinstance(operation.operation, UpdateMessage):
            # todo: leaf??????
            # self.process_update(operation.operation)
            raise RuntimeError()
        else:
            raise RuntimeError()

    # pylint: disable=no-self-use
    def _process_application(self, message: MLSCiphertext, handler: AbstractApplicationHandler) -> None:
        # todo: Usually, this would have to be decrypted right here
        plain = MLSPlaintext.from_bytes(message.ciphertext)

        if not plain.verify_metadata_from_cipher(message):
            raise RuntimeError()

        if not isinstance(plain.content, MLSPlaintextApplicationData):
            raise RuntimeError()

        handler.on_application_message(plain.content.application_data)

    # pylint: disable=no-self-use
    def process_message(self, message: MLSCiphertext, handler: AbstractApplicationHandler) -> None:
        if message.content_type == ContentType.APPLICATION:
            self._process_application(message=message, handler=handler)
        elif message.content_type == ContentType.HANDSHAKE:
            self._process_handshake(message=message, handler=handler)
        else:
            raise RuntimeError()

    @staticmethod
    def get_groupid_from_cipher(data: bytes) -> bytes:
        return MLSCiphertext.from_bytes(data).group_id
