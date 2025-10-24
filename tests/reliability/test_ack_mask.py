from ripple.reliability import AckMask
from ripple.network.protocol import Ack
from ripple.utils.int_types import UInt16


def test_ackmask_linear():
    m = AckMask(64)
    for s in [10, 11, 12, 13]:
        m.note_recv(s)
    v = m.to_ack_record()
    assert v.ack_base == 13
    # Mark 10, 11, 12 as received
    assert v.mask == 0b111


def test_ackmask_out_of_order():
    m = AckMask(8)
    m.note_recv(100)
    # behind by 2 → sets bit index 1 (base-1 is 99; base-2 is 98)
    m.note_recv(98)
    v = m.to_ack_record(max_bytes=1)
    # mark 98 as received, 99 as not received
    assert v.ack_base == 100
    assert v.mask == 0b10


def test_it_can_handle_rollover():
    m = AckMask(8)
    m.note_recv(-1)
    m.note_recv(1)
    v = m.to_ack_record(max_bytes=1)
    assert v.ack_base == 1
    assert v.mask == 0b10


def test_it_ignores_duplicates():
    m = AckMask(8)
    m.note_recv(0)
    m.note_recv(0)
    v = m.to_ack_record(max_bytes=1)
    assert v.ack_base == 0
    assert v.mask == 0


def test_it_can_expand_to_ack_seqs():
    v = Ack(ack_base=UInt16(9), mask=UInt16(0b1110101))
    expected_seqs = [9, 8, 6, 4, 3, 2]
    ack_seqs = v.expand_to_seqs()
    assert ack_seqs == expected_seqs
