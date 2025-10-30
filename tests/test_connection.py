import pytest

from ripple import Address, UdpEndpointConfig
from ripple.connection import ReliableConnection
from ripple.network.protocol import Delta, Ping
from ripple.core.metrics import Timer
from ripple.utils import UInt16, UInt32, BytesField
from ripple.diagnostics import signals as s


@pytest.fixture
def get_connection():
    connections = []

    def _get_connection(local_port, remote_port, mtu=1200):
        local_addr = Address("127.0.0.1", local_port)
        remote_addr = Address("127.0.0.1", remote_port)
        cfg = UdpEndpointConfig(
            local_addr=local_addr,
            remote_addr=remote_addr,
        )
        conn = ReliableConnection(cfg, mtu=mtu)
        connections.append(conn)
        return conn

    yield _get_connection

    for conn in connections:
        conn.close()


def test_basic_unreliable_send_receive(get_connection):
    sender = get_connection(7001, 7002)
    receiver = get_connection(7002, 7001)

    # Send unreliable ping
    ping = Ping(id=UInt16(1), ms=UInt32(100))
    sender.send_record(ping)

    timer = Timer()
    received = None
    while received is None:
        if timer.delta() > 0.01:
            assert False, "Did not receive in time"

        sender.tick()
        receiver.tick()
        received = receiver.recv_record()

    assert isinstance(received, Ping)
    assert received.ms == 100


def test_basic_reliable_send_receive(get_connection):
    sender = get_connection(7003, 7004)
    receiver = get_connection(7004, 7003)
    sender._rid = UInt16(15)

    # Send reliable delta
    delta = Delta(blob=BytesField(b"test payload"))
    sender.send_record(delta)

    timer = Timer()
    received = None
    while received is None:
        if timer.delta() > 0.01:
            assert False, "Did not receive in time"

        sender.tick()
        receiver.tick()
        received = receiver.recv_record()

    assert isinstance(received, Delta)
    assert received.blob == b"test payload"
    assert receiver.reliability.rx.initialised
    assert receiver.reliability.rx.base_seq == 15


def test_multiple_records_in_single_envelope(get_connection):
    sender = get_connection(7005, 7006)
    receiver = get_connection(7006, 7005)

    # Send multiple records
    sender.send_record(Ping(id=UInt16(1), ms=UInt32(1)))
    sender.send_record(Delta(blob=BytesField(b"first")))
    sender.send_record(Ping(id=UInt16(1), ms=UInt32(2)))
    sender.send_record(Delta(blob=BytesField(b"second")))

    timer = Timer()
    records = []
    while len(records) < 4:
        if timer.delta() > 0.01:
            assert False, f"Only received {len(records)}/4 records"

        sender.tick()
        receiver.tick()

        while (rec := receiver.recv_record()) is not None:
            records.append(rec)

    assert len(records) == 4
    assert isinstance(records[0], Ping)
    assert records[0].ms == 1

    assert isinstance(records[1], Delta)
    assert records[1].blob == b"first"

    assert isinstance(records[2], Ping)
    assert records[2].ms == 2

    assert isinstance(records[3], Delta)
    assert records[3].blob == b"second"


def test_bidirectional_communication(get_connection):
    conn_a = get_connection(7007, 7008)
    conn_b = get_connection(7008, 7007)

    # A sends to B
    conn_a.send_record(Delta(blob=BytesField(b"from A")))

    # B sends to A
    conn_b.send_record(Delta(blob=BytesField(b"from B")))

    timer = Timer()
    a_received = None
    b_received = None

    while a_received is None or b_received is None:
        if timer.delta() > 0.01:
            assert False, "Not all messages received in time"

        conn_a.tick()
        conn_b.tick()

        if a_received is None:
            a_received = conn_a.recv_record()
        if b_received is None:
            b_received = conn_b.recv_record()

    assert a_received.blob == b"from B"
    assert b_received.blob == b"from A"


def test_recv_all_returns_multiple_records(get_connection):
    sender = get_connection(7011, 7012)
    receiver = get_connection(7012, 7011)

    # Send several records
    for i in range(5):
        sender.send_record(Ping(id=UInt16(1), ms=UInt32(i)))

    timer = Timer()
    records = []
    while len(records) < 5:
        if timer.delta() > 0.01:
            assert False, "Did not receive all records"

        sender.tick()
        receiver.tick()

        records.extend(receiver.recv_all())

    assert len(records) == 5
    for i, record in enumerate(records):
        assert record.ms == i


def test_ack_generation_and_processing(get_connection):
    sender = get_connection(7013, 7014)
    receiver = get_connection(7014, 7013)

    # Send a reliable record
    sender.send_record(Delta(blob=BytesField(b"reliable data")))

    timer = Timer()
    received = False

    received_ack = False

    def recv_ack(sender, ack):
        nonlocal received_ack
        received_ack = True

    s.RECV_ACK.connect(recv_ack, sender=sender)

    # Run for a bit to allow ACK generation and processing
    while not received_ack:
        if timer.delta() > 0.01:
            assert False, "Did not receive ack in time"
        sender.tick()
        receiver.tick()

        if receiver.recv_record() is not None:
            received = True

    assert received, "Record was not received"

    # Check that receiver generated an ACK (dirty flag cleared)
    assert not receiver.reliability._pending_ack_dirty

    # Check that sender has no pending reliable records (ACK processed)
    # After ACKs are processed, resend queue should be empty
    assert len(sender.reliability.tx.pending) == 0


def test_connection_properties(get_connection):
    conn = get_connection(7015, 7016)

    # Test address property
    addr = conn.address
    assert addr[0] == "127.0.0.1"
    assert addr[1] == 7015


def test_it_can_deal_with_a_fragmented_package(get_connection):
    sender = get_connection(7013, 7014, mtu=20)
    receiver = get_connection(7014, 7013, mtu=20)

    sender.send_record(Delta(blob=BytesField(b"a" * 40)))
    assert len(sender.fragmenter._fragments) == 5

    timer = Timer()
    while (record := receiver.recv_record()) is None:
        if timer.delta() > 0.01:
            assert False, "Did not receive all records"
        sender.tick()
        receiver.tick()

    assert record.blob == b"a" * 40
