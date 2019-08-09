"""
Store Class zum Storen von Keys in Dateien.
"""
# pylint: disable=too-many-function-args
#false positive
import os
import json
from abc import ABC, abstractmethod
from typing import List

class Store(ABC):
    """
    class to manage the store of elements
    """
    def __init__(self, file_name: str):
        super().__init__()
        self.file_name = file_name
        path = str(os.path.dirname(os.path.realpath(__file__)))
        self.absolute_file_path = path + "/" +str(file_name)
        self.elements = []
        self.load_from_file()

    def to_json(self) -> dict:
        """
        converts elementstore to json
        """
        elements = []
        for element in self.elements:
            elements.append(element.to_json())
        return elements

    def add_or_update_element(self, element):
        """
        adds element to store updates if alredy in store
        add a single element to elementstore for authserver
        """
        existing_element = self.get_element(element)
        if existing_element is None:
            self.elements.append(element)
        else:
            self.remove_element(existing_element)
            self.add_element(element)

    @abstractmethod
    def get_element(self, element):
        """
        checks if element is in elements and returns it if true
        """

    def add_element(self, element):
        """
        add an element to the elements list
        """
        self.elements.append(element)

    def remove_element(self, element):
        """
        removes given element
        """
        self.elements.remove(element)

    def save_to_file(self):
        """
        saves stored data to file
        """
        json_data = self.to_json()
        with open(self.absolute_file_path, "w") as file_pointer:
            json.dump(json_data, file_pointer)

    @abstractmethod
    def load_from_file(self):
        """
        Loads Data with load_json_from_file and
        parses them into the needed Structure
        """

    def load_json_from_file(self) -> List[dict]:
        """
        loads stored data from file
        """
        data = []
        if os.path.exists(self.absolute_file_path):
            with open(self.absolute_file_path, "r") as file_pointer:
                data = json.load(file_pointer)
        else:
            with open(self.absolute_file_path, "w") as file_pointer:
                json.dump([], file_pointer)

        if not isinstance(data, list):
            raise ValueError("Data in elementstore file must be a List")
        return data
