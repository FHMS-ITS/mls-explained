"""
Refer to RFC-8446 https://tools.ietf.org/html/rfc8446#section-3.4
"""
from dataclasses import dataclass
from struct import pack

from enum import Enum
from typing import Union, List

from libMLS.libMLS.tree_node import TreeNode


class ContentType(Enum):
    INVALID = 0
    HANDSHAKE = 1
    APPLICATION = 2


class GroupOperationType(Enum):
    INIT = 0
    ADD = 1
    UPDATE = 2
    REMOVE = 3


class CipherSuiteType(Enum):
    P256_SHA256_AES128GCM = 0
    X25519_SHA256_AES128GCM = 1


class AbstractMessage:

    def __init__(self):
        return

    def pack(self) -> bytes:
        if not self.validate():
            raise RuntimeError(f'Validation failed for a message of type \"{self.__class__.__name__}\"')

        return self._pack()

    def _pack(self) -> bytes:
        # see https://docs.python.org/3.7/library/struct.html
        raise NotImplementedError()

    def validate(self) -> bool:
        raise NotImplementedError()


class InitMessage(AbstractMessage):
    pass


@dataclass
class AddMessage(AbstractMessage):
    index: int
    init_key: bytes
    welcome_info_hash: bytes

    def _pack(self) -> bytes:
        pass

    def validate(self) -> bool:
        return False


class UpdateMessage(AbstractMessage):
    pass


class RemoveMessage(AbstractMessage):
    pass


class GroupOperation(AbstractMessage):
    msg_type: GroupOperationType
    operation: Union[InitMessage, AddMessage, UpdateMessage, RemoveMessage]

    def validate(self) -> bool:
        return True

    def _pack(self) -> bytes:
        return pack('Bp',
                    self.msg_type,
                    self.operation.pack()
                    )


class MLSPlaintextHandshake(AbstractMessage):
    confirmation: int
    group_operation: GroupOperation

    def validate(self) -> bool:
        return True

    def _pack(self) -> bytes:
        return pack(
            'pB',
            self.group_operation.pack(),
            self.confirmation,
        )


class MLSPlaintextApplicationData(AbstractMessage):
    application_data: bytes

    def _pack(self) -> bytes:
        pass


class MLSPlaintext(AbstractMessage):
    group_id: bytes
    epoch: int
    sender: int
    content_type: ContentType
    content: Union[MLSPlaintextHandshake, MLSPlaintextApplicationData]
    signature: bytes

    def validate(self) -> bool:
        return len(self.group_id) <= 256 and len(self.signature) < 2 ** 16

    def _pack(self) -> bytes:
        return pack(
            'pIIBpH',
            self.group_id,
            self.epoch,
            self.sender,
            self.content_type,
            self.content.pack(),
            self.signature
        )


class HPKECiphertext(AbstractMessage):
    ephemeral_key: bytes
    cipher_text: bytes

    def _pack(self) -> bytes:
        return pack('pp', self.ephemeral_key, self.cipher_text)

    def validate(self) -> bool:
        return len(self.ephemeral_key) < 2 ** 16 and len(self.cipher_text) < 2 ** 16


class WelcomeInfoMessage(AbstractMessage):
    protocol_version: int
    group_id: bytes
    epoch: int
    tree: List[TreeNode]
    interim_transcript_hash: bytes
    init_secret: bytes
    key: bytes
    nounce: bytes

    def __eq__(self, other):

        if not isinstance(other, self.__class__):
            return False

        if not (other.interim_transcript_hash == self.interim_transcript_hash and
                self.protocol_version == other.protocol_version and
                self.group_id == other.group_id and
                self.init_secret == other.init_secret and
                self.key == other.key and
                self.nounce == other.nounce and
                len(self.tree) == len(other.tree)
        ):
            return False

        nodes_equal: bool = True
        for node_index in range(len(self.tree)):
            nodes_equal &= (self.tree[node_index] == other.tree[node_index])

        # todo Pack and unpack test
        return nodes_equal

    def _pack(self) -> bytes:
        return pack(
            'BIpIIpIpIpIpIp',
            self.protocol_version,
            len(self.group_id),
            self.group_id,
            self.epoch,
            len(self._packed_nodes()),
            self._packed_nodes(),
            len(self.interim_transcript_hash),
            self.interim_transcript_hash,
            len(self.init_secret),
            self.init_secret,
            len(self.key),
            self.key,
            len(self.nounce),
            self.nounce
        )

    def _packed_nodes(self) -> bytes:
        return b''

    def validate(self) -> bool:
        # todo: write auto validate for fmt string and dump this validation func
        return self.protocol_version < 256 and \
               len(self.group_id) < 256 and \
               self.epoch < 2 ** 32 and \
               len(self._packed_nodes()) < 2 ** 32 and \
               len(self.interim_transcript_hash) < 256 and \
               len(self.init_secret) < 256 and \
               len(self.key) < 256 and \
               len(self.nounce) < 256


class WelcomeMessage(AbstractMessage):
    client_init_key_id: bytes
    cipher_suite: CipherSuiteType
    encrypted_welcome_info: HPKECiphertext

    def _pack(self) -> bytes:
        return pack(
            'pBp',
            self.client_init_key_id,
            self.cipher_suite,
            self.encrypted_welcome_info
        )

    def validate(self) -> bool:
        return len(self.client_init_key_id) <= 256
