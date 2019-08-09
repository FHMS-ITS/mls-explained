import pytest
import json
import base64
from dirserver import server
from store.init_key_store import InitKey
from store.message_store import Message
APP = server.APP.test_client()
APP.testing = True

def test_check_dir_server():
    response = APP.get("/")
    assert response.status_code == 200
    assert response.get_data(as_text = True) == "MLS DIR SERVER"

def test_add_init_key():
    assert server.INITKEYSTORE.elements == []
    key_bytes = b"ad1236"
    decoded = key_bytes.decode("ascii")
    data = {"user": "Jan", "device": "Phone", "identifier": 1234, "key": decoded}
    data_string = json.dumps(data)
    response = APP.post("/keys", data=data_string)
    assert response.status_code == 200
    comp_list = [InitKey("Jan", 1234, b"ad1236")]
    assert comp_list == server.INITKEYSTORE.elements

def test_get_init_key():
    assert len(server.INITKEYSTORE.elements) == 1
    query = {"user": "Jan"}
    response = APP.get("/keys", query_string=query)
    assert response.status_code == 200
    result = response.get_json(force=True)
    comp_key = {"user": "Jan", "identifier": 1234, "key": "ad1236"}
    assert result == comp_key

    #key must be gone from store
    assert len(server.INITKEYSTORE.elements) == 0

def test_send_single_message():
    assert server.MESSAGESTORE.elements == []
    data = {"receivers": [{"user":"Jan", "device": "Phone"}], "message": "Hallo"}
    data_string = json.dumps(data)
    response = APP.post("/message", data=data_string)
    assert response.status_code == 200
    assert len(server.MESSAGESTORE.elements) == 1
    assert type(server.MESSAGESTORE.elements[0]) == Message

def test_get_messages():
    query = {"user": "Jan", "device": "Phone"}
    response = APP.get("/message", query_string=query)
    assert response.status_code == 200
    result = response.get_json(force=True)
    assert len(result) == 1
    assert type(result) == list

def test_message_fanout():
    #reset Keystore
    server.INITKEYSTORE.elements = []
    data = {"receivers": [{"user": "Jan", "device": "Phone"}, {"user": "Steffen", "device": "PC"}], "message": "Hallo"}
    data_string = json.dumps(data)
    response = APP.post("/message", data=data_string)
    assert response.status_code == 200
    assert len(server.MESSAGESTORE.elements) == 2
    assert type(server.MESSAGESTORE.elements[0]) == Message
    assert type(server.MESSAGESTORE.elements[1]) == Message
