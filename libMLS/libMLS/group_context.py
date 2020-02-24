from dataclasses import dataclass


@dataclass
class GroupContext:
    """
    RFC 6.4 Group State
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-6.4

    Each member of the group maintains a GroupContext object that
    summarizes the state of the group:

    struct {
        opaque group_id<0..255>;
        uint32 epoch;
        opaque tree_hash<0..255>;
        opaque confirmed_transcript_hash<0..255>;
    } GroupContext;

    The fields in this state have the following semantics:

    o  The "group_id" field is an application-defined identifier for the
       group.

    o  The "epoch" field represents the current version of the group key.

    o  The "tree_hash" field contains a commitment to the contents of the
       group's rachet tree and the credentials for the members of the
       group, as described in Section 6.3.

    o  The "confirmed_transcript_hash" field contains a running hash over
       the handshake messages that led to this state.
    """

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
