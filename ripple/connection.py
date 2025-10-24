from typing import Optional, List
from collections import deque

from .network.transport import UdpEndpoint
from .network.protocol import (
    EnvelopeBuilder,
    EnvelopeOpener,
    RecordTooLarge,
    Record,
    RecordFlags,
    PacketHeader,
    PacketFlags,
    Fragmenter,
    Defragmenter,
    Ping,
    Pong,
    Ack,
)
from .network.protocol.base_record import RecordType
from .network.health.ping_manager import PingManager
from .reliability.engine import ReliabilityEngine
from .core.models import UdpEndpointConfig
from .utils.int_types import UInt16
from .utils import monotonic
from .diagnostics import signals as s


class ReliableConnection:
    """
    Orchestrates transport, payload packing, and reliability layers.

    Provides high-level interface for sending/receiving records with
    automatic reliability tracking, ACK generation, and retransmission.
    """

    def __init__(
        self,
        endpoint_cfg: UdpEndpointConfig,
        mtu: int = 1200,
        ack_bits: int = 64,
    ):
        self.mtu = mtu
        self.endpoint = UdpEndpoint(endpoint_cfg)
        self.reliability = ReliabilityEngine(ack_bits=ack_bits)
        self.builder = EnvelopeBuilder(budget=mtu)
        self.fragmenter = Fragmenter(mtu=mtu)
        self.defragmenter = Defragmenter()
        self.opener = EnvelopeOpener()
        self.ping_manager = PingManager()
        self._seq = UInt16(0)
        self._rid = UInt16(0)

        # Incoming records ready for consumption
        self._recv_buffer: deque[RecordType] = deque()

    def _get_next_seq(self):
        seq = self._seq
        self._seq = seq + 1
        return seq

    def _get_next_rid(self):
        rid = self._rid
        self._rid = rid + 1
        return rid

    def send_record(self, record: Record) -> None:
        s.RECORD_QUEUED_FOR_SEND.send(self, record=record)
        try:
            self.builder.add(record)
        except RecordTooLarge as e:
            s.RECORD_TOO_LARGE.send(self, record=record)
            reliable = bool(record.flags() & RecordFlags.RELIABLE)
            self.fragmenter.fragment(e.payload, reliable=reliable)
        except Exception as e:
            s.RECORD_DROPPED_ON_SEND.send(self, record=record, exception=e)

    def recv_record(self) -> Optional[RecordType]:
        """Get next received record, if any."""
        if self._recv_buffer:
            return self._recv_buffer.popleft()
        return None

    def recv_all(self) -> List[RecordType]:
        """Get all received records."""
        records = list(self._recv_buffer)
        self._recv_buffer.clear()
        return records

    @monotonic
    def tick(
        self,
        now: float,
        rx_budget_ms: float = 0.5,
        tx_budget_ms: float = 0.5,
        max_rx: int = 64,
        max_tx: int = 64,
    ):
        self.endpoint.tick(rx_budget_ms, tx_budget_ms, max_rx, max_tx)

        self._process_incoming()
        self._send_pending_acks()
        self._send_ping()
        self._process_retransmits(now=now)
        self._process_outgoing(now=now)

    def _process_incoming(self):
        while (msg := self.endpoint.try_recv()) is not None:
            packet, addr = msg
            self._parse_packet(packet)

        for payload in self.defragmenter.finish():
            self._parse_records(payload)

    def _parse_packet(self, packet):
        s.PACKET_OFFERED_FOR_PARSING.send(self, packet=packet)
        buffer = memoryview(packet)
        try:
            header = PacketHeader.unpack(buffer)
        except ValueError as e:
            s.PACKET_DROPPED.send(reason="Invalid header", exception=e)
            return

        header_size = header.size()
        payload = buffer[header_size:]
        if PacketFlags.RELIABLE & header.flags:
            self.reliability.note_incoming_reliable(int(header.rid))

        if PacketFlags.FRAGMENT & header.flags:
            self._parse_fragment(payload)
        else:
            self._parse_records(payload)

    def _parse_fragment(self, payload):
        try:
            self.defragmenter.register_fragment(payload)
        except Exception as e:
            s.FRAGMENT_DROPPED.send(self, exception=e)
            return

    def _parse_records(self, payload):
        try:
            records = self.opener.unpack(payload)
        except Exception as e:
            s.RECORD_DROPPED_ON_RECEIVE.send(self, exception=e)
            return

        for record in records:
            if isinstance(record, Ack):
                s.RECV_ACK.send(self, ack=record)
                self.reliability.note_ack_record(record)
            elif isinstance(record, Ping):
                self.send_record(pong := self.ping_manager.on_recv_ping(record))
                s.PONG_SENT.send(self, pong=pong)
            elif isinstance(record, Pong):
                self.ping_manager.on_recv_pong(record)
            else:
                self._recv_buffer.append(record)

    def _send_pending_acks(self):
        ack = self.reliability.make_ack_record()
        if ack is not None:
            s.SEND_ACK.send(self, ack=ack)
            self.send_record(ack)

    def _send_ping(self):
        if self.ping_manager.is_due():
            self.send_record(ping := self.ping_manager.make_ping())
            s.PING_SENT.send(self, ping=ping)
        for pruned in self.ping_manager.prune():
            s.PING_LOST.send(self, ping=pruned)

    @monotonic
    def _process_retransmits(self, now: float):
        for seq, p in self.reliability.due_retransmits(now=now):
            payload = self.reliability.on_retransmit(seq, now=now)
            s.RETRANSMITTING.send(
                self, seq=seq, retries=p.retries, payload=payload
            )
            if payload is not None:
                # Resend the packet stored in ResendQueue
                self.endpoint.send(payload)

    @monotonic
    def _process_outgoing(self, now: float):
        for envelope in self.builder.finish().envelopes:
            self._pack_and_send(envelope.payload, envelope.reliable)

        for fragment in self.fragmenter.finish():
            self._pack_and_send(fragment.payload, fragment.reliable, True)

    def _pack_and_send(
        self,
        payload: bytes,
        reliable: bool,
        fragment: bool = False,
    ):
        flags = 0
        rid = 0
        if reliable:
            flags = PacketFlags.RELIABLE
            rid = self._get_next_rid()
        if fragment:
            flags |= PacketFlags.FRAGMENT
        header = PacketHeader(flags=flags, seq=self._get_next_seq(), rid=rid)
        payload = header.pack() + payload
        s.PACKET_PACKED.send(self, payload=payload, rid=rid, flags=flags)
        self.endpoint.send(payload)
        if reliable:
            self.reliability.note_sent(rid, payload)

    def close(self):
        self.endpoint.close()

    @property
    def address(self):
        return self.endpoint.address

    def __repr__(self):
        return f"<ReliableConnection mtu={self.mtu} endpoint={self.endpoint}>"
