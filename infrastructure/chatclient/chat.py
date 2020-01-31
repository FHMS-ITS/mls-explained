from dataclasses import dataclass
from typing import List

from libMLS.session import Session

from chatclient.user import User
from store.message_store import Message


@dataclass
class Chat:
    """
    Manages Chats and ascociated data on client
    """
    name: str
    users: List[User]
    messages: List[Message]

    def __init__(self, username: str, session: Session, chat_users: List[User]):
        self.name = username
        self.users = chat_users
        self.messages = []

        self.session = session

    @classmethod
    def from_welcome(cls, chat_users, username, session) -> "Chat":
        return cls(chat_users=chat_users, username=username, session=session)

    @classmethod
    def from_empty(cls, user: User, groupname: str, keystore):
        session = Session.from_empty(keystore, user.name, groupname)
        return cls(username=user.name, chat_users=[user], session=session)
