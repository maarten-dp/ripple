import pytest
from typing import Dict, List, Tuple, Set
from io import BytesIO
from dataclasses import dataclass

from ripple.utils import UInt8, UInt16, UInt32, BytesField
from ripple.utils.packable import (
    Packable,
    StructPacker,
    BytesPacker,
    DictPacker,
    PackablePacker,
    IterablePacker,
)


@pytest.mark.parametrize(
    "value",
    [
        UInt8(1),
        UInt16(2),
        UInt32(3),
        BytesField(b"some value"),
    ],
)
def test_it_can_pack_base_types(value):
    payload = value.pack()
    stream = BytesIO(payload)
    unpacked = type(value).unpack(stream)
    assert value == unpacked
    assert not stream.read()


def test_it_can_pack_struct_packable():
    @dataclass
    class StructPackable(Packable):
        field1: UInt8
        field2: UInt16
        field3: UInt32

    assert len(StructPackable._packer.packers) == 1
    assert isinstance(StructPackable._packer.packers[0], StructPacker)

    instance = StructPackable(UInt8(1), UInt16(2), UInt32(3))
    payload = instance.pack()
    stream = BytesIO(payload)
    unpacked = StructPackable.unpack(stream)
    assert instance == unpacked
    assert not stream.read()


def test_it_can_pack_bytes_field_packable():
    @dataclass
    class BytesPackable(Packable):
        field1: BytesField
        field2: BytesField

    assert len(BytesPackable._packer.packers) == 1
    assert isinstance(BytesPackable._packer.packers[0], BytesPacker)

    instance = BytesPackable(
        BytesField(b"Some value"),
        BytesField(b"Another value"),
    )
    payload = instance.pack()
    stream = BytesIO(payload)
    unpacked = BytesPackable.unpack(stream)
    assert instance == unpacked
    assert not stream.read()


def test_it_can_pack_packable_field_packable():
    @dataclass
    class SimplePackable(Packable):
        field1: UInt8 = UInt8(0)

    @dataclass
    class PackablePackable(Packable):
        field1: SimplePackable

    assert len(PackablePackable._packer.packers) == 1
    assert isinstance(PackablePackable._packer.packers[0], PackablePacker)

    instance = PackablePackable(SimplePackable(UInt8(1)))
    payload = instance.pack()
    stream = BytesIO(payload)
    unpacked = PackablePackable.unpack(stream)
    assert instance == unpacked
    assert not stream.read()


def test_it_can_pack_simple_iterable_field_packable():
    @dataclass
    class IterablePackable(Packable):
        field1: List[UInt8]
        field2: Tuple[BytesField, ...]
        field3: Set[UInt16]

    assert len(IterablePackable._packer.packers) == 1
    assert isinstance(IterablePackable._packer.packers[0], IterablePacker)

    instance = IterablePackable(
        [UInt8(1), UInt8(-1)],
        (BytesField(b"value"), BytesField(b"other")),
        {UInt16(3), UInt16(-1)},
    )
    payload = instance.pack()
    stream = BytesIO(payload)
    unpacked = IterablePackable.unpack(stream)
    assert instance == unpacked
    assert not stream.read()


def test_it_can_pack_simple_dict_field_packable():
    @dataclass
    class DictPackable(Packable):
        field1: Dict[UInt8, UInt16]
        field2: Dict[UInt16, UInt32]
        field3: Dict[UInt8, BytesField]

    assert len(DictPackable._packer.packers) == 1
    assert isinstance(DictPackable._packer.packers[0], DictPacker)

    instance = DictPackable(
        {
            UInt8(1): UInt16(2),
        },
        {
            UInt16(3): UInt32(4),
            UInt16(-1): UInt32(-1),
        },
        {
            UInt8(1): BytesField(b"value"),
        },
    )
    payload = instance.pack()
    stream = BytesIO(payload)
    unpacked = DictPackable.unpack(stream)
    assert instance == unpacked
    assert not stream.read()


def test_it_can_pack_nested_dict_field_packable():
    @dataclass
    class SimplePackable(Packable):
        field1: UInt8 = UInt8(0)

    @dataclass
    class NestedDictPackable(Packable):
        field1: Dict[UInt8, SimplePackable]

    assert len(NestedDictPackable._packer.packers) == 1
    assert isinstance(NestedDictPackable._packer.packers[0], DictPacker)

    instance = NestedDictPackable(
        {
            UInt8(1): SimplePackable(UInt8(1)),
            UInt8(2): SimplePackable(UInt8(2)),
        },
    )
    payload = instance.pack()
    stream = BytesIO(payload)
    unpacked = NestedDictPackable.unpack(stream)
    assert instance == unpacked
    assert not stream.read()


def test_it_can_pack_deeply_nested_dict_field_packable():
    @dataclass
    class SimplePackable(Packable):
        field1: UInt8 = UInt8(0)

    @dataclass
    class NestedDictPackable(Packable):
        field1: Dict[UInt8, SimplePackable]

    @dataclass
    class DeepNestedDictPackable(Packable):
        field1: Dict[UInt8, NestedDictPackable]

    assert len(NestedDictPackable._packer.packers) == 1
    assert isinstance(NestedDictPackable._packer.packers[0], DictPacker)

    instance = DeepNestedDictPackable(
        {
            UInt8(3): NestedDictPackable(
                {
                    UInt8(1): SimplePackable(UInt8(1)),
                    UInt8(2): SimplePackable(UInt8(2)),
                },
            )
        }
    )
    payload = instance.pack()
    stream = BytesIO(payload)
    unpacked = DeepNestedDictPackable.unpack(stream)
    assert instance == unpacked
    assert not stream.read()


def test_it_can_pack_mixed_field_packable():
    @dataclass
    class SimplePackable(Packable):
        field1: UInt8
        field2: List[UInt16]

    @dataclass
    class MixedPackable(Packable):
        field1: UInt8
        field2: BytesField
        field3: UInt16
        field4: BytesField
        field5: SimplePackable
        field6: Tuple[UInt16, ...]
        field7: Dict[UInt16, SimplePackable]
        field8: UInt32

    assert len(MixedPackable._packer.packers) == 5

    instance = MixedPackable(
        UInt8(1),
        BytesField(b"Some value"),
        UInt16(2),
        BytesField(b"Another value"),
        SimplePackable(UInt8(3), [UInt16(4), UInt16(5)]),
        (UInt16(5), UInt16(6)),
        {UInt16(7): SimplePackable(UInt8(8), [UInt16(9)])},
        UInt32(-1),
    )
    payload = instance.pack()
    stream = BytesIO(payload)
    unpacked = MixedPackable.unpack(stream)
    assert instance == unpacked
    assert not stream.read()
