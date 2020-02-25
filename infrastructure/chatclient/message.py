from dataclasses import dataclass

@dataclass
class Message:
    """
    Manages Message and associated data
    """
    description: str
    message: str
    state_path: str
    protocol: bool

    def __init__(self, description: str, message: str, protocol: bool):
        self.description = description
        self.protocol = protocol
        self.message = message
        self.state_path = ""
