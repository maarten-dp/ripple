from __future__ import annotations

import sys
import struct
from typing import (
    Annotated,
    List,
    ClassVar,
    Callable,
    get_type_hints,
    get_origin,
    get_args,
)
from typing_extensions import Self
from enum import IntFlag, IntEnum
from dataclasses import dataclass, field
from inspect import isclass

from .int_types import UIntBase, UInt16

_ENDIAN = "!"
_INT_ENUM_FMT = "B"


def _get_stuct_packer(struct_format, struct_fields, annotations):
    struct_size = struct.calcsize(struct_format)

    def packer(packable):
        values = []
        for field in struct_fields:
            values.append(getattr(packable, field))
        return struct.pack(struct_format, *values)

    def unpacker(buffer: memoryview):
        if len(buffer) < struct_size:
            raise ValueError("buffer too small for unpacking")
        values = {}
        payload_buffer = buffer[:struct_size]
        unpacked = struct.unpack_from(struct_format, payload_buffer)
        for field, value in zip(struct_fields, unpacked):
            values[field] = annotations[field](value)
        return values

    return PackInfo(
        struct_size=struct_size,
        struct_format=struct_format,
        struct_fields=struct_fields,
        packer=packer,
        unpacker=unpacker,
    )


def _get_freeform_packer(formfields):
    def packer(packable):
        payload = b""
        for field in formfields:
            payload += getattr(packable, field).pack()
        return payload

    def unpacker(buffer: memoryview):
        offset = 0
        values = {}
        for field in formfields:
            payload = FreeFormField.unpack(buffer[offset:])
            values[field] = payload
            offset += payload.length
        return values

    return PackInfo(
        struct_size=-1,
        struct_format="",
        struct_fields=formfields,
        packer=packer,
        unpacker=unpacker,
    )


def _get_combined_packer(struct_info: PackInfo, free_info: PackInfo):
    def packer(packable):
        payload = struct_info.packer(packable)
        payload += free_info.packer(packable)
        return payload

    def unpacker(buffer: memoryview):
        fields = struct_info.unpacker(buffer)
        offset = struct_info.struct_size
        fields.update(free_info.unpacker(buffer[offset:]))
        return fields

    return PackInfo(
        struct_size=-1,
        struct_format="",
        struct_fields=[
            *struct_info.struct_fields,
            *free_info.struct_fields,
        ],
        packer=packer,
        unpacker=unpacker,
    )


@dataclass(frozen=True)
class PackLen:
    n: int


@dataclass
class FreeFormField:
    payload: bytes
    length: UInt16 = field(init=False, default=UInt16(0))

    _fmt: ClassVar[str] = f"!{UInt16._struct_format}"
    _fmt_size: ClassVar[int] = struct.calcsize(_fmt)

    def __post_init__(self):
        self.length = len(self.payload)

    def pack(self) -> bytes:
        return struct.pack(self._fmt, self.length) + self.payload

    @classmethod
    def unpack(cls, buffer: memoryview) -> Self:
        (length,) = struct.unpack(cls._fmt, buffer[: cls._fmt_size])
        start = cls._fmt_size
        end = start + length
        payload = buffer[start:end]
        return cls(payload)

    def __eq__(self, other: FreeFormField | bytes):
        if isinstance(other, bytes):
            return self.payload == other
        self.payload == other.payload


@dataclass
class PackInfo:
    struct_size: int
    struct_format: str
    struct_fields: List[str]
    packer: Callable
    unpacker: Callable


class PackableMeta(type):
    def __new__(cls, name, bases, dct):
        cls = super().__new__(cls, name, bases, dct)

        struct_format = _ENDIAN
        struct_fields = []

        globalsns = vars(sys.modules[cls.__module__])
        globalsns.update(
            {
                "PackInfo": PackInfo,
                "ClassVar": ClassVar,
            }
        )

        annotations = get_type_hints(
            cls,
            globalns=globalsns,
            localns=vars(cls),
            include_extras=True,
        )

        freefields = []
        for field, ann_type in annotations.items():
            origin = get_origin(ann_type)
            if origin is ClassVar:
                continue
            elif origin is Annotated:
                base, *meta = get_args(ann_type)
                if base is bytes and len(meta) == 1:
                    if isinstance(meta[0], PackLen):
                        fmt = f"{meta[0].n}s"
            elif not isclass(ann_type):
                continue
            elif issubclass(ann_type, UIntBase):
                fmt = ann_type._struct_format
            elif issubclass(ann_type, (IntEnum, IntFlag)):
                fmt = _INT_ENUM_FMT
            elif ann_type is FreeFormField:
                freefields.append(field)
                continue
            else:
                continue

            struct_format = f"{struct_format}{fmt}"
            struct_fields.append(field)

        struct_pack_info = None
        free_pack_info = None
        if struct_fields:
            struct_pack_info = _get_stuct_packer(
                struct_format, struct_fields, annotations
            )
        if freefields:
            free_pack_info = _get_freeform_packer(freefields)

        pack_info = struct_pack_info or free_pack_info
        if struct_pack_info and free_pack_info:
            pack_info = _get_combined_packer(struct_pack_info, free_pack_info)

        cls._pack_info = pack_info
        return cls


class Packable(metaclass=PackableMeta):
    _pack_info: ClassVar[PackInfo]

    def pack(self) -> bytes:
        return self._pack_info.packer(self)

    @classmethod
    def unpack(cls, buffer: memoryview) -> Self:
        parameters = cls._pack_info.unpacker(buffer)
        return cls(**parameters)

    @classmethod
    def size(cls) -> int:
        return cls._pack_info.struct_size
