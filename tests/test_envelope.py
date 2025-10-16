import pytest

from ripple.network.payload import (
    Ack,
    Ping,
    Delta,
    EnvelopeBuilder,
    EnvelopeOpener,
    RecType,
)
from ripple.utils.int_types import UInt16


def test_it_can_roundtrip_single_ping():
    builder = EnvelopeBuilder(budget=1024)
    opener = EnvelopeOpener()

    original = Ping(ms=42)
    builder.add(original)
    result = builder.finish()

    assert len(result.envelopes) == 1
    records = opener.unpack(result.envelopes[0])
    assert len(records) == 1
    assert isinstance(records[0], Ping)
    assert records[0].ms == 42


def test_it_can_roundtrip_single_ack():
    builder = EnvelopeBuilder(budget=1024)
    opener = EnvelopeOpener()

    original = Ack(ack_base=UInt16(100), mask=UInt16(0xABCD))
    builder.add(original)
    result = builder.finish()

    assert len(result.envelopes) == 1
    records = opener.unpack(result.envelopes[0])
    assert len(records) == 1
    assert isinstance(records[0], Ack)
    assert records[0].ack_base == 100
    assert records[0].mask == 0xABCD


def test_it_can_roundtrip_single_delta():
    builder = EnvelopeBuilder(budget=1024)
    opener = EnvelopeOpener()

    original = Delta(blob=b"test data payload")
    builder.add(original)
    result = builder.finish()

    assert len(result.envelopes) == 1
    records = opener.unpack(result.envelopes[0])
    assert len(records) == 1
    assert isinstance(records[0], Delta)
    assert records[0].blob == b"test data payload"


def test_it_can_roundtrip_multiple_records_in_same_envelope():
    builder = EnvelopeBuilder(budget=1024)
    opener = EnvelopeOpener()

    ping1 = Ping(ms=100)
    ping2 = Ping(ms=200)
    ack = Ack(ack_base=UInt16(50), mask=UInt16(0xFF))
    delta = Delta(blob=b"some data")

    builder.add(ping1)
    builder.add(ping2)
    builder.add(ack)
    builder.add(delta)
    result = builder.finish()

    assert len(result.envelopes) == 1
    records = opener.unpack(result.envelopes[0])
    assert len(records) == 4

    assert isinstance(records[0], Ping)
    assert records[0].ms == 100

    assert isinstance(records[1], Ping)
    assert records[1].ms == 200

    assert isinstance(records[2], Ack)
    assert records[2].ack_base == 50
    assert records[2].mask == 0xFF

    assert isinstance(records[3], Delta)
    assert records[3].blob == b"some data"


def test_it_assigns_reliable_ids_during_roundtrip():
    builder = EnvelopeBuilder(budget=1024)
    opener = EnvelopeOpener()

    delta1 = Delta(blob=b"first")
    delta2 = Delta(blob=b"second")
    delta3 = Delta(blob=b"third")

    builder.add(delta1)
    builder.add(delta2)
    builder.add(delta3)
    result = builder.finish()

    assert len(result.envelopes) == 1
    assert result.index[0].rid == 0
    assert result.index[1].rid == 1
    assert result.index[2].rid == 2

    records = opener.unpack(result.envelopes[0])
    assert len(records) == 3
    assert records[0].rid == 0
    assert records[1].rid == 1
    assert records[2].rid == 2


def test_it_preserves_preset_reliable_id():
    builder = EnvelopeBuilder(budget=1024)
    opener = EnvelopeOpener()

    delta = Delta(blob=b"data", rid=UInt16(99))
    builder.add(delta)
    result = builder.finish()

    assert result.index[0].rid == 99

    records = opener.unpack(result.envelopes[0])
    assert len(records) == 1
    assert records[0].rid == 99


def test_it_preserves_unreliable_records():
    builder = EnvelopeBuilder(budget=1024)
    opener = EnvelopeOpener()

    ping = Ping(ms=123)
    builder.add(ping)
    result = builder.finish()

    assert result.index[0].rid is None

    records = opener.unpack(result.envelopes[0])
    assert len(records) == 1
    assert records[0].rid is None


def test_it_can_roundtrip_across_multiple_envelopes():
    # Ping records are 8 bytes large, forcing a new envelope
    # for each
    builder = EnvelopeBuilder(budget=8)
    opener = EnvelopeOpener()

    ping1 = Ping(ms=1)
    ping2 = Ping(ms=2)
    ping3 = Ping(ms=3)

    builder.add(ping1)
    builder.add(ping2)
    builder.add(ping3)
    result = builder.finish()

    assert len(result.envelopes) >= 2

    all_records = []
    for envelope in result.envelopes:
        records = opener.unpack(envelope)
        all_records.extend(records)

    assert len(all_records) == 3
    assert all_records[0].ms == 1
    assert all_records[1].ms == 2
    assert all_records[2].ms == 3


def test_it_handles_mixed_reliable_and_unreliable_records():
    builder = EnvelopeBuilder(budget=1024)
    opener = EnvelopeOpener()

    ping = Ping(ms=100)
    delta = Delta(blob=b"reliable data")
    ack = Ack(ack_base=UInt16(10), mask=UInt16(0))

    builder.add(ping)
    builder.add(delta)
    builder.add(ack)
    result = builder.finish()

    assert result.index[0].rid is None
    assert result.index[1].rid == 0
    assert result.index[2].rid is None

    records = opener.unpack(result.envelopes[0])
    assert len(records) == 3

    assert isinstance(records[0], Ping)
    assert records[0].rid is None

    assert isinstance(records[1], Delta)
    assert records[1].rid == 0

    assert isinstance(records[2], Ack)
    assert records[2].rid is None


def test_it_can_roundtrip_empty_delta():
    builder = EnvelopeBuilder(budget=1024)
    opener = EnvelopeOpener()

    delta = Delta(blob=b"")
    builder.add(delta)
    result = builder.finish()

    records = opener.unpack(result.envelopes[0])
    assert len(records) == 1
    assert isinstance(records[0], Delta)
    assert records[0].blob == b""


def test_it_can_roundtrip_large_delta():
    builder = EnvelopeBuilder(budget=2048)
    opener = EnvelopeOpener()

    large_data = b"x" * 1024
    delta = Delta(blob=large_data)
    builder.add(delta)
    result = builder.finish()

    records = opener.unpack(result.envelopes[0])
    assert len(records) == 1
    assert isinstance(records[0], Delta)
    assert records[0].blob == large_data


def test_it_handles_wraparound_values():
    builder = EnvelopeBuilder(budget=1024)
    opener = EnvelopeOpener()

    ack = Ack(ack_base=UInt16(0xFFFF), mask=UInt16(0xFFFF))
    ping = Ping(ms=0xFFFFFFFF)

    builder.add(ack)
    builder.add(ping)
    result = builder.finish()

    records = opener.unpack(result.envelopes[0])
    assert len(records) == 2
    assert isinstance(records[0], Ack)
    assert records[0].ack_base == 0xFFFF
    assert records[0].mask == 0xFFFF
    assert isinstance(records[1], Ping)
    assert records[1].ms == 0xFFFFFFFF


def test_it_can_roundtrip_all_record_types():
    builder = EnvelopeBuilder(budget=2048)
    opener = EnvelopeOpener()

    records_to_pack = [
        Ack(ack_base=UInt16(42), mask=UInt16(0x1234)),
        Ping(ms=9999),
        Delta(blob=b"test blob data"),
    ]

    for rec in records_to_pack:
        builder.add(rec)

    result = builder.finish()
    unpacked_records = opener.unpack(result.envelopes[0])

    assert len(unpacked_records) == len(records_to_pack)

    assert isinstance(unpacked_records[0], Ack)
    assert unpacked_records[0].ack_base == 42
    assert unpacked_records[0].mask == 0x1234

    assert isinstance(unpacked_records[1], Ping)
    assert unpacked_records[1].ms == 9999

    assert isinstance(unpacked_records[2], Delta)
    assert unpacked_records[2].blob == b"test blob data"


def test_it_preserves_record_order():
    builder = EnvelopeBuilder(budget=1024)
    opener = EnvelopeOpener()

    for i in range(10):
        builder.add(Ping(ms=i))

    result = builder.finish()

    all_records = []
    for envelope in result.envelopes:
        all_records.extend(opener.unpack(envelope))

    assert len(all_records) == 10
    for i, record in enumerate(all_records):
        assert record.ms == i


def test_it_creates_separate_envelopes_after_flush():
    builder = EnvelopeBuilder(budget=1024)
    opener = EnvelopeOpener()

    builder.add(Ping(ms=1))
    builder.flush()
    builder.add(Ping(ms=2))
    builder.flush()
    builder.add(Ping(ms=3))

    result = builder.finish()
    assert len(result.envelopes) == 3

    records_0 = opener.unpack(result.envelopes[0])
    records_1 = opener.unpack(result.envelopes[1])
    records_2 = opener.unpack(result.envelopes[2])

    assert len(records_0) == 1
    assert isinstance(records_0[0], Ping)
    assert records_0[0].ms == 1

    assert len(records_1) == 1
    assert isinstance(records_1[0], Ping)
    assert records_1[0].ms == 2

    assert len(records_2) == 1
    assert isinstance(records_2[0], Ping)
    assert records_2[0].ms == 3
