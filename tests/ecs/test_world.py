import pytest
from dataclasses import dataclass

from ripple.ecs.world import World
from ripple.ecs.snapshot import Snapshot
from ripple.ecs.observability import Observable
from ripple.utils import UInt16


@pytest.fixture
def world():
    return World(entities={})


def test_it_can_create_and_destroy_entities(world: World):
    entity = world.create_entity()
    assert entity.entity_id in world.entities
    world.destroy_entity(entity)
    assert entity.entity_id not in world.entities


def test_it_can_snapshot_world_and_produce_deltas(world: World):
    @dataclass
    class Pos(Observable):
        x: UInt16

    entity = world.create_entity(Pos(UInt16(1)))

    snap1 = Snapshot.from_world(world)

    # modify component to create dirty
    comp = entity.get_component(Pos)
    comp.x = UInt16(2)

    snap2 = Snapshot.from_world(world)

    delta = snap2.get_delta_from(snap1)
    assert delta is not None
    # expect spawned maybe empty, updates should include our entity id
    assert entity.entity_id in delta.updates
    ent_delta = delta.updates[entity.entity_id]
    # component updates should contain the component id
    assert len(ent_delta.updates) >= 1


def test_component_apply_validates_and_applies(world: World):
    @dataclass
    class P(Observable):
        x: UInt16

    e = world.create_entity()
    p = P(UInt16(5))
    e.add_component(p)

    comp = e.components[e.entity_id]
    snap = comp.packer.pack(p)
    # create a fake ComponentSnapshot with wrong id
    from ripple.ecs.snapshot import ComponentSnapshot

    bad = ComponentSnapshot(id=UInt16(9999), version=UInt16(1), data=snap)
    with pytest.raises(ValueError):
        comp.apply(bad)

    # create a good delta: use from_component to produce snapshot
    good = ComponentSnapshot.from_component(comp)
    # mutate instance so apply does something
    comp.instance.x = UInt16(6)
    # now apply should raise if version mismatch (since from_component used current comp.version)
    # create a future version (jump ahead)
    future = ComponentSnapshot(
        id=comp.component_id, version=comp.version_id + 2, data=snap
    )
    with pytest.raises(ValueError):
        comp.apply(future)
