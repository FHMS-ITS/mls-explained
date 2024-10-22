"""
MLS CLient
"""
import json
from typing import List, Dict, Optional

import requests

from libMLS.abstract_application_handler import AbstractApplicationHandler
from libMLS.messages import WelcomeInfoMessage, MLSCiphertext, GroupOperation
from libMLS.session import Session

from chatclient.chat import Chat
from chatclient.message import Message
from chatclient.key_service import KeyService
from chatclient.user import User

from .chat_protocol import ChatProtocolMessage, ChatMessage, ChatUserListMessage, ChatProtocolMessageType


class MLSClient(AbstractApplicationHandler):
    """
    Client of the MLS Infrastructure
    """
    def check_auth_server(self) -> bool:
        """
        checks a given ip_address for a running MLS Auth Server
        """
        try:
            response = requests.get("http://" + self.auth_server + "/")
            return response.text == "MLS AUTH SERVER"
        except requests.exceptions.ConnectionError:
            raise ConnectionError


    def check_dir_server(self) -> bool:
        """
        checks a given ip_address for a running MLS Dir Server
        """
        try:
            response = requests.get("http://" + self.dir_server + "/")
            return response.text == "MLS DIR SERVER"
        except requests.exceptions.ConnectionError:
            raise ConnectionError

    def __init__(self, auth_server: str, dir_server: str, user: str, device: str):
        super().__init__()
        self.auth_server = auth_server
        self.dir_server = dir_server
        self.user = user
        self.device = device
        self.chats: Dict[str, Chat] = {}
        self.keystore = KeyService(user, dir_server)
        self.keystore.clear_data(self.user, self.device)

    def get_auth_key(self, user: str, device: str):
        """
        Request auth_key from auth-server for given user device combination
        :param user:
        :param device:
        :return:
        """
        params = {"user": user, "device": device}
        requests.get("http://" + self.auth_server + "/keys", params=params)

    def publish_auth_key(self, user: str, device: str, key: str):
        """
        Publish an Authentificaiton key to a keyserver
        :param user:
        :param device:
        :param key:
        :return:
        """
        key_data = json.dumps({"user": user, "device": device, "long_term_key": key})
        requests.post("http://" + self.auth_server + "/keys", data=key_data)

    def send_welcome_to_user(self, user_name: str, message: WelcomeInfoMessage):
        message_data = json.dumps(
            {
                "receivers": [{"user": user_name, "device": "phone"}],
                "message": {"message": message.pack().hex(), "is_welcome": True}
            })
        requests.post("http://" + self.dir_server + "/message",
                      data=message_data)

    def send_message_to_group(self,
                              group_name: str,
                              message: Optional[bytes] = None,
                              handshake: Optional[GroupOperation] = None):
        """
        Sends message to dirserver to do serverside fanout

        Since the dir server should not have permanent information about
        groups the client is responsible for
        sending messages to all menbers of a group
        :param group_name:
        :param handshake:
        :param message: The Message itself
        """
        try:
            if message is not None and handshake is not None or handshake is None and message is None:
                raise ValueError("Specify either a handshake or an app message")

            chat = self.chats[group_name]

            all_users = []
            for some_user in chat.users:
                all_users.append({"user": some_user.name, "device": some_user.devices[0]})

            # print(f"Sending message to users [{';'.join([u.name for u in chat.users])}]")
            if message is not None:
                encrypted_message = chat.session.encrypt_application_message(message=message)
            else:
                encrypted_message = chat.session.encrypt_handshake_message(group_op=handshake)

            message_data = json.dumps(
                {
                    "receivers": all_users,
                    "message": {"message": encrypted_message.pack().hex(), "is_welcome": False}
                }
            )
            response = requests.post("http://" + self.dir_server + "/message",
                                     data=message_data)
            # print(response.text)
        except requests.exceptions.ConnectionError:
            raise ConnectionError

    def get_messages(self, user: str, device: str):
        """
        Requests messages from dirserver using own identity
        :return:
        """
        try:
            params = {"user": user, "device": device}
            response = requests.get("http://" + self.dir_server + "/message", params=params)

            # print(response.content)

            if response.status_code != 200:
                raise RuntimeError(f'GetMessage status code {response.status_code}')

            messages: Dict = json.loads(response.content)
            print(f"Got {len(messages)} messages!")

            for message in messages:
                print(message)
                message_wrapper = message['message']
                is_welcome: bool = message_wrapper['is_welcome']
                message_content: bytes = bytes.fromhex(message_wrapper['message'])

                if is_welcome:
                    session: Session = Session.from_welcome(WelcomeInfoMessage.from_bytes(message_content), self.keystore,
                                                            self.user)
                    chat_name = session.get_state().get_group_context().group_id.decode('ASCII')
                    self.chats[chat_name] = Chat.from_welcome([], chat_name, session)
                    print("Got added to group " + chat_name)
                    continue

                name = Session.get_groupid_from_cipher(data=message_content).decode('UTF-8')
                self.chats[name].session.process_message(message=MLSCiphertext.from_bytes(message_content), handler=self)
            return len(messages)
        except requests.exceptions.ConnectionError:
            raise ConnectionError

    def on_application_message(self, application_data: bytes, group_id: str):

        msg = ChatProtocolMessage.from_bytes(application_data)

        if isinstance(msg.contents, ChatMessage):

            message = Message(description="Application Message:",
                              message=msg.contents.message,
                              protocol=False)
            message.state_path = self.dump_state_image(group_id)

            self.chats[group_id].messages.append(message)
            print(f"Received Message in Group {group_id}:\n{msg.contents.message}")
        elif isinstance(msg.contents, ChatUserListMessage):
            users_string = ", ".join(msg.contents.user_names)
            message = Message(description="User List:",
                              message=users_string,
                              protocol=True)
            message.state_path = self.dump_state_image(group_id)

            self.chats[group_id].messages.append(message)
            self.chats[group_id].users = [User(name) for name in msg.contents.user_names]
            print(f"Updated members of group {group_id}: {';'.join([user.name for user in self.chats[group_id].users])}")
        else:
            raise RuntimeError()

    def send_chat_message(self, message: str, group_id: str):
        # pylint: disable=unexpected-keyword-arg

        name_update_msg = ChatProtocolMessage(
            msg_type=ChatProtocolMessageType.MESSAGE,
            contents=ChatMessage(message=message)
        )

        self.send_message_to_group(group_name=group_id, message=name_update_msg.pack())

    def on_group_welcome(self, session: Session):

        groupname = session.get_state().get_group_context().group_id.decode('ASCII')
        chat = Chat.from_welcome(
            chat_users=[],
            groupname=groupname,
            session=session,
        )

        self.chats[groupname] = chat

        message = Message(description="Welcome Message:",
                          message=groupname,
                          protocol=True)
        message.state_path = self.dump_state_image(groupname)

        self.chats[groupname].messages.append(message)

    def on_group_member_added(self, group_id: bytes):
        group_name = group_id.decode('ASCII')
        message = Message(description="Group Member Added!",
                          message=group_name,
                          protocol=True)
        message.state_path = self.dump_state_image(group_name)

        self.chats[group_name].messages.append(message)

    def on_keys_updated(self, group_id: bytes):
        group_name = group_id.decode('ASCII')
        message = Message(description="Updated Keys:",
                          message=group_name,
                          protocol=True)
        message.state_path = self.dump_state_image(group_name)

        self.chats[group_name].messages.append(message)

    def group_creation(self, group_name: str):
        """
        create a group with yourself and user
        :param group_name:
        :return:
        """

        # Download init-Keys for all users form dir Server(requestinitialkey messages to dir server)

        # initialize group-state only containing oneself

        # Compute Welcome and add messaged

        # Send welcome messaged directly to the member added first

        # Add further Members with group_add
        try:
            print(group_name)
            self.chats[group_name] = Chat.from_empty(User(self.user), group_name, self.keystore)
            print(self.chats[group_name])
            message = Message(description="Dummy Message: Group Created",
                              message=group_name,
                              protocol=True)
            message.state_path = self.dump_state_image(group_name)

            self.chats[group_name].messages.append(message)
        except requests.exceptions.ConnectionError:
            raise ConnectionError()


    def group_add(self, group_name: str, user: str):
        """
        Add a member to a group
        Just adding to channel for now
        :return:
        """

        # get init-key of new member

        # broadcast add message

        # update state(every member)

        # send welcome message
        try:
            chat = self.chats[group_name]

            welcome, add = chat.session.add_member(user, b'0')
            group_op = GroupOperation.from_instance(add)

            # add_payload = chat.session.encrypt_handshake_message(add)

            self.send_welcome_to_user(user, welcome)
            chat.users.append(User(user))
            self.send_message_to_group(group_name=group_name, handshake=group_op)

            # pylint: disable=unexpected-keyword-arg
            name_update_msg = ChatProtocolMessage(
                msg_type=ChatProtocolMessageType.USER_LIST,
                contents=ChatUserListMessage(user_names=[user.name for user in chat.users])
            )

            self.send_message_to_group(group_name=group_name, message=name_update_msg.pack())
        except requests.exceptions.ConnectionError:
            raise ConnectionError

    def group_update(self, chat: Chat):
        update_message = chat.session.update()
        group_op = GroupOperation.from_instance(update_message)
        self.send_message_to_group(group_name=chat.name, handshake=group_op)

    def get_recievers(self, chat_identifier: str) -> List[User]:
        """
        returns all receivers in a given chat
        """
        for chat_name, chat in self.chats:
            if chat_name == chat_identifier:
                return chat.users
        return []

    def dump_state_image(self, group_name: str):
        return self.chats[group_name].dumper.dump_next_state()
