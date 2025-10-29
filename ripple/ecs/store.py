from __future__ import annotations
from typing import Dict, Iterable, Type, TYPE_CHECKING
from dataclasses import dataclass, field
from collections import defaultdict

from ..utils import UInt16

if TYPE_CHECKING:
    from .entity import Component
    from .observability import Observable


@dataclass(slots=True)
class ComponentStore:
    data: Dict[UInt16, Component] = field(default_factory=dict)

    def add(self, eid: UInt16, component: Component) -> None:
        self.data[eid] = component

    def remove(self, eid: UInt16) -> None:
        self.data.pop(eid, None)

    def has(self, eid: UInt16) -> bool:
        return eid in self.data

    def get(self, eid: UInt16) -> Component:
        return self.data[eid]

    def entities(self) -> Iterable[UInt16]:
        return self.data.keys()

    def empty(self):
        return not bool(self.data)


@dataclass
class Store:
    stores: Dict[Type[Observable], ComponentStore] = field(
        default_factory=lambda: defaultdict(ComponentStore)
    )

    def add_component(self, eid: UInt16, component: Component):
        self.stores[component.type].add(eid, component)

    def remove_component(self, eid: UInt16, component: Component) -> None:
        self.stores[component.type].remove(eid)

    def get_component(
        self,
        eid: UInt16,
        component_type: Type[Observable],
    ) -> Observable:
        component = self.stores[component_type].get(eid)
        return component.instance

    def get_components(self, *component_types: Type[Observable]):
        if not component_types:
            return

        # map types -> stores; bail if any type unseen
        stores = [self.stores[t] for t in component_types]
        if any(s.empty() for s in stores):
            return

        # choose smallest driving set to minimize probes
        driving_idx = min(range(len(stores)), key=lambda i: len(stores[i].data))
        driving = stores[driving_idx]
        others = [s for i, s in enumerate(stores) if i != driving_idx]

        store_datas = [s.data for s in stores]
        for eid in driving.entities():
            if all(eid in s.data for s in others):
                yield eid, tuple(d[eid].instance for d in store_datas)
