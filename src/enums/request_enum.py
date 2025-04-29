
from enum import Enum, auto

class RequestMethod(Enum):
    GET = auto()
    POST = auto()
    PUT = auto()
    DELETE = auto()

    def __str__(self):
        return self.name