from dataclasses import dataclass

from ripple.ecs.observability import Observable
from ripple.utils import UInt16, UInt8


def test_it_can_make_an_observable_object():
    @dataclass
    class MyModel(Observable):
        field1: UInt8
        field2: UInt16 = UInt16(0)

    model = MyModel(UInt8(1))
    assert model._values == {"field1": UInt8(1), "field2": UInt16(0)}
    assert model._dirty == set()


def test_it_can_observe_fields_changing():
    @dataclass
    class MyModel(Observable):
        field1: UInt8
        field2: UInt16 = UInt16(0)

    model = MyModel(UInt8(1))
    model.field1 += 1
    assert model._values == {"field1": UInt8(2), "field2": UInt16(0)}
    assert model.field1 == 2
    assert model.field2 == 0
    assert model._dirty == {"field1"}
