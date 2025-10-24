"""
| Acronym | Full name                 | Meaning                                                                                                                  |
| ------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| RTT     | Round-Trip Time           | How long it takes for a packet to go from you → peer → back again (measured when an ACK comes back).                     |
| SRTT    | Smoothed Round-Trip Time  | A running *average* of recent RTT samples. Smooths out jitter so we don’t react too wildly to spikes.                    |
| RTTVAR  | Round-Trip Time Variation | An estimate of how much the RTT is *changing* — like a moving standard deviation. High variation means unstable latency. |
| RTO     | Retransmission Timeout    | How long to wait before deciding a packet was lost and retransmitting it.                                                |
| RTP     | Real-Time Protocol        |
"""

from dataclasses import dataclass

from ..utils import clamp


ALPHA = 1 / 8
BETA = 1 / 4
INV_ALPHA = 1 - ALPHA
INV_BETA = 1 - BETA
# https://datatracker.ietf.org/doc/html/rfc3550#section-6.4.1
JITTER_SMOOTHING = 16


@dataclass
class RtoEstimator:
    """
    RFC6298-ish SRTT/RTTVAR estimator.
    Use note_sample(rtt) ONLY for non-retransmitted packets (Karn's rule).
    """

    rto: float = 0.2
    tick: float = 1 / 60
    srtt: float = 0.0
    rttvar: float = 0.0
    initialised: bool = False

    def note_sample(self, rtt: float) -> None:
        if not self.initialised:
            self.srtt = rtt
            self.rttvar = rtt / 2
            self.initialised = True
        else:
            # section (2.3) of https://datatracker.ietf.org/doc/html/rfc6298
            self.rttvar = INV_BETA * self.rttvar + BETA * abs(self.srtt - rtt)
            self.srtt = INV_ALPHA * self.srtt + ALPHA * rtt
        rto = self.srtt + max(self.tick, 4 * self.rttvar)
        self.rto = clamp(rto, 0.10, 2.0)


@dataclass
class RtpJitter:
    j_ms: float = 0.0
    last_rtt_ms: float | None = None

    def note_sample(self, rtt_ms: float) -> None:
        if self.last_rtt_ms is None:
            self.last_rtt_ms = rtt_ms
            return
        d = abs(rtt_ms - self.last_rtt_ms)
        self.j_ms += (d - self.j_ms) / JITTER_SMOOTHING
        self.last_rtt_ms = rtt_ms


@dataclass
class OnlineStdDev:
    n: int = 0
    mean: float = 0.0
    M2: float = 0.0

    def note_sample(self, rtt: float) -> None:
        self.n += 1
        delta = rtt - self.mean
        self.mean += delta / self.n
        delta2 = rtt - self.mean
        self.M2 += delta * delta2

    @property
    def variance(self) -> float:
        return self.M2 / (self.n - 1) if self.n > 1 else 0.0

    @property
    def stddev(self) -> float:
        v = self.variance
        return v**0.5
