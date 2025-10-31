from enum import IntFlag, IntEnum, auto


class RecType(IntEnum):
    HELLO = auto()
    WELCOME = auto()
    AUTH = auto()
    AUTH_RESULT = auto()
    DISCONNECT = auto()

    ACK = auto()
    PING = auto()
    PONG = auto()

    SNAPSHOT = auto()
    DELTA = auto()
    INPUT = auto()

    RESERVED = auto()


class RecordFlags(IntFlag):
    NONE = auto()
    RELIABLE = auto()
    URGENT = auto()


class PacketFlags(IntFlag):
    NONE = auto()
    RELIABLE = auto()
    FRAGMENT = auto()
    CONTROL = auto()


class DisconnectReason(IntEnum):
    UNSPECIFIED = auto()
    PROTOCOL_MISMATCH = auto()
    AUTH_FAILED = auto()
    KICK = auto()
    CAPACITY = auto()
    TIMEOUT = auto()
