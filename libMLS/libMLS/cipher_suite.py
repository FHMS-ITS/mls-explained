from typing import Tuple
from cryptography.hazmat.primitives.hashes import Hash


class CipherSuite:
    """
    RFC 6 Cryptographic Objects
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-6

    Each MLS session uses a single ciphersuite that specifies the
    following primitives to be used in group key computations:

    o  A hash function
    o  A Diffie-Hellman finite-field group or elliptic curve
    o  An AEAD encryption algorithm [RFC5116]

    The ciphersuite must also specify an algorithm "Derive-Key-Pair" that
    maps octet strings with the same length as the output of the hash
    function to key pairs for the asymmetric encryption scheme.

    Public keys used in the protocol are opaque values in a format
    defined by the ciphersuite, using the following types:

    opaque HPKEPublicKey<1..2^16-1>;
    opaque SignaturePublicKey<1..2^16-1>;

    Cryptographic algorithms are indicated using the following types:

    enum {
        ecdsa_secp256r1_sha256(0x0403),
        ed25519(0x0807),
        (0xFFFF)
    } SignatureScheme;

    enum {
        P256_SHA256_AES128GCM(0x0000),
        X25519_SHA256_AES128GCM(0x0001),
        (0xFFFF)
    } CipherSuite;
    """

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
