import string
from typing import Optional, Dict


class RemoteKeyStoreMock:

    # pylint: disable=invalid-name,too-few-public-methods
    class __RemoteKeyStoreMock:

        def __init__(self):
            self.user_init_key_map: Dict[string, bytes] = {}

    instance: Optional[__RemoteKeyStoreMock] = None

    def __init__(self):
        if not RemoteKeyStoreMock.instance:
            RemoteKeyStoreMock.instance = RemoteKeyStoreMock.__RemoteKeyStoreMock()

    def register_init_key(self, user_name: string, public_key: bytes) -> None:

        self.instance.user_init_key_map[user_name] = public_key

    def fetch_init_key(self, user_name: string) -> Optional[bytes]:

        if user_name not in self.instance.user_init_key_map:
            return None

        return self.instance.user_init_key_map[user_name]
