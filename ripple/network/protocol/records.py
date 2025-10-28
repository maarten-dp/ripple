from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from typing_extensions import Self
import struct

from .base_record import Record, RecType
from ...utils.int_types import UInt16, UInt32


@dataclass(slots=True)
class Ack(Record):
    TYPE: ClassVar[RecType] = RecType.ACK
    ack_base: UInt16 = UInt16(0)
    mask: UInt16 = UInt16(0)

    def expand_to_seqs(self):
        out = [self.ack_base]
        mask = self.mask
        bit = 1
        while mask:
            if mask & 1:
                seq = self.ack_base - bit
                out.append(seq)
            mask >>= 1
            bit += 1
        return out


@dataclass(slots=True)
class Ping(Record):
    TYPE: ClassVar[RecType] = RecType.PING
    id: UInt16
    ms: UInt32

    def to_pong(self) -> Pong:
        return Pong(id=self.id, ms=self.ms)


@dataclass(slots=True)
class Pong(Ping):
    TYPE: ClassVar[RecType] = RecType.PONG


@dataclass(slots=True)
class Delta(Record):
    TYPE: ClassVar[RecType] = RecType.DELTA
    RELIABLE_BY_DEFAULT = True

    blob: bytes = b""
