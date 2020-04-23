# pylint: disable-all

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtSvg import QSvgWidget
from chatclient.client import *
from chatclient.chat_protocol import *
from chatclient.message import Message
from chatclient.key_service import NoKeysAvailableException

from dataclasses import dataclass
import sys
import json
import argparse
import os
import requests

APP = None

@dataclass
class DotImage:
    path: str
    name: str

class DotWidget(QWidget):
    def __init__(self, path:str, gui):
        super().__init__()
        self.gui = gui

        self.label = QLabel(f"Dot Dump:")
        self.display = QSvgWidget()
        self.display.load(path)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.display)

        self.setWindowTitle(self.gui.windowTitle())

        self.setLayout(self.layout)

class MessageWidget(QWidget):
    def __init__(self, message: Message, gui):
        super().__init__()
        self.gui = gui
        self.message = message

        self.horizontal_layout = QHBoxLayout()
        self.message_and_description = QWidget()
        self.message_and_description_layout = QVBoxLayout()
        self.message_and_description_layout.addWidget(QLabel(message.description))
        self.message_and_description_layout.addWidget(QLabel(message.message))
        self.message_and_description.setLayout(self.message_and_description_layout)
        self.horizontal_layout.addWidget(self.message_and_description)
        self.state_button = QPushButton("State Diagram")
        self.state_button.clicked.connect(self.button_function)
        self.horizontal_layout.addStretch()
        self.horizontal_layout.addWidget(self.state_button)
        self.setLayout(self.horizontal_layout)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum))



    def button_function(self):
        if self.message.state_path is not "":
            self.dot_widget = DotWidget(self.message.state_path, self.gui)
            self.dot_widget.move(self.gui.pos())
            self.dot_widget.show()
        else:
            self.message_box = QMessageBox()
            self.message_box.setText("No state generated for this Message")
            self.message_box.move(self.gui.pos())
            self.gui.status_bar.showMessage("No state generated for this Message")
            self.message_box.show()


class ChatWidget(QWidget):
    def __init__(self, chat: Chat, gui):
        super().__init__()
        self.chat = chat
        self.gui = gui

        self.groupname_label = QLabel(chat.name)
        user_string = ', '.join([user.name for user in gui.client.chats[chat.name].users])
        self.userlist_label = QLabel(user_string)

        self.horizontal_layout = QHBoxLayout()

        self.button = QPushButton("Show")

        self.vertical_widget = QWidget()
        self.vertical_layout = QVBoxLayout()
        self.vertical_layout.addWidget(self.groupname_label)
        self.vertical_layout.addWidget(self.userlist_label)

        self.vertical_widget.setLayout(self.vertical_layout)

        self.horizontal_layout.addWidget(self.vertical_widget)
        self.horizontal_layout.addStretch()
        self.horizontal_layout.addWidget(self.button)

        self.setLayout(self.horizontal_layout)

        self.button.clicked.connect(self.activate_chat)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum))

    def activate_chat(self):
        self.gui.active_chat = self.chat
        self.gui.message_list.chat = self.chat
        self.gui.message_list.display_chat(self.chat)
        self.gui.status_bar.showMessage(f"Activated Chat: {self.chat.name}")


class ChatMenuBar(QToolBar):
    def __init__(self, client: MLSClient, gui):
        super().__init__()
        self.client = client
        self.gui = gui

        self.add_user_button = QToolButton()
        self.add_user_button.setText("Add User")
        self.add_user_button.clicked.connect(self.add_user_button_function)
        self.addWidget(self.add_user_button)

        self.show_state_button = QToolButton()
        self.show_state_button.setText("Show Tree")
        self.show_state_button.clicked.connect(self.show_state_button_function)
        self.addWidget(self.show_state_button)

        self.send_update_button = QToolButton()
        self.send_update_button.setText("Send Update")
        self.send_update_button.clicked.connect(self.send_update_button_function)
        self.addWidget(self.send_update_button)

        self.protocol_check_box = QCheckBox("Show Protocol Messages")
        self.protocol_check_box.setChecked(True)
        self.addWidget(self.protocol_check_box)

    def add_user_button_function(self):
        if not self.gui.enforce_refresh:
            if self.gui.active_chat is not None:
                self.add_user_window = AddUserWindow(self.client, self.gui)
                self.add_user_window.move(self.gui.pos())
                self.add_user_window.show()
            else:
                self.no_chat_selected_message()
        else:
            self.message_box = QMessageBox()
            self.message_box.setText("Please refresh before adding another user!")
            self.message_box.move(self.gui.pos())
            self.message_box.show()

    def show_state_button_function(self):
        if self.gui.active_chat is not None:
            path = self.client.dump_state_image(self.gui.active_chat.name)
            self.dotwidget = DotWidget(path, self.gui)
            self.dotwidget.move(self.gui.pos())
            self.dotwidget.show()
        else:
            self.no_chat_selected_message()

    def send_update_button_function(self):
        if self.gui.active_chat is not None:
            self.client.group_update(self.gui.active_chat)
            self.gui.status_bar.showMessage("Sent Update Message. Refresh!")
        else:
            self.no_chat_selected_message()

    def no_chat_selected_message(self):
        self.message_box = QMessageBox()
        self.message_box.setText("Please select and/or create a Chat first")
        self.message_box.move(self.gui.pos())
        self.gui.status_bar.showMessage("Please select and/or create a Chat first")
        self.message_box.show()

class MainMenuBar(QToolBar):
    def __init__(self, client: MLSClient, gui):
        super().__init__()
        self.client = client
        self.gui = gui

        self.post_init_key_button = QToolButton()
        self.post_init_key_button.setText("Post Init Keys")
        self.post_init_key_button.clicked.connect(self.post_init_key_button_function)
        self.addWidget(self.post_init_key_button)

        self.refresh_button = QToolButton()
        self.refresh_button.setText("Refresh")
        self.refresh_button.clicked.connect(self.refresh_button_function)
        self.addWidget(self.refresh_button)

        self.create_chat_button = QToolButton()
        self.create_chat_button.setText("Create Group")
        self.create_chat_button.clicked.connect(self.create_chat_function)
        self.addWidget(self.create_chat_button)

    def post_init_key_button_function(self):
        try:
            for _ in range(10):
                key = os.urandom(10)
                self.client.keystore.register_keypair(key, b'0')
            self.message_box = QMessageBox()
            self.message_box.setText("10 init-keys stored on dirserver")
            self.message_box.move(self.gui.pos())
            self.gui.status_bar.showMessage("10 init-keys stored on dirserver")
            self.message_box.show()
        except ConnectionError:
            self.message_box = QMessageBox()
            self.message_box.setText("There must be a Dirserver running to store Initkeys")
            self.message_box.move(self.gui.pos())
            self.gui.status_bar.showMessage("There must be a Dirserver running to store Initkeys")
            self.message_box.show()

    def create_chat_function(self):
        self.create_chat_window = CreateChatWindow(self.client, self.gui)
        self.create_chat_window.move(self.gui.pos())
        self.create_chat_window.show()


    def refresh_button_function(self):
        try:
            self.gui.refresh()
            self.gui.status_bar.showMessage("Refreshed!")
        except ConnectionError:
            self.message_box = QMessageBox()
            self.message_box.setText("There must be a Dirserver running to recieve Messages")
            self.message_box.move(self.gui.pos())
            self.gui.status_bar.showMessage("There must be a Dirserver running to recieve Messages")
            self.message_box.show()


class AddUserWindow(QWidget):
    def okayButtonFunction(self):
        try:
            if self.gui.active_chat is not None:
                user_name = self.user_name_line_edit.text()
                self.client.group_add(self.gui.active_chat.name, user_name)
                self.gui.enforce_refresh = True
                self.gui.status_bar.showMessage("Welcome Message sent to Dirserver. Refresh!")
                self.message_box = QMessageBox()
                self.message_box.setText("Welcome Message sent to Dirserver. Refresh before adding another user!")
                self.message_box.move(self.gui.pos())
                self.close()
        except NoKeysAvailableException:
            self.message_box = QMessageBox()
            self.message_box.setText("The given user has no Keys on the dir server")
            self.message_box.move(self.gui.pos())
            self.gui.status_bar.showMessage("The given user has no Keys on the dir server")
            self.message_box.show()
        except ConnectionError:
            self.message_box = QMessageBox()
            self.message_box.setText("There must be a dirserver running to add a User")
            self.message_box.move(self.gui.pos())
            self.message_box.show()
            self.gui.status_bar.showMessage("There must be a dirserver running to add a User")
            self.close()

    def cancelButtonFunction(self):
        self.gui.status_bar.showMessage("Add User Canceled")
        self.close()

    def __init__(self, client: MLSClient, gui):
        super().__init__()
        self.gui = gui
        self.client = client
        self.group_name_label = QLabel("User Name")
        self.user_name_line_edit = QLineEdit()

        self.okay_button = QPushButton("Okay")
        self.okay_button.clicked.connect(self.okayButtonFunction)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancelButtonFunction)

        self.fbox = QFormLayout()
        self.fbox.addRow(self.group_name_label, self.user_name_line_edit)
        self.fbox.addRow(self.okay_button, self.cancel_button)

        self.setLayout(self.fbox)
        self.setWindowTitle("Add User")


class CreateChatWindow(QWidget):
    def okayButtonFunction(self):
        try:
            group_name = self.group_name_line_edit.text()
            self.client.group_creation(group_name)
            self.gui.chat_list.display_chats()
            self.close()
            self.gui.active_chat = self.client.chats[group_name]
            self.gui.message_list.display_chat(self.gui.active_chat)
            self.gui.status_bar.showMessage("Local Group Creation Done. Add a User now!")
        except ConnectionError:
            self.message_box = QMessageBox()
            self.message_box.setText("There must be a Dirserver running to create a Chat")
            self.message_box.move(self.gui.pos())
            self.gui.status_bar.showMessage("There must be a Dirserver running to create a Chat")
            self.message_box.show()
            self.close()
        except NoKeysAvailableException:
            self.message_box = QMessageBox()
            self.message_box.setText("There must be Init Keys on the Dirserver. Please add them first")
            self.message_box.move(self.gui.pos())
            self.gui.status_bar.showMessage("There must be Init Keys on the Dirserver. Please add them first")
            self.message_box.show()
            self.close()

    def cancelButtonFunction(self):
        self.close()

    def __init__(self, client: MLSClient, gui):
        super().__init__()
        self.gui = gui
        self.client = client
        self.group_name_label = QLabel("Group Name")
        self.group_name_line_edit = QLineEdit()

        self.okay_button = QPushButton("Okay")
        self.okay_button.clicked.connect(self.okayButtonFunction)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancelButtonFunction)

        self.fbox = QFormLayout()
        self.fbox.addRow(self.group_name_label, self.group_name_line_edit)
        self.fbox.addRow(self.okay_button, self.cancel_button)

        self.setLayout(self.fbox)
        self.setWindowTitle("Group Creation")

class MessageTextField(QWidget):
    def __init__(self, client: MLSClient, gui):
        super().__init__()
        self.gui = gui
        self.client = client
        self.layout = QHBoxLayout()
        self.line_edit = QLineEdit()
        self.send_button = QPushButton("Send")
        self.layout.addWidget(self.line_edit)
        self.layout.addWidget(self.send_button)
        self.send_button.clicked.connect(self.send_function)
        self.setLayout(self.layout)

    def send_function(self):
        try:
            if self.gui.active_chat is not None:
                self.client.send_chat_message(self.line_edit.text(), self.gui.active_chat.name)
                self.gui.status_bar.showMessage("Message Sent. Refresh!")
            else:
                self.message_box = QMessageBox()
                self.message_box.setText("You must select a Chat to send a Message")
                self.message_box.move(self.gui.pos())
                self.gui.status_bar.showMessage("You must select a Chat to send a Message")
                self.message_box.show()
            self.line_edit.setText("")
        except ConnectionError:
            self.message_box = QMessageBox()
            self.message_box.setText("There must be a Dirserver running to send a Message")
            self.message_box.move(self.gui.pos())
            self.message_box.show()
            self.gui.status_bar.showMessage("There must be a Dirserver running to send a Message")
            self.close()

class MessageList(QScrollArea):
    def __init__(self, client: MLSClient, gui, chat = None):
        super().__init__()
        self.chat = chat
        self.widget = QWidget()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.widget)
        self.display_chat(self.chat)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setWidgetResizable(True)
        self.setWidget(self.widget)
        self.client = client
        self.gui = gui

    def display_chat(self, chat=None):
        self.widget.deleteLater()
        self.layout = QVBoxLayout()
        self.widget = QWidget()
        self.chat = chat
        if chat is None:
            self.label = QLabel()
            self.label.setText("No Chat Selected")
            self.layout.addWidget(self.label)
            self.widget.setLayout(self.layout)
        else:
            if self.gui.chat_menu_bar.protocol_check_box.isChecked():
                for message in chat.messages:
                    message_widget = MessageWidget(message, self.gui)
                    self.layout.addWidget(message_widget)
            else:
                for message in chat.messages:
                    if message.protocol is False:
                        message_widget = MessageWidget(message, self.gui)
                        self.layout.addWidget(message_widget)
            self.layout.addStretch()
            self.widget.setLayout(self.layout)
            self.setWidget(self.widget)


class ChatList(QScrollArea):
    def __init__(self, client: MLSClient, gui):
        super().__init__()
        self.widget = QWidget()
        self.layout = QVBoxLayout()
        self.client = client
        self.gui = gui
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setWidgetResizable(True)
        self.setWidget(self.widget)
        self.display_chats()

    def display_chats(self):
        self.widget.deleteLater()
        self.layout = QVBoxLayout()
        self.widget = QWidget()
        print(self.client.chats)
        if self.client is None:
            label = QLabel("No Client Configured")
            self.layout.addWidget(label)
            self.widget.setLayout(self.layout)
        elif self.client.chats == {}:
            print("testing")
            label = QLabel("No Chats Found")
            self.layout.addWidget(label)
            self.widget.setLayout(self.layout)
        else:
            for chat in self.client.chats:
                self.layout.addWidget(ChatWidget(self.client.chats[chat], self.gui))
                self.widget.setLayout(self.layout)
            self.layout.addStretch()
        self.setWidget(self.widget)


class GUI(QMainWindow):
    def __init__(self, client: MLSClient):
        super().__init__()
        self.client = client

        self.enforce_refresh = False

        self.active_chat = None

        self.toolbar = MainMenuBar(client, self)
        self.addToolBar(self.toolbar)

        self.chat_list = ChatList(client, self)

        self.message_list = MessageList(client, self)

        self.message_text_field = MessageTextField(client, self)
        self.left_side_widget = QWidget()
        self.left_side_widget_layout = QVBoxLayout()
        self.chat_menu_bar = ChatMenuBar(client, self)
        self.left_side_widget_layout.addWidget(self.chat_menu_bar)
        self.left_side_widget_layout.addWidget(self.message_list)
        self.left_side_widget_layout.addWidget(self.message_text_field)
        self.left_side_widget.setLayout(self.left_side_widget_layout)

        self.qhboxlayout = QHBoxLayout()
        self.qhboxlayout.addWidget(self.chat_list)
        self.qhboxlayout.addWidget(self.left_side_widget)
        self.horizontal_widget = QWidget()
        self.horizontal_widget.setLayout(self.qhboxlayout)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.setCentralWidget(self.horizontal_widget)
        self.setWindowTitle(f"MLS Client GUI von {self.client.user}")

        self.resize(1000, 600)
        self.show()

    def refresh(self):
        amount_of_new_messages = self.client.get_messages(self.client.user, self.client.device)
        self.chat_list.display_chats()
        self.message_list.display_chat(self.active_chat)

        self.amount_of_new_messages_message_box = QMessageBox()
        self.amount_of_new_messages_message_box.setText(f"{amount_of_new_messages} new messages received")
        self.amount_of_new_messages_message_box.move(self.pos())
        self.amount_of_new_messages_message_box.show()

        self.status_bar.showMessage(f"{amount_of_new_messages} new messages received")

        self.enforce_refresh = False

class SetUpWindow(QWidget):
    def okayButtonFunction(self):
        checks = True
        self.auth_server = self.auth_server_line_edit.text()
        self.dir_server = self.dir_server_line_edit.text()
        checks = self.check_dir_server()
        if self.user_name_line_edit.text() == "":
            print("test")
            self.message_box1 = QMessageBox()
            self.message_box1.setText("Please add a user name")
            self.message_box1.show()
            checks = False
        else:
            self.user = self.user_name_line_edit.text()

        self.device = "phone"

        if checks:
            self.close()

    def check_dir_server(self):
        try:
            response = requests.get("http://" + self.dir_server_line_edit.text() + "/")
            if response.text != "MLS DIR SERVER":
                raise requests.exceptions.ConnectionError
            return True
        except requests.exceptions.ConnectionError:
            self.check_dir_server_message_box = QMessageBox()
            self.check_dir_server_message_box.setText(f"No Dir Server reachable on this IP")
            self.check_dir_server_message_box.move(self.pos())
            self.check_dir_server_message_box.show()

    def check_auth_server(self):
        try:
            response = requests.get("http://" + self.auth_server_line_edit.text() + "/")
            if response.text != "MLS AUTH SERVER":
                raise requests.exceptions.ConnectionError
        except requests.exceptions.ConnectionError:
            self.check_auth_server_message_box = QMessageBox()
            self.check_auth_server_message_box.setText(f"No Auth Server reachable on this IP")
            self.check_auth_server_message_box.move(self.pos())
            self.check_auth_server_message_box.show()


    def cancelButtonFunction(self):
        self.close()

    def retrieve_inputs(self):
        return self.auth_server, self.dir_server, self.user, "phone"

    def __init__(self, auth_server:str, dir_server:str, user:str, device:str):
        super().__init__()

        self.auth_server = auth_server
        self.dir_server = dir_server
        self.user = user
        self.device = device

        self.dir_server_label = QLabel("Directory Server")
        self.dir_server_line_edit = QLineEdit()
        self.dir_server_line_edit.setText(self.dir_server)

        self.auth_server_label = QLabel("Auth Server")
        self.auth_server_line_edit = QLineEdit()
        self.auth_server_line_edit.setText(self.auth_server)

        self.user_name_label = QLabel("User Name")
        self.user_name_line_edit = QLineEdit()
        self.user_name_line_edit.setText(self.user)

        #self.device_name_label = QLabel("Device")
        #self.device_name_line_edit = QLineEdit()
        #self.device_name_line_edit.setText(self.device)

        self.okay_button = QPushButton("Okay")
        self.okay_button.clicked.connect(self.okayButtonFunction)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancelButtonFunction)

        self.fbox = QFormLayout()
        self.fbox.addRow(self.dir_server_label, self.dir_server_line_edit)
        self.fbox.addRow(self.auth_server_label, self.auth_server_line_edit)
        self.fbox.addRow(self.user_name_label, self.user_name_line_edit)
        #self.fbox.addRow(self.device_name_label, self.device_name_line_edit)
        self.fbox.addRow(self.okay_button, self.cancel_button)

        self.setLayout(self.fbox)
        self.setWindowTitle("MLS Setup")


def parse_arguments():
    parser = argparse.ArgumentParser(description='MLS Client')
    parser.add_argument('-u', '--user', type=str)
    parser.add_argument('-d', '--device', type=str)
    parser.add_argument('-ds', '--dirserver', default='127.0.0.1:5001', type=str)
    parser.add_argument('-as', '--authserver', default='127.0.0.1:5000', type=str)
    return parser.parse_args()

def main():
    args = parse_arguments()

    SetupApplication = QApplication(sys.argv)

    setup_window = SetUpWindow(args.authserver, args.dirserver, args.user, args.device)
    setup_window.show()

    SetupApplication.exec_()

    auth_server, dir_server, user, device = setup_window.retrieve_inputs()

    client = MLSClient(auth_server, dir_server, user, device)
    APP = QApplication(sys.argv)
    main_window = GUI(client)
    sys.exit(APP.exec_())

if __name__ == '__main__':
    main()
