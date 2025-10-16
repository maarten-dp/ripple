import pytest
from ripple.network.payload import (
    RecType,
    RecordMeta,
    Ack,
    Ping,
    Delta,
    EnvelopeBuilder,
    RecordFlags,
    RecordHeader,
)
from ripple.utils.int_types import UInt16


def test_ack_encode_decode():
    ack = Ack(ack_base=UInt16(100), mask=UInt16(0xABCD))
    payload = ack.encode_payload()
    decoded = Ack.decode_payload(memoryview(payload))
    assert decoded.ack_base == 100
    assert decoded.mask == 0xABCD


def test_ack_flags():
    ack = Ack(ack_base=UInt16(1), mask=UInt16(0))
    assert ack.flags() == RecordFlags.NONE


def test_ack_flags_with_rid():
    ack = Ack(ack_base=UInt16(1), mask=UInt16(0), rid=UInt16(42))
    assert ack.flags() == RecordFlags.RELIABLE


def test_ping_encode_decode():
    ping = Ping(ms=1234567)
    payload = ping.encode_payload()
    decoded = Ping.decode_payload(memoryview(payload))
    assert decoded.ms == 1234567


def test_ping_flags():
    ping = Ping(ms=100)
    assert ping.flags() == RecordFlags.NONE


def test_ping_flags_with_rid():
    ping = Ping(ms=100, rid=UInt16(99))
    assert ping.flags() == RecordFlags.RELIABLE


def test_delta_encode_decode():
    data = b"test payload data"
    delta = Delta(blob=data)
    payload = delta.encode_payload()
    decoded = Delta.decode_payload(memoryview(payload))
    assert decoded.blob == data


def test_delta_reliable_by_default():
    delta = Delta(blob=b"test")
    assert delta.flags() == RecordFlags.RELIABLE


def test_delta_flags_with_rid():
    delta = Delta(blob=b"test", rid=UInt16(10))
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
    ping = Ping(ms=123)
    builder.add(ping)
    result = builder.finish()
    assert len(result.envelopes) == 1
    assert len(result.index) == 1
    assert result.index[0].type_code == RecType.PING
    assert result.index[0].envelope_idx == 0


def test_envelope_builder_multiple_records():
    builder = EnvelopeBuilder(budget=1024)
    builder.add(Ping(ms=1))
    builder.add(Ping(ms=2))
    builder.add(Ping(ms=3))
    result = builder.finish()
    assert len(result.envelopes) == 1
    assert len(result.index) == 3


def test_envelope_builder_rollover():
    small_budget = RecordHeader.size() + 10
    builder = EnvelopeBuilder(budget=small_budget)
    builder.add(Ping(ms=1))
    builder.add(Ping(ms=2))
    result = builder.finish()
    assert len(result.envelopes) == 2
    assert len(result.index) == 2
    assert result.index[0].envelope_idx == 0
    assert result.index[1].envelope_idx == 1


def test_envelope_builder_record_too_large():
    small_budget = RecordHeader.size() + 5
    builder = EnvelopeBuilder(budget=small_budget)
    large_delta = Delta(blob=b"x" * 1000)
    with pytest.raises(ValueError, match="Record size too big"):
        builder.add(large_delta)


def test_envelope_builder_assign_rid():
    builder = EnvelopeBuilder(budget=1024)
    builder.add(Delta(blob=b"data1"))
    builder.add(Delta(blob=b"data2"))
    result = builder.finish()
    assert result.index[0].rid == 0
    assert result.index[1].rid == 1


def test_envelope_builder_flush():
    builder = EnvelopeBuilder(budget=1024)
    builder.add(Ping(ms=1))
    builder.flush()
    builder.add(Ping(ms=2))
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
    ping = Ping(ms=42, rid=UInt16(7))
    builder.add(ping)
    result = builder.finish()
    packed = result.index[0]
    assert packed.envelope_idx == 0
    assert packed.type_code == RecType.PING
    assert packed.rid == 7
    assert packed.size_bytes > 0


def test_envelope_builder_unreliable_ping():
    builder = EnvelopeBuilder(budget=1024)
    ping = Ping(ms=100)
    builder.add(ping)
    result = builder.finish()
    assert result.index[0].rid is None


def test_ack_value_wrapping():
    ack = Ack(ack_base=UInt16(0x10000), mask=UInt16(0x10000))
    payload = ack.encode_payload()
    decoded = Ack.decode_payload(memoryview(payload))
    assert decoded.ack_base == 0
    assert decoded.mask == 0


def test_ping_value_wrapping():
    ping = Ping(ms=0x100000000)
    payload = ping.encode_payload()
    decoded = Ping.decode_payload(memoryview(payload))
    assert decoded.ms == 0


def test_delta_empty_blob():
    delta = Delta(blob=b"")
    payload = delta.encode_payload()
    decoded = Delta.decode_payload(memoryview(payload))
    assert decoded.blob == b""
