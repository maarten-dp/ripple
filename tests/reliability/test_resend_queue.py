import pytest

from ripple.reliability.resend_queue import ResendQueue


def approx(x, tol=1e-9):
    return pytest.approx(x, abs=tol, rel=tol)


def test_it_can_add_pending_packet_on_send():
    queue = ResendQueue()
    queue.on_send(seq=1, payload=b"hello", now=1.0)

    assert 1 in queue.pending
    assert queue.pending[1].payload == b"hello"
    assert queue.pending[1].sent_at == approx(1.0)
    assert queue.pending[1].retries == 0


def test_it_can_add_multiple_pending_packets():
    queue = ResendQueue()
    queue.on_send(seq=1, payload=b"first", now=1.0)
    queue.on_send(seq=2, payload=b"second", now=1.1)
    queue.on_send(seq=3, payload=b"third", now=1.2)

    assert len(queue.pending) == 3
    assert queue.pending[1].payload == b"first"
    assert queue.pending[2].payload == b"second"
    assert queue.pending[3].payload == b"third"


def test_it_can_remove_acked_packet():
    queue = ResendQueue()
    queue.on_send(seq=1, payload=b"hello", now=1.0)
    queue.on_send(seq=2, payload=b"world", now=1.0)

    queue.on_acked(seqs=[1], now=1.5)

    assert 1 not in queue.pending
    assert 2 in queue.pending


def test_it_can_remove_multiple_acked_packets():
    queue = ResendQueue()
    queue.on_send(seq=1, payload=b"one", now=1.0)
    queue.on_send(seq=2, payload=b"two", now=1.0)
    queue.on_send(seq=3, payload=b"three", now=1.0)

    queue.on_acked(seqs=[1, 3], now=1.5)

    assert 1 not in queue.pending
    assert 2 in queue.pending
    assert 3 not in queue.pending


def test_it_samples_rtt_for_non_retransmitted_packets():
    queue = ResendQueue()
    queue.on_send(seq=1, payload=b"hello", now=1.0)

    queue.on_acked(seqs=[1], now=1.12)

    # Check that RTO estimator recorded the sample (0.12 seconds RTT)
    assert queue.rto.initialised is True
    assert queue.rto.srtt == approx(0.12)


def test_it_does_not_sample_rtt_for_retransmitted_packets():
    queue = ResendQueue()
    queue.on_send(seq=1, payload=b"hello", now=1.0)

    # Simulate retransmission
    queue.on_retransmit(seq=1, now=1.5)

    # Now ACK arrives
    queue.on_acked(seqs=[1], now=2.0)

    # RTO should not be initialized because packet was retransmitted
    assert queue.rto.initialised is False


def test_it_handles_ack_for_unknown_sequence():
    queue = ResendQueue()
    queue.on_send(seq=1, payload=b"hello", now=1.0)

    # ACK for non-existent sequence should not crash
    queue.on_acked(seqs=[99], now=1.5)

    assert 1 in queue.pending


def test_it_can_identify_timed_out_packets():
    queue = ResendQueue(min_rto=0.1, max_rto=2.0)
    queue.on_send(seq=1, payload=b"hello", now=1.0)
    queue.on_send(seq=2, payload=b"world", now=1.0)

    # After 0.3 seconds, packets should time out (default RTO ~0.25s)
    timeouts = list(queue.due_timeouts(now=1.3))

    assert len(timeouts) == 2
    seqs = [seq for seq, _ in timeouts]
    assert 1 in seqs
    assert 2 in seqs


def test_it_does_not_report_timeouts_before_rto():
    queue = ResendQueue(min_rto=0.5, max_rto=2.0)
    queue.on_send(seq=1, payload=b"hello", now=1.0)

    # Check before RTO expires
    timeouts = list(queue.due_timeouts(now=1.3))

    assert len(timeouts) == 0


def test_it_can_retransmit_packet():
    queue = ResendQueue()
    queue.on_send(seq=1, payload=b"hello", now=1.0)

    payload = queue.on_retransmit(seq=1, now=1.5)

    assert payload == b"hello"
    assert queue.pending[1].retries == 1
    assert queue.pending[1].sent_at == approx(1.5)


def test_it_increments_retry_count_on_retransmit():
    queue = ResendQueue()
    queue.on_send(seq=1, payload=b"hello", now=1.0)

    queue.on_retransmit(seq=1, now=1.5)
    queue.on_retransmit(seq=1, now=2.0)
    queue.on_retransmit(seq=1, now=2.5)

    assert queue.pending[1].retries == 3


def test_it_removes_packet_after_max_retries():
    queue = ResendQueue(max_retries=3)
    queue.on_send(seq=1, payload=b"hello", now=1.0)

    # Retransmit 3 times successfully
    queue.on_retransmit(seq=1, now=1.5)
    queue.on_retransmit(seq=1, now=2.0)
    queue.on_retransmit(seq=1, now=2.5)

    assert 1 in queue.pending

    # Fourth retransmit should remove packet and return None
    payload = queue.on_retransmit(seq=1, now=3.0)

    assert payload is None
    assert 1 not in queue.pending


def test_it_returns_none_for_unknown_sequence_on_retransmit():
    queue = ResendQueue()
    queue.on_send(seq=1, payload=b"hello", now=1.0)

    payload = queue.on_retransmit(seq=99, now=1.5)

    assert payload is None


def test_it_applies_exponential_backoff_to_rto():
    queue = ResendQueue(backoff=2.0, min_rto=0.1, max_rto=10.0)
    queue.on_send(seq=1, payload=b"hello", now=1.0)

    # Get base RTO (around 0.25s by default)
    base_rto = queue._effective_rto(retries=0)

    # After 1 retry, RTO should double
    rto_after_1 = queue._effective_rto(retries=1)
    assert rto_after_1 == approx(base_rto * 2.0)

    # After 2 retries, RTO should quadruple
    rto_after_2 = queue._effective_rto(retries=2)
    assert rto_after_2 == approx(base_rto * 4.0)


def test_it_respects_min_rto_limit():
    queue = ResendQueue(min_rto=0.5, max_rto=2.0)

    # Even with 0 retries and low base RTO
    effective = queue._effective_rto(retries=0)

    assert effective >= 0.5


def test_it_respects_max_rto_limit():
    queue = ResendQueue(backoff=10.0, min_rto=0.1, max_rto=1.0)

    # With high backoff and many retries, should still clamp to max
    effective = queue._effective_rto(retries=10)

    assert effective <= 1.0


def test_it_calculates_different_timeouts_for_different_retry_counts():
    queue = ResendQueue(backoff=1.5, min_rto=0.1, max_rto=5.0)
    queue.on_send(seq=1, payload=b"one", now=1.0)
    queue.on_send(seq=2, payload=b"two", now=1.0)

    # Simulate seq=1 being retransmitted once
    queue.on_retransmit(seq=1, now=1.5)

    # seq=1 has retries=1, seq=2 has retries=0
    # Their effective RTOs should differ
    rto_seq1 = queue._effective_rto(queue.pending[1].retries)
    rto_seq2 = queue._effective_rto(queue.pending[2].retries)

    assert rto_seq1 > rto_seq2


def test_it_uses_monotonic_time_by_default():
    queue = ResendQueue()

    # When no 'now' is provided, should use time.monotonic()
    queue.on_send(seq=1, payload=b"hello")

    assert 1 in queue.pending
    assert queue.pending[1].sent_at > 0


def test_it_has_configurable_max_retries():
    queue = ResendQueue(max_retries=5)

    assert queue.max_retries == 5


def test_it_has_configurable_backoff():
    queue = ResendQueue(backoff=2.5)

    assert queue.backoff == approx(2.5)


def test_it_has_configurable_rto_limits():
    queue = ResendQueue(min_rto=0.05, max_rto=5.0)

    assert queue.min_rto == approx(0.05)
    assert queue.max_rto == approx(5.0)


def test_it_yields_correct_pending_objects_in_due_timeouts():
    queue = ResendQueue(min_rto=0.1, max_rto=2.0)
    queue.on_send(seq=1, payload=b"hello", now=1.0)

    timeouts = list(queue.due_timeouts(now=1.3))

    seq, pending = timeouts[0]
    assert seq == 1
    assert pending.payload == b"hello"
    assert pending.sent_at == approx(1.0)
    assert pending.retries == 0


def test_it_correctly_tracks_pending_count():
    queue = ResendQueue()

    assert len(queue.pending) == 0

    queue.on_send(seq=1, payload=b"one", now=1.0)
    assert len(queue.pending) == 1

    queue.on_send(seq=2, payload=b"two", now=1.0)
    assert len(queue.pending) == 2

    queue.on_acked(seqs=[1], now=1.5)
    assert len(queue.pending) == 1

    queue.on_acked(seqs=[2], now=1.5)
    assert len(queue.pending) == 0


def test_it_handles_empty_ack_list():
    queue = ResendQueue()
    queue.on_send(seq=1, payload=b"hello", now=1.0)

    queue.on_acked(seqs=[], now=1.5)

    assert 1 in queue.pending


def test_it_handles_duplicate_sequence_number_by_overwriting():
    queue = ResendQueue()
    queue.on_send(seq=1, payload=b"first", now=1.0)
    queue.on_send(seq=1, payload=b"second", now=1.5)

    assert len(queue.pending) == 1
    assert queue.pending[1].payload == b"second"
    assert queue.pending[1].sent_at == approx(1.5)