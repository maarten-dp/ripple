# Ripple-sync MVP TODO

This file tracks the core tasks required to deliver the MVP for Ripple-sync.

---

## 0. Bootstrap & Infrastructure
- [X] Initialize repo (pyproject, README, license)
- [X] Set up formatter (black), linter (ruff), type-checker (mypy)
- [X] Add CI (pytest + coverage on PR)

## 1. Transport & Protocol Core
- [X] UDP endpoint wrapper with poll/send loop
- [X] Packet headers: sequence number, protocol version
- [X] Reliability layer: selective ACKs, resend queue
- [X] Fragmentation/defrag (MTU safe)
- [X] Ping/pong for RTT + jitter measurement

## 2. Serialization & Messages
- [ ] Define schema for `Hello`, `Auth`, `Snapshot`, `Delta`, `Ack`
- [ ] Implement serializer with bit-packing + float quantization
- [ ] Delta encoding: per-component + snapshot-to-snapshot

## 3. State Replication
- [ ] Entity & component model with stable IDs + version counters
- [ ] Snapshot builder (change detection)
- [ ] Spawn/despawn logic; full snapshot on join
- [ ] Interest management: simple grid AOI filter

## 4. Client Pipeline
- [ ] Interpolation buffer (2–3 deep, clamp at 150 ms)
- [ ] Dead-reckoning: predict transforms using velocity
- [ ] Late-join bootstrap (apply full state)

## 5. Prediction & Reconciliation
- [ ] Input buffer tagged with `input_seq`
- [ ] Client-side movement prediction
- [ ] Server authoritative state with last processed `input_seq`
- [ ] Reconcile: rewind + reapply pending inputs, smoothing snap tolerance

## 6. Bandwidth & Metrics
- [ ] Per-client bandwidth budget (bytes/s)
- [ ] Priority: nearby entities first
- [ ] Metrics counters: RTT, packet loss, resend rate, bandwidth
- [ ] Lag/loss simulator tool

## 7. Security & Auth
- [ ] Token-based handshake (`Hello` + `Auth`)
- [ ] Nonce + TTL for replay protection
- [ ] Basic sanity checks (speed/teleport caps)

## 8. Demo & Docs
- [ ] Example: cubes demo (spawn/move cubes, sync transforms)
- [ ] Quickstart docs (setup, run demo)
- [ ] Troubleshooting guide (warping, packet loss, divergence)

---

✅ When all boxes are checked, you’ll have a working MVP that matches the goals we set earlier.
