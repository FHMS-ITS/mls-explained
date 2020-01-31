"""
Keystore Class zum Storen von Keys in Dateien.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List

from store.store import Store


@dataclass
class Message:
    """
    Class to store messages and associated data
    """
    user: str
    device: str
    message: str
    timestamp: datetime

    def __init__(self, user: str, device: str, message: str,
                 timestamp: datetime = datetime.now()):
        self.user = user
        self.device = device
        self.message = message
        self.timestamp = timestamp

    def to_json(self) -> dict:
        """
        canverts class into json
        """
        timestamp_string = self.timestamp.isoformat(sep=" ")
        return {
            "user": self.user,
            "device": self.device,
            "message": self.message,
            "timestamp": timestamp_string
        }

    def __eq__(self, other):
        if (self.user == other.user
                and self.device == other.device
                and self.message == other.message
                and self.timestamp == other.timestamp):
            return True
        return False

    def same_user_device(self, other) -> bool:
        """
        compares messages only for user and device
        """
        return self.user == other.user and self.device == other.device


    def __lt__(self, other):
        if self.timestamp < other.timestamp:
            return True
        return False

class Messagestore(Store):
    """
    Manages Messages for Dirserver
    """
    @classmethod
    def from_json(cls, file_path: str, json_data):
        """
        creates Messagestore Class from a json_data and creates storefile at file_path
        """
        messagestore = Messagestore(file_path)
        for data in json_data:
            message = Message(data["user"], data["device"], data["message"], data["timestamp"])
            messagestore.add_element(message)
        return messagestore

    def to_json(self) -> dict:
        """
        Converts Messagestore into json
        """
        json_data = []
        for element in self.elements:
            json_data.append(element.to_json())
            return json_data


    def add_element(self, element: Message):
        """
        Adds a Message to Messgestore.
        Since the Server Decides the sequence the time is added here.
        """
        element.timestamp = datetime.now()
        self.elements.append(element)

    def get_messages(self, user: str, device: str) -> List[Message]:
        """
        gets all messages for a given user device
        for server use
        """
        search_message = Message(user, device, None, None)
        result_list = []

        for message in self.elements:
            if search_message.same_user_device(message):
                result_list.append(message)
        for message in result_list:
            self.elements.remove(message)

        return result_list


    def get_element(self, element: Message) -> Message:
        """
        returns first message for given user
        """
        for message in self.elements:
            if element.same_user_device(message):
                return message
        return None

    def get_element_by_user_device(self, user: str, device: str):
        """
        wrapper for get_element to search without creating a class manually
        """
        search_message = Message(user, device, None, None)
        return self.get_element(search_message)

    def remove_message(self, message_data: Message):
        """
        deletes given message from server
        """
        for message in self.elements:
            if message == message_data:
                self.elements.remove(message)
                return
        raise ValueError("Message to be removed was not in list")

    def load_from_file(self):
        json_data = super().load_json_from_file()

        #load elements with necesary values into List
        for datum in json_data:
            message_data = Message(datum["user"],
                                   datum["device"],
                                   datum["message"],
                                   datum["timestamp"])
            self.elements.append(message_data)
