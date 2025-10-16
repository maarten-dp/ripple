import struct
from typing import Optional, List, TypeAlias, Union
from dataclasses import dataclass
from typing import List, Optional

from .base_record import Record

from .headers import RecordFlags
from ..payload.base_record import Record
from ...utils.int_types import UInt16

# from ...utils.types import RecordType


from typing import TypeAlias

from .records import Ack, Delta, Ping
from .fragments import Fragmenter, Defragmenter

RecordType: TypeAlias = Ack | Delta | Ping


@dataclass(slots=True)
class PackedRecord:
    envelope_idx: int
    type_code: int
    rid: Optional[UInt16]
    size_bytes: int


@dataclass(slots=True)
class PackResult:
    envelopes: List[bytes]
    index: List[PackedRecord]


class EnvelopeBuilder:
    """
    Streaming packer that rolls over to a new envelope when budget is exceeded.
    Produces N envelopes and an index describing what was packed where.
    """

    def __init__(
        self,
        budget: int,
    ):
        self.budget = budget
        self._current_envelope = bytearray()
        self._envelopes: List[bytes] = []
        self._index: List[PackedRecord] = []
        self._current_rid = UInt16(-1)
        self._fragmenter = Fragmenter(budget)

    def _get_next_rid(self):
        self._current_rid = self._current_rid + 1
        return self._current_rid

    def _fragment(self, payload):
        pass

    def seal_envelope(self):
        if not self._current_envelope:
            return
        self._envelopes.append(bytes(self._current_envelope))
        self._current_envelope = bytearray()

    def add(self, record: Record):
        if RecordFlags.RELIABLE in record.flags() and record.rid is None:
            record.rid = self._get_next_rid()

        payload = record.pack()
        payload_size = len(payload)
        rollover_size = payload_size + len(self._current_envelope)
        if rollover_size > self.budget:
            self.seal_envelope()
            if payload_size > self.budget:
                for fragment in self._fragmenter.fragment(payload):
                    self.add(fragment)

        self._current_envelope.extend(payload)

        self._index.append(
            PackedRecord(
                envelope_idx=len(self._envelopes),
                type_code=record.TYPE,
                rid=record.rid,
                size_bytes=payload_size,
            )
        )

    def flush(self):
        self.seal_envelope()

    def finish(self) -> PackResult:
        self.seal_envelope()
        return PackResult(envelopes=self._envelopes, index=self._index)


class EnvelopeOpener:
    def __init__(self):
        self.defragmenter = Defragmenter()

    def unpack(self, payload: bytes) -> List[RecordType]:
        buffer = memoryview(payload)
        buffer_size = len(buffer)
        offset = 0
        records = []

        while offset < buffer_size:
            record, header = Record.unpack(buffer[offset:])
            offset += header.record_size()
            records.append(record)
        return records
