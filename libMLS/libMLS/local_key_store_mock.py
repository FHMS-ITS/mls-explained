import string
from typing import Dict, Optional

from libMLS.abstract_keystore import AbstractKeystore
from libMLS.remote_key_store_mock import RemoteKeyStoreMock


class LocalKeyStoreMock(AbstractKeystore):

    def __init__(self, user_name: string):
        super().__init__(user_name)
        self._name: string = user_name

        self._public_private_keymap: Dict[bytes, bytes] = {}

    def register_keypair(self, public_key: bytes, private_key: bytes):
        self._public_private_keymap[public_key] = private_key
        RemoteKeyStoreMock().register_init_key(user_name=self._name, public_key=public_key)

    # pylint: disable=no-self-use
    def fetch_init_key(self, user_name: string) -> Optional[bytes]:
        return RemoteKeyStoreMock().fetch_init_key(user_name=user_name)

    def get_private_key(self, public_key: bytes) -> Optional[bytes]:

        if public_key not in self._public_private_keymap:
            return None

        return self._public_private_keymap[public_key]
