"""
Init Key Store
"""
import os
from typing import Dict, List, Tuple, Optional

from flask import json


class InitKeyStore:

    def __init__(self, path: str):
        self.keys: Dict[str, List[Tuple[str, bytes]]] = {}
        self.path = os.path.abspath(path)

        if os.path.exists(self.path):
            with open(self.path, 'r') as handle:
                self.keys = json.load(handle)

    def _on_modify(self):
        with open(self.path, 'w') as file:
            json.dump(self.keys, file)

    def add_key(self, user: str, key: bytes, identifier: str = ""):

        if user not in self.keys:
            self.keys[user] = []

        self.keys[user].append((identifier, key.hex()))
        self._on_modify()

    def get_key_for_user(self, user: str) -> bytes:
        return bytes.fromhex(self.keys[user][0][1])

    def take_key_for_user(self, user) -> Optional[bytes]:
        if user in self.keys and len(self.keys[user]) > 0:
            key = self.keys[user].pop()[1]
            self._on_modify()
            return bytes.fromhex(key)

        return None

    def clear_user(self, user):
        if user in self.keys:
            self.keys[user] = []
            self._on_modify()
