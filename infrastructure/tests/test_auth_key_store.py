# pylint: disable=R0124
# pylint: disable=C0111
import filecmp
import os

from store.auth_key_store import AuthKeyStore, AuthKey

def test_get_key():
    storage = AuthKeyStore("test_auth_key_store.json")
    data = AuthKey("Jan", "Phone", b"11234")
    storage.elements.append(data)

    comp_key = AuthKey("Jan", "Phone")
    other_key = storage.get_element(comp_key)
    assert data == other_key

def test_add_key():
    storage = AuthKeyStore("test_auth_key_store.json")
    data = AuthKey("Jan", "Phone", b"11234")
    storage.add_element(data)

    found = False
    for key in storage.elements:
        if key == data:#is overloaded i think check!!!
            found = True

    assert found


def test_to_json():
    storage = AuthKeyStore("test_auth_key_store.json")
    data = AuthKey("Jan","Phone", b"11234")
    data2 = AuthKey("Jan","PC", b"123415")

    storage.add_element(data)
    json = storage.to_json()
    assert json == [{"user": "Jan", "device": "Phone", "key": "11234"}]
    storage.add_element(data2)
    json = storage.to_json()
    assert json == [{"user": "Jan", "device": "Phone", "key": "11234"},
                    {"user": "Jan", "device": "PC", "key": "123415"}]


def test_remove_key():
    storage = AuthKeyStore("test_auth_key_store.json")
    data = AuthKey("Jan", "Phone", b"11234")

    storage.elements.append(data)
    storage.remove_element(data)

    assert storage.elements == []


def test_update_key():
    old_key = AuthKey("Jan","Phone", b"11234")
    new_key = AuthKey("Jan","Phone", b"1234")

    storage = AuthKeyStore("test_auth_key_store.json")

    storage.add_element(old_key)
    storage.add_element(new_key)

    comp_key = AuthKey("Jan", "Phone")
    found_key = storage.get_element(comp_key)

    assert found_key.key == b"1234"


def test_save_to_file():
    storage = AuthKeyStore("test_auth_key_store.json")
    data = AuthKey("Jan","Phone", b"11234")

    #get absolute path of comp_file.json
    comp_file_absolute_path = str(os.path.dirname(os.path.realpath(__file__))) + "/" + str("comp_file_auth_key_store.json")
    storage.add_element(data)

    storage.save_to_file()

    assert filecmp.cmp(storage.absolute_file_path, comp_file_absolute_path)
