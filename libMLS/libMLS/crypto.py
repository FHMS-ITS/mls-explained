"""
todo: Helper klassen sind böse
"""
from dataclasses import dataclass

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDFExpand, HKDF

from libMLS.cipher_suite import CipherSuite
from libMLS.group_context import GroupContext

@dataclass
class HkdfLabel:
    """
    RFC 6.6 Key Schedule
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-6.6

    Where HkdfLabel is specified as:

    struct {
        opaque group_context<0..255> = Hash(GroupContext_[n]);
        uint16 length = Length;
        opaque label<7..255> = "mls10 " + Label;
        opaque context<0..2^32-1> = Context;
    } HkdfLabel;
    """
    group_context: bytes
    length: int
    label: bytes
    context: GroupContext

    def __bytes__(self):
        """
        Converts HkdfLabel object to bytes
        :return: HkdfLabel object as bytes
        """
        tmp = b"".join([self.group_context, bytes([self.length])])
        tmp = b"".join([tmp, self.label])
        tmp = b"".join([tmp, bytes(self.context)])
        return tmp

# pylint: disable=pointless-string-statement
"""
    RFC 6.6 Key Schedule
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-6.6

    Group keys are derived using the HKDF-Extract and HKDF-Expand
    functions as defined in [RFC5869], as well as the functions defined
    below:

    HKDF-Expand-Label(Secret, Label, Context, Length) =
        HKDF-Expand(Secret, HkdfLabel, Length)

    Derive-Secret(Secret, Label) =
        HKDF-Expand-Label(Secret, Label, "", Hash.length)

    The Hash function used by HKDF is the ciphersuite hash algorithm.
    Hash.length is its output length in bytes. 
"""


# pylint: disable=unused-argument
def hkdf_expand_label(secret: bytes, label: bytes, context: GroupContext, cipher_suite: CipherSuite) -> bytes:
    """
    Generates a secret from given secret, label and GroupContext object
    :param secret: secret argument for HKDFExpand
    :param label: label used in HKDFExpand
    :param context: GroupContext object used in HKDFExpand
    :param cipher_suite: CipherSuite which should be used
    :return: secret derived from given parameters
    """
    context_hash = cipher_suite.get_hash()
    context_hash.update(bytes(context))
    label_part = bytes(HkdfLabel(context_hash.finalize(), cipher_suite.get_hash_length(), label, context))
    hkdf_label: bytes = b'mls10 ' + label_part

    # todo: support hash from cipher suite
    return HKDFExpand(length=cipher_suite.get_hash_length(), info=hkdf_label,
                      algorithm=hashes.SHA256(), backend=default_backend()).derive(secret)


def hkdf_extract(secret: bytes, salt: bytes, cipher_suite: CipherSuite) -> bytes:
    """
    Generates a secret from given secret and salt
    :param secret: secret argument for HKDF
    :param salt:  salt argument for HKDF
    :param cipher_suite: CipherSuite which should be used
    :return: secret derived from given parameters
    """
    # todo: support hash from cipher suite
    return HKDF(length=cipher_suite.get_hash_length(), info=None, salt=salt,
                algorithm=hashes.SHA256(), backend=default_backend()).derive(secret)


def derive_secret(secret: bytes, label: bytes, context: GroupContext, cipher_suite: CipherSuite) -> bytes:
    """
    (Same as hkdf_expand_label, see RFC 6.6)

    Derives a secret from given secret, label and GroupContext object
    :param secret: secret argument for hkdf_expand_label
    :param label: label used in hkdf_expand_label
    :param context: GroupContext object used in hkdf_expand_label
    :param cipher_suite: CipherSuite which should be used
    :return: secret derived from given parameters in hkdf_expand_label
    """
    return hkdf_expand_label(secret=secret, label=label, context=context, cipher_suite=cipher_suite)
