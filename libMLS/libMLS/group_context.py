from dataclasses import dataclass


@dataclass
class GroupContext:
    group_id: bytes
    epoch: int
    tree_hash: bytes
    confirmed_transcript_hash: bytes

    def __eq__(self, other):
        if not isinstance(other, GroupContext):
            return False

        return self.group_id == other.group_id and \
               self.epoch == other.epoch and \
               self.confirmed_transcript_hash == other.confirmed_transcript_hash and \
               self.tree_hash == other.tree_hash

    def __bytes__(self):
        tmp = b"".join([self.group_id, bytes([self.epoch])])
        tmp = b"".join([tmp, self.tree_hash])
        tmp = b"".join([tmp, self.confirmed_transcript_hash])
        return tmp
