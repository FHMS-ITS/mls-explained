import json
from typing import Optional, Dict

import requests

from libMLS.abstract_keystore import AbstractKeystore


class NoKeysAvailableException(Exception):
    pass


class KeyService(AbstractKeystore):

    def __init__(self, user_name: str, dir_server_url: str):
        super().__init__(user_name)
        self._username = user_name
        self._dir_server_url = dir_server_url
        self._private_public_map: Dict[bytes, bytes] = {}

    def register_keypair(self, public_key: bytes, private_key: bytes):
        try:
            keydata = json.dumps({"user": self._username, "key": public_key.hex(), "identifier": ""})
            response = requests.post("http://" + self._dir_server_url + "/keys", data=keydata)
            if response.status_code == 200:
                self._private_public_map[public_key] = private_key
            else:
                raise RuntimeError("Failed to store key at server")
        except requests.exceptions.ConnectionError:
            raise ConnectionError

    def fetch_init_key(self, user_name: str) -> Optional[bytes]:
        try:
            params = {"user": user_name}
            response = requests.get("http://" + self._dir_server_url + "/keys", params=params)

            if response.status_code != 200:
                raise NoKeysAvailableException()

            return bytes.fromhex(json.loads(response.content))
        except requests.exceptions.ConnectionError:
            raise ConnectionError

    def get_private_key(self, public_key: bytes) -> Optional[bytes]:
        if public_key in self._private_public_map.keys():
            return self._private_public_map[public_key]

        return None

    def is_available(self) -> bool:
        try:
            requests.get("http://" + self._dir_server_url + "/keys", timeout=2)
        except requests.exceptions.Timeout:
            return False
        except requests.exceptions.ConnectionError:
            return False

        return True

    def clear_data(self, user_name: str, device_name: str) -> None:
        params = {"user": user_name, "device": device_name}
        requests.delete("http://" + self._dir_server_url + "/clear", params=params)
