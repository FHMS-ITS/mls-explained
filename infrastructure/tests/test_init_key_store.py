# pylint: disable=R0124
# pylint: disable=C0111
import filecmp
import os

from store.init_key_store import InitKey, InitKeyStore

def test_get_element():
    storage = InitKeyStore("test_init_keystore.json")

    data = InitKey("Jan", 1234, b"11234")

    storage.elements.append(data)

    other_key = storage.get_element_by_user("Jan")

    assert data == other_key


def test_add_element():

    storage = InitKeyStore("test_init_keystore.json")
    data = InitKey("Jan", 1234, b"11234")

    storage.add_element(data)

    found = False

    for key in storage.elements:
        if key == data:
            found = True

    assert found


def test_to_json():
    storage = InitKeyStore("test_init_keystore.json")
    data = InitKey("Jan", 1234, b"11234")
    data2 = InitKey("Sebastian", 12345,  b"14")
    storage.add_element(data)

    json = storage.to_json()
    assert json == [{"user": "Jan", "identifier": 1234, "key": "11234"}]
    storage.add_element(data2)
    json = storage.to_json()
    assert json == [{"user": "Jan", "identifier": 1234, "key": "11234"},
                    {"user": "Sebastian", "identifier": 12345, "key": "14"}]


def test_remove_element():
    storage = InitKeyStore("test_init_keystore.json")
    data = InitKey("Jan", 1234, b"11234")

    storage.add_element(data)
    storage.remove_element(data)

    assert storage.elements == []


def test_add_multiple_keys():
    key = InitKey("Jan", 1234, b"11234")
    key2 = InitKey("Jan", 12345, b"1234")

    storage = InitKeyStore("test_init_keystore.json")

    storage.add_element(key)
    storage.add_element(key2)

    comp_list = [key, key2]

    assert storage.elements == comp_list

def test_save_to_file():
    storage = InitKeyStore("test_init_keystore.json")
    data = InitKey("Jan", 1234, b"11234")

    #get absolute path of comp_file.json
    comp_file_absolute_path = str(os.path.dirname(os.path.realpath(__file__))) + "/" + str("comp_file_init_key_store.json")
    storage.add_element(data)
    storage.save_to_file()
    assert filecmp.cmp(storage.absolute_file_path, comp_file_absolute_path)
