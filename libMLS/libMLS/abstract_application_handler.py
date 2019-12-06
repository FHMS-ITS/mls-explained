
class AbstractApplicationHandler:

    def __init__(self):
        pass

    def on_application_message(self, application_data: bytes):
        raise NotImplementedError()

    def on_group_welcome(self, session):
        raise NotImplementedError()

    def on_group_member_added(self, group_id: bytes):
        raise NotImplementedError()
