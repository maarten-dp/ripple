from __future__ import annotations

import sys
import struct
from inspect import get_annotations
from typing import (
    Annotated,
    List,
    Dict,
    ClassVar,
    Tuple,
    Type,
    get_type_hints,
    get_origin,
    get_args,
)
from typing_extensions import Self
from enum import IntFlag, IntEnum
from dataclasses import dataclass, field
from inspect import isclass

from .numerical_types import UIntBase, UInt8, UInt16, UInt32
from ..interfaces import PackerType

_ENDIAN = "!"
_INT_ENUM_FMT = "B"


def make_packer(cls) -> Packer:
    annotations = get_annotations(cls, eval_str=True)
    struct_format = _ENDIAN
    struct_fields = []
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
        elif ann_type is BytesField:
            freefields.append(field)
            continue
        else:
            continue

        struct_format = f"{struct_format}{fmt}"
        struct_fields.append(field)

    packer = Packer()
    if struct_fields:
        struct_instance = struct.Struct(struct_format)
        packer.add(StructPacker(struct_instance, struct_fields, annotations))
    if freefields:
        packer.add(BytesPacker(freefields))
    return packer


@dataclass(frozen=True)
class PackLen:
    n: int


@dataclass
class StructPacker:
    struct: struct.Struct
    struct_fields: List[str]
    annotations: Dict[str, Type[UInt8 | UInt16 | UInt32]]

    @property
    def size(self) -> int:
        return self.struct.size

    def pack(self, packable: UIntBase) -> bytes:
        values = []
        for field in self.struct_fields:
            values.append(getattr(packable, field))
        return self.struct.pack(*values)

    def unpack(
        self, buffer: memoryview
    ) -> Tuple[Dict[str, UInt8 | UInt16 | UInt32], int]:
        if len(buffer) < self.size:
            raise ValueError("buffer too small for unpacking")
        values = {}
        payload_buffer = buffer[: self.size]
        unpacked = self.struct.unpack_from(payload_buffer)
        for field, value in zip(self.struct_fields, unpacked):
            values[field] = self.annotations[field](value)
        return values, self.size


@dataclass
class BytesPacker:
    formfields: List[str]

    @property
    def size(self) -> int:
        raise ValueError("Cannot determine size for BytesField")

    def pack(self, packable: BytesField) -> bytes:
        payload = b""
        for field in self.formfields:
            payload += getattr(packable, field).pack()
        return payload

    def unpack(self, buffer: memoryview) -> Tuple[Dict[str, BytesField], int]:
        offset = 0
        values = {}
        for field in self.formfields:
            payload = BytesField.unpack(buffer[offset:])
            values[field] = payload
            offset += payload.length
        return values, offset


@dataclass
class Packer:
    packers: List[PackerType] = field(default_factory=list)

    def add(self, packer: PackerType):
        self.packers.append(packer)

    @property
    def size(self) -> int:
        return sum([p.size for p in self.packers])

    def pack(self, packable: Packables) -> bytes:
        payload = b""
        for packer in self.packers:
            payload += packer.pack(packable)
        return payload

    def unpack(self, buffer: memoryview) -> Tuple[Dict[str, Packables], int]:
        offset = 0
        fields = {}
        for packer in self.packers:
            unpacked_fields, offset = packer.unpack(buffer[offset:])
            fields.update(unpacked_fields)
        return fields, offset


@dataclass
class BytesField:
    payload: bytes
    length: UInt16 = field(init=False, default=UInt16(0))

    _fmt: ClassVar[str] = f"!{UInt16._struct_format}"
    _fmt_size: ClassVar[int] = struct.calcsize(_fmt)

    def __post_init__(self):
        if len(self.payload) > UInt16(-1):
            raise ValueError("Payload too large")
        self.length = UInt16(len(self.payload))

    def pack(self) -> bytes:
        return struct.pack(self._fmt, self.length) + self.payload

    @classmethod
    def unpack(cls, buffer: memoryview) -> Self:
        (length,) = struct.unpack(cls._fmt, buffer[: cls._fmt_size])
        start = cls._fmt_size
        end = start + length
        payload = buffer[start:end]
        return cls(bytes(payload))

    def __eq__(self, other: BytesField | bytes):
        if isinstance(other, bytes):
            return self.payload == other
        self.payload == other.payload


class PackableMeta(type):
    def __new__(cls, name, bases, dct):
        cls = super().__new__(cls, name, bases, dct)
        cls._packer = make_packer(cls)
        return cls


class Packable(metaclass=PackableMeta):
    _packer: ClassVar[Packer]

    def pack(self) -> bytes:
        return self._packer.pack(self)

    @classmethod
    def unpack(cls, buffer: memoryview) -> Self:
        parameters, _ = cls._packer.unpack(buffer)
        return cls(**parameters)

    @classmethod
    def size(cls) -> int:
        return cls._packer.size


Packables = UInt8 | UInt16 | UInt32 | BytesField | Packable
PackablesType = Type[Packables]
