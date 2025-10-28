from __future__ import annotations
from typing import Protocol, ClassVar, Tuple
from typing_extensions import Self

from .enums import RecType, RecordFlags


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
