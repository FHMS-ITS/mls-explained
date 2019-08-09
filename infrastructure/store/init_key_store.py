"""
Init Key Store
"""
from dataclasses import dataclass

from store.store import Store


@dataclass
class InitKey:
    """
    Key Struct to store InitKeys and associated data
    """
    user: str
    identifier: int
    key: bytes

    def __init__(self, user: str, identifier: int, key: bytes):
        self.user = user
        self.identifier = identifier
        self.key = key

    def to_json(self) -> dict:
        """
        converts Keystruct to json
        """
        key_string = self.key.decode("ascii")
        return {"user": self.user, "identifier": self.identifier, "key": key_string}

    def __eq__(self, other):
        if self.user == other.user and self.key == other.key:
            return True
        return False

    def same_user(self, other):
        """
        true if same user to get init keys for one specific user
        """
        if self.user == other.user:
            return True
        return False

class InitKeyStore(Store):
    """
    Implementation of store to store init_keys
    """
    @classmethod
    def from_json(cls, file_path: str, json_data):
        """
        creates keystore from given json_data
        and stores the data in file_path
        """
        keystore = InitKeyStore(file_path)
        for data in json_data:
            key_bytes = data["key"].encode("ascii")
            key = InitKey(data["user"], data["identifier"], key_bytes)
            keystore.add_element(key)
        return keystore

    def request_key(self, user: str):
        """
        for server use
        init keys are one time usable
        """
        found_key = self.get_element_by_user(user)
        if found_key is not None:
            self.remove_element(found_key)
            return found_key
        return None

    def get_element(self, element: InitKey) -> InitKey:
        """
        get the key to a given user/device
        """
        for key in self.elements:
            if key.same_user(element):
                return key
        return None

    def get_element_by_user(self, user: str) -> InitKey:
        """
        get element wrapper to search by user str
        """
        search_key = InitKey(user, None, None)
        return self.get_element(search_key)

    def load_from_file(self):
        """
        load json from file and parse into elements
        """
        json_data = super().load_json_from_file()
        #load elements with necesary values into List
        for datum in json_data:
            key_data = InitKey(datum["user"], datum["device"], datum["key"])
            self.elements.append(key_data)
