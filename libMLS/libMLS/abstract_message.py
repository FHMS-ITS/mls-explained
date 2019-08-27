

class AbstractMessage:

    def __init__(self):
        return

    @classmethod
    def from_bytes(cls, data: bytes):
        raise NotImplementedError()

    def pack(self) -> bytes:
        if not self.validate():
            raise RuntimeError(f'Validation failed for a message of type \"{self.__class__.__name__}\"')

        return self._pack()

    def _pack(self) -> bytes:
        # see https://docs.python.org/3.7/library/struct.html
        raise NotImplementedError()

    def validate(self) -> bool:
        raise NotImplementedError()
