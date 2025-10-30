from typing import ClassVar
from dataclasses import dataclass

import pytest

from ripple.network.protocol import (
    RecType,
    Record,
)
from ripple.utils import BytesField


@dataclass(slots=True)
class _ReliableRecord(Record):
    TYPE: ClassVar[RecType] = RecType.RESERVED
    RELIABLE_BY_DEFAULT = True

    blob: BytesField = BytesField(b"")


@pytest.fixture
def ReliableRecord():
    return _ReliableRecord
