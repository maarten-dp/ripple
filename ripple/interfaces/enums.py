from enum import IntFlag, IntEnum, auto


class RecType(IntEnum):
    ACK = auto()
    PING = auto()
    PONG = auto()
    HELLO = auto()
    AUTH = auto()
    SNAPSHOT = auto()
    DELTA = auto()
    INPUT = auto()
    FRAG_SNAPSHOT = auto()
    FRAG_GENERIC = auto()


class RecordFlags(IntFlag):
    NONE = 0
    RELIABLE = 0x01
    URGENT = 0x02
