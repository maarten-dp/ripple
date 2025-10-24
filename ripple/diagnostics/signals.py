from blinker import signal

# from typing import Any, Callable
# from blinker import NamedSignal, Namespace, ANY, F


# class SafeNamedSignal(NamedSignal):
#     """
#     wraps handlers in a try/except as to not impede on normal operations
#     during event handling
#     """

#     def safe_connect(
#         self, receiver: F, sender: Any = ANY, weak: bool = True
#     ) -> F:
#         def _safe_handler(fn):


# class SafeNameSpace(Namespace):
#     def signal(self, name: str, doc: str | None = None) -> SafeNamedSignal:
#         if name not in self:
#             self[name] = SafeNamedSignal(name, doc)
#         return self[name]


# default_namespace: SafeNameSpace = SafeNameSpace()
# signal = default_namespace.signal


# Connection
RECORD_QUEUED_FOR_SEND = signal("RECORD_QUEUED_FOR_SEND")
RECORD_TOO_LARGE = signal("RECORD_TOO_LARGE")
RECORD_DROPPED_ON_SEND = signal("RECORD_DROPPED_ON_SEND")
RECORD_DROPPED_ON_RECEIVE = signal("RECORD_DROPPED_ON_RECEIVE")

PACKET_OFFERED_FOR_PARSING = signal("PACKET_OFFERED_FOR_PARSING")
PACKET_DROPPED = signal("PACKET_DROPPED")
PACKET_PACKED = signal("PACKET_PACKED")

FRAGMENT_OFFERED_FOR_PARSING = signal("FRAGMENT_OFFERED_FOR_PARSING")
FRAGMENT_DROPPED = signal("FRAGMENT_DROPPED")

RETRANSMITTING = signal("RETRANSMITTING")

SEND_ACK = signal("SEND_ACK")
RECV_ACK = signal("RECV_ACK")

# ringbuffer
RING_EVENT = signal("RING_EVENT")

# UdpEndpoint
TICK_EVENT = signal("TICK_EVENT")
DRAIN_EVENT = signal("DRAIN_EVENT")

# PingManager
PING_SENT = signal("PING_SENT")
PONG_SENT = signal("PONG_RECEIVED")
PONG_RECEIVED = signal("PONG_RECEIVED")
PING_LOST = signal("PING_LOST")
