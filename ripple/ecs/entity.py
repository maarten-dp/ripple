from __future__ import annotations
from typing import Type, List, Dict, cast, TYPE_CHECKING
from dataclasses import dataclass, field

from .utils import IdGenerator
from .observability import Observable
from ..utils import UInt16
from ..utils.packable import Packer, Packable, make_packer


if TYPE_CHECKING:
    from .world import World
    from .snapshot import Snapshot, EntitySnapshot, ComponentSnapshot


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

    def apply(self, delta: ComponentSnapshot):
        if delta.id != self.component_id:
            raise ValueError("Cannot apply delta from other component")
        if delta.version > self.version_id + 1:
            raise ValueError("Missing delta version")

        unpacked, _ = self.packer.unpack(memoryview(delta.data))
        self.instance._values.update(unpacked)
        self.version_id = delta.version
        self.instance._dirty.clear()


@dataclass
class Entity:
    world: World
    entity_id: UInt16 = field(init=False, default_factory=IdGenerator())
    version_id: UInt16 = UInt16(0)
    components: Dict[UInt16, Component] = field(default_factory=dict)

    def add_component(self, value_component: Observable):
        component = Component(
            instance=value_component,
            type=type(value_component),
            packer=get_packer(value_component.__class__),
        )
        # Keep a local cache for snapshotting
        self.components[component.component_id] = component
        self.world.store.add_component(self.entity_id, component)

    def add_components(self, components: List[Observable]):
        for component in components:
            self.add_component(component)

    def get_component(self, component_type: Type[Observable]) -> Observable:
        return self.world.store.get_component(self.entity_id, component_type)
