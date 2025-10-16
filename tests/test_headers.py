import pytest
from ripple.network.payload import PacketHeader, PacketFlags


def test_packet_header_roundtrip():
    flags = PacketFlags.RELIABLE | PacketFlags.CONTROL
    h = PacketHeader(flags=flags, seq=42)
    blob = h.pack()
    h2 = PacketHeader.unpack(blob)
    assert h2.flags == h.flags
    assert h2.seq == h.seq


def test_packet_header_bad_magic():
    h = PacketHeader(flags=0, seq=0)
    blob = h.pack()
    bad = b"XX" + blob[2:]
    with pytest.raises(ValueError, match="bad magic"):
        PacketHeader.unpack(bad)


def test_packet_header_reserved_must_be_zero():
    h = PacketHeader(flags=0, seq=0)
    blob = bytearray(h.pack())
    blob[-1] = 1
    with pytest.raises(ValueError, match="reserved field must be zero"):
        PacketHeader.unpack(bytes(blob))


def test_packet_header_seq_wrap_compare():
    a = PacketHeader(flags=0, seq=65530)
    b = PacketHeader(flags=0, seq=5)
    assert a < b
    assert a.distance(b) == (5 - 65530) & 0xFFFF
    assert b > a


def test_packet_header_buffer_too_small():
    with pytest.raises(ValueError, match="buffer too small"):
        PacketHeader.unpack(b"RP")


def test_packet_header_unsupported_version():
    h = PacketHeader(flags=0, seq=0)
    blob = bytearray(h.pack())
    blob[2] = 0x99
    with pytest.raises(ValueError, match="unsupported version"):
        PacketHeader.unpack(bytes(blob))


def test_packet_header_flags_combinations():
    h1 = PacketHeader(flags=PacketFlags.RELIABLE, seq=1)
    h2 = PacketHeader(flags=PacketFlags.FRAGMENT, seq=2)
    h3 = PacketHeader(flags=PacketFlags.RELIABLE | PacketFlags.FRAGMENT, seq=3)
    assert h1.flags == PacketFlags.RELIABLE
    assert h2.flags == PacketFlags.FRAGMENT
    assert h3.flags == (PacketFlags.RELIABLE | PacketFlags.FRAGMENT)


def test_packet_header_size():
    assert PacketHeader.size() == 8


def test_packet_header_distance():
    a = PacketHeader(flags=0, seq=10)
    b = PacketHeader(flags=0, seq=20)
    assert a.distance(b) == 10
    assert b.distance(a) == -10 & 0xFFFF
