from __future__ import annotations
from typing import List, Dict, TYPE_CHECKING
from dataclasses import dataclass, field, asdict

from .entity import Entity, Component
from .utils import IdGenerator
from ..utils import UInt16, BytesField
from ..utils.packable import Packable

if TYPE_CHECKING:
    from .world import World


@dataclass(frozen=True)
class ComponentSnapshot(Packable):
    id: UInt16
    version: UInt16
    data: BytesField

    @classmethod
    def from_component(cls, component: Component):
        if component.instance._dirty:
            component.version_id += 1
            component.instance._dirty.clear()
        return cls(
            id=component.component_id,
            version=component.version_id,
            data=BytesField(component.pack()),
        )


@dataclass(frozen=True)
class EntitySnapshot(Packable):
    id: UInt16
    version: UInt16
    components: Dict[UInt16, ComponentSnapshot] = field(default_factory=dict)

    @classmethod
    def from_entity(cls, entity: Entity):
        component_snapshots = {}
        dirty = []
        for comp_id, component in entity.components.items():
            cversion = component.version_id
            delta = ComponentSnapshot.from_component(component)
            dirty.append(cversion != component.version_id)
            component_snapshots[comp_id] = delta

        if any(dirty):
            entity.version_id += 1

        return cls(
            id=entity.entity_id,
            version=entity.version_id,
            components=component_snapshots,
        )

    def get_delta_from(
        self,
        snapshot: EntitySnapshot,
    ) -> DeltaEntitySnapshot | None:
        """Get delta from snapshot to self"""
        if self.version == snapshot.version:
            return
        from_cids = set(snapshot.components)
        to_cids = set(self.components)

        despawned = list(from_cids.difference(to_cids))
        spawned = [self.components[e] for e in to_cids.difference(from_cids)]
        candidates = to_cids.intersection(from_cids)
        updates = {}

        for cid in candidates:
            component = self.components[cid]
            if snapshot.components[cid].version != component.version:
                updates[cid] = component

        return DeltaEntitySnapshot(
            base_snapshot=snapshot.version,
            target_snapshot=self.version,
            spawns=spawned,
            despawns=despawned,
            updates=updates,
        )

    def apply_delta(self, delta: DeltaEntitySnapshot) -> EntitySnapshot:
        components = {}
        for component in delta.spawns:
            components[component.id] = component
        for eid, component in self.components.items():
            if eid in delta.despawns:
                continue
            elif eid in delta.updates:
                components[eid] = delta.updates[eid]
            else:
                components[eid] = component
        return EntitySnapshot(
            id=self.id,
            version=delta.target_snapshot,
            components=components,
        )


@dataclass(frozen=True)
class Snapshot(Packable):
    id: UInt16 = field(default_factory=IdGenerator())
    entities: Dict[UInt16, EntitySnapshot] = field(default_factory=dict)

    @classmethod
    def from_world(self, world: World):
        entities = {}
        for eid, entity in world.entities.items():
            entities[eid] = EntitySnapshot.from_entity(entity)
        return Snapshot(entities=entities)

    def get_delta_from(self, snapshot: Snapshot) -> DeltaSnapshot | None:
        """Get delta from snapshot to self"""
        if self.id == snapshot.id:
            return
        from_eids = set(snapshot.entities)
        to_eids = set(self.entities)

        despawned = list(from_eids.difference(to_eids))
        spawned = [self.entities[e] for e in to_eids.difference(from_eids)]
        candidates = to_eids.intersection(from_eids)
        updates = {}

        for eid in candidates:
            entity = snapshot.entities[eid]
            if delta := self.entities[eid].get_delta_from(entity):
                updates[eid] = delta

        return DeltaSnapshot(
            base_snapshot=snapshot.id,
            target_snapshot=self.id,
            spawns=spawned,
            despawns=despawned,
            updates=updates,
        )

    def apply_delta(self, delta: DeltaSnapshot) -> Snapshot:
        if delta.base_snapshot != self.id:
            raise ValueError("Cannot apply delta")

        entities = {}
        for entity in delta.spawns:
            entities[entity.id] = entity
        for eid, entity in self.entities.items():
            if eid in delta.despawns:
                continue
            elif eid in delta.updates:
                entities[eid] = entity.apply_delta(delta.updates[eid])
            else:
                entities[eid] = entity
        return Snapshot(
            id=delta.target_snapshot,
            entities=entities,
        )


@dataclass(frozen=True)
class DeltaEntitySnapshot(Packable):
    base_snapshot: UInt16
    target_snapshot: UInt16
    spawns: List[ComponentSnapshot]
    despawns: List[UInt16]
    updates: Dict[UInt16, ComponentSnapshot]

    def __bool__(self):
        return bool(self.spawns or self.despawns or self.updates)


@dataclass(frozen=True)
class DeltaSnapshot(Packable):
    base_snapshot: UInt16
    target_snapshot: UInt16
    spawns: List[EntitySnapshot]
    despawns: List[UInt16]
    updates: Dict[UInt16, DeltaEntitySnapshot]

    def __bool__(self):
        return bool(self.spawns or self.despawns or self.updates)
