from typing import Optional


class AbstractKeystore:
    def __init__(self, user_name: str):
        pass

    def register_keypair(self, public_key: bytes, private_key: bytes):
        raise NotImplementedError()

    def fetch_init_key(self, user_name: str) -> Optional[bytes]:
        raise NotImplementedError()

    def get_private_key(self, public_key: bytes) -> Optional[bytes]:
        raise NotImplementedError()
