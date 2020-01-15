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
        keydata = json.dumps({"user": self._username, "key": public_key.hex(), "identifier": ""})
        requests.post("http://" + self._dir_server_url + "/keys", data=keydata)

    def fetch_init_key(self, user_name: str) -> Optional[bytes]:
        params = {"user": user_name}
        response = requests.get("http://" + self._dir_server_url + "/keys", params=params)

        if response.status_code != 200:
            raise RuntimeError("No keys available")

        return bytes.fromhex(json.loads(response.content))

    def get_private_key(self, public_key: bytes) -> Optional[bytes]:
        return None
