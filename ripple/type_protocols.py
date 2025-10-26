from __future__ import annotations
from typing import Protocol, ClassVar, Tuple, Optional, List
from typing_extensions import Self
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


class HeaderType(Protocol):
    def pack(self) -> bytes: ...

    @classmethod
    def unpack(cls, buffer: memoryview) -> HeaderType: ...

    @staticmethod
    def size() -> int: ...


class RecordType(Protocol):
    TYPE: ClassVar[RecType]
    RELIABLE_BY_DEFAULT: ClassVar[bool]

    def flags(self) -> RecordFlags: ...
    def pack(self) -> bytes: ...

    @classmethod
    def unpack(
        cls, buffer: memoryview
    ) -> Tuple[Self | RecordType, HeaderType]: ...

    def encode_payload(self) -> bytes: ...
    @classmethod
    def decode_payload(cls, payload: memoryview) -> Self: ...


class ConnectionExtension(Protocol):
    def init(self, connection: ConnectionType) -> None: ...
    def on_tick(self) -> None: ...
    def on_record(self, record: RecordType) -> bool: ...


class ConnectionType(Protocol):
    def send_record(self, record: RecordType) -> None: ...
    def recv_record(self) -> Optional[RecordType]: ...
    def recv_all(self) -> List[RecordType]: ...
    def tick(*args, **kwargs) -> None: ...
    def close(self) -> None: ...
