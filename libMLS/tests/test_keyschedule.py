from libMLS.libMLS.key_schedule import KeySchedule
from libMLS.libMLS.group_context import GroupContext
from libMLS.libMLS.x25519_cipher_suite import X25519CipherSuite


def test_new_keyschedule():
    cipher_suite = X25519CipherSuite()
    key_schedule = KeySchedule(cipher_suite)

    assert key_schedule.get_init_secret() == bytes(bytearray(b'\x00') * cipher_suite.get_hash_length())
    assert key_schedule.get_epoch_secret() == b''
    assert key_schedule.get_sender_data_secret() == b''
    assert key_schedule.get_handshake_secret() == b''
    assert key_schedule.get_application_secret() == b''
    assert key_schedule.get_confirmation_key() == b''


# def test_update_keyschedule():
    cipher_suite = X25519CipherSuite()
    key_schedule = KeySchedule(cipher_suite)
    context = GroupContext(b'0', 0, b'treehash', b'confirmed_transcript')

    key_schedule.update_key_schedule(b'update secret', context=context)

    assert key_schedule.get_init_secret() == \
           b'Hr?\xb7\xde\xfd\x1f)\xf83\xc8@\xeaJ\r\x86\x9e]\xc0!I}\x02\xed\xd5]}\xf0N$l\x99'
    assert key_schedule.get_epoch_secret() == \
           b'\x0c\xafJ\xc8J}I\xab:\xdf\xd2\xff\xcdQ\x16\x9b4ZL:,\t\xffg\x05\\W\xc1\xe0Gv\xd7'
    assert key_schedule.get_sender_data_secret() == \
           b'\xd9\x98w\xc3\xe6\xd9\xe9d\xe5Y\x93\x9e0\\3,|\xaae\x1d\x88e\x0e\x9cD\xcb\xa3i\xf2\xcd\xa6\xec'
    assert key_schedule.get_handshake_secret() == \
           b'k\xd7\xab!\xc2Kx\xcd"\xcf}=\xe1\x86M\xbc\xf8\x90:l\x83|b\t\np\x7f\xe7\xef\xa0\x7f\n'
    assert key_schedule.get_application_secret() == \
           b'C^\x83\xc4\xee\xc39A(\xec$\xde\x0f\x82\xd41\xc8\xfd4\x15%\x1b\x15IwOz\xf9\x1a\x1d0J'
    assert key_schedule.get_confirmation_key() == \
           b'aY\xdbl\xa1O\x9cp\n\xc4\x97\xe1\xfd\xd9\x9do\xe5z\x85\x8e\tv\xca\xcf\x1cn@<\xeecD\xff'

    context = GroupContext(b'0', 1, b'treehash2', b'confirmed_transcript2')
    key_schedule.update_key_schedule(b'update secret2', context=context)

    assert key_schedule.get_init_secret() == \
           b':\x98\x9f\xbf\x92\x8a[\xb09"&?\x0c\x03x;\x08\x05\x9er\xa7\xb9[\xef\xf7\x86\xdcQ=\xa9\xa8;'
    assert key_schedule.get_epoch_secret() == \
           b'\xe4<\x8fHg\x9e;\x92Z\xd4:]l\x00c\x1d\xdb\x90\x13\x0b n\xc0o!.=\xae{|\xc2^'
    assert key_schedule.get_sender_data_secret() == \
           b'\xb4>/3Brm\xd6\xff\x83\x11\xbd\xc1\x96\xc4%]\x1bq\x1a%l\xae\x05\x94\x16\xe4\x95TS\r\xb5'
    assert key_schedule.get_handshake_secret() == \
           b'\xba\xa5Z<\x1e\x7f\xb28/^\xf3\x0b\x19\x1c\t\xe4>"\x07\x84\xe5\'"\x99t\xe51\x8b2QH\x16'
    assert key_schedule.get_application_secret() == \
           b'"t\xdd\x82\xfcm\x8a\xc5*G\x84\x91\xc4\x86\xef\\\xcct\xb9\xe9\x0c\xc9\n;\xfeqi\x90\x17\x08\x8f\x83'
    assert key_schedule.get_confirmation_key() == \
           b',\xb4\xc8\x83\xd9\\h>)\x0f\r \xf4\x1f\nZ\xec.\xb7\x82\xb4"V)\xaa\xd7\xceYb\x83\xae\x96'


def test_changing_init_secret():
    cipher_suite = X25519CipherSuite()
    key_schedule = KeySchedule(cipher_suite)

    assert key_schedule.get_init_secret() == bytes(bytearray(b'\x00') * cipher_suite.get_hash_length())

    context = GroupContext(b'0', 0, b'treehash', b'confirmed_transcript')
    key_schedule.update_key_schedule(b'update secret', context=context)
    old_init_secret = key_schedule.get_init_secret()

    assert old_init_secret != bytes(bytearray(b'\x00') * cipher_suite.get_hash_length())

    context = GroupContext(b'0', 1, b'treehash2', b'confirmed_transcript2')
    key_schedule.update_key_schedule(b'update secret2', context=context)

    assert old_init_secret != key_schedule.get_init_secret()
