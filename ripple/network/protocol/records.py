from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar

from .base_record import Record, RecType
from ...utils import UInt8, UInt16, UInt32
from ...interfaces import DisconnectReason
from ...utils.packable import BytesField
from ...ecs.snapshot import DeltaSnapshot, Snapshot


@dataclass(slots=True)
class Hello(Record):
    TYPE: ClassVar[RecType] = RecType.HELLO

    protocol_version: UInt8
    client_nonce: UInt32
    app_id: UInt32


@dataclass(slots=True)
class Welcome(Record):
    TYPE: ClassVar[RecType] = RecType.WELCOME

    server_nonce: UInt32
    assigned_client_id: UInt16
    max_record_size: UInt16


@dataclass(slots=True)
class Auth(Record):
    TYPE: ClassVar[RecType] = RecType.AUTH

    method: UInt8
    credential: BytesField


@dataclass(slots=True)
class AuthResult(Record):
    TYPE: ClassVar[RecType] = RecType.AUTH_RESULT

    ok: UInt8
    session_id: UInt32
    msg: BytesField


@dataclass(slots=True)
class Disconnect(Record):
    TYPE: ClassVar[RecType] = RecType.DISCONNECT

    reason_code: DisconnectReason
    msg: BytesField


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

    snapshot: DeltaSnapshot


@dataclass(slots=True)
class Snapshot(Record):
    TYPE: ClassVar[RecType] = RecType.SNAPSHOT
    RELIABLE_BY_DEFAULT = True

    snapshot: Snapshot


@dataclass(slots=True)
class Input(Record):
    TYPE: ClassVar[RecType] = RecType.INPUT
    RELIABLE_BY_DEFAULT = True

    key: UInt16
    modifiers: UInt8
    up_down: UInt8
