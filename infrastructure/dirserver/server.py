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


@APP.route('/message', methods=["POST"])
def message_fanout():
    """
    Do a Message Fanout to all Receivers of the message
    """
    data = json.loads(request.data)
    try:
        receivers = data["receivers"]
        message = data["message"]
        for receiver in receivers:
            jans_gutes_message_object = Message(receiver["user"], receiver["device"], message)
            MESSAGESTORE.add_element(jans_gutes_message_object)
        print(len(MESSAGESTORE.elements))
        return "OK", 200
    except KeyError:
        return "Post has wrong format", 400


def _get_messages(user: str, device: str):
    found_messages = MESSAGESTORE.get_messages(user, device)
    found_messages_json = []
    for message in found_messages:
        found_messages_json.append(message.to_json())
    return json.dumps(found_messages_json), 200


@APP.route('/clear', methods=["DELETE"])
def clear_information():
    """
    Clear all information associated with this user
    INOFFICIAL PROTOCOL EXTENSION
    """
    try:
        args = request.args.to_dict(flat=True)
        INITKEYSTORE.clear_user(args["user"])
        _get_messages(args["user"], args["device"])

        return "success", 200
    except KeyError:
        return "Unknown User", 404


@APP.route('/message', methods=["GET"])
def get_messages():
    """
    Return all Messages to client
    """
    try:
        requested_user = request.args["user"]
        requested_device = request.args["device"]
        return _get_messages(requested_user, requested_device)
    except KeyError:
        return "Get has wrong format", 400


if __name__ == '__main__':
    main()
