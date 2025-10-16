from __future__ import annotations
from typing import TypeAlias

from ..network.payload.records import Ack, Delta, Ping

RecordType: TypeAlias = Ack | Delta | Ping
