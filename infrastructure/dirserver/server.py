"""
MLS Dirserver
"""
import json
from flask import Flask, request

from store.init_key_store import InitKeyStore
from store.message_store import Message, Messagestore

APP = Flask(__name__)
INITKEYSTORE = InitKeyStore("./init_key_store.json")
MESSAGESTORE = Messagestore("./message_store.json")


def main():
    """
    get Message and delegate according to message type
    :return:
    """
    APP.run(host="localhost", port=5001)


@APP.route('/')
def index():
    """
    Index return for Reachablility Tests
    """
    return "MLS DIR SERVER"


@APP.route('/keys', methods=["GET"])
def get_init_key():
    """
    Return requested init_keys to client
    """
    try:
        args = request.args.to_dict(flat=True)
        key = INITKEYSTORE.take_key_for_user(args["user"])
        if key is not None:
            return json.dumps(key.hex()), 200
        return "No Key for Given User", 400
    except KeyError:
        return "Get has wrong format", 400


@APP.route('/keys', methods=["POST"])
def add_init_keys():
    """
    Add Posted init_keys to INITKEYSTORE
    """
    data = json.loads(request.data)

    try:
        if "key" in data:
            INITKEYSTORE.add_key(user=data["user"], key=bytes.fromhex(data["key"]), identifier=data["identifier"])
            return "OK", 200
        # if "keys" in data:
        #     for key in data["keys"]:
        #         key_bytes = key.encode("ascii")
        #         init_key = InitKey(data["identifier"], data["user"], key_bytes)
        #         INITKEYSTORE.add_key(data["user"], key)
        #     return "OK", 200
        return "Send either key with one key or Keys with list of keys", 400
    except KeyError:
        return "Post has wrong format", 400


# pylint: disable=too-many-function-args
# false positive?
@APP.route('/message', methods=["POST"])
def message_fanout():
    """
    Do a Message Fanout to all Receivers of the message
    """
    data = json.loads(request.data)
    print(data)
    try:
        receivers = data["receivers"]
        message = data["message"]
        for receiver in receivers:
            message = Message(receiver["user"], receiver["device"], message)
            MESSAGESTORE.add_element(message)
        return "OK", 200
    except KeyError:
        return "Post has wrong format", 400


@APP.route('/message', methods=["GET"])
def get_messages():
    """
    Return all Messages to client
    """
    try:
        requested_user = request.args["user"]
        requested_device = request.args["device"]
        found_messages = MESSAGESTORE.get_messages(requested_user, requested_device)
        found_messages_json = []
        for message in found_messages:
            # print(message)
            found_messages_json.append(message.to_json())
            return json.dumps(found_messages_json), 200
    except KeyError:
        return "Get has wrong format", 400

    return json.dumps([]), 200


if __name__ == '__main__':
    main()
