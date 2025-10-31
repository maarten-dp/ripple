from __future__ import annotations
from typing import Type, Iterable, Dict, cast, TYPE_CHECKING
from dataclasses import dataclass, field
from io import BytesIO

from .utils import IdGenerator
from .observability import Observable
from .snapshot import EntitySnapshot
from ..utils import UInt16
from ..utils.packable import Packer, Packable, make_packer


if TYPE_CHECKING:
    from .world import World
    from .snapshot import ComponentSnapshot

PACKERS = {}


def get_packer(cls) -> Packer:
    if (packer := PACKERS.get(cls)) is None:
        packer = make_packer(cls)
        PACKERS[cls] = packer
    return packer


@dataclass
class Component:
    instance: Observable
    type: Type
    packer: Packer
    component_id: UInt16 = field(init=False, default_factory=IdGenerator())
    version_id: UInt16 = UInt16(0)

    def pack(self):
        return self.packer.pack(cast(Packable, self.instance))

    @classmethod
    def from_snapshot(cls, world: World, snapshot: ComponentSnapshot):
        comp_type = world.component_type_ids[snapshot.type_id].type
        packer = get_packer(comp_type)
        unpacked = packer.unpack(BytesIO(delta.data.payload))
        return cls(
            instance=comp_type(**unpacked),
            type=comp_type,
            packer=packer,
            component_id=snapshot.id,
            version_id=snapshot.version_id,
        )

    def apply(self, delta: ComponentSnapshot):
        if delta.id != self.component_id:
            raise ValueError("Cannot apply delta from other component")
        if delta.version > self.version_id + 1:
            raise ValueError("Version too far in the future")

        unpacked = self.packer.unpack(BytesIO(delta.data.payload))
        self.instance._values.update(unpacked)
        self.version_id = delta.version
        self.instance._dirty.clear()


@dataclass
class Entity:
    world: World
    entity_id: UInt16 = field(init=False, default_factory=IdGenerator())
    version_id: UInt16 = UInt16(0)
    components: Dict[UInt16, Component] = field(default_factory=dict)

    @classmethod
    def from_snapshot(cls, world: World, snapshot: EntitySnapshot):
        components = {}
        for component in snapshot.components:
            component = Component.from_snapshot(world, snapshot)
            components[component.component_id] = component
        self.world.store.add_component(entity.id, component)

        return cls(
            world=self,
            entity_id=entity.id,
            version_id=entity.version,
            components=components,
        )

    def apply_delta(self, world: world, delta: DeltaEntitySnapshot):
        for cid, component_delta in delta.updates.items():
            self.components[cid].apply_delta(component_delta)
        for cid in delta.despawns:
            component = self.components.pop(cid)
            self.world.store.remove_component(self.entity_id, component)
        for component_snap in delta.spawns:
            component = Component.from_snapshot(component_snap)
            self.components[component.component_id] = component
            self.world.store.add_component(self.entity_id, component)

    def add_component(self, value_component: Observable):
        component = Component(
            instance=value_component,
            type=type(value_component),
            packer=get_packer(value_component.__class__),
        )
        # Keep a local cache for snapshotting
        self.components[component.component_id] = component
        self.world.store.add_component(self.entity_id, component)

    def add_components(self, components: Iterable[Observable]):
        for component in components:
            self.add_component(component)

    def get_component(self, component_type: Type[Observable]) -> Observable:
        return self.world.store.get_component(self.entity_id, component_type)
