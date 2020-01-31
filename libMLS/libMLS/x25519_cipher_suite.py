from typing import Tuple

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.hashes import Hash
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from libMLS.cipher_suite import CipherSuite


class X25519CipherSuite(CipherSuite):
    """
    A ciphersuite consisting of the three primitives:
    Curve25519
    AES-128-GCM
    SHA-256

    see also https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-6.1
    """

    def get_suite_identifier(self) -> int:
        return 1

    # we are cool with iv as an parametername
    # pylint: disable=invalid-name
    def get_encryption_algorithm(
            self,
            key: bytes,
            iv: bytes = bytes.fromhex('4fc8604d3aacc9ae5c3158e4c7e4d74e')
    ) -> Cipher:
        # https://cryptography.io/en/latest/hazmat/primitives/symmetric-encryption
        # AES-GCM-128 is required -> check whether key is 16byte long
        # todo: No IV is given

        if len(key) != 16:
            raise RuntimeError(f"Key length {len(key)} violates length requirement of 16bytes")

        if len(iv) != 16:
            raise RuntimeError(f"IV length {len(iv)} violates length requirement of 16bytes")

        return Cipher(algorithms.AES(key), modes.GCM(iv), default_backend())

    def get_hash(self) -> Hash:
        # see https://cryptography.io/en/latest/hazmat/primitives/cryptographic-hashes/?highlight=SHA
        return Hash(hashes.SHA256(), default_backend())

    def get_hash_length(self) -> int:
        return hashes.SHA256().digest_size

    def get_curve(self):
        # see https://cryptography.io/en/latest/hazmat/primitives/asymmetric/x25519/?highlight=X25519
        pass

    def derive_key_pair(self, material: bytes) -> Tuple[bytes, bytes]:
        digest: Hash = self.get_hash()
        digest.update(material)
        private_key: bytes = digest.finalize()

        # todo: Public key is mostlikely wrong, quote "The corresponding public key is X25519(SHA-256(X), 9)"
        public_key = X25519PrivateKey.\
            from_private_bytes(private_key).\
            public_key().\
            public_bytes(encoding=Encoding.Raw, format=PublicFormat.Raw)

        return public_key, private_key
