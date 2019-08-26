import string
import struct

from struct import unpack_from
from typing import List

MESSAGE_PACKER_LENGTH_FIELD_SIZE: int = struct.calcsize('L')
MESSAGE_PACKER_BYTE_ORDERING: str = '@'


class DynamicPackingException(Exception):
    pass


def pack_dynamic(pack_fmt: string, *args) -> bytes:
    out_fmt: string = ""
    out_args = []

    digit_backlog: string = ""
    arg_index = 0

    # todo: padbytes
    for pack_char in pack_fmt:

        if pack_char.isdigit():
            digit_backlog += pack_char
            continue

        if pack_char != 'V':
            out_fmt += digit_backlog + pack_char

            if pack_char == 's' or digit_backlog == "":
                out_args.append(args[arg_index])
                arg_index += 1
            else:
                out_args += [*args[arg_index:arg_index + int(digit_backlog)]]
                arg_index += int(digit_backlog)

            digit_backlog = ""
            continue

        if digit_backlog != "":
            raise DynamicPackingException(f'\'V\' may not be used with quantifiers, \"{digit_backlog}\" given')

        if not isinstance(args[arg_index], bytes):
            raise DynamicPackingException('Argument provided for \'V\' is not of type \'bytes\'!')

        # todo: check len
        vec_len = len(args[arg_index])
        out_fmt += 'L'
        out_args.append(vec_len)
        if vec_len > 0:
            out_fmt += f'{len(args[arg_index])}s'
            out_args.append(args[arg_index])
        arg_index += 1

    return struct.pack(MESSAGE_PACKER_BYTE_ORDERING+out_fmt, *out_args)


def unpack_dynamic(pack_fmt: string, buffer: bytes) -> tuple:
    out_tuple: tuple = ()

    digit_backlog = ""

    for fmt_char in pack_fmt:

        if fmt_char.isdigit():
            digit_backlog += fmt_char
            continue

        if fmt_char != 'V':
            multiplier = 1
            if digit_backlog != "":
                multiplier = int(digit_backlog)
            to_remove = struct.calcsize(fmt_char) * multiplier

            out_tuple = out_tuple + struct.unpack(
                f'{MESSAGE_PACKER_BYTE_ORDERING}{digit_backlog}{fmt_char}', buffer[:to_remove])
            buffer = buffer[to_remove:]
            continue

        vector_size = struct.unpack(f'{MESSAGE_PACKER_BYTE_ORDERING}L', buffer[:struct.calcsize('L')])[0]
        buffer = buffer[struct.calcsize('L'):]

        vector_contents = struct.unpack(f'{MESSAGE_PACKER_BYTE_ORDERING}{vector_size}s', buffer[:vector_size])
        buffer = buffer[vector_size:]

        out_tuple = out_tuple + vector_contents

    return out_tuple


def unpack_byte_list(buffer: bytes) -> List[bytes]:
    pointer: int = 0
    out_list: List[bytes] = []
    while pointer < len(buffer):
        entry_len: int = unpack_from(f'{MESSAGE_PACKER_BYTE_ORDERING}L', buffer, pointer)[0]
        pointer += struct.calcsize('L')

        entry: bytes = unpack_from(f'{MESSAGE_PACKER_BYTE_ORDERING}{entry_len}s', buffer, pointer)[0]
        pointer += entry_len

        out_list.append(entry)

    return out_list
