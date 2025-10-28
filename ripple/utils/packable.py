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
from dataclasses import dataclass
from inspect import isclass

from .int_types import UIntBase

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
        header_buffer = buffer[:struct_size]
        unpacked = struct.unpack_from(struct_format, header_buffer)
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


def _get_freeform_packer(formfield):
    def packer(packable):
        return getattr(packable, formfield)

    def unpacker(buffer: memoryview):
        return {formfield: bytes(buffer)}

    return PackInfo(
        struct_size=-1,
        struct_format="",
        struct_fields=[formfield],
        packer=packer,
        unpacker=unpacker,
    )


@dataclass(frozen=True)
class PackLen:
    n: int


@dataclass
class PackInfo:
    struct_size: int
    struct_format: str
    struct_fields: List[str]
    packer: Callable
    unpacker: Callable


class PackableMeta(type):
    def __new__(cls, name, bases, dct):
        struct_format = _ENDIAN
        struct_fields = []
        cls = super().__new__(cls, name, bases, dct)

        globalsns = vars(sys.modules[cls.__module__])
        globalsns["PackInfo"] = PackInfo

        annotations = get_type_hints(
            cls,
            globalns=globalsns,
            localns=vars(cls),
            include_extras=True,
        )

        freefield = None
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
            elif ann_type is bytes:
                if freefield is not None:
                    raise ValueError("Only one bytes field is allowed")
                freefield = field
                continue

            struct_format = f"{struct_format}{fmt}"
            struct_fields.append(field)

        if freefield is not None:
            if struct_fields:
                raise ValueError("Cannot mix bytes type with pack types")
            pack_info = _get_freeform_packer(freefield)
        else:
            pack_info = _get_stuct_packer(
                struct_format, struct_fields, annotations
            )
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
