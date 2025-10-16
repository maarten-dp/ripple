from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar, Optional, Type, Dict, Tuple
from typing_extensions import Self
import struct

from .headers import RecordFlags, RecordHeader
from ...utils.int_types import UInt16, UInt8


_RID_FMT = ">H"
_RID_SIZE = struct.calcsize(_RID_FMT)


class RecType(IntEnum):
    ACK = 0x01
    PING = 0x02
    HELLO = 0x03
    AUTH = 0x04
    SNAPSHOT = 0x10
    DELTA = 0x11
    INPUT = 0x12
    FRAG_SNAPSHOT = 0x20
    FRAG_GENERIC = 0x21


class RecordMeta(type):
    _registry: Dict[RecType, Type[RecordType]] = {}

    def __init__(cls: Type[RecordType], name, bases, namespace):
        super().__init__(name, bases, namespace)
        if hasattr(cls, "TYPE"):
            RecordMeta._registry[cls.TYPE] = cls

    @classmethod
    def get_registry(mcs) -> Dict[RecType, Type[RecordType]]:
        return dict(mcs._registry)


@dataclass(slots=True)
class Record(metaclass=RecordMeta):
    TYPE: ClassVar[RecType]
    RELIABLE_BY_DEFAULT: ClassVar[bool] = False

    rid: Optional[UInt16] = None

    def flags(self) -> RecordFlags:
        if self.RELIABLE_BY_DEFAULT or (self.rid is not None):
            return RecordFlags.RELIABLE
        return RecordFlags.NONE

    def pack(self) -> bytes:
        payload = self.encode_payload()
        if self.rid is not None:
            payload += struct.pack(">H", self.rid)
        header = RecordHeader(
            type=UInt8(self.TYPE),
            flags=UInt8(self.flags()),
            length=UInt16(len(payload)),
        )
        return header.pack() + payload

    @classmethod
    def unpack(
        cls,
        buffer: memoryview,
    ) -> Tuple[RecordType, RecordHeader]:
        header = RecordHeader.unpack(buffer)

        # If called on base class, dispatch to concrete type
        if cls is Record:
            record_class = cls._registry.get(RecType(int(header.type)))
            if record_class is None:
                raise KeyError(f"Unknown record type: {header.type}")
            return record_class.unpack(buffer)
        cls = cast(Type[RecordType], cls)

        # If called on concrete class, validate type matches
        if header.type != cls.TYPE:
            raise ValueError(
                f"Type mismatch: header={header.type}, class={cls.TYPE}"
            )

        # Extract payload
        payload_start = header.size()
        payload_end = header.record_size()
        payload = buffer[payload_start:payload_end]

        # Attach reliability metadata if needed
        rid = None
        if header.flags & RecordFlags.RELIABLE:
            (rid,) = struct.unpack(_RID_FMT, payload[-_RID_SIZE:])
            payload = payload[:-_RID_SIZE]

        # Decode payload
        record = cls.decode_payload(payload)
        if rid is not None:
            record.rid = UInt16(rid)

        return record, header

    def encode_payload(self) -> bytes:
        raise NotImplementedError

    @classmethod
    def decode_payload(cls, payload: memoryview) -> Self:
        raise NotImplementedError


# from ...utils.types import RecordType
from typing import TypeAlias, cast

from .records import Ack, Delta, Ping

RecordType: TypeAlias = Ack | Delta | Ping
