import string
from typing import Optional

from libMLS.abstract_application_handler import AbstractApplicationHandler
from libMLS.abstract_keystore import AbstractKeystore
from libMLS.group_context import GroupContext
from libMLS.messages import WelcomeInfoMessage, AddMessage, UpdateMessage, MLSCiphertext, ContentType, \
    MLSSenderData, MLSPlaintext, MLSPlaintextApplicationData, MLSPlaintextHandshake, GroupOperation
from libMLS.state import State
from libMLS.x25519_cipher_suite import X25519CipherSuite


class Session:

    def __init__(self, state: State, key_store: AbstractKeystore, user_name: string, user_index: Optional[int]):
        self._state: State = state
        self._key_store = key_store
        self._user_name = user_name
        self._user_index: Optional[int] = user_index

    @classmethod
    def from_welcome(cls, welcome: WelcomeInfoMessage, key_store: AbstractKeystore, user_name: string) -> 'Session':
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
    def from_empty(cls, key_store: AbstractKeystore, user_name: string, group_name: string) -> 'Session':
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
        """
        RFC 9.2 Add
        https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-9.2

        The client joining the group processes Welcome and Add messages
        together as follows:

        o  Prepare a new GroupContext object based on the Welcome message
        o  Process the Add message as an existing member would

        An existing member receiving a Add message first verifies the
        signature on the message, then updates its state as follows:

        o  If the "index" value is equal to the size of the group, increment
           the size of the group, and extend the tree accordingly
        o  Verify the signature on the included ClientInitKey; if the
           signature verification fails, abort
        o  Generate a WelcomeInfo object describing the state prior to the
           add, and verify that its hash is the same as the value of the
           "welcome_info_hash" field
        o  Update the ratchet tree by setting to blank all nodes in the
           direct path of the new node
        o  Set the leaf node in the tree at position "index" to a new node
           containing the public key from the ClientInitKey in the Add
           corresponding to the ciphersuite in use, as well as the credential
           under which the ClientInitKey was signed

        The "update_secret" resulting from this change is an all-zero octet
        string of length Hash.length.

        After processing an Add message, the new member SHOULD send an Update
        immediately to update its key.  This will help to limit the tree
        structure degrading into subtrees, and thus maintain the protocol's
        efficiency.

        :param add_message:
        :param private_key:
        :return:
        """

        private_key = self._key_store.get_private_key(add_message.init_key)

        if private_key is not None:
            # we possess the private key for this given init_key
            if self._user_index is not None:
                # if we are not new to the group ( i.e. already know our index), this cant be right
                raise RuntimeError()
            self._user_index = add_message.index

        self._state.process_add(add_message=add_message, private_key=private_key)

    def update(self) -> UpdateMessage:
        """
        RFC 9.3 Update
        https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-9.3

        An Update message is sent by a group member to update its leaf secret
        and key pair. This operation provides post-compromise security with
        regard to the member's prior leaf private key.

        :return: the UpdateMessage
        """
        # TODO: ACTHUNG ACHTUNG RESEQUENCING
        # DIESE METHODE IST NICHT RESEQUENCING SICHER
        # Gegensätzlich zum RFC müssten wir auch das leaf secret mit versenden, damit wir im resequencing fall
        # nicht unseren tree borken. Gerade erstzen wir das leaf secret sofort, wenn die update nachricht dann
        # resequenced wird ist der updatende client raus. MLSpp von cisco hat das gleiche problem.

        return self._state.update(self._user_index)

    def process_update(self, leaf_index: int, update_message: UpdateMessage) -> None:
        """
        RFC 9.3 Update
        https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-9.3

        A member receiving a Update message first verifies the signature on
        the message, then updates its state as follows:

        o  Update the cached ratchet tree by replacing nodes in the direct
           path from the updated leaf using the information contained in the
           Update message

        :param leaf_index: the leaf which gets updated
        :param update_message: the updateMessage
        """
        # todo: We still do not know which leaf to update with this add message
        self._state.process_update(leaf_index=leaf_index, message=update_message)

    def encrypt_application_message(self, message: str) -> MLSCiphertext:
        """
        RFC 11.1 Tree of Application Secrets
        RFC 11.2 Sender Ratchets
        RFC 11.3 Deletion Schedule

        Here would be the encryption using the ApplicationSecretTree and DoubleRatchets

        :param message: the message to encrypt
        :return: the encrypted MLSCiphertext object
        """

        # todo: fix this shait :

        # pylint: disable=unexpected-keyword-arg
        sender_data = MLSSenderData(sender=self._user_index, generation=0)

        # pylint: disable=unexpected-keyword-arg
        plaintext = MLSPlaintext(
            group_id=self._state.get_group_context().group_id,
            epoch=self._state.get_group_context().epoch,
            content_type=ContentType.APPLICATION,
            sender=self._user_index,
            signature=b'0',
            content=MLSPlaintextApplicationData(application_data=message.encode('UTF-8'))
        )

        # pylint: disable=unexpected-keyword-arg
        out = MLSCiphertext(
            content_type=ContentType.APPLICATION,
            group_id=plaintext.group_id,
            epoch=plaintext.epoch,
            sender_data_nounce=b'0',
            encrypted_sender_data=sender_data.pack(),
            ciphertext=plaintext.pack()
        )

        return out

    def encrypt_handshake_message(self, group_op: GroupOperation) -> MLSCiphertext:
        """
        RFC 9 Handshake Message
        https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-9

        An MLS handshake message encapsulates a specific GroupOperation
        message that accomplishes a change to the group state.  It is carried
        in an MLSPlaintext message that provides a signature by the sender of
        the message.  Applications may choose to send handshake messages in
        encrypted form, as MLSCiphertext messages.

        :param group_op: which Handshake operation is encrypted
        :return: the encrypted object MLSCiphertext
        """
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
            ciphertext=plaintext.pack()
        )

        return encrypted

    def _process_handshake(self, message: MLSCiphertext, handler: AbstractApplicationHandler) -> None:
        """
        RFC 9 Handshake Message
        https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-9

        The high-level flow for processing a handshake message is as follows:

        1.  If the handshake message is encrypted (i.e., encoded as an
            MLSCiphertext object), decrypt it following the procedures
            described in Section 8.
        2.  Verify that the "epoch" field of enclosing MLSPlaintext message
            is equal the "epoch" field of the current GroupContext object.
        3.  Verify that the signature on the MLSPlaintext message verifies
            using the public key from the credential stored at the leaf in
            the tree indicated by the "sender" field.
        4.  Use the "operation" message to produce an updated, provisional
            GroupContext object incorporating the proposed changes.
        5.  Use the "confirmation_key" for the new epoch to compute the
            confirmation MAC for this message, as described below, and verify
            that it is the same as the "confirmation" field in the
            MLSPlaintext object.
        6.  If the the above checks are successful, consider the updated
            GroupContext object as the current state of the group.

        The confirmation value confirms that the members of the group have
        arrived at the same state of the group:

        MLSPlaintext.confirmation =
            HMAC(confirmation_key, GroupContext.transcript_hash)

        HMAC [RFC2104] uses the Hash algorithm for the ciphersuite in use.
        Sign uses the signature algorithm indicated by the signer's
        credential.

        :param message: the HandshakeMesssage to be processed
        :param handler: handler for processing
        """
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
            self.process_update(leaf_index=plain.sender, update_message=operation.operation)
            raise RuntimeError()
        else:
            raise RuntimeError()

    # pylint: disable=no-self-use
    def _process_application(self, message: MLSCiphertext, handler: AbstractApplicationHandler) -> None:
        """
        RFC 11 Application Messages
        https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-11
        RFC 11.1 Tree of Application Secrets
        RFC 11.2 Sender Ratchets
        RFC 11.3 Deletion Schedule

        The primary purpose of the Handshake protocol is to provide an
        authenticated group key exchange to clients.  In order to protect
        Application messages sent among the members of a group, the
        Application secret provided by the Handshake key schedule is used to
        derive nonces and encryption keys for the Message Protection Layer
        according to the Application Key Schedule.  That is, each epoch is
        equipped with a fresh Application Key Schedule which consist of a
        tree of Application Secrets as well as one symmetric ratchet per
        group member.

        Each client maintains their own local copy of the Application Key
        Schedule for each epoch during which they are a group member.  They
        derive new keys, nonces and secrets as needed while deleting old ones
        as soon as they have been used.

        Application messages MUST be protected with the Authenticated-
        Encryption with Associated-Data (AEAD) encryption scheme associated
        with the MLS ciphersuite using the common framing mechanism.  Note

        that "Authenticated" in this context does not mean messages are known
        to be sent by a specific client but only from a legitimate member of
        the group.  To authenticate a message from a particular member,
        signatures are required.  Handshake messages MUST use asymmetric
        signatures to strongly authenticate the sender of a message.

        :param message: the ApplicationMessage
        :param handler: handler for Application Message
        """
        # todo: Usually, this would have to be decrypted right here
        plain = MLSPlaintext.from_bytes(message.ciphertext)

        if not plain.verify_metadata_from_cipher(message):
            raise RuntimeError()

        if not isinstance(plain.content, MLSPlaintextApplicationData):
            raise RuntimeError()

        handler.on_application_message(plain.content.application_data, plain.group_id.decode('ASCII'))

    # pylint: disable=no-self-use
    def process_message(self, message: MLSCiphertext, handler: AbstractApplicationHandler) -> None:
        """
        Determines if a message is of type Handshake or type Application
        :param message: the message to determine the type
        :param handler: Handler for the message
        """
        if message.content_type == ContentType.APPLICATION:
            self._process_application(message=message, handler=handler)
        elif message.content_type == ContentType.HANDSHAKE:
            self._process_handshake(message=message, handler=handler)
        else:
            raise RuntimeError()

    @staticmethod
    def get_groupid_from_cipher(data: bytes) -> bytes:
        return MLSCiphertext.from_bytes(data).group_id
