import pytest
from dataclasses import dataclass, asdict

from ripple.ecs.world import World
from ripple.ecs.snapshot import Snapshot, ComponentSnapshot
from ripple.ecs.observability import Observable
from ripple.utils import UInt16, BytesField


@dataclass
class Pos(Observable):
    x: UInt16


@pytest.fixture(scope="function")
def world():
    return World(entities={})


def test_it_can_create_and_destroy_entities(world: World):
    entity = world.create_entity()
    assert entity.entity_id in world.entities
    world.destroy_entity(entity)
    assert entity.entity_id not in world.entities


def test_it_can_make_a_world_snapshot(world: World):
    world.create_entity(Pos(UInt16(1)))
    snapshot = Snapshot.from_world(world)
    expected_snapshot = {
        "id": UInt16(0),
        "entities": {
            UInt16(0): {
                "version": UInt16(0),
                "id": UInt16(0),
                "components": {
                    UInt16(0): {
                        "id": UInt16(0),
                        "version": UInt16(0),
                        "data": {
                            "payload": b"\x00\x01",
                            "length": UInt16(2),
                        },
                    }
                },
            }
        },
    }
    assert asdict(snapshot) == expected_snapshot


def test_it_can_make_a_snapshot_delta_when_enitity_is_dirty(world: World):
    pos = Pos(UInt16(1))
    entity = world.create_entity(pos)
    snapshot_t1 = Snapshot.from_world(world)

    pos.x = UInt16(2)

    snapshot_t2 = Snapshot.from_world(world)

    delta = snapshot_t2.get_delta_from(snapshot_t1)
    assert delta
    assert entity.entity_id in delta.updates
    entity_delta = delta.updates[entity.entity_id]
    assert len(entity_delta.updates) == 1


def test_it_can_make_an_empty_snapshot_delta_when_enitity_is_not_dirty(
    world: World,
):
    world.create_entity(Pos(UInt16(1)))
    snapshot_t1 = Snapshot.from_world(world)
    snapshot_t2 = Snapshot.from_world(world)

    delta = snapshot_t2.get_delta_from(snapshot_t1)
    assert not delta


def test_it_cannot_apply_snapshots_from_different_component(world: World):
    pos = Pos(UInt16(1))
    entity = world.create_entity(pos)
    pos_component = list(entity.components.values())[0]

    bad = ComponentSnapshot(
        id=UInt16(9999), version=UInt16(1), data=BytesField(b"")
    )
    with pytest.raises(
        ValueError, match="Cannot apply delta from other component"
    ):
        pos_component.apply(bad)


def test_it_cannot_apply_snapshots_from_version_too_far_in_the_future(
    world: World,
):
    pos = Pos(UInt16(1))
    entity = world.create_entity(pos)
    pos_component = list(entity.components.values())[0]

    future = ComponentSnapshot(
        id=pos_component.component_id,
        version=pos_component.version_id + 2,
        data=BytesField(b""),
    )
    with pytest.raises(ValueError, match="Version too far in the future"):
        pos_component.apply(future)


def test_it_yields_the_same_snapshot_after_applying_a_delta(world: World):
    pos = Pos(UInt16(1))
    world.create_entity(pos)
    entity2 = world.create_entity()
    snapshot_t1 = Snapshot.from_world(world)
    world.destroy_entity(entity2)
    pos.x = UInt16(2)
    world.create_entity(Pos(UInt16(1)))
    snapshot_t2 = Snapshot.from_world(world)
    delta = snapshot_t2.get_delta_from(snapshot_t1)
    assert delta
    delta_snapshot = snapshot_t1.apply_delta(delta)

    assert snapshot_t2 == delta_snapshot
