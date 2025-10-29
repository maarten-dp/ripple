from __future__ import annotations
from typing import Dict
from dataclasses import dataclass

from .entity import Entity
from .store import Store
from ..utils import UInt16


@dataclass
class World:
    entities: Dict[UInt16, Entity]
    store: Store = Store()

    def create_entity(self) -> Entity:
        entity = Entity(world=self)
        self.entities[entity.entity_id] = entity
        return entity

    def destroy_entity(self, entity_or_id: Entity | UInt16):
        if isinstance(entity_or_id, Entity):
            entity_or_id = entity_or_id.entity_id
        self.entities.pop(entity_or_id)
