from __future__ import annotations
from typing import Dict, TYPE_CHECKING
from dataclasses import dataclass

from .entity import Entity
from .store import Store
from ..utils import UInt16

if TYPE_CHECKING:
    from .observability import Observable


@dataclass
class World:
    entities: Dict[UInt16, Entity]
    store: Store = Store()

    def create_entity(self, *components: Observable) -> Entity:
        entity = Entity(world=self)
        self.entities[entity.entity_id] = entity
        entity.add_components(components)
        return entity

    def destroy_entity(self, entity_or_id: Entity | UInt16):
        if isinstance(entity_or_id, Entity):
            entity_or_id = entity_or_id.entity_id
        self.entities.pop(entity_or_id)
