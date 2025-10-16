from __future__ import annotations
from dataclasses import dataclass
import struct
from .base_record import Record, RecType, RecordFlags
from ...utils.int_types import UInt16

ACK_FMT = "!HH"  # ack_base, mask (16-bit bitmap)
PING_FMT = "!I"  # u32 milliseconds


@dataclass(slots=True)
class Ack(Record):
    TYPE = RecType.ACK
    ack_base: UInt16 = UInt16(0)
    mask: UInt16 = UInt16(0)

    def encode_payload(self) -> bytes:
        return struct.pack(ACK_FMT, self.ack_base.value, self.mask.value)

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


@dataclass(slots=True)
class Ping(Record):
    TYPE = RecType.PING
    ms: int = 0

    def encode_payload(self) -> bytes:
        return struct.pack(PING_FMT, self.ms & 0xFFFFFFFF)

    @classmethod
    def decode_payload(cls, payload: memoryview) -> "Ping":
        (ms,) = struct.unpack_from(PING_FMT, payload, 0)
        return cls(ms=ms)


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


@dataclass(slots=True)
class Fragment(Record):
    TYPE = RecType.FRAG_GENERIC
    RELIABLE_BY_DEFAULT = True

    blob: bytes = b""

    def flags(self):
        return super().flags() | RecordFlags.RELIABLE

    def encode_payload(self) -> bytes:
        return self.blob

    @classmethod
    def decode_payload(cls, payload: memoryview) -> Delta:
        return cls(blob=bytes(payload))
