from time import monotonic_ns
from typing import Optional, Dict

from ..protocol.records import Ping, Pong
from ...diagnostics.rto import RtoEstimator, RtpJitter, OnlineStdDev
from ...utils import monotonic, UInt16, UInt32


HALF_UINT32 = UInt32(-1) / 2


class PingManager:
    def __init__(
        self,
        interval_ms: int = 1000,
        max_outstanding: int = 16,
    ):
        self.interval_ms = interval_ms
        self.ping_id = UInt16(-1)
        self.next_due_ms = UInt32()

        self.outstanding: Dict[UInt16, Ping] = {}
        self.max_outstanding = max_outstanding

        self.rtt = RtoEstimator()
        self.jitter_rtp = RtpJitter()
        self.jitter_std = OnlineStdDev()

    def _get_next_id(self):
        self.ping_id += 1
        return self.ping_id

    @monotonic
    def is_due(self, now: int) -> bool:
        now = UInt32(now)
        # wrap-safe
        is_due = UInt32(now) - self.next_due_ms < HALF_UINT32
        is_flooded = len(self.outstanding) >= self.max_outstanding
        return is_due and not is_flooded

    @monotonic
    def make_ping(self, now: int) -> Ping:
        ping_id = self._get_next_id()
        ping = Ping(ping_id, UInt32(now))
        self.outstanding[ping_id] = ping
        self.next_due_ms += self.interval_ms
        return ping

    def on_recv_ping(self, ping: Ping) -> Pong:
        return ping.to_pong()

    @monotonic
    def on_recv_pong(self, pong: Pong, now: int):
        if (ping := self.outstanding.pop(pong.id, None)) is None:
            return None

        rtt_sample = float(UInt32(now) - UInt32(ping.ms))

        self.rtt.note_sample(rtt_sample)
        self.jitter_rtp.note_sample(rtt_sample)
        self.jitter_std.note_sample(rtt_sample)

    @monotonic
    def prune(self, now: int):
        now = UInt32(now)
        for ping_id, ping in list(self.outstanding.items()):
            stale = ping.ms + self.interval_ms
            if (now - stale) < HALF_UINT32:
                yield self.outstanding.pop(ping_id)
