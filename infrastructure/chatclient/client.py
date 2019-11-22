"""
MLS CLient
"""
import json
from dataclasses import dataclass, field
from typing import List, Dict
import requests
import LibMLS

from store.message_store import Message

from infrastructure.chatclient.KeyService import KeyService


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


@dataclass
class User:
    """
    Manages Data and devices ascociated with a user
    """
    name: str
    devices: List[str] = field(default_factory=['phone'])


@dataclass
class Chat:
    """
    Manages Chats and ascociated data on client
    """
    name: str
    users: List[User]
    messages: List[Message]

    def __init__(self, username: str, groupname: str, keystore: KeyService):
        self.name = username
        self.users = []
        self.messages = []

        self.session = LibMLS.Session.from_empty(keystore, username, groupname)


class MLSClient:
    """
    Client of the MLS Infrastructure
    """

    def __init__(self, auth_server: str, dir_server: str, user: str, device: str):
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
        # contact = User(user, [device])
        # chat = Chat(user)
        # chat.users.append(contact)
        # self.chats.append(chat)
        pass

    def send_message(self, receivers: List[User], message: str):
        """
        Sends message to dirserver to do serverside fanout

        Since the dir server should not have permanent information about
        groups the client is responsible for
        sending messages to all menbers of a group
        :param receivers: List of Reciever of the message
        :param message: The Message itself
        :return: some Return code???
        """
        message_data = json.dumps({"receivers": receivers, "message": message})
        response = requests.post("http://" + self.dir_server + "/message",
                                 data=message_data)
        print(response.text)

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

    def get_messages(self, user: str):
        """
        Requests messages from dirserver using own identity
        :return:
        """
        params = {"user": user}
        response = requests.get("http://" + self.dir_server + "/message", params=params)



    def group_creation(self, group_name: str, user: str):
        """
        create a group with yourself and user
        :param user:
        :return:
        """

        # Download init-Keys for all users form dir Server(requestinitialkey messages to dir server)

        # initialize group-state only containing oneself

        # Compute Welcome and add messaged

        # Send welcome messaged directly to the member added first

        # Add further Members with group_add
        self.chats[group_name] = (Chat(user, group_name, self.keystore))

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
        user = User(name=user)

        WelcomeInfoMessage, AddMessage = chat.session.add_member(user, b'0')

        welcome_payload = WelcomeInfoMessage.pack()
        add_payload = AddMessage.pack()

        self.send_message([user], welcome_payload.decode('ascii'))
        chat.users.append(user)
        self.send_message(chat.users, add_payload.decode('ascii'))

    def get_recievers(self, chat_identifier: str) -> List[User]:
        """
        returns all receivers in a given chat
        """
        for chat in self.chats:
            if chat.name == chat_identifier:
                return chat.users
        return None


def print_main_menu():
    """
    Pylint: Duh?!
    """
    print("Main Menu")
    print("1) Send Message")
    print("2) Request Messages")
    print("3) Send Authkey to Authserver")
    print("4) Send Initkey to Dirserver")
    print("5) Create Group")
    print("6) Add Member")
    print("7) Remove Member")
    print("99) Exit")


# pylint: disable=too-many-function-args
# false positive?
def main():
    """
    print menu and pass to according functions
    quick and dirty menu
    """
    menu_item = 0

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
        dir_server = "127.0.0.1:5000"
        auth_server = "127.0.0.1:5001"
        user = "Jan"
        device = "Phone"

    client = MLSClient(auth_server, dir_server, user, device)

    while menu_item != "99":
        print_main_menu()
        menu_item = input("Enter number of menu item: ")

        if menu_item == "1":
            receiver = input("Enter Receiving Channel:")
            receiver_list = client.get_recievers(receiver)
            if receiver_list is not None:
                message = input("Enter Message:")
                client.send_message(receiver_list, message)
                continue
            print("No Receiver found")
            continue
        if menu_item == "2":
            print(client.get_messages(client.user))
            continue
        if menu_item == "3":
            key = input("Enter new Auth Key")
            client.publish_auth_key(client.user, client.device, key)
            continue
        if menu_item == "4":
            key = input("Enter new init key")
            client.keystore.register_keypair(key.encode('ascii'), b'0')
            continue
        if menu_item == "5":
            # create grp
            pass
        if menu_item == "6":
            # Add member
            pass
        if menu_item == "7":
            # Remove member
            pass
