from dataclasses import dataclass, field
from typing import List


@dataclass
class User:
    """
    Manages Data and devices ascociated with a user
    """
    name: str
    devices: List[str] = field(default_factory=lambda: ['phone'])
