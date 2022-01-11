import time
from typing import Any


class Event:
    def __init__(self, data: Any = None) -> None:
        self.created: float = time.time()
        self.data: Any = data
