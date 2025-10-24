import socket
import select
import time
from typing import Optional, Tuple

from ..utils.ringbuffer import RingBuffer
from ..core.metrics import Event, Timer
from ..core.models import UdpEndpointConfig
from ..diagnostics import signals as s


class UdpEndpoint:
    def __init__(self, cfg: UdpEndpointConfig):
        self.cfg = cfg
        self.sock = self._open_socket()
        self.rx_queue = RingBuffer("rx", cfg.rx.capacity, cfg.rx.drop_policy)
        self.tx_queue = RingBuffer("tx", cfg.tx.capacity, cfg.tx.drop_policy)

    @property
    def address(self):
        return self.sock.getsockname()

    def _open_socket(self):
        sock = socket.socket(self.cfg.local_addr.family, socket.SOCK_DGRAM)
        sock.setblocking(False)

        for option in self.cfg.get_local_socket_options():
            sock.setsockopt(*option)

        sock.bind(self.cfg.local_addr.bind_address)
        if self.cfg.remote_addr:
            sock.connect(self.cfg.remote_addr.bind_address)

        return sock

    def send(self, payload: bytes, addr: Optional[Tuple[str, int]] = None):
        return self.tx_queue.push((payload, addr))

    def try_recv(self):
        return self.rx_queue.pop()

    def tick(self, rx_budget_ms=0.5, tx_budget_ms=0.5, max_rx=64, max_tx=64):
        timer = Timer()
        self._drain("rx", max_rx, rx_budget_ms, self._rx)
        self._drain("tx", max_tx, tx_budget_ms, self._tx)
        s.TICK_EVENT.send(event=Event.TICK_TIME, delta=timer.delta())

    def _drain(self, name, max_msg, budget, drainer):
        timer = Timer()
        deadline = timer.start + budget / 1000.0

        x = 0
        while x < max_msg and time.perf_counter() < deadline and drainer():
            s.DRAIN_EVENT.send(
                buffer_name=name, event=Event.DRAIN, time=timer.lap()
            )
            x += 1

        s.DRAIN_EVENT.send(
            buffer_name=name, event=Event.DRAIN_TIME, time=timer.delta()
        )

    def _rx(self):
        r, _, _ = select.select([self.sock], [], [], 0)
        if not r:
            return False
        try:
            data, addr = self.sock.recvfrom(self.cfg.rx.max_size)
        except BlockingIOError:
            return False
        self.rx_queue.push((data, addr))
        return True

    def _tx(self):
        if (item := self.tx_queue.pop()) is None:
            return False
        payload, addr = item
        try:
            if addr:
                self.sock.sendto(payload, addr)
            else:
                self.sock.send(payload)
        except BlockingIOError:
            self.tx_queue.emit(Event.DEQUEUE_DROPPED)
            return False
        return True

    def close(self):
        self.sock.close()

    def __repr__(self):
        return (
            f"<UdpEndpoint local={self.cfg.local_addr}> "
            f"remote={self.cfg.remote_addr}"
        )
