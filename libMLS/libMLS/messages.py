"""
Refer to RFC-8446 https://tools.ietf.org/html/rfc8446#section-3.4
"""
from dataclasses import dataclass
from enum import Enum
from struct import pack
from typing import Union, List

from libMLS.abstract_message import AbstractMessage
from libMLS.message_packer import pack_dynamic, unpack_dynamic, unpack_byte_list
from libMLS.tree_node import TreeNode


class ContentType(Enum):
    """
    RFC Section 8 Message Framing
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-8

    enum {
        invalid(0),
        handshake(1),
        application(2),
        (255)
    } ContentType;
    """
    INVALID = 0
    HANDSHAKE = 1
    APPLICATION = 2


class GroupOperationType(Enum):
    """
    RFC Section 9 Handshake Messages
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-9

    enum {
        init(0),
        add(1),
        update(2),
        remove(3),
        (255)
    } GroupOperationType;

    """
    INIT = 0
    ADD = 1
    UPDATE = 2
    REMOVE = 3


class CipherSuiteType(Enum):
    P256_SHA256_AES128GCM = 0
    X25519_SHA256_AES128GCM = 1


class InitMessage(AbstractMessage):
    """
    RFC Section 9.1 Init
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-9.1

    A group can always be created by initializing a one-member group and
    using adding members individually.  For cases where the initial list
    of members is known, the Init message allows a group to be created
    more efficiently.

    struct {
        opaque group_id<0..255>;
        ProtocolVersion version;
        CipherSuite cipher_suite;
        ClientInitKey members<0..2^32-1>;
        DirectPath path;
    } Init;
    """
    def validate(self) -> bool:
        return False

    def _pack(self) -> bytes:
        pass

    @classmethod
    def from_bytes(cls, data: bytes):
        pass


@dataclass
class AddMessage(AbstractMessage):
    """
    RFC Section 9.2 Add
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-9.2

    An Add message provides existing group members with the information
    they need to update their GroupContext with information about the new
    member:

    struct {
        uint32 index;
        ClientInitKey init_key;
        opaque welcome_info_hash<0..255>;
    } Add;

    The "index" field indicates where in the tree the new member should
    be added.  The new member can be added at an existing, blank leaf
    node, or at the right edge of the tree.  In any case, the "index"
    value MUST satisfy "0 <= index <= n", where "n" is the size of the
    group.  The case "index = n" indicates an add at the right edge of
    the tree).  If "index < n" and the leaf node at position "index" is
    not blank, then the recipient MUST reject the Add as malformed.

    The "welcome_info_hash" field contains a hash of the WelcomeInfo
    object sent in a Welcome message to the new member.
    """
    index: int
    init_key: bytes
    welcome_info_hash: bytes

    def _pack(self) -> bytes:
        return pack_dynamic('IVV', self.index, self.init_key, self.welcome_info_hash)

    def validate(self) -> bool:
        return True

    @classmethod
    def from_bytes(cls, data: bytes):
        box: tuple = unpack_dynamic('IVV', data)
        # pylint: disable=unexpected-keyword-arg
        inst: AddMessage = cls(index=box[0], init_key=box[1], welcome_info_hash=box[2])

        if not inst.validate():
            raise RuntimeError()

        return inst

    def __eq__(self, other):

        if not isinstance(other, self.__class__):
            return False

        return self.index == other.index and \
               self.init_key == other.init_key and \
               self.welcome_info_hash == other.welcome_info_hash


@dataclass
class DirectPathNode(AbstractMessage):
    """
    RFC Section 6.5 Direct Paths
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-6.5

    As described in Section 5.4, each MLS message needs to transmit node
    values along the direct path of a leaf.  The path contains a public
    key for the leaf node, and a public key and encrypted secret value
    for intermediate nodes in the path.  In both cases, the path is
    ordered from the leaf to the root; each node MUST be the parent of
    its predecessor.

    struct {
        HPKEPublicKey public_key;
        HPKECiphertext encrypted_path_secret<0..2^16-1>;
    } DirectPathNode;

    struct {
        DirectPathNode nodes<0..2^16-1>;
    } DirectPath;

    The length of the "encrypted_path_secret" vector MUST be zero for the
    first node in the path.  For the remaining elements in the vector,
    the number of ciphertexts in the "encrypted_path_secret" vector MUST
    be equal to the length of the resolution of the corresponding copath
    node.  Each ciphertext in the list is the encryption to the
    corresponding node in the resolution.
    """
    public_key: bytes
    encrypted_path_secret: List['HPKECiphertext']

    def _pack(self) -> bytes:

        path_secret_buffer: bytes = b''
        for entry in self.encrypted_path_secret:
            path_secret_buffer += pack_dynamic('V', entry.pack())

        return pack_dynamic('32sV', self.public_key, path_secret_buffer)

    @classmethod
    def from_bytes(cls, data: bytes):
        box: tuple = unpack_dynamic('32sV', data)

        public_key: bytes = box[0]
        encrypted_messages_bytes: List[bytes] = unpack_byte_list(box[1])
        encrypted_messages: List[HPKECiphertext] = []
        for entry in encrypted_messages_bytes:
            encrypted_messages.append(HPKECiphertext.from_bytes(entry))

        # pylint: disable=unexpected-keyword-arg
        inst: DirectPathNode = cls(public_key=public_key, encrypted_path_secret=encrypted_messages)
        if not inst.validate():
            raise RuntimeError()

        return inst

    def validate(self) -> bool:
        return True

    def __eq__(self, other):

        if not isinstance(other, self.__class__):
            return False

        if self.public_key != other.public_key:
            return False

        for index, node in enumerate(self.encrypted_path_secret):
            if node != other.encrypted_path_secret[index]:
                return False

        return True


@dataclass
class UpdateMessage(AbstractMessage):
    """
    RFC Section 9.3 Update
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-9.3

    An Update message is sent by a group member to update its leaf secret
    and key pair.  This operation provides post-compromise security with
    regard to the member's prior leaf private key.

    struct {
        DirectPath path;
    } Update;
    """
    direct_path: List[DirectPathNode]

    def _pack(self) -> bytes:

        nodes_buffer: bytes = b''
        for node in self.direct_path:
            nodes_buffer += pack_dynamic('V', node.pack())

        return pack_dynamic('V', nodes_buffer)

    @classmethod
    def from_bytes(cls, data: bytes):
        node_bytes: List[bytes] = unpack_byte_list(unpack_dynamic('V', data)[0])

        direct_path: List[DirectPathNode] = []
        for entry in node_bytes:
            direct_path.append(DirectPathNode.from_bytes(entry))

        # pylint: disable=unexpected-keyword-arg
        inst: UpdateMessage = cls(direct_path=direct_path)

        if not inst.validate():
            raise RuntimeError()

        return inst

    def validate(self) -> bool:
        return True

    def __eq__(self, other):

        if not isinstance(other, self.__class__):
            return False

        for index, node in enumerate(self.direct_path):
            if node != other.direct_path[index]:
                return False

        return True


class RemoveMessage(AbstractMessage):
    """
    RFC Section 9.4 Remove
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-9.4

    A Remove message is sent by a group member to remove one or more
    other members from the group.  A member MUST NOT use a Remove message
    to remove themselves from the group.  If a member of a group receives
    a Remove message where the removed index is equal to the signer
    index, the recipient MUST reject the message as malformed.

    struct {
        uint32 removed;
        DirectPath path;
    } Remove;
    """
    def validate(self) -> bool:
        return False

    def _pack(self) -> bytes:
        pass

    @classmethod
    def from_bytes(cls, data: bytes):
        pass


@dataclass
class GroupOperation(AbstractMessage):
    """
    RFC Section 9 Handshake
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-9

    In MLS, these changes are accomplished by broadcasting "handshake"
    messages to the group.  Note that unlike TLS and DTLS, there is not a
    consolidated handshake phase to the protocol.  Rather, handshake
    messages are exchanged throughout the lifetime of a group, whenever a
    change is made to the group state.  This means an unbounded number of
    interleaved application and handshake messages.

    An MLS handshake message encapsulates a specific GroupOperation
    message that accomplishes a change to the group state.  It is carried
    in an MLSPlaintext message that provides a signature by the sender of
    the message.  Applications may choose to send handshake messages in
    encrypted form, as MLSCiphertext messages.
    """
    msg_type: GroupOperationType
    operation: Union[InitMessage, AddMessage, UpdateMessage, RemoveMessage]

    def validate(self) -> bool:
        return True

    def _pack(self) -> bytes:
        return pack_dynamic('BV',
                            self.msg_type.value,
                            self.operation.pack()
                            )

    @classmethod
    def from_instance(cls, group_operation: Union[InitMessage, AddMessage, UpdateMessage, RemoveMessage]):

        if isinstance(group_operation, AddMessage):
            op_type = GroupOperationType.ADD
        elif isinstance(group_operation, RemoveMessage):
            op_type = GroupOperationType.REMOVE
        elif isinstance(group_operation, UpdateMessage):
            op_type = GroupOperationType.UPDATE
        else:
            raise ValueError()

        # pylint: disable=unexpected-keyword-arg
        return cls(operation=group_operation, msg_type=op_type)

    @classmethod
    def from_bytes(cls, data: bytes):
        box: tuple = unpack_dynamic('BV', data)

        group_operation_type: GroupOperationType = GroupOperationType(box[0])

        if group_operation_type == GroupOperationType.ADD:
            group_operation = AddMessage.from_bytes(data=box[1])
        elif group_operation_type == GroupOperationType.UPDATE:
            group_operation = UpdateMessage.from_bytes(data=box[1])
        elif group_operation_type == GroupOperationType.INIT:
            raise NotImplementedError()
        elif group_operation_type == GroupOperationType.REMOVE:
            raise NotImplementedError()
        else:
            raise ValueError()

        # pylint: disable=unexpected-keyword-arg
        inst: GroupOperation = cls(msg_type=group_operation_type, operation=group_operation)

        if not inst.validate():
            raise RuntimeError()

        return inst

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.msg_type == other.msg_type and \
               self.operation == other.operation


@dataclass
class MLSPlaintextHandshake(AbstractMessage):
    confirmation: int
    group_operation: GroupOperation

    def validate(self) -> bool:
        return isinstance(self.group_operation, GroupOperation)

    def _pack(self) -> bytes:
        return pack_dynamic(
            'IV',
            self.confirmation,
            self.group_operation.pack()
        )

    @classmethod
    def from_bytes(cls, data: bytes):
        box: tuple = unpack_dynamic('IV', data)

        group_op: GroupOperation = GroupOperation.from_bytes(data=box[1])

        # pylint: disable=unexpected-keyword-arg
        inst: MLSPlaintextHandshake = cls(confirmation=box[0], group_operation=group_op)

        if not inst.validate():
            raise RuntimeError()

        return inst

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.confirmation == other.confirmation and \
               self.group_operation == other.group_operation


@dataclass
class MLSPlaintextApplicationData(AbstractMessage):
    application_data: bytes

    def validate(self) -> bool:
        return True

    def _pack(self) -> bytes:
        return pack_dynamic('V', self.application_data)
        # return self.application_data

    @classmethod
    def from_bytes(cls, data: bytes):
        box: tuple = unpack_dynamic('V', data)
        # pylint: disable=unexpected-keyword-arg
        inst: MLSPlaintextApplicationData = cls(application_data=box[0])

        if not inst.validate():
            raise RuntimeError()

        return inst

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.application_data == other.application_data


@dataclass
class MLSSenderData(AbstractMessage):
    """
    RFC Section 8.1 Metadata Encryption
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-8.1

    The "sender data" used to look up the key for the content encryption
    is encrypted under AEAD using the MLSCiphertext sender_data_nonce and
    the sender_data_key from the keyschedule.  It is encoded as an object
    of the following form:

    struct {
        uint32 sender;
        uint32 generation;
    } MLSSenderData;

    When parsing a SenderData struct as part of message decryption, the
    recipient MUST verify that the sender field represents an occupied
    leaf in the ratchet tree.  In particular, the sender index value MUST
    be less than the number of leaves in the tree.
    """
    sender: int
    generation: int

    def validate(self) -> bool:
        return self.sender is not None

    @classmethod
    def from_bytes(cls, data: bytes):
        box: tuple = unpack_dynamic('II', data)
        # pylint: disable=unexpected-keyword-arg
        inst: MLSSenderData = cls(sender=box[0], generation=box[1])

        if not inst.validate():
            raise RuntimeError()

        return inst

    def _pack(self) -> bytes:
        return pack_dynamic(
            'II',
            self.sender,
            self.generation
        )

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.sender == other.sender and self.generation == other.generation


@dataclass
class MLSPlaintext(AbstractMessage):
    """
    RFC Section 8 Message Framing
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-8

    Handshake and application messages use a common framing structure.
    This framing provides encryption to assure confidentiality within the
    group, as well as signing to authenticate the sender within the
    group.

    The two main structures involved are MLSPlaintext and MLSCiphertext.
    MLSCiphertext represents a signed and encrypted message, with
    protections for both the content of the message and related metadata.
    MLSPlaintext represents a message that is only signed, and not
    encrypted.  Applications SHOULD use MLSCiphertext to encode both
    application and handshake messages, but MAY transmit handshake
    messages encoded as MLSPlaintext objects in cases where it is
    necessary for the delivery service to examine such messages.

    struct {
        opaque group_id<0..255>;
        uint32 epoch;
        uint32 sender;
        ContentType content_type;

        select (MLSPlaintext.content_type) {
            case handshake:
                GroupOperation operation;
                opaque confirmation<0..255>;
            case application:
                opaque application_data<0..2^32-1>;
        }
        opaque signature<0..2^16-1>;
    } MLSPlaintext;
    """
    group_id: bytes
    epoch: int
    sender: int
    content_type: ContentType
    content: Union[MLSPlaintextHandshake, MLSPlaintextApplicationData]
    signature: bytes

    def validate(self) -> bool:
        # return len(self.group_id) <= 256 and len(self.signature) < 2 ** 16
        return True

    def _pack(self) -> bytes:
        return pack_dynamic(
            'VIIBVV',
            self.group_id,
            self.epoch,
            self.sender,
            self.content_type.value,
            self.content.pack(),
            self.signature
        )

    @classmethod
    def from_bytes(cls, data: bytes):
        box: tuple = unpack_dynamic('VIIBVV', data)

        content_bytes = box[4]
        content_type = ContentType(box[3])
        if content_type == ContentType.HANDSHAKE:
            content = MLSPlaintextHandshake.from_bytes(content_bytes)
        elif content_type == ContentType.APPLICATION:
            content = MLSPlaintextApplicationData.from_bytes(content_bytes)
        else:
            raise RuntimeError()

        # pylint: disable=unexpected-keyword-arg
        inst: MLSPlaintext = cls(group_id=box[0],
                                 epoch=box[1],
                                 sender=box[2],
                                 content_type=content_type,
                                 content=content,
                                 signature=box[5]
                                 )

        if not inst.validate():
            raise RuntimeError()

        return inst

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.group_id == other.group_id and \
               self.epoch == other.epoch and \
               self.sender == other.sender and \
               self.content_type == other.content_type and \
               self.signature == other.signature and \
               self.content == other.content

    def verify_metadata_from_cipher(self, encrypted: 'MLSCiphertext'):
        return self.group_id == encrypted.group_id and \
               self.epoch == encrypted.epoch and \
               self.content_type == encrypted.content_type


@dataclass
class MLSCiphertext(AbstractMessage):
    """
    RFC Section 8 Message Framing
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-8

    Handshake and application messages use a common framing structure.
    This framing provides encryption to assure confidentiality within the
    group, as well as signing to authenticate the sender within the
    group.

    The two main structures involved are MLSPlaintext and MLSCiphertext.
    MLSCiphertext represents a signed and encrypted message, with
    protections for both the content of the message and related metadata.
    MLSPlaintext represents a message that is only signed, and not
    encrypted.  Applications SHOULD use MLSCiphertext to encode both
    application and handshake messages, but MAY transmit handshake
    messages encoded as MLSPlaintext objects in cases where it is
    necessary for the delivery service to examine such messages.

    struct {
       opaque group_id<0..255>;
       uint32 epoch;
       ContentType content_type;
       opaque sender_data_nonce<0..255>;
       opaque encrypted_sender_data<0..255>;
       opaque ciphertext<0..2^32-1>;
   } MLSCiphertext;
    """
    # todo: Replace prefix with SenderDataAAD
    group_id: bytes
    epoch: int
    content_type: ContentType
    sender_data_nounce: bytes
    encrypted_sender_data: bytes
    ciphertext: bytes

    def validate(self) -> bool:
        return True

    def _pack(self) -> bytes:
        return pack_dynamic('VIBVVV',
                            self.group_id,
                            self.epoch,
                            self.content_type.value,
                            self.sender_data_nounce,
                            self.encrypted_sender_data,
                            self.ciphertext
                            )

    @classmethod
    def from_bytes(cls, data: bytes):
        box: tuple = unpack_dynamic('VIBVVV', data)
        # pylint: disable=unexpected-keyword-arg
        inst: MLSCiphertext = cls(group_id=box[0],
                                  epoch=box[1],
                                  content_type=ContentType(box[2]),
                                  sender_data_nounce=box[3],
                                  encrypted_sender_data=box[4],
                                  ciphertext=box[5]
                                  )

        if not inst.validate():
            raise RuntimeError()

        return inst

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.group_id == other.group_id and \
               self.epoch == other.epoch and \
               self.content_type == other.content_type and \
               self.sender_data_nounce == other.sender_data_nounce and \
               self.encrypted_sender_data == other.encrypted_sender_data and \
               self.ciphertext == other.ciphertext


@dataclass
class HPKECiphertext(AbstractMessage):
    """
    RFC Section 6.5 Direct Paths
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-6.5

    struct {
        HPKEPublicKey ephemeral_key;
        opaque ciphertext<0..2^16-1>;
    } HPKECiphertext;

    The HPKECiphertext values are computed as

    ephemeral_key, context = SetupBaseI(node_public_key, "")
    ciphertext = context.Seal("", path_secret)

    where "node_public_key" is the public key of the node that the path
    secret is being encrypted for, and the functions "SetupBaseI" and
    "Seal" are defined according to [I-D.irtf-cfrg-hpke].

    Decryption is performed in the corresponding way, using the private
    key of the resolution node and the ephemeral public key transmitted
    in the message.
    """
    ephemeral_key: bytes
    cipher_text: bytes

    def _pack(self) -> bytes:
        return pack_dynamic('32sV', self.ephemeral_key, self.cipher_text)

    def validate(self) -> bool:
        return True

    @classmethod
    def from_bytes(cls, data: bytes):
        box: tuple = unpack_dynamic('32sV', data)
        # pylint: disable=unexpected-keyword-arg
        inst: HPKECiphertext = cls(ephemeral_key=box[0], cipher_text=box[1])

        if not inst.validate():
            raise RuntimeError()

        return inst

    def __eq__(self, other):

        if not isinstance(other, self.__class__):
            return False

        return self.ephemeral_key == other.ephemeral_key and self.cipher_text == other.cipher_text


@dataclass
# pylint: disable=too-many-instance-attributes
class WelcomeInfoMessage(AbstractMessage):
    """
    RFC Section 9.2 Add
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-9.2

    The Welcome message contains the information that the new member
    needs to initialize a GroupContext object that can be updated to the
    current state using the Add message.  This information is encrypted
    for the new member using HPKE.  The recipient key pair for the HPKE
    encryption is the one included in the indicated ClientInitKey,
    corresponding to the indicated ciphersuite.  The "add_key_nonce"
    field contains the key and nonce used to encrypt the corresponding
    Add message; if it is not encrypted, then this field MUST be set to
    the null optional value.

    struct {
        ProtocolVersion version;
        opaque group_id<0..255>;
        uint32 epoch;
        optional<RatchetNode> tree<1..2^32-1>;
        opaque interim_transcript_hash<0..255>;
        opaque init_secret<0..255>;
        optional<KeyAndNonce> add_key_nonce;
    } WelcomeInfo;

    struct {
        opaque client_init_key_id<0..255>;
        CipherSuite cipher_suite;
        HPKECiphertext encrypted_welcome_info;
    } Welcome;

    In the description of the tree as a list of nodes, the "credential"
    field for a node MUST be populated if and only if that node is a leaf
    in the tree.
    """
    protocol_version: bytes
    group_id: bytes
    epoch: int
    tree: List[TreeNode]
    interim_transcript_hash: bytes
    init_secret: bytes
    key: bytes
    nounce: bytes

    def __eq__(self, other):

        if not isinstance(other, self.__class__):
            return False

        if not (other.interim_transcript_hash == self.interim_transcript_hash and
                self.protocol_version == other.protocol_version and
                self.group_id == other.group_id and
                self.init_secret == other.init_secret and
                self.key == other.key and
                self.nounce == other.nounce and
                len(self.tree) == len(other.tree)):
            return False

        nodes_equal: bool = True
        for node_index in range(len(self.tree)):
            nodes_equal &= (self.tree[node_index] == other.tree[node_index])

        # todo Pack and unpack test
        return nodes_equal

    def _pack(self) -> bytes:
        return pack_dynamic(
            'VVIVVVVV',
            self.protocol_version,
            self.group_id,
            self.epoch,
            self._packed_nodes(),
            self.interim_transcript_hash,
            self.init_secret,
            self.key,
            self.nounce
        )

    def _packed_nodes(self) -> bytes:
        # packed_list: List[bytes] = []
        packed_list: bytes = b''
        for node in self.tree:
            packed_list += pack_dynamic('V', node.pack())

        return packed_list

    def validate(self) -> bool:
        # todo: write auto validate for fmt string and dump this validation func
        return True

    @classmethod
    def from_bytes(cls, data: bytes):
        box = unpack_dynamic('VVIVVVVV', data)

        raw_nodes: List[bytes] = unpack_byte_list(box[3])
        nodes: List[TreeNode] = []

        # if there are no nodes in the tree, the raw_nodes list contains just one empty entry
        if raw_nodes != [] and raw_nodes[0] != b'':
            for raw_node in raw_nodes:
                nodes.append(TreeNode.from_bytes(raw_node))

        # pylint: disable=unexpected-keyword-arg
        inst = cls(protocol_version=box[0],
                   group_id=box[1],
                   epoch=box[2],
                   tree=nodes,
                   interim_transcript_hash=box[4],
                   init_secret=box[5],
                   key=box[6],
                   nounce=box[7])

        if not inst.validate():
            raise RuntimeError()

        return inst


@dataclass
class WelcomeMessage(AbstractMessage):
    """
    RFC Section 9.2 Add
    https://tools.ietf.org/html/draft-ietf-mls-protocol-07#section-9.2

    struct {
        opaque client_init_key_id<0..255>;
        CipherSuite cipher_suite;
        HPKECiphertext encrypted_welcome_info;
    } Welcome;

    Note that the "init_secret" in the Welcome message is the
    "init_secret" at the output of the key schedule diagram in
    Section 6.6.  That is, if the "epoch" value in the Welcome message is
    "n", then the "init_secret" value is "init_secret_[n]".  The new
    member can combine this init secret with the update secret
    transmitted in the corresponding Add message to get the epoch secret
    for the epoch in which it is added.  No secrets from prior epochs are
    revealed to the new member.

    Since the new member is expected to process the Add message for
    itself, the Welcome message should reflect the state of the group
    before the new user is added.  The sender of the Welcome message can
    simply copy all fields from their GroupContext object.
    """
    client_init_key_id: bytes
    cipher_suite: CipherSuiteType
    encrypted_welcome_info: HPKECiphertext

    def _pack(self) -> bytes:
        return pack(
            'pBp',
            self.client_init_key_id,
            self.cipher_suite,
            self.encrypted_welcome_info
        )

    def validate(self) -> bool:
        return len(self.client_init_key_id) <= 256

    @classmethod
    def from_bytes(cls, data: bytes):
        pass
