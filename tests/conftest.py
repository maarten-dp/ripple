from typing import ClassVar, cast
from dataclasses import dataclass, fields

import pytest

from ripple.network.protocol import RecType, Record
from ripple.utils import BytesField
from ripple.ecs.utils import IdGenerator
from ripple.ecs.entity import Component, Entity
from ripple.ecs.snapshot import Snapshot


@dataclass(slots=True)
class _ReliableRecord(Record):
    TYPE: ClassVar[RecType] = RecType.RESERVED
    RELIABLE_BY_DEFAULT = True

    blob: BytesField = BytesField(b"")


@pytest.fixture
def ReliableRecord():
    return _ReliableRecord


@pytest.fixture(autouse=True, scope="function")
def reset():
    def _reset(cls, *id_fields):
        dc_fields = {f.name: f for f in fields(cls)}
        for id_field in id_fields:
            cast(IdGenerator, dc_fields[id_field].default_factory).reset()

    _reset(Component, "component_id")
    _reset(Entity, "entity_id")
    _reset(Snapshot, "id")
