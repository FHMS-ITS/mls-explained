import json
from typing import Optional

import requests

from libMLS.abstract_keystore import AbstractKeystore


class KeyService(AbstractKeystore):

    def __init__(self, user_name: str, dir_server_url: str):
        super().__init__(user_name)
        self._username = user_name
        self._dir_server_url = dir_server_url

    def register_keypair(self, public_key: bytes, private_key: bytes):
        keydata = json.dumps({"user": self._username, "init_keys": public_key})
        response = requests.post("http://" + self._dir_server_url + "/keys", data=keydata)

    def fetch_init_key(self, user_name: str) -> Optional[bytes]:
        params = {"user": user_name}
        response = requests.get("http://" + self._dir_server_url + "/message", params=params)
        return response.content['key'].encode('ascii')

    def get_private_key(self, public_key: bytes) -> Optional[bytes]:
        return None
