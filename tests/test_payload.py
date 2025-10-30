from typing import ClassVar
from dataclasses import dataclass
from io import BytesIO

import pytest
from ripple.network.protocol import (
    RecType,
    Delta,
    RecordMeta,
    Ack,
    Ping,
    EnvelopeBuilder,
    RecordHeader,
    RecordTooLarge,
)
from ripple.utils import UInt16, UInt32, BytesField
from ripple.interfaces import RecordFlags


def test_ack_encode_decode():
    ack = Ack(ack_base=UInt16(100), mask=UInt16(0xABCD))
    payload = ack.pack()
    decoded, _ = Ack.unpack(BytesIO(payload))
    assert decoded.ack_base == 100
    assert decoded.mask == 0xABCD


def test_ack_flags():
    ack = Ack(ack_base=UInt16(1), mask=UInt16(0))
    assert ack.flags() == RecordFlags.NONE


def test_ping_encode_decode():
    ping = Ping(id=UInt16(1), ms=UInt32(1234567))
    payload = ping.pack()
    decoded, _ = Ping.unpack(BytesIO(payload))
    assert decoded.ms == 1234567


def test_ping_flags():
    ping = Ping(id=UInt16(1), ms=UInt32(100))
    assert ping.flags() == RecordFlags.NONE


def test_delta_encode_decode():
    data = b"test payload data"
    delta = Delta(blob=BytesField(data))
    payload = delta.pack()
    decoded, _ = Delta.unpack(BytesIO(payload))
    assert decoded.blob == data


def test_delta_reliable_by_default():
    delta = Delta(blob=BytesField(b"test"))
    assert delta.flags() == RecordFlags.RELIABLE


def test_record_meta_registry():
    registry = RecordMeta.get_registry()
    assert RecType.ACK in registry
    assert RecType.PING in registry
    assert RecType.DELTA in registry
    assert registry[RecType.ACK] is Ack
    assert registry[RecType.PING] is Ping
    assert registry[RecType.DELTA] is Delta


def test_envelope_builder_single_record():
    builder = EnvelopeBuilder(budget=1024)
    ping = Ping(id=UInt16(1), ms=UInt32(123))
    builder.add(ping)
    result = builder.finish()
    assert len(result.envelopes) == 1
    assert len(result.index) == 1
    assert result.index[0].type_code == RecType.PING
    assert result.index[0].envelope_idx == 0


def test_envelope_builder_multiple_records():
    builder = EnvelopeBuilder(budget=1024)
    builder.add(Ping(id=UInt16(1), ms=UInt32(1)))
    builder.add(Ping(id=UInt16(1), ms=UInt32(2)))
    builder.add(Ping(id=UInt16(1), ms=UInt32(3)))
    result = builder.finish()
    assert len(result.envelopes) == 1
    assert len(result.index) == 3


def test_envelope_builder_rollover():
    small_budget = RecordHeader.size() + 10
    builder = EnvelopeBuilder(budget=small_budget)
    builder.add(Ping(id=UInt16(1), ms=UInt32(1)))
    builder.add(Ping(id=UInt16(1), ms=UInt32(2)))
    result = builder.finish()
    assert len(result.envelopes) == 2
    assert len(result.index) == 2
    assert result.index[0].envelope_idx == 0
    assert result.index[1].envelope_idx == 1


def test_envelope_builder_record_too_large():
    small_budget = RecordHeader.size() + 5
    builder = EnvelopeBuilder(budget=small_budget)
    large_delta = Delta(blob=BytesField(b"x" * 1000))
    with pytest.raises(RecordTooLarge):
        builder.add(large_delta)


def test_envelope_builder_flush():
    builder = EnvelopeBuilder(budget=1024)
    builder.add(Ping(id=UInt16(1), ms=UInt32(1)))
    builder.flush()
    builder.add(Ping(id=UInt16(1), ms=UInt32(2)))
    result = builder.finish()
    assert len(result.envelopes) == 2
    assert result.index[0].envelope_idx == 0
    assert result.index[1].envelope_idx == 1


def test_envelope_builder_empty_finish():
    builder = EnvelopeBuilder(budget=1024)
    result = builder.finish()
    assert len(result.envelopes) == 0
    assert len(result.index) == 0


def test_envelope_builder_packed_record_info():
    builder = EnvelopeBuilder(budget=1024)
    ping = Ping(id=UInt16(1), ms=UInt32(42))
    builder.add(ping)
    result = builder.finish()
    packed = result.index[0]
    assert packed.envelope_idx == 0
    assert packed.type_code == RecType.PING
    assert packed.size_bytes > 0


def test_envelope_builder_unreliable_ping():
    builder = EnvelopeBuilder(budget=1024)
    ping = Ping(id=UInt16(1), ms=UInt32(100))
    builder.add(ping)
    result = builder.finish()


def test_ack_value_wrapping():
    ack = Ack(ack_base=UInt16(0x10000), mask=UInt16(0x10000))
    payload = ack.pack()
    decoded, _ = Ack.unpack(BytesIO(payload))
    assert decoded.ack_base == 0
    assert decoded.mask == 0


def test_ping_value_wrapping():
    ping = Ping(id=UInt16(1), ms=UInt32(0x100000000))
    payload = ping.pack()
    decoded, _ = Ping.unpack(BytesIO(payload))
    assert decoded.ms == 0


def test_delta_empty_blob():
    delta = Delta(blob=BytesField(b""))
    payload = delta.pack()
    decoded, _ = Delta.unpack(BytesIO(payload))
    assert decoded.blob == b""
