from typing import Optional
from dataclasses import dataclass

from libMLS.libMLS.abstract_message import AbstractMessage
from libMLS.libMLS.cipher_suite import CipherSuite
from libMLS.libMLS.message_packer import pack_dynamic, unpack_dynamic


@dataclass
class LeafNodeInfo:
    public_key: bytes
    credentials: bytes

    def __bytes__(self):
        if self.credentials:
            return b"".join([self.public_key, self.credentials])
        return self.public_key

@dataclass
class LeafNodeHashInput:
    info: Optional[LeafNodeInfo]
    hash_type: int = 0

    def __bytes__(self):
        if self.info:
            return b"".join([bytes([self.hash_type]), self.info.__bytes__()])
        return bytes([self.hash_type])

@dataclass
class ParentNodeHashInput:
    public_key: Optional[bytes]
    left_hash: bytes
    right_hash: bytes
    hash_type: int = 1

    def __bytes__(self):
        tmp = b"".join([bytes([self.hash_type]), self.left_hash])
        tmp = b"".join([tmp, self.right_hash])
        if self.public_key:
            tmp = b"".join([tmp, self.public_key])
        return tmp


class TreeNode(AbstractMessage):

    def __init__(self, public_key: bytes, private_key: Optional[bytes] = None, credentials: Optional[bytes] = None):
        super().__init__()
        self._public_key: bytes = public_key
        self._private_key: Optional[bytes] = private_key
        self._credentials: Optional[bytes] = credentials

    def get_public_key(self) -> bytes:
        return self._public_key

    def get_private_key(self) -> Optional[bytes]:
        return self._private_key

    def get_credentials(self) -> Optional[bytes]:
        return self._credentials

    def has_private_key(self) -> bool:
        return self._private_key is not None

    @classmethod
    def from_node_secret(cls, node_secret: bytes, cipher_suite: CipherSuite):
        public_key, private_key = cipher_suite.derive_key_pair(node_secret)
        return TreeNode(public_key, private_key, None)

    def __eq__(self, other):
        if not isinstance(other, TreeNode):
            return False

        return self._public_key == other.get_public_key()

    def deep_eq(self, other) -> bool:

        if not isinstance(other, TreeNode):
            return False

        # test public part
        if not self == other:
            return False

        return self.get_private_key() == other.get_private_key() and self.get_credentials() == other.get_credentials()

    def __str__(self):
        return f'Public:{self._public_key.hex()} | Private:{self._private_key.hex() if self._private_key else "None"}'

    @classmethod
    def from_bytes(cls, data: bytes) -> 'TreeNode':
        box: tuple = unpack_dynamic('VVV', data)

        private_key: Optional[bytes] = box[1] if box[1] != b'' else None
        credential: Optional[bytes] = box[2] if box[2] != b'' else None

        inst: TreeNode = cls(public_key=box[0], private_key=private_key, credentials=credential)
        if not inst.validate():
            raise RuntimeError()

        return inst

    def _pack(self) -> bytes:
        return pack_dynamic('VVV',
                            self._public_key,
                            self._private_key if self._private_key is not None else b'',
                            self._credentials if self._credentials is not None else b'')

    def validate(self) -> bool:
        return self._public_key is not None
