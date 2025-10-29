from dataclasses import dataclass

from ..utils import UInt16
from ..network.protocol import Ack

MAX16 = 1 << 16
HALF16 = 1 << 15


def seq_lt(a: UInt16, b: UInt16) -> bool:
    return (a - b) > HALF16
    # return ((a - b) & 0xFFFF) > HALF16


def seq_distance(newer: UInt16, older: UInt16) -> UInt16:
    """Unsigned distance from older -> newer in [0, 65535]."""
    return (newer - older) & 0xFFFF


class AckMask:
    """
    Tracks received reliable seqs relative to a moving base (largest seen).
    - base_seq is monotone non-decreasing (mod 2^16).
    - bitmap captures which of the previous `capacity_bits` packets have also
      been received (out of order). Bit i => have (base_seq - 1 - i).
    """

    def __init__(self, capacity_bits: int = 64):
        if capacity_bits > 1024:
            raise ValueError("Whoa now buster, take it easy")
        if capacity_bits < 0:
            raise ValueError("Capacity bits should be higher than 0")

        self.capacity = capacity_bits
        self.capacity_mask = (1 << self.capacity) - 1
        self.base_seq = UInt16(0)
        # LSB-first window
        self.bitmap = UInt16(0)
        self.initialised = False

    def note_recv(self, seq: int | UInt16) -> None:
        seq = UInt16(seq)
        if not self.initialised:
            self.base_seq = seq
            self.initialised = True
            return
        elif seq == self.base_seq:
            # Duplicate => Ignore
            return
        elif seq_lt(self.base_seq, seq):
            # Newer, move window to new base seq
            distance = seq_distance(seq, self.base_seq)
            self._slide_forward(seq, distance)
            self._mark_received(distance - 1)
        else:
            # Older, mark as received in mask
            distance = seq_distance(self.base_seq, seq)
            self._mark_received(distance - 1)

    def _slide_forward(self, seq: UInt16, distance: UInt16) -> None:
        # slide the bitmap mask => e.g. 0b1101
        # With a distance of 2, the window will slide to 0b110100
        self.bitmap = (self.bitmap << distance) & self.capacity_mask
        self.base_seq = seq

    def _mark_received(self, distance: UInt16) -> None:
        # seq < base; set a bit behind the base if in range
        if 0 <= distance < self.capacity:
            self.bitmap |= 1 << distance

    def to_ack_record(self, max_bytes: int = 8) -> Ack:
        nbits = min(self.capacity, max_bytes * 8)
        mask = self.bitmap & ((1 << nbits) - 1)
        return Ack(
            ack_base=max(UInt16(0), self.base_seq),
            mask=UInt16(mask),
        )
