"""
MLS CLient
"""
import argparse
import json
from typing import List, Dict, Optional

import requests
from libMLS.messages import WelcomeInfoMessage, MLSCiphertext, GroupOperation
from libMLS.session import Session
from libMLS.abstract_application_handler import AbstractApplicationHandler

from chatclient.chat import Chat
from chatclient.user import User
from chatclient.key_service import KeyService


def check_auth_server(ip_address: str) -> bool:
    """
    checks a given ip_address for a running MLS Auth Server
    """
    response = requests.get("http://" + ip_address + "/")
    return response.text == "MLS AUTH SERVER"


def check_dir_server(ip_address: str) -> bool:
    """
    checks a given ip_address for a running MLS Dir Server
    """
    response = requests.get("http://" + ip_address + "/")
    return response.text == "MLS DIR SERVER"


class MLSClient(AbstractApplicationHandler):
    """
    Client of the MLS Infrastructure
    """

    def __init__(self, auth_server: str, dir_server: str, user: str, device: str):
        super().__init__()
        self.auth_server = auth_server
        self.dir_server = dir_server
        self.user = user
        self.device = device
        self.chats: Dict[str, Chat] = {}
        self.keystore = KeyService(user, dir_server)

    def add_contact(self, user: str, device: str):
        """
        #TODO: Rename app_add_contact
        creates and adds chat for single user
        """

    def get_auth_key(self, user: str, device: str):
        """
        Request auth_key from auth-server for given user device combination
        :param user:
        :param device:
        :return:
        """
        params = {"user": user, "device": device}
        response = requests.get("http://" + self.auth_server + "/keys", params=params)
        print(response.text)

    def publish_auth_key(self, user: str, device: str, key: str):
        """
        Publish an Authentificaiton key to a keyserver
        :param user:
        :param device:
        :param key:
        :return:
        """
        key_data = json.dumps({"user": user, "device": device, "long_term_key": key})
        response = requests.post("http://" + self.auth_server + "/keys", data=key_data)
        print(response.text)

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
                              message: Optional[str] = None,
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

    def get_messages(self, user: str, device: str):
        """
        Requests messages from dirserver using own identity
        :return:
        """
        params = {"user": user, "device": device}
        response = requests.get("http://" + self.dir_server + "/message", params=params)

        # print(response.content)

        if response.status_code != 200:
            raise RuntimeError(f'GetMessage status code {response.status_code}')

        messages: Dict = json.loads(response.content)
        print(f"Got {len(messages)} messages!")
        for message in messages:

            message_wrapper = message['message']
            is_welcome: bool = message_wrapper['is_welcome']
            message_content: bytes = bytes.fromhex(message_wrapper['message'])

            if is_welcome:
                session: Session = Session.from_welcome(WelcomeInfoMessage.from_bytes(message_content), self.keystore,
                                                        self.user)
                chat_name = session.get_state().get_group_context().group_id.decode('ASCII')
                self.chats[chat_name] = Chat.from_welcome([], user, session)
                print("Got added to group " + chat_name)
                continue

            name = Session.get_groupid_from_cipher(data=message_content).decode('UTF-8')
            self.chats[name].session.process_message(message=MLSCiphertext.from_bytes(message_content), handler=self)

    def on_application_message(self, application_data: bytes, group_id: str):
        print(f"Received Message in Group {group_id}:\n{application_data.decode('UTF-8')}")

    def on_group_welcome(self, session: Session):
        group_name = session.get_state().get_group_context().group_id.decode('ASCII')
        chat = Chat.from_welcome(
            chat_users=[],
            username=self.user,
            session=session,
        )

        self.chats[group_name] = chat

    def on_group_member_added(self, group_id: bytes):
        pass

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
        self.chats[group_name] = Chat.from_empty(User(self.user), group_name, self.keystore)

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

        chat = self.chats[group_name]

        welcome, add = chat.session.add_member(user, b'0')
        group_op = GroupOperation.from_instance(add)

        # add_payload = chat.session.encrypt_handshake_message(add)

        self.send_welcome_to_user(user, welcome)
        chat.users.append(User(user))
        self.send_message_to_group(group_name=group_name, handshake=group_op)

    def get_recievers(self, chat_identifier: str) -> List[User]:
        """
        returns all receivers in a given chat
        """
        for chat_name, chat in self.chats:
            if chat_name == chat_identifier:
                return chat.users
        return []


class Menu:

    def __init__(self, client: MLSClient):
        self.client = client

    def run(self):

        menu_item: int = -1
        while menu_item != 99:
            print_main_menu()
            menu_item = int(input("Enter number of menu item: ").strip())

            self.process_input(menu_item)

    def process_input(self, menu_item: int):
        if menu_item == 1:
            receiver = input("Enter Groupname:")
            if receiver != "":
                message = input("Enter Message:")
                self.client.send_message_to_group(receiver, message=message)
                return
            print("No Receiver found")
        if menu_item == 2:
            print(self.client.get_messages(self.client.user, self.client.device))
        if menu_item == 3:
            key = input("Enter new Auth Key")
            self.client.publish_auth_key(self.client.user, self.client.device, key)
        if menu_item == 4:
            key = input("Enter new init key: ")
            self.client.keystore.register_keypair(key.encode('ascii'), b'0')
        if menu_item == 5:
            # create grp
            group_name = input("Group Name:").strip()
            self.client.group_creation(group_name=group_name)
        if menu_item == 6:
            # Add member
            group_name = input("Group Name:").strip()
            user_to_add = input("User to add:").strip()

            self.client.group_add(group_name=group_name, user=user_to_add)
        if menu_item == 7:
            # Remove member
            pass


def parse_arguments():
    parser = argparse.ArgumentParser(description='MLS yo.')
    parser.add_argument('-u', '--user', default='jan', type=str)

    return parser.parse_args()


def print_main_menu():
    print("++++++++++++Main Menu++++++++++++")
    print("1) Send Message")
    print("2) Request Messages")
    print("3) Send Authkey to Authserver")
    print("4) Send Initkey to Dirserver")
    print("5) Create Group")
    print("6) Add Member")
    print("7) Remove Member")
    print("99) Exit")
    print("+++++++++++++++++++++++++++++++++")


def main():
    """
    print menu and pass to according functions
    quick and dirty menu
    """

    args = parse_arguments()
    # load config_file
    try:
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
            dir_server = config["dir_server"]
            auth_server = config["auth_server"]
            user = config["user"]
            device = config["device"]
    except (KeyError, FileNotFoundError):
        # set defaults
        dir_server = "127.0.0.1:5001"
        auth_server = "127.0.0.1:5000"
        user = args.user
        device = "phone"

    print(f"----Chatclient for----")
    print(f"\tUser: {user}")
    print(f"\tDevice: {device} ")

    client = MLSClient(auth_server, dir_server, user, device)
    menu = Menu(client=client)
    menu.run()
