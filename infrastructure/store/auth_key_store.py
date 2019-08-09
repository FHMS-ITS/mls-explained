"""
Auth Key Store
"""
from dataclasses import dataclass
from store.store import Store

@dataclass
class AuthKey:
    """
    Key Struct to store Keys and associeted data
    """
    user: str
    device: str
    key: bytes

    def __init__(self, user: str, device: str, key: int = None):
        self.user = user
        self.device = device
        self.key = key


    def to_json(self) -> dict:
        """
        converts Keystruct to json
        """
        key_string = self.key.decode("ascii")
        return {"user": self.user, "device": self.device, "key": key_string}

    def __eq__(self, other):
        if self.user == other.user and self.device == other.device and self.key == other.key:
            return True
        return False

    def same_user_device(self, other):
        """
        Compare only user and device to get key from specific user
        """
        if self.user == other.user and self.device == other.device:
            return True
        return False

class AuthKeyStore(Store):
    """
    Implementation of Store to store AuthKeys
    """

    @classmethod
    def from_json(cls, file_path: str, json_data):
        """
        creates elementstore from given json_data
        and stores the data in file_path
        """
        elementstore = AuthKeyStore(file_path)
        for data in json_data:
            key = data["key"].encode("ascii")
            element = AuthKey(data["user"], data["device"], key)
            elementstore.add_element(element)
        return elementstore

    def add_element(self, element: AuthKey):
        found_key = self.get_element(element)
        if found_key is not None:
            self.remove_element(found_key)
        self.elements.append(element)

    def get_element_by_user_device(self, user: str, device: str):
        """
        wrapper for serching by user and device as str
        """
        comp_key = AuthKey(user, device)
        found_key = self.get_element(comp_key)
        return found_key

    def get_element(self, element: AuthKey) -> AuthKey:
        """
        get the element to a given user/device
        """
        for key in self.elements:
            if key.same_user_device(element):
                return key
        return None

    def load_from_file(self):
        """
        load json from file and parse to elements list
        """
        json_data = super().load_json_from_file()
        #load elements with necesary values into List
        for datum in json_data:
            element_data = AuthKey(datum["user"], datum["device"], datum["key"])
            self.elements.append(element_data)
