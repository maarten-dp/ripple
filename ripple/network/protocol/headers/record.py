from __future__ import annotations
from dataclasses import dataclass
from functools import partial
import struct

from ....utils.int_types import UInt8, UInt16

_ENDIAN = ">"
_TYPE = "B"
_FLAGS = "B"
_LENGTH = "H"

_RECORD_HEADER_FMT = f"{_ENDIAN}{_TYPE}{_FLAGS}{_LENGTH}"
_RECORD_HEADER_SIZE = struct.calcsize(_RECORD_HEADER_FMT)
pack = partial(struct.pack, _RECORD_HEADER_FMT)
unpack = partial(struct.unpack_from, _RECORD_HEADER_FMT)


@dataclass(frozen=True)
class RecordHeader:
    type: UInt8 | int
    flags: UInt8 | int
    length: UInt16 | int

    def __post_init__(self):
        object.__setattr__(self, "type", UInt8(self.type))
        object.__setattr__(self, "flags", UInt8(self.flags))
        object.__setattr__(self, "length", UInt16(self.length))

    def pack(self) -> bytes:
        return pack(int(self.type), int(self.flags), int(self.length))

    @classmethod
    def unpack(cls, buffer: memoryview) -> RecordHeader:
        if len(buffer) < _RECORD_HEADER_SIZE:
            raise ValueError("buffer too small for header")
        type, flags, length = unpack(buffer)
        return cls(type=type, flags=flags, length=length)

    @staticmethod
    def size() -> int:
        return _RECORD_HEADER_SIZE

    def record_size(self) -> int:
        return self.size() + int(self.length)
