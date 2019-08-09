# pylint: disale=R0124
# pylint: disable=C0111
import filecmp
import os
from datetime import datetime
from store.message_store import Messagestore, Message

sample_timestamp = datetime(2017, 11, 28, 23, 55, 59, 342380)
sample_timestamp2 = datetime(2019, 11, 28, 23, 55, 59, 237456)

def test_get_message():
    storage = Messagestore("test_messagestore.json")

    data = Message("Jan", "Phone", "Hallo", sample_timestamp)

    storage.elements.append(data)

    other_message = storage.get_element_by_user_device("Jan", "Phone")

    assert data == other_message

def test_get_multiple_messages():

    storage = Messagestore("test_messagestore.json")

    message1 = Message("Jan", "Phone", "Hallo", sample_timestamp)
    message2 = Message("Jan", "Phone", "Wie Gehts?", sample_timestamp)

    storage.add_element(message1)
    storage.add_element(message2)

    assert storage.elements == [message1, message2]

def test_multiple_messages():
    storage = Messagestore("test_messagestore.json")

    message1 = Message("Jan", "Phone", "Hallo", sample_timestamp)
    message2 = Message("Jan", "Phone", "Wie Gehts?", sample_timestamp)

    storage.add_element(message1)

    result_list =  storage.get_messages("Jan", "Phone")

    assert result_list == [message1]

    storage.add_element(message1)
    storage.add_element(message2)

    result_list = storage.get_messages("Jan", "Phone")

    assert result_list == [message1, message2]


def test_add_element():

    storage = Messagestore("test_messagestore.json")

    data = Message("Jan", "Phone", "Hallo", sample_timestamp)

    storage.add_element(data)

    found = False

    for message in storage.elements:
        if message == data:
            found = True

    assert found


def test_to_json():
    storage = Messagestore("test_messagestore.json")
    data = Message("Jan", "Phone", "Hallo", sample_timestamp)

    storage.elements.append(data)

    json = storage.to_json()

    assert json == [{"user": "Jan", "device": "Phone", "message": "Hallo","timestamp": "2017-11-28 23:55:59.342380"}]


def test_remove_element():
    storage = Messagestore("test_messagestore.json")
    data = Message("Jan", "Phone", "Hallo", sample_timestamp)

    storage.add_element(data)
    storage.remove_element(data)

    assert storage.elements == []


def test_save_to_file():
    storage = Messagestore("test_messagestore.json")
    data = Message("Jan", "Phone", "hallo", sample_timestamp)

    #get absolute path of comp_file.json
    comp_file_absolute_path = str(os.path.dirname(os.path.realpath(__file__))) + "/" + str("comp_file_message_store.json")
    storage.elements.append(data)

    storage.save_to_file()
    assert filecmp.cmp(storage.absolute_file_path, comp_file_absolute_path)
