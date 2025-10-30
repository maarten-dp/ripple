import zlib
from io import BytesIO

from ripple.network.protocol.fragmenter import (
    Fragmenter,
    FragmentHeader,
    Defragmenter,
)
from ripple.utils import UInt16


def test_it_can_fragment_a_payload():
    mtu = FragmentHeader.size() + 10
    fragmenter = Fragmenter(mtu=mtu)
    fragmenter._msg_id = UInt16(5)

    payload = b"a" * 40
    crc32 = zlib.crc32(payload)
    fragmenter.fragment(payload)
    fragments = fragmenter.finish()

    reconstructed_payload = b""
    for idx, fragment in enumerate(fragments):
        header = FragmentHeader.unpack(BytesIO(fragment.payload))
        assert header.msg_id == 5
        assert header.index == idx
        assert header.count == 4
        assert header.total_len == 40
        assert header.msg_crc32 == crc32
        reconstructed_payload += fragment.payload[FragmentHeader.size() :]
    assert len(reconstructed_payload) == 40
    assert zlib.crc32(reconstructed_payload) == crc32
    assert payload == reconstructed_payload


def test_it_can_register_a_defragment_payload():
    mtu = FragmentHeader.size() + 10
    fragmenter = Fragmenter(mtu=mtu)
    fragmenter._msg_id = UInt16(5)
    defragmenter = Defragmenter()

    payload = b"a" * 40
    crc32 = zlib.crc32(payload)
    fragmenter.fragment(payload)
    fragments = fragmenter.finish()

    assert not defragmenter._buckets
    defragmenter.register_fragment(BytesIO(fragments[0].payload))
    assert len(defragmenter._buckets) == 1
    bucket = defragmenter._buckets[UInt16(5)]
    # 1 fragment and 3 None slots
    assert len(bucket.fragments) == 4
    assert bucket.crc32 == crc32
    assert bucket.received == 1
    assert not bucket.can_reconstruct


def test_it_can_defragment_a_payload():
    mtu = FragmentHeader.size() + 10
    fragmenter = Fragmenter(mtu=mtu)
    fragmenter._msg_id = UInt16(5)
    defragmenter = Defragmenter()

    payload = b"a" * 40
    fragmenter.fragment(payload)
    for fragment in fragmenter.finish():
        defragmenter.register_fragment(BytesIO(fragment.payload))
    defragmented_payload = defragmenter.finish()[0]
    assert payload == defragmented_payload
