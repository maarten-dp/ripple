from __future__ import annotations
from io import BytesIO
from typing import (
    ClassVar,
    Type,
    Dict,
    Tuple,
)
from typing_extensions import Self

from .headers import RecordHeader
from ...utils import UInt16, UInt8
from ...utils.packable import PackableMeta, PackerType
from ...interfaces import RecordFlags, RecType, RecordType, RecordHeaderType


class RecordMeta(PackableMeta):
    _registry: Dict[RecType, Type[RecordType]] = {}

    def __init__(cls: Type[RecordType], name, bases, namespace):
        super().__init__(name, bases, namespace)
        if hasattr(cls, "TYPE"):
            RecordMeta._registry[cls.TYPE] = cls

    @classmethod
    def get_registry(mcs) -> Dict[RecType, Type[RecordType]]:
        return dict(mcs._registry)


class Record(metaclass=RecordMeta):
    TYPE: ClassVar[RecType]
    RELIABLE_BY_DEFAULT: ClassVar[bool] = False
    _packer: ClassVar[PackerType]

    def flags(self) -> RecordFlags:
        if self.RELIABLE_BY_DEFAULT:
            return RecordFlags.RELIABLE
        return RecordFlags.NONE

    def pack(self) -> bytes:
        payload = self._packer.pack(self)

        header = RecordHeader(
            type=UInt8(self.TYPE),
            flags=UInt8(self.flags()),
            length=UInt16(len(payload)),
        )
        return header.pack() + payload

    @classmethod
    def unpack(
        cls,
        buffer: BytesIO,
        header: RecordHeader | None = None,
    ) -> Tuple[Self | RecordType, RecordHeader]:
        if header is None:
            header = RecordHeader.unpack(buffer)

        if cls is Record:
            record_class = cls._registry.get(RecType(int(header.type)))
            if record_class is None:
                raise KeyError(f"Unknown record type: {header.type}")
            return record_class.unpack(buffer, header)

        if header.type != cls.TYPE:
            raise ValueError(
                f"Type mismatch: header={header.type}, class={cls.TYPE}"
            )

        record = cls(**cls._packer.unpack(buffer))
        return record, header
