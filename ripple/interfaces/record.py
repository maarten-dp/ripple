from __future__ import annotations
from typing import Protocol, ClassVar, Tuple
from typing_extensions import Self
from io import BytesIO

from .enums import RecType, RecordFlags


class PackableType(Protocol):
    def pack(self) -> bytes: ...

    @classmethod
    def unpack(cls, buffer: BytesIO) -> Self: ...

    @classmethod
    def size(cls) -> int: ...


class HeaderType(PackableType): ...


class RecordHeaderType(PackableType):
    def record_size(self) -> int: ...


class RecordType(Protocol):
    TYPE: ClassVar[RecType]
    RELIABLE_BY_DEFAULT: ClassVar[bool]

    def flags(self) -> RecordFlags: ...
    def pack(self) -> bytes: ...

    @classmethod
    def unpack(
        cls, buffer: BytesIO
    ) -> Tuple[Self | RecordType, RecordHeaderType]: ...
