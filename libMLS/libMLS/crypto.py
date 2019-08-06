"""
todo: Helper klassen sind böse
"""
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from libMLS.libMLS.cipher_suite import CipherSuite
from libMLS.libMLS.state import GroupContext
from cryptography.hazmat.primitives.kdf.hkdf import HKDFExpand


def hkdf_expand_label(secret: bytes, label: bytes, context: GroupContext, length: int,
                      cipher_suite: CipherSuite) -> bytes:
    """
    todo: implement real label
    struct {
         opaque group_context<0..255> = Hash(GroupContext_[n]);
         uint16 length = Length;
         opaque label<7..255> = "mls10 " + Label;
         opaque context<0..2^32-1> = Context;
       } HkdfLabel;

    :param secret:
    :param label:
    :param context:
    :param length:
    :return:
    """
    label: bytes = b'mls10 ' + label

    # todo: support hash from cipher suite

    return HKDFExpand(length=length, info=label, algorithm=hashes.SHA256(), backend=default_backend()).derive(secret)
