from __future__ import annotations
from dataclasses import dataclass
import struct
from .base_record import Record, RecType
from ...utils.int_types import UInt16, UInt32

ACK_FMT = "!HH"  # ack_base, mask (16-bit bitmap)
PING_FMT = "!HI"  # u32 milliseconds


@dataclass(slots=True)
class Ack(Record):
    TYPE = RecType.ACK
    ack_base: UInt16 = UInt16(0)
    mask: UInt16 = UInt16(0)

    def encode_payload(self) -> bytes:
        return struct.pack(ACK_FMT, self.ack_base, self.mask)

    @classmethod
    def decode_payload(cls, payload: memoryview) -> Ack:
        ack_base, mask = struct.unpack_from(ACK_FMT, payload, 0)
        return cls(ack_base=ack_base, mask=mask)

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


from typing import overload


@dataclass(slots=True)
class Ping(Record):
    TYPE = RecType.PING
    id: UInt16
    ms: UInt32

    def encode_payload(self) -> bytes:
        return struct.pack(PING_FMT, self.id, self.ms)

    @classmethod
    def decode_payload(cls, payload: memoryview) -> Ping:
        ping_id, ms = struct.unpack_from(PING_FMT, payload, 0)
        return cls(id=ping_id, ms=ms)

    def to_pong(self):
        return Pong(id=self.id, ms=self.ms)


@dataclass(slots=True)
class Pong(Ping):
    TYPE = RecType.PONG


@dataclass(slots=True)
class Delta(Record):
    TYPE = RecType.DELTA
    RELIABLE_BY_DEFAULT = True

    blob: bytes = b""

    def encode_payload(self) -> bytes:
        return self.blob

    @classmethod
    def decode_payload(cls, payload: memoryview) -> Delta:
        return cls(blob=bytes(payload))
