import pytest

from ripple.network.protocol import (
    Ack,
    Ping,
    Delta,
    EnvelopeBuilder,
    EnvelopeOpener,
)
from ripple.utils import UInt16, UInt32, FreeFormField


def test_it_can_roundtrip_single_ping():
    builder = EnvelopeBuilder(budget=1024)
    opener = EnvelopeOpener()

    original = Ping(id=UInt16(1), ms=UInt32(42))
    builder.add(original)
    result = builder.finish()

    assert len(result.envelopes) == 1
    records = opener.unpack(result.envelopes[0].payload)
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
    records = opener.unpack(result.envelopes[0].payload)
    assert len(records) == 1
    assert isinstance(records[0], Ack)
    assert records[0].ack_base == 100
    assert records[0].mask == 0xABCD


def test_it_can_roundtrip_single_delta():
    builder = EnvelopeBuilder(budget=1024)
    opener = EnvelopeOpener()

    original = Delta(blob=FreeFormField(b"test data payload"))
    builder.add(original)
    result = builder.finish()

    assert len(result.envelopes) == 1
    records = opener.unpack(result.envelopes[0].payload)
    assert len(records) == 1
    assert isinstance(records[0], Delta)
    assert records[0].blob == b"test data payload"


def test_it_can_roundtrip_multiple_records_in_same_envelope():
    builder = EnvelopeBuilder(budget=1024)
    opener = EnvelopeOpener()

    ping1 = Ping(id=UInt16(1), ms=UInt32(100))
    ping2 = Ping(id=UInt16(1), ms=UInt32(200))
    ack = Ack(ack_base=UInt16(50), mask=UInt16(0xFF))
    delta = Delta(blob=FreeFormField(b"some data"))

    builder.add(ping1)
    builder.add(ping2)
    builder.add(ack)
    builder.add(delta)
    result = builder.finish()

    assert len(result.envelopes) == 1
    records = opener.unpack(result.envelopes[0].payload)
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


def test_it_can_roundtrip_across_multiple_envelopes():
    # Ping records are 12 bytes large, forcing a new envelope
    # for each
    builder = EnvelopeBuilder(budget=12)
    opener = EnvelopeOpener()

    ping1 = Ping(id=UInt16(1), ms=UInt32(1))
    ping2 = Ping(id=UInt16(1), ms=UInt32(2))
    ping3 = Ping(id=UInt16(1), ms=UInt32(3))

    builder.add(ping1)
    builder.add(ping2)
    builder.add(ping3)
    result = builder.finish()

    assert len(result.envelopes) >= 2

    all_records = []
    for envelope in result.envelopes:
        records = opener.unpack(envelope.payload)
        all_records.extend(records)

    assert len(all_records) == 3
    assert all_records[0].ms == 1
    assert all_records[1].ms == 2
    assert all_records[2].ms == 3


def test_it_can_roundtrip_empty_delta():
    builder = EnvelopeBuilder(budget=1024)
    opener = EnvelopeOpener()

    delta = Delta(blob=FreeFormField(b""))
    builder.add(delta)
    result = builder.finish()

    records = opener.unpack(result.envelopes[0].payload)
    assert len(records) == 1
    assert isinstance(records[0], Delta)
    assert records[0].blob == b""


def test_it_can_roundtrip_large_delta():
    builder = EnvelopeBuilder(budget=2048)
    opener = EnvelopeOpener()

    large_data = b"x" * 1024
    delta = Delta(blob=FreeFormField(large_data))
    builder.add(delta)
    result = builder.finish()

    records = opener.unpack(result.envelopes[0].payload)
    assert len(records) == 1
    assert isinstance(records[0], Delta)
    assert records[0].blob == large_data


def test_it_handles_wraparound_values():
    builder = EnvelopeBuilder(budget=1024)
    opener = EnvelopeOpener()

    ack = Ack(ack_base=UInt16(0xFFFF), mask=UInt16(0xFFFF))
    ping = Ping(id=UInt16(1), ms=UInt32(0xFFFFFFFF))

    builder.add(ack)
    builder.add(ping)
    result = builder.finish()

    records = opener.unpack(result.envelopes[0].payload)
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
        Ping(id=UInt16(1), ms=UInt32(9999)),
        Delta(
            blob=FreeFormField(b"test blob data"),
        ),
    ]

    for rec in records_to_pack:
        builder.add(rec)

    result = builder.finish()
    unpacked_records = opener.unpack(result.envelopes[0].payload)

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
        builder.add(Ping(id=UInt16(i), ms=UInt32(i)))

    result = builder.finish()

    all_records = []
    for envelope in result.envelopes:
        all_records.extend(opener.unpack(envelope.payload))

    assert len(all_records) == 10
    for i, record in enumerate(all_records):
        assert record.ms == i


def test_it_creates_separate_envelopes_after_flush():
    builder = EnvelopeBuilder(budget=1024)
    opener = EnvelopeOpener()

    builder.add(Ping(id=UInt16(1), ms=UInt32(1)))
    builder.flush()
    builder.add(Ping(id=UInt16(1), ms=UInt32(2)))
    builder.flush()
    builder.add(Ping(id=UInt16(1), ms=UInt32(3)))

    result = builder.finish()
    assert len(result.envelopes) == 3

    records_0 = opener.unpack(result.envelopes[0].payload)
    records_1 = opener.unpack(result.envelopes[1].payload)
    records_2 = opener.unpack(result.envelopes[2].payload)

    assert len(records_0) == 1
    assert isinstance(records_0[0], Ping)
    assert records_0[0].ms == 1

    assert len(records_1) == 1
    assert isinstance(records_1[0], Ping)
    assert records_1[0].ms == 2

    assert len(records_2) == 1
    assert isinstance(records_2[0], Ping)
    assert records_2[0].ms == 3
