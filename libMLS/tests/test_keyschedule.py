from libMLS.libMLS.key_schedule import KeySchedule
from libMLS.libMLS.group_context import GroupContext
from libMLS.libMLS.x25519_cipher_suite import X25519CipherSuite


def test_new_keyschedule():
    keyschedule = KeySchedule()

    assert keyschedule.get_init_secret() == b'0'
    assert keyschedule.get_epoch_secret() == b''
    assert keyschedule.get_sender_data_secret() == b''
    assert keyschedule.get_handshake_secret() == b''
    assert keyschedule.get_application_secret() == b''
    assert keyschedule.get_confirmation_key() == b''


def test_update_keyschedule():
    keyschedule = KeySchedule()
    context = GroupContext(b'0', 0, b'treehash', b'confirmed_transcript')

    keyschedule.update_key_schedule(b'update secret', context=context, cipher_suite=X25519CipherSuite())

    assert keyschedule.get_init_secret() == \
           b'\x07\x15z|(\xd2k{\n\xa0\x94v{\xeb=\xec}\\\xb4tF>[\xc0\x8e\xa0\xf5|\x81\x94\x7fX'
    assert keyschedule.get_epoch_secret() == \
           b'\x8e\xfbDW\x15\x0e\xe2\xcd\x99\xbc\x16J\xad\x9eY\xa6F>\xe1\xe9ORX\xcd)\xc6O\xa9\xa70\xe0\x1f'
    assert keyschedule.get_sender_data_secret() == \
           b'\xbf\xa1f\xe9\xa4\t#\xb1S\xe0\xd2\x1f7\\\x1e-\xd4\xcf?\x01\xc0\xa0^=\xe1\xe0\xdf\xaf\xbcg\xf2\xf2'
    assert keyschedule.get_handshake_secret() == \
           b'\xef\xc8]nX/\xcc\xben\xfb\xe9\x88\xba\xf3(\xec\xd5J.\xee\xad\x0b\xdc\x8a;\x82\x99\xef\xde\x01\x16\xc4'
    assert keyschedule.get_application_secret() == \
           b'\x02\xb8\xb2\x8b\xdf\x84\xe7a9\x04\xfdQ\xda\x17(`8\x98\xc0-\x15\x16\x0e<E\x8a\x82\xdb^\x8c\xe8s'
    assert keyschedule.get_confirmation_key() == \
           b"\xf3\xf3\xc1'\xfa*\xd9BQg\x9a\xea\x18\xee\x8aS\xe8\x89\xa5\x85\t\x14F\x13\x04x\x88\xdd96R\xdd"


    context = GroupContext(b'0', 1, b'treehash2', b'confirmed_transcript2')
    keyschedule.update_key_schedule(b'update secret2', context=context, cipher_suite=X25519CipherSuite())

    assert keyschedule.get_init_secret() == \
           b'bS\x8ej\xd2\xf9\xef+q\nK\xef\x02?\x15\xf1\xf9@.\x9f\xeb\xee\xd8p\xd1\xc4\xa9F\xa5\x8c\xc8\xb6'
    assert keyschedule.get_epoch_secret() == \
           b'#\xb9\xf4\xae$jR\xcb\xfaF\x82!1(\x16\xec\x86\xa6\x06\x9d\xba\x05,Y);m\x1d\x05\xe4\xfc{'
    assert keyschedule.get_sender_data_secret() == \
           b'\xd1U\xe1\x07{hT\x19\xc4\xaf\x18\xaa=,\x88-\xe8v\xf7\x8bu\xe1\x17\rGl\x91v\x15\xaf\x7f\xa8'
    assert keyschedule.get_handshake_secret() == \
           b'\xa1\x8a\x0b&\x7fv\xe1_\xc6\xfc \xa8$\xa5\x16\xec\xf0\x16\xf3\xc6\x85\xd4i\x1c\xfd:Xw\xf5\x81U='
    assert keyschedule.get_application_secret() == \
           b'\x8d+!\xea\x14\xdfH\x87\xf8\xb2y\xf7\xa28\xa1\xcb\x1cp\x05\xa6b\x8a\xda\xf3\x94\xfa\x19\xe3\xb2%\xb8S'
    assert keyschedule.get_confirmation_key() == \
           b'ln\xcaT\x02\xe2\xb9\xea\xb5\xdb\x0b\xe94\xb6\x82\xe4h\x8a\x0e\xdd\xe6\xdd\xa5aP&OX\x05\xef\x83~'


def test_changing_init_secret():
    keyschedule = KeySchedule()

    assert keyschedule.get_init_secret() == b'0'

    context = GroupContext(b'0', 0, b'treehash', b'confirmed_transcript')
    keyschedule.update_key_schedule(b'update secret', context=context, cipher_suite=X25519CipherSuite())
    old_init_secret = keyschedule.get_init_secret()

    assert old_init_secret != b'0'

    context = GroupContext(b'0', 1, b'treehash2', b'confirmed_transcript2')
    keyschedule.update_key_schedule(b'update secret2', context=context, cipher_suite=X25519CipherSuite())

    assert old_init_secret != keyschedule.get_init_secret()
