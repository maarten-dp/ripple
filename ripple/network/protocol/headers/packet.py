from __future__ import annotations
from dataclasses import dataclass, field
from functools import partial
from enum import IntFlag
import struct

from ....utils.int_types import UInt8, UInt16

MAGIC = b"RP"
VERSION_V1 = 0x01

U16_MOD = 1 << 16
U16_HALF = 1 << 15

_ENDIAN = ">"
_MAGIC = "2s"
_VERSION = "B"
_FLAGS = "B"
_SEQ = "H"
_RID = "H"
_RESERVERD = "H"

_HEADER_FMT = f"{_ENDIAN}{_MAGIC}{_VERSION}{_FLAGS}{_SEQ}{_RID}{_RESERVERD}"
_HEADER_SIZE = struct.calcsize(_HEADER_FMT)
pack = partial(struct.pack, _HEADER_FMT, MAGIC, VERSION_V1)
unpack = partial(struct.unpack, _HEADER_FMT)


class PacketFlags(IntFlag):
    RELIABLE = 0x01
    FRAGMENT = 0x02
    CONTROL = 0x04


@dataclass(frozen=True)
class PacketHeader:
    flags: PacketFlags | int
    seq: UInt16 | int
    rid: UInt16 | int = 0

    def __post_init__(self):
        object.__setattr__(self, "flags", PacketFlags(int(self.flags)))
        object.__setattr__(self, "seq", UInt16(self.seq))
        object.__setattr__(self, "rid", UInt16(self.rid))

    def pack(self) -> bytes:
        return pack(int(self.flags), int(self.seq), int(self.rid), 0)

    @classmethod
    def unpack(cls, buf: memoryview | bytes) -> PacketHeader:
        if len(buf) < _HEADER_SIZE:
            raise ValueError("buffer too small for header")
        magic, ver, flags, seq, rid, reserved = unpack(buf[:_HEADER_SIZE])
        if magic != MAGIC:
            raise ValueError("bad magic")
        if ver != VERSION_V1:
            raise ValueError(f"unsupported version {ver}")
        if reserved != 0:
            raise ValueError("reserved field must be zero in v1")
        return cls(flags=flags, seq=seq, rid=rid)

    @staticmethod
    def size() -> int:
        return _HEADER_SIZE

    def distance(self, other: PacketHeader) -> int:
        return int(other.seq - self.seq)

    def __lt__(self, other: PacketHeader) -> bool:
        """Return True if a is 'less than' b in u16 wraparound space."""
        return (self.seq - other.seq) > U16_HALF

    def __gt__(self, other: PacketHeader) -> bool:
        """Return True if a is 'greater than' b in u16 wraparound space."""
        return (self.seq - other.seq) < U16_HALF
