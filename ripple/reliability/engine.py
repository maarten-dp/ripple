from dataclasses import dataclass
from typing import Optional
from .ackmask import AckMask
from .resend_queue import ResendQueue
from ..network.payload import Ack
from ..utils import monotonic


class ReliabilityEngine:
    """Unordered reliability with selective ACKs + resend queue.

    - Receiver tracks a monotone base and rolling bitmask (AckMask).
    - Sender stores pending reliable datagrams and retransmits on timeout.
    - ACKs are produced on-demand (for piggyback) or via a small delayed timer
      in your transport loop (not included here).
    """

    def __init__(self, ack_bits: int = 64):
        self.rx = AckMask(capacity_bits=ack_bits)
        self.tx = ResendQueue()
        self._pending_ack_dirty = False

    # ==== Receiver side ====
    def note_incoming_reliable(self, seq: int) -> None:
        self.rx.note_recv(seq)
        self._pending_ack_dirty = True

    def make_ack_record(self, max_bytes: int = 8) -> Optional[Ack]:
        if not self._pending_ack_dirty:
            return None
        self._pending_ack_dirty = False
        return self.rx.to_ack_record(max_bytes=max_bytes)

    # ==== Sender side ====
    @monotonic
    def note_sent(self, seq: int, payload: bytes, now: float) -> None:
        self.tx.on_send(seq, payload, now=now)

    @monotonic
    def note_ack_record(self, rec: Ack, now: float) -> None:
        seqs = rec.expand_to_seqs()
        self.tx.on_acked(seqs, now=now)

    @monotonic
    def due_retransmits(self, now: float):
        yield from self.tx.due_timeouts(now=now)

    @monotonic
    def on_retransmit(self, seq: int, now: float) -> Optional[bytes]:
        return self.tx.on_retransmit(seq, now=now)
