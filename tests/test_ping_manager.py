import pytest
from ripple.network.health.ping_manager import PingManager
from ripple.network.protocol.records import Ping, Pong
from ripple.utils import UInt32, UInt16


@pytest.fixture
def pm():
    return PingManager(interval_ms=100, max_outstanding=4)


def test_it_can_generate_sequential_ids(pm):
    id1 = pm._get_next_id()
    id2 = pm._get_next_id()
    assert int(id2) == (int(id1) + 1) & 0xFFFF


def test_it_wraps_id(pm):
    pm.ping_id = UInt16(0xFFFF)
    next_id = pm._get_next_id()
    assert int(next_id) == 0


def test_it_knows_when_due_and_respects_flooding(pm):
    assert pm.is_due(now=0) is True

    for i in range(pm.max_outstanding):
        pm.outstanding[UInt16(i)] = Ping(UInt16(i), UInt32(0))

    assert pm.is_due(now=0) is False


def test_it_can_make_ping_and_register_outstanding(pm):
    ping = pm.make_ping(now=10)
    assert isinstance(ping, Ping)
    assert ping in pm.outstanding.values()
    assert int(pm.next_due_ms) == 100


def test_it_converts_ping_to_pong(pm):
    ping = Ping(UInt16(5), UInt32(1234))
    pong = pm.on_recv_ping(ping)
    assert isinstance(pong, Pong)
    assert int(pong.id) == int(ping.id)
    assert int(pong.ms) == int(ping.ms)


def test_it_processes_pong_and_updates_estimators(pm):
    ping = pm.make_ping(now=1000)
    pid = ping.id
    now_ms = 1100
    # ensure outstanding contains pid
    assert pid in pm.outstanding
    # process pong
    pm.on_recv_pong(Pong(id=pid, ms=ping.ms), now=now_ms)
    # outstanding removed
    assert pid not in pm.outstanding
    # rtt estimator should have been updated
    assert pm.rtt.initialised is True
    # jitter trackers should have at least 1 sample recorded
    assert pm.jitter_rtp.last_rtt_ms is not None
    assert pm.jitter_std.n >= 1


def test_it_prunes_stale_pings(pm):
    old = Ping(UInt16(1), UInt32(0))
    new = Ping(UInt16(2), UInt32(10000))
    pm.outstanding[old.id] = old
    pm.outstanding[new.id] = new

    pruned = list(pm.prune(now=200))
    assert old in pruned
    assert old.id not in pm.outstanding
    assert new.id in pm.outstanding
