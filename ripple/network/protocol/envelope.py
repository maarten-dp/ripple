import struct
from typing import Optional, List
from dataclasses import dataclass, field

from .base_record import Record, RecordType
from ...type_protocols import RecordFlags, RecordType


class RecordTooLarge(Exception):
    def __init__(self, record, payload):
        super().__init__("Record too large")
        self.record = record
        self.payload = payload


@dataclass(slots=True)
class PackedRecord:
    envelope_idx: int
    type_code: int
    size_bytes: int


@dataclass(slots=True)
class Envelope:
    _payload: bytearray = field(default_factory=bytearray)
    reliable: bool = False

    def __len__(self):
        return len(self._payload)

    @property
    def payload(self) -> bytes:
        return bytes(self._payload)

    def extend(self, payload):
        self._payload.extend(payload)


@dataclass(slots=True)
class PackResult:
    envelopes: List[Envelope]
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
        self._current_envelope = Envelope()
        self._envelopes: List[Envelope] = []
        self._index: List[PackedRecord] = []

    def seal_envelope(self):
        if not self._current_envelope:
            return
        self._envelopes.append(self._current_envelope)
        self._current_envelope = Envelope()

    def add(self, record: RecordType):
        payload = record.pack()
        payload_size = len(payload)
        rollover_size = payload_size + len(self._current_envelope)
        if rollover_size > self.budget:
            if payload_size > self.budget:
                raise RecordTooLarge(record, payload)
            self.seal_envelope()

        self._current_envelope.extend(payload)
        if RecordFlags.RELIABLE in record.flags():
            self._current_envelope.reliable = True

        self._index.append(
            PackedRecord(
                envelope_idx=len(self._envelopes),
                type_code=record.TYPE,
                size_bytes=payload_size,
            )
        )

    def flush(self):
        self.seal_envelope()

    def finish(self) -> PackResult:
        self.seal_envelope()
        envelopes = self._envelopes
        index = self._index
        if self._envelopes:
            self._envelopes = []
            self._index = []
        return PackResult(envelopes=envelopes, index=index)


class EnvelopeOpener:
    def __init__(self):
        pass

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
