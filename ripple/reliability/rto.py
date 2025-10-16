"""
| Acronym | Full name                 | Meaning                                                                                                                  |
| ------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| RTT     | Round-Trip Time           | How long it takes for a packet to go from you → peer → back again (measured when an ACK comes back).                     |
| SRTT    | Smoothed Round-Trip Time  | A running *average* of recent RTT samples. Smooths out jitter so we don’t react too wildly to spikes.                    |
| RTTVAR  | Round-Trip Time Variation | An estimate of how much the RTT is *changing* — like a moving standard deviation. High variation means unstable latency. |
| RTO     | Retransmission Timeout    | How long to wait before deciding a packet was lost and retransmitting it.                                                |
"""

from ..utils import clamp


ALPHA = 1 / 8
BETA = 1 / 4
INV_ALPHA = 1 - ALPHA
INV_BETA = 1 - BETA


class RtoEstimator:
    """
    RFC6298-ish SRTT/RTTVAR estimator.
    Use note_sample(rtt) ONLY for non-retransmitted packets (Karn's rule).
    """

    def __init__(
        self,
        rto_init: float = 0.2,
        clock_granularity: float = 1 / 60,
    ):
        self.rto = rto_init
        self.tick = clock_granularity
        self.srtt = 0.0
        self.rttvar = 0.0
        self.initialised = False

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
