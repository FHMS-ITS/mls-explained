"""
todo: Helper klassen sind böse
"""
from dataclasses import dataclass

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDFExpand, HKDF

from libMLS.libMLS.cipher_suite import CipherSuite
from libMLS.libMLS.group_context import GroupContext


@dataclass
class HkdfLabel:
    group_context: bytes
    length: int
    label: bytes
    context: GroupContext

    def __bytes__(self):
        tmp = b"".join([self.group_context, bytes([self.length])])
        tmp = b"".join([tmp, self.label])
        tmp = b"".join([tmp, bytes(self.context)])
        return tmp


# pylint: disable=unused-argument
def hkdf_expand_label(secret: bytes, label: bytes, context: GroupContext, cipher_suite: CipherSuite) -> bytes:
    context_hash = cipher_suite.get_hash()
    context_hash.update(bytes(context))
    label_part = bytes(HkdfLabel(context_hash.finalize(), cipher_suite.get_hash_length(), label, context))
    hkdf_label: bytes = b'mls10 ' + label_part

    # todo: support hash from cipher suite
    return HKDFExpand(length=cipher_suite.get_hash_length(), info=hkdf_label,
                      algorithm=hashes.SHA256(), backend=default_backend()).derive(secret)


def hkdf_extract(secret: bytes, salt: bytes, cipher_suite: CipherSuite) -> bytes:
    # wie ist das label hier zu setzen?
    # todo: support hash from cipher suite
    return HKDF(length=cipher_suite.get_hash_length(), info=b'0', salt=salt,
                algorithm=hashes.SHA256(), backend=default_backend()).derive(secret)


def derive_secret(secret: bytes, label: bytes, context: GroupContext, cipher_suite: CipherSuite) -> bytes:
    return hkdf_expand_label(secret=secret, label=label, context=context, cipher_suite=cipher_suite)
