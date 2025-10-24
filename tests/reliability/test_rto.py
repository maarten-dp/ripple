import pytest

from ripple.diagnostics.rto import RtoEstimator


def approx(x, tol=1e-9):
    return pytest.approx(x, abs=tol, rel=tol)


def test_initial_sample_sets_baseline():
    est = RtoEstimator()
    est.note_sample(0.120)  # 120 ms

    # First sample: srtt = R', rttvar = R'/2
    assert est.srtt == approx(0.120)
    assert est.rttvar == approx(0.060)

    # RTO = srtt + max(0.050, 4 * rttvar) = 0.12 + max(0.05, 0.24) = 0.36
    assert est.rto == approx(0.36)


def test_second_sample_smoothing():
    est = RtoEstimator()
    est.note_sample(0.120)

    # Second sample: 100 ms
    est.note_sample(0.100)

    # RFC 6298: alpha=1/8, beta=1/4
    # rttvar = (1-β)*0.060 + β*|0.120 - 0.100| = 0.045 + 0.005 = 0.050
    # srtt   = (1-α)*0.120 + α*0.100      = 0.105 + 0.0125 = 0.1175
    # RTO    = 0.1175 + max(0.050, 4*0.050=0.2) = 0.3175
    assert est.rttvar == approx(0.050)
    assert est.srtt == approx(0.1175)
    assert est.rto == approx(0.3175)


def test_min_rto_clamp_applies():
    est = RtoEstimator()
    est.note_sample(0.005)  # 5 ms
    # RTO = 0.005 + max(0.050, 0.01) = 0.055 → clamp to 0.10
    assert est.rto == approx(0.10)


def test_max_rto_clamp_applies():
    est = RtoEstimator()
    est.note_sample(1.5)  # 1500 ms
    # srtt=1.5, rttvar=0.75 → raw RTO=1.5 + max(0.05, 3.0)=4.5 → clamp to 2.0
    assert est.rto == approx(2.0)


def test_rto_increases_with_jitter():
    est = RtoEstimator()
    # Start stable around 100 ms
    est.note_sample(0.100)
    baseline_rto = est.rto

    # A bigger, jittery sample (300 ms) should raise RTO
    est.note_sample(0.300)
    assert est.rto > baseline_rto


def test_rto_decreases_when_latency_improves():
    est = RtoEstimator()
    # Start with a big latency sample to push RTO up (will clamp to 2.0)
    est.note_sample(1.2)
    high_rto = est.rto
    assert high_rto == approx(2.0)

    # Several low-latency samples should pull RTO down
    for _ in range(15):
        est.note_sample(0.120)

    assert est.rto < high_rto
    # And it should still respect the minimum clamp
    assert est.rto >= 0.10 - 1e-9


def test_consecutive_identical_samples_converge():
    est = RtoEstimator(tick=0.05)
    # First sample sets baseline
    est.note_sample(0.150)

    # Feed identical samples; SRTT should converge to 0.150, RTTVAR to 0
    for _ in range(20):
        est.note_sample(0.150)

    assert est.srtt == approx(0.150)
    assert est.rttvar < 1e-3
    assert est.rto == approx(0.2)
