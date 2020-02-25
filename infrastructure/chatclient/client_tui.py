import argparse

from chatclient.client import MLSClient

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
                self.client.send_chat_message(message=message, group_id=receiver)
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
            group_name = input("Group Name:").strip()
            chat = self.client.chats[group_name]
            self.client.group_update(chat)
        if menu_item == 8:
            group_name = input("Group Name:").strip()
            self.client.dump_state_image(group_name=group_name)


def parse_arguments():
    parser = argparse.ArgumentParser(description='MLS Client')
    parser.add_argument('-u', '--user', default='jan', type=str)
    parser.add_argument('-d', '--device', default='phone', type=str)
    parser.add_argument('-ds', '--dirserver', default='127.0.0.1:5001', type=str)
    parser.add_argument('-as', '--authserver', default='127.0.0.1:5000', type=str)
    return parser.parse_args()

def print_main_menu():
    print("++++++++++++Main Menu++++++++++++")
    print("1) Send Message")
    print("2) Request Messages")
    print("3) Send Authkey to Authserver")
    print("4) Send Initkey to Dirserver")
    print("5) Create Group")
    print("6) Add Member")
    print("7) Update Keys")
    print("8) Dump state")
    print("99) Exit")
    print("+++++++++++++++++++++++++++++++++")


def main():
    """
    print menu and pass to according functions
    quick and dirty menu
    """

    args = parse_arguments()
    # load config_file


    client = MLSClient(args.authserver, args.dirserver, args.user, args.device)

    print(f"----Chatclient for----")
    print(f"\tUser: {args.user}")
    print(f"\tDevice: {args.device} ")

    menu = Menu(client)
    menu.run()
