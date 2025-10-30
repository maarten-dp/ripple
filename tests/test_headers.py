from io import BytesIO

import pytest
from ripple.network.protocol import PacketHeader, PacketFlags
from ripple.utils import UInt16


def test_packet_header_roundtrip():
    flags = PacketFlags.RELIABLE | PacketFlags.CONTROL
    h = PacketHeader(flags=flags, seq=UInt16(42))
    blob = h.pack()
    h2 = PacketHeader.unpack(BytesIO(blob))
    assert h2.flags == h.flags
    assert h2.seq == h.seq


def test_packet_header_bad_magic():
    h = PacketHeader(flags=PacketFlags(0), seq=UInt16(0))
    blob = h.pack()
    bad = b"XX" + blob[2:]
    with pytest.raises(ValueError, match="bad magic"):
        PacketHeader.unpack(BytesIO(bad))


def test_packet_header_reserved_must_be_zero():
    h = PacketHeader(flags=PacketFlags(0), seq=UInt16(0))
    blob = bytearray(h.pack())
    blob[-1] = 1
    with pytest.raises(ValueError, match="reserved field must be zero"):
        PacketHeader.unpack(BytesIO(bytes(blob)))


def test_packet_header_seq_wrap_compare():
    a = PacketHeader(flags=PacketFlags(0), seq=UInt16(65530))
    b = PacketHeader(flags=PacketFlags(0), seq=UInt16(5))
    assert a < b
    assert a.distance(b) == (5 - 65530) & 0xFFFF
    assert b > a


def test_packet_header_buffer_too_small():
    with pytest.raises(ValueError, match="buffer too small"):
        PacketHeader.unpack(BytesIO(b"RP"))


def test_packet_header_unsupported_version():
    h = PacketHeader(flags=PacketFlags(0), seq=UInt16(0))
    blob = bytearray(h.pack())
    blob[2] = 0x99
    with pytest.raises(ValueError, match="unsupported version"):
        PacketHeader.unpack(BytesIO(bytes(blob)))


def test_packet_header_flags_combinations():
    h1 = PacketHeader(flags=PacketFlags.RELIABLE, seq=UInt16(1))
    h2 = PacketHeader(flags=PacketFlags.FRAGMENT, seq=UInt16(2))
    h3 = PacketHeader(
        flags=PacketFlags.RELIABLE | PacketFlags.FRAGMENT, seq=UInt16(3)
    )
    assert h1.flags == PacketFlags.RELIABLE
    assert h2.flags == PacketFlags.FRAGMENT
    assert h3.flags == (PacketFlags.RELIABLE | PacketFlags.FRAGMENT)


def test_packet_header_size():
    assert PacketHeader.size() == 10


def test_packet_header_distance():
    a = PacketHeader(flags=PacketFlags(0), seq=UInt16(10))
    b = PacketHeader(flags=PacketFlags(0), seq=UInt16(20))
    assert a.distance(b) == 10
    assert b.distance(a) == -10 & 0xFFFF
