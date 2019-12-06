"""
Refer to RFC-8446 https://tools.ietf.org/html/rfc8446#section-3.4
"""
from dataclasses import dataclass
from struct import pack

from enum import Enum
from typing import Union, List

from libMLS.libMLS.abstract_message import AbstractMessage
from libMLS.libMLS.message_packer import pack_dynamic, unpack_dynamic, unpack_byte_list
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


class InitMessage(AbstractMessage):

    def validate(self) -> bool:
        return False

    def _pack(self) -> bytes:
        pass

    @classmethod
    def from_bytes(cls, data: bytes):
        pass


@dataclass
class AddMessage(AbstractMessage):
    index: int
    init_key: bytes
    welcome_info_hash: bytes

    def _pack(self) -> bytes:
        return pack_dynamic('IVV', self.index, self.init_key, self.welcome_info_hash)

    def validate(self) -> bool:
        return True

    @classmethod
    def from_bytes(cls, data: bytes):
        box: tuple = unpack_dynamic('IVV', data)
        # pylint: disable=unexpected-keyword-arg
        inst: AddMessage = cls(index=box[0], init_key=box[1], welcome_info_hash=box[2])

        if not inst.validate():
            raise RuntimeError()

        return inst

    def __eq__(self, other):

        if not isinstance(other, self.__class__):
            return False

        return self.index == other.index and \
               self.init_key == other.init_key and \
               self.welcome_info_hash == other.welcome_info_hash


@dataclass
class DirectPathNode(AbstractMessage):
    public_key: bytes
    encrypted_path_secret: List['HPKECiphertext']

    def _pack(self) -> bytes:

        path_secret_buffer: bytes = b''
        for entry in self.encrypted_path_secret:
            path_secret_buffer += pack_dynamic('V', entry.pack())

        return pack_dynamic('32sV', self.public_key, path_secret_buffer)

    @classmethod
    def from_bytes(cls, data: bytes):
        box: tuple = unpack_dynamic('32sV', data)

        public_key: bytes = box[0]
        encrypted_messages_bytes: List[bytes] = unpack_byte_list(box[1])
        encrypted_messages: List[HPKECiphertext] = []
        for entry in encrypted_messages_bytes:
            encrypted_messages.append(HPKECiphertext.from_bytes(entry))

        # pylint: disable=unexpected-keyword-arg
        inst: DirectPathNode = cls(public_key=public_key, encrypted_path_secret=encrypted_messages)
        if not inst.validate():
            raise RuntimeError()

        return inst

    def validate(self) -> bool:
        return True

    def __eq__(self, other):

        if not isinstance(other, self.__class__):
            return False

        if self.public_key != other.public_key:
            return False

        for index, node in enumerate(self.encrypted_path_secret):
            if node != other.encrypted_path_secret[index]:
                return False

        return True


@dataclass
class UpdateMessage(AbstractMessage):
    direct_path: List[DirectPathNode]

    def _pack(self) -> bytes:

        nodes_buffer: bytes = b''
        for node in self.direct_path:
            nodes_buffer += pack_dynamic('V', node.pack())

        return pack_dynamic('V', nodes_buffer)

    @classmethod
    def from_bytes(cls, data: bytes):
        node_bytes: List[bytes] = unpack_byte_list(unpack_dynamic('V', data)[0])

        direct_path: List[DirectPathNode] = []
        for entry in node_bytes:
            direct_path.append(DirectPathNode.from_bytes(entry))

        # pylint: disable=unexpected-keyword-arg
        inst: UpdateMessage = cls(direct_path=direct_path)

        if not inst.validate():
            raise RuntimeError()

        return inst

    def validate(self) -> bool:
        return True

    def __eq__(self, other):

        if not isinstance(other, self.__class__):
            return False

        for index, node in enumerate(self.direct_path):
            if node != other.direct_path[index]:
                return False

        return True


class RemoveMessage(AbstractMessage):

    def validate(self) -> bool:
        return False

    def _pack(self) -> bytes:
        pass

    @classmethod
    def from_bytes(cls, data: bytes):
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

    @classmethod
    def from_bytes(cls, data: bytes):
        pass


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

    @classmethod
    def from_bytes(cls, data: bytes):
        pass


@dataclass
class MLSPlaintextApplicationData(AbstractMessage):
    application_data: bytes

    def validate(self) -> bool:
        return True

    def _pack(self) -> bytes:
        return pack_dynamic('v', self.application_data)

    @classmethod
    def from_bytes(cls, data: bytes):
        box: tuple = unpack_dynamic('V', data)
        # pylint: disable=unexpected-keyword-arg
        inst: MLSPlaintextApplicationData = cls(application_data=box[0])

        if not inst.validate():
            raise RuntimeError()

        return inst


@dataclass
class MLSSenderData(AbstractMessage):
    sender: int
    generation: int

    def validate(self) -> bool:
        return True

    @classmethod
    def from_bytes(cls, data: bytes):
        box: tuple = unpack_dynamic('II', data)
        # pylint: disable=unexpected-keyword-arg
        inst: MLSSenderData = cls(sender=box[0], generation=box[1])

        if not inst.validate():
            raise RuntimeError()

        return inst

    def _pack(self) -> bytes:
        return pack_dynamic(
            'II',
            self.sender,
            self.generation
        )


@dataclass
class MLSPlaintext(AbstractMessage):
    group_id: bytes
    epoch: int
    sender: int
    content_type: ContentType
    content: Union[MLSPlaintextHandshake, MLSPlaintextApplicationData]
    signature: bytes

    def validate(self) -> bool:
        # return len(self.group_id) <= 256 and len(self.signature) < 2 ** 16
        return True

    def _pack(self) -> bytes:
        return pack_dynamic(
            'VIIBVV',
            self.group_id,
            self.epoch,
            self.sender,
            self.content_type,
            self.content.pack(),
            self.signature
        )

    @classmethod
    def from_bytes(cls, data: bytes):
        box: tuple = unpack_dynamic('VIIBVV', data)
        # pylint: disable=unexpected-keyword-arg
        inst: MLSPlaintext = cls(group_id=box[0], epoch=box[1], sender=box[2], content_type=box[3], content=box[4],
                                 signature=box[5])

        if not inst.validate():
            raise RuntimeError()

        return inst


@dataclass
class MLSCiphertext(AbstractMessage):
    # todo: Replace prefix with SenderDataAAD
    group_id: bytes
    epoch: int
    content_type: ContentType
    sender_data_nounce: bytes
    encrypted_sender_data: bytes
    ciphertext: bytes

    def validate(self) -> bool:
        return True

    def _pack(self) -> bytes:
        return pack_dynamic('VIBVVV',
                            self.group_id,
                            self.epoch,
                            self.content_type,
                            self.sender_data_nounce,
                            self.encrypted_sender_data,
                            self.ciphertext
                            )

    @classmethod
    def from_bytes(cls, data: bytes):
        pass


@dataclass
class HPKECiphertext(AbstractMessage):
    ephemeral_key: bytes
    cipher_text: bytes

    def _pack(self) -> bytes:
        return pack_dynamic('32sV', self.ephemeral_key, self.cipher_text)

    def validate(self) -> bool:
        return True

    @classmethod
    def from_bytes(cls, data: bytes):
        box: tuple = unpack_dynamic('32sV', data)
        # pylint: disable=unexpected-keyword-arg
        inst: HPKECiphertext = cls(ephemeral_key=box[0], cipher_text=box[1])

        if not inst.validate():
            raise RuntimeError()

        return inst

    def __eq__(self, other):

        if not isinstance(other, self.__class__):
            return False

        return self.ephemeral_key == other.ephemeral_key and self.cipher_text == other.cipher_text


@dataclass
# pylint: disable=too-many-instance-attributes
class WelcomeInfoMessage(AbstractMessage):
    protocol_version: bytes
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
                len(self.tree) == len(other.tree)):
            return False

        nodes_equal: bool = True
        for node_index in range(len(self.tree)):
            nodes_equal &= (self.tree[node_index] == other.tree[node_index])

        # todo Pack and unpack test
        return nodes_equal

    def _pack(self) -> bytes:
        return pack_dynamic(
            'VVIVVVVV',
            self.protocol_version,
            self.group_id,
            self.epoch,
            self._packed_nodes(),
            self.interim_transcript_hash,
            self.init_secret,
            self.key,
            self.nounce
        )

    def _packed_nodes(self) -> bytes:
        # packed_list: List[bytes] = []
        packed_list: bytes = b''
        for node in self.tree:
            packed_list += pack_dynamic('V', node.pack())

        return packed_list

    def validate(self) -> bool:
        # todo: write auto validate for fmt string and dump this validation func
        return True

    @classmethod
    def from_bytes(cls, data: bytes):
        box = unpack_dynamic('VVIVVVVV', data)

        raw_nodes: List[bytes] = unpack_byte_list(box[3])
        nodes: List[TreeNode] = []

        # if there are no nodes in the tree, the raw_nodes list contains just one empty entry
        if raw_nodes != [] and raw_nodes[0] != b'':
            for raw_node in raw_nodes:
                nodes.append(TreeNode.from_bytes(raw_node))

        # pylint: disable=unexpected-keyword-arg
        inst = cls(protocol_version=box[0],
                   group_id=box[1],
                   epoch=box[2],
                   tree=nodes,
                   interim_transcript_hash=box[4],
                   init_secret=box[5],
                   key=box[6],
                   nounce=box[7])

        if not inst.validate():
            raise RuntimeError()

        return inst


@dataclass
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

    @classmethod
    def from_bytes(cls, data: bytes):
        pass
