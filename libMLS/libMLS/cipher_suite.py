from typing import Tuple
from cryptography.hazmat.primitives.hashes import Hash


class CipherSuite:

    def __init__(self):
        return

    # we are cool with iv as an parametername
    # pylint: disable=invalid-name
    def get_encryption_algorithm(self, key: bytes, iv: bytes = bytes.fromhex('4fc8604d3aacc9ae5c3158e4c7e4d74e')):
        raise NotImplementedError()

    def get_hash(self) -> Hash:
        raise NotImplementedError()

    def get_hash_length(self) -> int:
        raise NotImplementedError

    def get_curve(self):
        raise NotImplementedError()

    def get_suite_identifier(self) -> int:
        raise NotImplementedError()

    def derive_key_pair(self, material: bytes) -> Tuple[bytes, bytes]:
        """
        Returns a public/private key pair computed from the given keying material
        :param material:
        :return: A tuple consisting of [public_key, private_key]
        """
        raise NotImplementedError()
