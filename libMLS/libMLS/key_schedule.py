from libMLS.libMLS.crypto import derive_secret, hkdf_extract
from libMLS.libMLS.group_context import GroupContext
from libMLS.libMLS.cipher_suite import CipherSuite


class KeySchedule:
    def __init__(self, cipher_suite: CipherSuite):
        self._init_secret: bytes = bytes(bytearray(b'\x00') * cipher_suite.get_hash_length())
        self._update_secret: bytes = b''
        self._epoch_secret: bytes = b''
        self._sender_data_secret: bytes = b''
        self._handshake_secret: bytes = b''
        self._application_secret: bytes = b''
        self._confirmation_key: bytes = b''

    def update_key_schedule(self, update_secret: bytes, context: GroupContext, cipher_suite: CipherSuite):
        self._epoch_secret = hkdf_extract(secret=update_secret, salt=self._init_secret, cipher_suite=cipher_suite)

        self._sender_data_secret = derive_secret(secret=self._epoch_secret, label=str.encode("sender data"),
                                                 context=context, cipher_suite=cipher_suite)
        self._handshake_secret = derive_secret(secret=self._epoch_secret, label=str.encode("handshake"),
                                               context=context, cipher_suite=cipher_suite)
        self._application_secret = derive_secret(secret=self._epoch_secret, label=str.encode("app"),
                                                 context=context, cipher_suite=cipher_suite)
        self._confirmation_key = derive_secret(secret=self._epoch_secret, label=str.encode("confirm"),
                                               context=context, cipher_suite=cipher_suite)

        self._init_secret = derive_secret(secret=self._epoch_secret, label=str.encode("init"),
                                          context=context, cipher_suite=cipher_suite)

    def set_init_secret(self, init_secret: bytes):
        self._init_secret = init_secret

    def get_init_secret(self) -> bytes:
        return self._init_secret

    def get_update_secret(self) -> bytes:
        return self._update_secret

    def get_epoch_secret(self) -> bytes:
        return self._epoch_secret

    def get_sender_data_secret(self) -> bytes:
        return self._sender_data_secret

    def get_handshake_secret(self) -> bytes:
        return self._handshake_secret

    def get_application_secret(self) -> bytes:
        return self._application_secret

    def get_confirmation_key(self) -> bytes:
        return self._confirmation_key
