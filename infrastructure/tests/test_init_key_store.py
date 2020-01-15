# pylint: disable=R0124
# pylint: disable=C0111
import filecmp
import os
import tempfile

from flask import json
from store.init_key_store import InitKeyStore


def test_to_json():
    file = tempfile.mktemp()
    storage = InitKeyStore(file)
    storage.add_key("Jan", b'11234', "1234")

    with open(file) as handle:
        json_content = json.load(handle)

    assert json_content == {"Jan": [["1234", "3131323334"]]}
    storage.add_key("Sebastian", b"14", "12345")

    with open(file) as handle:
        json_content = json.load(handle)

    assert json_content == {"Jan": [["1234", "3131323334"]], "Sebastian": [["12345", "3134"]]}


def test_remove_element():
    file = tempfile.mktemp()
    storage = InitKeyStore(file)

    storage.add_key("Jan", b'11234', "1234")

    assert storage.take_key_for_user("Jan") == b'11234'

    assert storage.keys == {"Jan": []}
