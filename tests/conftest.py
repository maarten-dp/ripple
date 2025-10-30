from typing import ClassVar
from dataclasses import dataclass

import pytest
from unittest import mock

from ripple.network.protocol import (
    RecType,
    Record,
)
from ripple.utils import BytesField
from ripple.network import protocol


# TODO: Find a better way to deal with the fact
# that the delta record has evolved beyond the tests
@dataclass(slots=True)
class Delta(Record):
    TYPE: ClassVar[RecType] = RecType.DELTA
    RELIABLE_BY_DEFAULT = True

    blob: BytesField = BytesField(b"")


protocol.records.Delta = Delta
protocol.Delta = Delta
