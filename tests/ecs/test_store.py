import pytest
from dataclasses import dataclass
from unittest import mock

from ripple.ecs.store import Store
from ripple.utils import UInt16
from ripple.utils.packable import Packer
from ripple.ecs.observability import Observable
from ripple.ecs.entity import Component


@pytest.fixture
def observables():
    @dataclass
    class Pos(Observable):
        x: UInt16
        y: UInt16 = UInt16(0)

    @dataclass
    class Vel(Observable):
        dx: UInt16
        dy: UInt16 = UInt16(0)

    return Pos, Vel


@pytest.fixture
def make_component():
    def _make_component(instance):
        return Component(
            instance=instance,
            type=type(instance),
            packer=mock.Mock(),
        )

    return _make_component


def test_it_can_add_and_get_components(observables, make_component):
    Pos, _ = observables
    store = Store()
    eid = UInt16(1)

    pos = Pos(UInt16(10), UInt16(20))
    store.add_component(eid, make_component(pos))

    result = store.get_component(eid, Pos)
    assert result is pos


def test_it_can_remove_components(observables, make_component):
    Pos, _ = observables
    store = Store()
    eid = UInt16(1)

    pos = Pos(UInt16(10), UInt16(20))
    comp = make_component(pos)
    store.add_component(eid, comp)
    assert store.get_component(eid, Pos)
    store.remove_component(eid, comp)
    with pytest.raises(KeyError):
        store.get_component(eid, Pos)


def test_it_can_query_multiple_components(observables, make_component):
    Pos, Vel = observables
    store = Store()

    for i in range(3):
        eid = UInt16(i)
        p = Pos(UInt16(i * 10), UInt16(i * 20))
        v = Vel(UInt16(i * 2), UInt16(i * 3))

        store.add_component(eid, make_component(p))
        store.add_component(eid, make_component(v))

    results = list(store.get_components(Pos, Vel))
    assert len(results) == 3
    for i, (eid, (p, v)) in enumerate(results):
        assert isinstance(p, Pos)
        assert p.x == i * 10
        assert p.y == i * 20
        assert isinstance(v, Vel)
        assert v.dx == i * 2
        assert v.dy == i * 3
