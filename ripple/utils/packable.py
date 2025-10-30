from __future__ import annotations

from io import BytesIO
import struct
from inspect import get_annotations
from typing import (
    Annotated,
    List,
    Set,
    Tuple,
    Dict,
    ClassVar,
    Type,
    Iterable,
    get_origin,
    get_args,
)
from typing_extensions import Self
from enum import IntFlag, IntEnum
from dataclasses import dataclass, field
from inspect import isclass

from .packable_types import UIntBase, UInt8, UInt16, UInt32, BytesField
from ..interfaces import PackerType


_ENDIAN = "!"
_INT_ENUM_FMT = "B"


def make_packer(cls) -> Packer:
    packer = Packer()
    annotations = get_annotations(cls, eval_str=True)
    struct_format = _ENDIAN
    struct_fields = []
    bytes_fields = []
    dict_fields = []
    iterable_fields = []
    packable_fields = []

    for field, ann_type in annotations.items():
        origin = get_origin(ann_type)
        if origin is ClassVar:
            continue
        elif origin is Annotated:
            base, *meta = get_args(ann_type)
            if base is bytes and len(meta) == 1:
                if isinstance(meta[0], PackLen):
                    fmt = f"{meta[0].n}s"
        elif origin is dict:
            key_type, value_type = get_args(ann_type)
            if not issubclass(key_type, UIntBase):
                raise ValueError("Dict keys must inherit from UIntBase")
            dict_fields.append((field, key_type, value_type))
            continue
        elif origin in (list, set, tuple):
            value_type = get_args(ann_type)
            if len(value_type) > 1:
                raise ValueError(
                    "Only one type is supported for iterables for now"
                )
            iterable_fields.append((field, origin, value_type[0]))
            continue
        elif not isclass(ann_type):
            continue
        elif issubclass(ann_type, UIntBase):
            fmt = ann_type._struct_format
        elif issubclass(ann_type, (IntEnum, IntFlag)):
            fmt = _INT_ENUM_FMT
        elif issubclass(ann_type, Packable):
            packable_fields.append((field, ann_type))
            continue
        elif ann_type is BytesField:
            bytes_fields.append(field)
            continue
        else:
            continue

        struct_format = f"{struct_format}{fmt}"
        struct_fields.append(field)

    if struct_fields:
        struct_instance = struct.Struct(struct_format)
        packer.add(StructPacker(struct_instance, struct_fields, annotations))
    if bytes_fields:
        packer.add(BytesPacker(bytes_fields))
    if dict_fields:
        packer.add(DictPacker(dict_fields))
    if iterable_fields:
        packer.add(IterablePacker(iterable_fields))
    if packable_fields:
        packer.add(PackablePacker(packable_fields))
    return packer


@dataclass(frozen=True)
class PackLen:
    n: int


@dataclass
class StructPacker:
    struct: struct.Struct
    struct_fields: List[str]
    annotations: Dict[str, Type[UInt8 | UInt16 | UInt32]]

    def pack(self, packable: Packable) -> bytes:
        values = []
        for field in self.struct_fields:
            field_value = getattr(packable, field)
            values.append(field_value)
        return self.struct.pack(*values)

    def unpack(
        self, buffer: BytesIO
    ) -> Tuple[Dict[str, UInt8 | UInt16 | UInt32], int]:
        payload = buffer.read(self.struct.size)
        if len(payload) < self.struct.size:
            raise ValueError("buffer too small for unpacking")
        values = {}
        unpacked = self.struct.unpack_from(payload)
        for field, value in zip(self.struct_fields, unpacked):
            values[field] = self.annotations[field](value)
        return values


@dataclass
class BytesPacker:
    bytes_fields: List[str]

    def pack(self, packable: Packable) -> bytes:
        payload = b""
        for field in self.bytes_fields:
            field = getattr(packable, field)
            if not isinstance(field, BytesField):
                raise ValueError(f"{field} is not of type BytesField")
            payload += field.pack()
        return payload

    def unpack(self, buffer: BytesIO) -> Tuple[Dict[str, BytesField], int]:
        values = {}
        for field in self.bytes_fields:
            payload = BytesField.unpack(buffer)
            values[field] = payload
        return values


@dataclass
class PackablePacker:
    packable_fields: Iterable[str, Packable]

    def pack(self, packable: Packable) -> bytes:
        payload = b""
        for field_name, packable_type in self.packable_fields:
            field = getattr(packable, field_name)
            if not isinstance(field, packable_type):
                raise ValueError(f"{field_name} is not of type {packable_type}")
            payload += field.pack()
        return payload

    def unpack(
        self, buffer: BytesIO
    ) -> Dict[str, Dict[Type[UInt8 | UInt16 | UInt32], Packables]]:
        values = {}
        for field_name, packable_type in self.packable_fields:
            values[field_name] = packable_type.unpack(buffer)
        return values


@dataclass
class DictPacker:
    dict_fields: Iterable[str, Type[UInt8 | UInt16 | UInt32], PackablesType]

    def pack(self, packable: Packable) -> bytes:
        payload = b""
        for field_name, key_type, value_type in self.dict_fields:
            field = getattr(packable, field_name)
            payload += UInt16(len(field)).pack()
            for key, value in field.items():
                if not isinstance(key, key_type):
                    raise ValueError(f"{key} is not of type {key_type}")
                if not isinstance(value, value_type):
                    raise ValueError(f"{value} is not of type {value_type}")
                payload += key.pack()
                payload += value.pack()
        return payload

    def unpack(
        self, buffer: BytesIO
    ) -> Dict[str, Dict[UInt8 | UInt16 | UInt32, Packables]]:
        values = {}
        for field_name, key_type, value_type in self.dict_fields:
            items = UInt16.unpack(buffer)
            field_value = {}
            for _ in range(items):
                key = key_type.unpack(buffer)
                value = value_type.unpack(buffer)
                field_value[key] = value
            values[field_name] = field_value
        return values


@dataclass
class IterablePacker:
    iterable_fields: Iterable[str, Type[List | Set | Tuple], PackablesType]

    def pack(self, packable: Packable) -> bytes:
        payload = b""
        for field_name, iterable_type, packable_type in self.iterable_fields:
            field = getattr(packable, field_name)
            payload += UInt16(len(field)).pack()
            if not isinstance(field, iterable_type):
                raise ValueError(f"{field} is not of type {iterable_type}")
            for value in field:
                if not isinstance(value, packable_type):
                    raise ValueError(f"{value} is not of type {packable_type}")
                payload += value.pack()
        return payload

    def unpack(self, buffer: BytesIO) -> Dict[str, Iterable[Packables]]:
        values = {}
        for field_name, iterable_type, value_type in self.iterable_fields:
            items = UInt16.unpack(buffer)
            field_value = [value_type.unpack(buffer) for _ in range(items)]
            values[field_name] = iterable_type(field_value)
        return values


@dataclass
class Packer:
    packers: List[PackerType] = field(default_factory=list)

    def add(self, packer: PackerType):
        self.packers.append(packer)

    def pack(self, packable: Packables) -> bytes:
        payload = b""
        for packer in self.packers:
            payload += packer.pack(packable)
        return payload

    def unpack(self, buffer: BytesIO) -> Tuple[Dict[str, Packables], int]:
        fields = {}
        for packer in self.packers:
            unpacked_fields = packer.unpack(buffer)
            fields.update(unpacked_fields)
        return fields


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
    def unpack(cls, buffer: BytesIO) -> Self:
        parameters = cls._packer.unpack(buffer)
        return cls(**parameters)


Packables = UInt8 | UInt16 | UInt32 | BytesField | Packable
PackablesType = Type[Packables]
