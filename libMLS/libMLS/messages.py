from struct import pack

from enum import Enum
from typing import Union


class ContentType(Enum):
    INVALID = 0
    HANDSHAKE = 1
    APPLICATION = 2


class GroupOperationType(Enum):
    INIT = 0
    ADD = 1
    UPDATE = 2
    REMOVE = 3


class AbstractMessage:

    def __init__(self):
        return

    def pack(self) -> bytes:
        if not self.validate():
            raise RuntimeError()

        return self._pack()

    def _pack(self) -> bytes:
        # see https://docs.python.org/3.7/library/struct.html
        raise NotImplementedError()

    def validate(self) -> bool:
        raise NotImplementedError()


class MLSPlaintextHandshake(AbstractMessage):
    confirmation: bytes

    # GroupOperation

    def _pack(self) -> bytes:
        pass


class MLSPlaintextApplicationData(AbstractMessage):
    application_data: bytes

    def _pack(self) -> bytes:
        pass


class MLSPlaintext(AbstractMessage):
    group_id: int
    epoch: int
    sender: int
    content_type: ContentType
    content: Union[MLSPlaintextHandshake, MLSPlaintextApplicationData]
    signature: bytes

    def validate(self) -> bool:
        return self.group_id < 256 and self.signature < 2 ** 16

    def _pack(self) -> bytes:
        return pack(
            'BIIBpH',
            self.group_id,
            self.epoch,
            self.sender,
            self.content_type,
            self.content.pack(),
            self.signature
        )
