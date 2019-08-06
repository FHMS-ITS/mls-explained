from typing import Optional

from libMLS.libMLS.cipher_suite import CipherSuite


class TreeNode:

    def __init__(self, public_key: bytes, private_key: Optional[bytes] = None, credential: Optional[bytes] = None):
        super().__init__()
        self._public_key: bytes = public_key
        self._private_key: Optional[bytes] = private_key
        self._credential: Optional[bytes] = credential

    def get_public_key(self) -> bytes:
        return self._public_key

    def get_private_key(self) -> Optional[bytes]:
        return self._private_key

    def has_private_key(self) -> bool:
        return self._private_key is not None

    @classmethod
    def from_node_secret(cls, node_secret: bytes, cipher_suite: CipherSuite):
        public_key, private_key = cipher_suite.derive_key_pair(node_secret)
        return TreeNode(public_key, private_key, None)

    def __eq__(self, other):
        if not isinstance(other, TreeNode):
            return False

        # return self._private_key == other._private_key and \
        #        self._public_key == other._public_key and \
        #        self._credential == other._credential

        return self._public_key == other._public_key
