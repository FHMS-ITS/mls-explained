from typing import Optional

from libMLS.crypto import derive_secret, hkdf_extract
from libMLS.group_context import GroupContext
from libMLS.cipher_suite import CipherSuite


# pylint: disable=too-many-instance-attributes
class KeySchedule:
    """
    RFC Section 6.6 Key Schedule
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-6.6

    When processing a handshake message, a client combines the following
    information to derive new epoch secrets:

    o  The init secret from the previous epoch
    o  The update secret for the current epoch
    o  The GroupContext object for current epoch

    In the below diagram:

    o  HKDF-Extract takes its salt argument from the top and its IKM
       argument from the left
    o  Derive-Secret takes its Secret argument from the incoming arrow

    Given these inputs, the derivation of secrets for an epoch proceeds
    as shown in the following diagram:

                       init_secret_[n-1] (or 0)
                         |
                         V
    update_secret -> HKDF-Extract = epoch_secret
                         |
                         +--> Derive-Secret(., "sender data", GroupContext_[n])
                         |    = sender_data_secret
                         |
                         +--> Derive-Secret(., "handshake", GroupContext_[n])
                         |    = handshake_secret
                         |
                         +--> Derive-Secret(., "app", GroupContext_[n])
                         |    = application_secret
                         |
                         +--> Derive-Secret(., "confirm", GroupContext_[n])
                         |    = confirmation_key
                         |
                         V
                   Derive-Secret(., "init", GroupContext_[n])
                         |
                         V
                   init_secret_[n]
    """

    def __init__(self, cipher_suite: CipherSuite, init_secret: Optional[bytes] = None):
        """
        Initializes the KeySchedule
        :param cipher_suite: the used CipherSuite
        :param init_secret: initial Secret is 0 or init_secret[n-1]
        """

        if init_secret is None:
            self._init_secret: bytes = bytes(bytearray(b'\x00') * cipher_suite.get_hash_length())
        else:
            self._init_secret = init_secret

        self._update_secret: bytes = b''
        self._epoch_secret: bytes = b''
        self._sender_data_secret: bytes = b''
        self._handshake_secret: bytes = b''
        self._application_secret: bytes = b''
        self._confirmation_key: bytes = b''
        self._cipher_suite: CipherSuite = cipher_suite

    def update_key_schedule(self, update_secret: bytes, context: GroupContext):
        """
        Calculates new epoch_secret and updates all secrets contained in KeySchedule according to the new epoch_secret
        :param update_secret: Secret argument for new epoch_secret
        :param context: GroupContext object
        """
        self._epoch_secret = hkdf_extract(secret=update_secret, salt=self._init_secret,
                                          cipher_suite=self._cipher_suite)

        self._sender_data_secret = derive_secret(secret=self._epoch_secret, label=str.encode("sender data"),
                                                 context=context, cipher_suite=self._cipher_suite)
        self._handshake_secret = derive_secret(secret=self._epoch_secret, label=str.encode("handshake"),
                                               context=context, cipher_suite=self._cipher_suite)
        self._application_secret = derive_secret(secret=self._epoch_secret, label=str.encode("app"),
                                                 context=context, cipher_suite=self._cipher_suite)
        self._confirmation_key = derive_secret(secret=self._epoch_secret, label=str.encode("confirm"),
                                               context=context, cipher_suite=self._cipher_suite)

        self._init_secret = derive_secret(secret=self._epoch_secret, label=str.encode("init"),
                                          context=context, cipher_suite=self._cipher_suite)

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


def advance_epoch(context: GroupContext, key_schedule: KeySchedule, update_secret: bytes):
    """
    Advances the Key Schedule to a new epoch
    :param context: GroupContext object
    :param key_schedule: KeySchedule which should be advanced
    :param update_secret: The new GroupSecret negotiated in RatchetTree
    """
    context.epoch += 1
    key_schedule.update_key_schedule(update_secret, context)
