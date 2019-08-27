import string
import struct
from typing import List, Dict

import pytest

from libMLS.libMLS.message_packer import pack_dynamic, MP_LENGTH_FIELD_SIZE, DynamicPackingException, \
    unpack_dynamic, unpack_byte_list, MP_BYTE_ORDERING


def test_plain_vector():
    cases: List[bytes] = [b'\x30', b'hallo', b'@@@!#?<>-_---_+*-^', 'ÄÜÖß'.encode('utf-8')]

    for some_byte_string in cases:
        out: bytes = pack_dynamic('V', some_byte_string)
        assert len(out) == MP_LENGTH_FIELD_SIZE + len(some_byte_string)
        assert struct.unpack(f'{MP_BYTE_ORDERING}L', out[0:MP_LENGTH_FIELD_SIZE])[0] == len(some_byte_string)


def test_normal_format_chars_pack():
    cases: Dict = {'c': b'a', 'L': 1337, '2s': b'aa'}

    for fmt_char, value in cases.items():
        assert pack_dynamic(fmt_char, value) == struct.pack(MP_BYTE_ORDERING + fmt_char, value)


def test_normal_format_chars_unpack():
    cases: Dict = {'c': [b'a'], 'L': [1337], '2s': [b'aa'], '2l': [1337, 7331]}

    for fmt_char, value in cases.items():
        assert list(unpack_dynamic(fmt_char, struct.pack(MP_BYTE_ORDERING + fmt_char, *value))) == value


def test_combined_payloads():
    dyn_payload = b'a' * 10

    cases: Dict[string, List] = {
        'Vc': [dyn_payload, b'a'],
        'LLV': [1337, 7331, dyn_payload],
        '2LV': [1337, 7331, dyn_payload],
        '32sV': [b'a' * 32, dyn_payload],

    }

    for fmt_string, arguments in cases.items():
        plain_fmt = fmt_string.replace('V', '')
        plain_size = struct.calcsize(MP_BYTE_ORDERING + plain_fmt)
        expected_size = plain_size + MP_LENGTH_FIELD_SIZE + len(dyn_payload)

        assert expected_size == len(pack_dynamic(fmt_string, *arguments))


def test_stacked_payloads():
    payload = b'' + pack_dynamic('V', b'a' * 32) + pack_dynamic('V', b'b' * 64)

    payload_payload = pack_dynamic('V', payload)

    unpacked_payload = unpack_dynamic('V', payload_payload)[0]
    assert payload == unpacked_payload

    payload_list = unpack_byte_list(unpacked_payload)
    assert len(payload_list) == 2
    assert payload_list[0] == b'a' * 32
    assert payload_list[1] == b'b' * 64


def test_quantifier_untouched():
    fmt = '2L'
    values = [1337, 7331]
    assert pack_dynamic(fmt, *values) == struct.pack(MP_BYTE_ORDERING + fmt, *values)


def test_pack_unpack_combinations():
    dyn_payload = b'a' * 10

    cases: Dict[string, List] = {
        'V': [dyn_payload],
        'Vc': [dyn_payload, b'a'],
        'LLV': [1337, 7331, dyn_payload],
        'LVL': [1337, b'b' * 16, 7331],
        '32sV': [b'a' * 32, pack_dynamic('V', b'a' * 72)]
    }

    for fmt_string, arguments in cases.items():
        packed_unpacked_values = unpack_dynamic(fmt_string, pack_dynamic(fmt_string, *arguments))

        for i, arg in enumerate(arguments):
            assert arg == packed_unpacked_values[i]


def test_empty_vector():
    packed = pack_dynamic('V', b'')
    assert len(packed) == struct.calcsize(MP_BYTE_ORDERING + 'L')
    assert struct.unpack(MP_BYTE_ORDERING + 'L', packed)[0] == 0

    unpacked = unpack_dynamic('V', packed)
    assert len(unpacked) == 1
    assert isinstance(unpacked[0], bytes)
    assert unpacked[0] == b''


def test_non_binary_must_fail():
    cases: List = [1, 'hallo', []]

    for case in cases:
        with pytest.raises(DynamicPackingException):
            pack_dynamic('V', case)
