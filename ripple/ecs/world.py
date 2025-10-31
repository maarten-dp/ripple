from __future__ import annotations
from typing import Dict, TYPE_CHECKING
from dataclasses import dataclass, field

from .entity import Entity
from .store import Store
from .utils import IdGenerator
from ..utils import UInt16

if TYPE_CHECKING:
    from .observability import Observable


@dataclass
class ComponentEntry:
    id: UInt16 = field(init=False, default_factory=IdGenerator())
    type: Type


@dataclass
class World:
    entities: Dict[UInt16, Entity] = field(default_factory=dict)
    store: Store = Store()
    component_types: Dict[Type, ComponentEntry] = field(default_factory=dict)
    component_type_ids: Dict[UInt16, ComponentEntry] = field(
        default_factory=dict
    )

    def create_entity(self, *components: Observable) -> Entity:
        entity = Entity(world=self)
        self.entities[entity.entity_id] = entity
        entity.add_components(components)
        return entity

    def destroy_entity(self, entity_or_id: Entity | UInt16):
        if isinstance(entity_or_id, Entity):
            entity_or_id = entity_or_id.entity_id
        entity = self.entities.pop(entity_or_id)
        self.store.purge_entity(entity)

    def get_components(self, *component_types: Type[Observable]):
        yield from self.store.get_components(*component_types)

    def register_component_type(self, component_type):
        entry = ComponentEntry(component_type)
        self.component_types[component_type] = entry
        self.component_type_ids[entry.id] = entry

    def apply_delta(self, delta):
        for eid, entity_delta in delta.updates.items():
            self.entities[eid].apply_delta(world, entity_delta)
        for eid in delta.despawns:
            self.destroy_entity(eid)
        for entity_snap in delta.spawns:
            entity = Entity.from_snapshot(world, entity_snap)
            self.entities[entity.entity_id] = entity
