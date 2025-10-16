from dataclasses import dataclass
from typing import Dict, Iterable, Optional
from .rto import RtoEstimator
from ..utils import clamp, monotonic


@dataclass
class Pending:
    payload: bytes
    sent_at: float
    retries: int


class ResendQueue:
    def __init__(
        self,
        max_retries: int = 8,
        backoff: float = 1.5,
        min_rto: float = 0.1,
        max_rto: float = 2.0,
    ):
        self.pending: Dict[int, Pending] = {}
        self.rto = RtoEstimator()
        self.max_retries = max_retries
        self.backoff = backoff
        self.min_rto = min_rto
        self.max_rto = max_rto

    @monotonic
    def on_send(
        self,
        seq: int,
        payload: bytes,
        now: float,
    ):
        self.pending[seq] = Pending(payload=payload, sent_at=now, retries=0)

    @monotonic
    def on_acked(
        self,
        seqs: Iterable[int],
        now: float,
    ) -> None:
        """Clear acked packets and sample RTT for those never retransmitted."""
        for s in seqs:
            p = self.pending.pop(s, None)
            if p and p.retries == 0:
                self.rto.note_sample(now - p.sent_at)

    def _effective_rto(self, retries: int) -> float:
        r = (self.rto.rto or 0.25) * (self.backoff**retries)
        return clamp(r, self.min_rto, self.max_rto)

    @monotonic
    def due_timeouts(self, now: float):
        for seq, p in self.pending.items():
            eff = self._effective_rto(p.retries)
            if now - p.sent_at >= eff:
                yield seq, p

    @monotonic
    def on_retransmit(self, seq: int, now: float) -> Optional[bytes]:
        p = self.pending.get(seq)
        if not p:
            return None
        if p.retries >= self.max_retries:
            self.pending.pop(seq, None)
            return None
        p.retries += 1
        p.sent_at = now
        return p.payload
