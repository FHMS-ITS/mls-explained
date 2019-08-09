import pytest
import json
from authserver import server
from store.auth_key_store import AuthKey

APP = server.APP.test_client()
APP.testing = True

def test_check_auth_server():
    response = APP.get("/")
    assert response.status_code == 200
    assert response.get_data(as_text = True) == "MLS AUTH SERVER"

def test_post_long_term_key():
    assert server.AUTHKEYSTORE.elements == []
    key_string = b"1234".decode("ascii")
    data = {"user": "Jan", "device": "Phone", "key": key_string}
    data_string = json.dumps(data)
    response = APP.post("/keys", data=data_string)
    assert response.status_code == 200
    comp_list = [AuthKey("Jan", "Phone", b"1234")]
    assert server.AUTHKEYSTORE.elements == comp_list

def test_get_long_term_key():
    assert len(server.AUTHKEYSTORE.elements) == 1
    query = {"user": "Jan", "device": "Phone"}
    response = APP.get("/keys", query_string=query)
    assert response.status_code == 200
    result = response.get_json(force=True)
    comp_key = {"user": "Jan", "device": "Phone", "key": "1234"}
    assert result == comp_key

    #Key must still be in store
    assert len(server.AUTHKEYSTORE.elements) == 1
