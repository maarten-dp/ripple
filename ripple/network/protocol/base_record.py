from __future__ import annotations
from dataclasses import dataclass
from typing import (
    ClassVar,
    Type,
    Dict,
    Tuple,
)
from typing_extensions import Self

from .headers import RecordHeader
from ...utils.int_types import UInt16, UInt8
from ...interfaces import RecordFlags, RecType, RecordType


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

    def flags(self) -> RecordFlags:
        if self.RELIABLE_BY_DEFAULT:
            return RecordFlags.RELIABLE
        return RecordFlags.NONE

    def pack(self) -> bytes:
        payload = self.encode_payload()

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
    ) -> Tuple[Self | RecordType, RecordHeader]:
        header = RecordHeader.unpack(buffer)

        # If called on base class, dispatch to concrete type
        if cls is Record:
            record_class = cls._registry.get(RecType(int(header.type)))
            if record_class is None:
                raise KeyError(f"Unknown record type: {header.type}")
            return record_class.unpack(buffer)

        # If called on concrete class, validate type matches
        if header.type != cls.TYPE:
            raise ValueError(
                f"Type mismatch: header={header.type}, class={cls.TYPE}"
            )

        # Extract payload
        payload_start = header.size()
        payload_end = header.record_size()
        payload = buffer[payload_start:payload_end]

        # Decode payload
        record = cls.decode_payload(payload)

        return record, header

    def encode_payload(self) -> bytes:
        raise NotImplementedError

    @classmethod
    def decode_payload(cls, payload: memoryview) -> Self:
        raise NotImplementedError
