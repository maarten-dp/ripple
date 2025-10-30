from __future__ import annotations
from typing import Annotated, cast
from dataclasses import dataclass

from ...utils import UInt8, UInt16, UInt32
from ...interfaces import PacketFlags
from ...utils.packable import Packable, PackLen, StructPacker

MAGIC = b"RP"
VERSION_V1 = 0x01

U16_MOD = 1 << 16
U16_HALF = 1 << 15


class Header(Packable):
    @classmethod
    def size(cls):
        packer = cast(StructPacker, cls._packer.packers[0])
        return packer.struct.size


@dataclass(frozen=True)
class PacketHeader(Header):
    magic: Annotated[bytes, PackLen(2)] = MAGIC
    version: UInt8 = UInt8(VERSION_V1)
    flags: PacketFlags = PacketFlags.NONE
    seq: UInt16 = UInt16(0)
    rid: UInt16 = UInt16(0)
    reserved: UInt16 = UInt16(0)

    def __post_init__(self):
        if self.magic != MAGIC:
            raise ValueError("bad magic")
        if self.version != VERSION_V1:
            raise ValueError(f"unsupported version {self.version}")
        if self.reserved != 0:
            raise ValueError("reserved field must be zero in v1")

    def distance(self, other: PacketHeader) -> int:
        return int(other.seq - self.seq)

    def __lt__(self, other: PacketHeader) -> bool:
        """Return True if a is 'less than' b in u16 wraparound space."""
        return (self.seq - other.seq) > U16_HALF

    def __gt__(self, other: PacketHeader) -> bool:
        """Return True if a is 'greater than' b in u16 wraparound space."""
        return (self.seq - other.seq) < U16_HALF


@dataclass(frozen=True)
class RecordHeader(Header):
    type: UInt8
    flags: UInt8
    length: UInt16


@dataclass(frozen=True)
class FragmentHeader(Header):
    msg_id: UInt16
    index: UInt8
    count: UInt8
    total_len: UInt16
    msg_crc32: UInt32
