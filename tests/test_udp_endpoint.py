import pytest

from ripple import (
    Address,
    DropPolicy,
    UdpEndpoint,
    DatagramConfig,
    UdpEndpointConfig,
)
from ripple.core.metrics import Event, Timer
from ripple.diagnostics import signals as s


@pytest.fixture
def get_udp_endpoint():
    endpoints = []

    def _get_udp_endpoint(local, remote, **kwargs):
        local_address = Address("127.0.0.1", local)
        remote_address = Address("127.0.0.1", remote)
        config = UdpEndpointConfig(
            local_addr=local_address,
            remote_addr=remote_address,
            **kwargs,
        )
        endpoint = UdpEndpoint(config)
        endpoints.append(endpoint)
        return endpoint

    yield _get_udp_endpoint

    for endpoint in endpoints:
        endpoint.close()


def test_basic_send_receiver(get_udp_endpoint):
    sender = get_udp_endpoint(6321, 6322)
    receiver = get_udp_endpoint(6322, 6321)

    payload = b"hello world!"

    sender.send(payload)

    timer = Timer()
    while (message := receiver.try_recv()) is None:
        if timer.delta() > 1:
            assert False, "Did not receive in a timely manner"
        sender.tick()
        receiver.tick()

    expected_message = (payload, sender.address)
    assert message == expected_message


def test_tx_queue_drop_newest(get_udp_endpoint):
    buffer_config = DatagramConfig(capacity=4)
    sender = get_udp_endpoint(6321, 6322, tx=buffer_config)

    dropped = 0

    def capture(_, buffer_name, event):
        nonlocal dropped
        if event == Event.ENQUEUE_DROP_NEWEST:
            dropped += 1

    s.RING_EVENT.connect(capture, sender=sender.tx_queue)

    for i in range(6):
        sender.send(f"{i}".encode(), addr=sender.address)

    assert len(sender.tx_queue) == buffer_config.capacity
    assert len(sender.tx_queue._buf) == buffer_config.capacity

    assert dropped == 2
    items = [int(m.decode()) for (m, _) in sender.tx_queue._buf]
    assert items == [0, 1, 2, 3]


def test_rx_queue_drop_oldest(get_udp_endpoint):
    buffer_config = DatagramConfig(capacity=4, drop_policy=DropPolicy.OLDEST)
    sender = get_udp_endpoint(6321, 6322)
    receiver = get_udp_endpoint(6322, 6321, rx=buffer_config)

    dropped = 0

    def capture(_, buffer_name, event):
        nonlocal dropped
        if event == Event.ENQUEUE_DROP_OLDEST:
            dropped += 1

    s.RING_EVENT.connect(capture, sender=receiver.rx_queue)

    for i in range(6):
        sender.send(f"{i}".encode(), addr=receiver.address)

    timer = Timer()
    while receiver.rx_queue.empty:
        if timer.delta() > 1:
            assert False, "Did not receive in a timely manner"
        sender.tick()
        receiver.tick()

    assert len(receiver.rx_queue) == buffer_config.capacity
    assert len(receiver.rx_queue._buf) == buffer_config.capacity

    assert dropped == 2
    items = [int(m.decode()) for (m, _) in receiver.rx_queue._buf]
    assert items == [4, 5, 2, 3]
