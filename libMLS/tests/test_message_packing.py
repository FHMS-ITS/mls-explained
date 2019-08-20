import string
import struct
from typing import List, Dict

import pytest

from libMLS.libMLS.message_packer import pack_dynamic, MESSAGE_PACKER_LENGTH_FIELD_SIZE, DynamicPackingException, \
    unpack_dynamic


def test_plain_vector():
    cases: List[bytes] = [b'\x30', b'hallo', b'@@@!#?<>-_---_+*-^', 'ÄÜÖß'.encode('utf-8')]

    for some_byte_string in cases:
        out: bytes = pack_dynamic('V', some_byte_string)
        assert len(out) == MESSAGE_PACKER_LENGTH_FIELD_SIZE + len(some_byte_string)
        assert struct.unpack('L', out[0:MESSAGE_PACKER_LENGTH_FIELD_SIZE])[0] == len(some_byte_string)


def test_normal_format_chars_pack():
    cases: Dict = {'c': b'a', 'L': 1337, '2s': b'aa'}

    for fmt_char, value in cases.items():
        assert pack_dynamic(fmt_char, value) == struct.pack(fmt_char, value)


def test_normal_format_chars_unpack():
    cases: Dict = {'c': [b'a'], 'L': [1337], '2s': [b'aa'], '2l': [1337, 7331]}

    for fmt_char, value in cases.items():
        assert list(unpack_dynamic(fmt_char, struct.pack(fmt_char, *value))) == value


def test_combined_payloads():
    dyn_payload = b'a' * 10

    cases: Dict[string, List] = {
        'Vc': [dyn_payload, b'a'],
        'LLV': [1337, 7331, dyn_payload],
        '2LV': [1337, 7331, dyn_payload]
    }

    for fmt_string, arguments in cases.items():
        plain_fmt = fmt_string.replace('V', '')
        plain_size = struct.calcsize(plain_fmt)
        expected_size = plain_size + MESSAGE_PACKER_LENGTH_FIELD_SIZE + len(dyn_payload)

        assert expected_size == len(pack_dynamic(fmt_string, *arguments))


def test_quantifier_untouched():
    fmt = '2L'
    values = [1337, 7331]
    assert pack_dynamic(fmt, *values) == struct.pack(fmt, *values)


def test_pack_unpack_combinations():
    dyn_payload = b'a' * 10

    cases: Dict[string, List] = {
        'V': [dyn_payload],
        'Vc': [dyn_payload, b'a'],
        'LLV': [1337, 7331, dyn_payload],
        'LVL': [1337, b'b' * 16, 7331]
    }

    for fmt_string, arguments in cases.items():
        packed_unpacked_values = unpack_dynamic(fmt_string, pack_dynamic(fmt_string, *arguments))

        for i, arg in enumerate(arguments):
            assert arg == packed_unpacked_values[i]


def test_empty_vector():
    pytest.skip('We must check whether this should be allowed')
    pack_dynamic('V', b'')


def test_non_binary_must_fail():
    cases: List = [1, 'hallo', []]

    for case in cases:
        with pytest.raises(DynamicPackingException):
            pack_dynamic('V', case)
