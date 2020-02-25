"""
Auth-Server Implementation
"""

import json

from flask import Flask, request
from store.auth_key_store import AuthKeyStore, AuthKey

APP = Flask(__name__)
AUTHKEYSTORE = AuthKeyStore("auth_key_store.json")

@APP.route('/')
def index():
    """
    Return on Index
    :return:
    """
    return "MLS AUTH SERVER"


@APP.route('/keys', methods=["GET"])
def get_key():
    """
    Return Key of Requested User
    :return:
    """
    try:
        requested_user = request.args["user"]
        requested_device = request.args["device"]
        key = AUTHKEYSTORE.get_element_by_user_device(requested_user, requested_device)
        if key is not None:
            return json.dumps(key.to_json()), 200
        return "No Key Found", 400
    except KeyError:
        return "Get has wrong format", 400


@APP.route('/keys', methods=["POST"])
def add_key():
    """
    Check received data and add to keystore
    :return:
    """
    try:
        data = json.loads(request.data)
        user = data["user"]
        device = data["device"]
        key = data["key"].encode("ascii")
        auth_key = AuthKey(user, device, key)
        AUTHKEYSTORE.add_or_update_element(auth_key)
        return "OK", 200
    except KeyError:
        return "Get has wrong format", 400

def main():
    """
    get Message and delegate according to message type
    :return:
    """

    APP.run(host="localhost", port=5000)


if __name__ == '__main__':
    main()
