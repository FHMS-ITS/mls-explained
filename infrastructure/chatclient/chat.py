from dataclasses import dataclass
from typing import List

from libMLS.dot_dumper import DotDumper
from libMLS.session import Session

from chatclient.user import User
#from store.message_store import Message


@dataclass
class Chat:
    """
    Manages Chats and ascociated data on client
    """
    name: str
    users: List[User]
    messages: List[str]

    def __init__(self, groupname: str, session: Session, chat_users: List[User]):
        self.name = groupname
        self.users = chat_users
        self.messages = []
        self.session = session

        self.dumper = DotDumper(
            self.session,
            group_name=self.session.get_state().get_group_context().group_id.decode('utf-8')
        )

    @classmethod
    def from_welcome(cls, chat_users, groupname, session) -> "Chat":
        return cls(chat_users=chat_users, groupname=groupname, session=session)

    @classmethod
    def from_empty(cls, user: User, groupname: str, keystore):
        session = Session.from_empty(keystore, user.name, groupname)
        return cls(groupname=groupname, chat_users=[user], session=session)
