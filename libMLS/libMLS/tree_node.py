from typing import Optional


class TreeNode:

    def __init__(self, public_key: bytes, private_key: Optional[bytes] = None, credential: Optional[bytes] = None):
        super().__init__()
        self._public_key: bytes = public_key
        self._private_key: Optional[bytes] = private_key
        self._credential: Optional[bytes] = credential

    def __eq__(self, other):
        if not isinstance(other, TreeNode):
            return False

        # return self._private_key == other._private_key and \
        #        self._public_key == other._public_key and \
        #        self._credential == other._credential

        return self._public_key == other._public_key
