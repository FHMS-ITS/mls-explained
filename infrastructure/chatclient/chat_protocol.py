from enum import Enum
from typing import Union, List

from dataclasses import dataclass

from libMLS.abstract_message import AbstractMessage
from libMLS.message_packer import pack_dynamic, unpack_dynamic


@dataclass
class ChatUserListMessage(AbstractMessage):
    user_names: List[str]

    @classmethod
    def from_bytes(cls, data: bytes):
        box: tuple = unpack_dynamic('V', data)

        user_bytes: bytes = box[0]
        users = user_bytes.decode('UTF-8').split('\n')

        # pylint: disable=unexpected-keyword-arg
        return cls(user_names=users)

    def _pack(self) -> bytes:
        return pack_dynamic('V', '\n'.join(self.user_names).encode('UTF-8'))

    def validate(self) -> bool:
        for name in self.user_names:
            if name.find('\n') != -1:
                return False

        return True


@dataclass
class ChatMessage(AbstractMessage):
    message: str

    @classmethod
    def from_bytes(cls, data: bytes):
        box: tuple = unpack_dynamic('V', data)
        message: str = box[0].decode('UTF-8')

        # pylint: disable=unexpected-keyword-arg
        return cls(message=message)

    def _pack(self) -> bytes:
        return pack_dynamic('V', self.message.encode('UTF-8'))

    def validate(self) -> bool:
        return True


class ChatProtocolMessageType(Enum):
    MESSAGE = 1
    USER_LIST = 2


@dataclass
class ChatProtocolMessage(AbstractMessage):
    msg_type: ChatProtocolMessageType
    contents: Union[ChatMessage, ChatUserListMessage]

    @classmethod
    def from_bytes(cls, data: bytes):
        box: tuple = unpack_dynamic('BV', data)
        msg_type = ChatProtocolMessageType(box[0])

        if msg_type == ChatProtocolMessageType.MESSAGE:
            content = ChatMessage.from_bytes(box[1])
        elif msg_type == ChatProtocolMessageType.USER_LIST:
            content = ChatUserListMessage.from_bytes(box[1])
        else:
            raise ValueError()

        # pylint: disable=unexpected-keyword-arg
        return cls(msg_type=msg_type, contents=content)

    def _pack(self) -> bytes:
        return pack_dynamic('BV', self.msg_type.value, self.contents.pack())

    def validate(self) -> bool:
        return True
