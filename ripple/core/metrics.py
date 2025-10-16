import time
from enum import Enum, auto
from typing import Protocol, Literal
from collections import defaultdict


class Event(Enum):
    ENQUEUE_OK = auto()
    ENQUEUE_DROP_NEWEST = auto()
    ENQUEUE_DROP_OLDEST = auto()
    DEQUEUE_OK = auto()
    DEQUEUE_EMPTY = auto()
    DEQUEUE_DROPPED = auto()

    DRAIN = auto()
    DRAIN_TIME = auto()
    TICK_TIME = auto()


class MetricsSink(Protocol):
    def ring_event(
        self, name: str, event: Event, size: int = 0, fill: float = 0.0
    ) -> None: ...
    def drain_event(
        self, name: str, event: Event, time: float | None = None
    ) -> None: ...
    def tick_event(self, event: Event, time: float) -> None: ...
    def gauge(self, name: str, value: float) -> None: ...
    def timing_ns(self, name: str, delta_ns: int) -> None: ...


class NoOpMetrics:
    def ring_event(self, *args, **kwargs):
        pass

    def drain_event(self, *args, **kwargs):
        pass

    def tick_event(self, *args, **kwargs):
        pass

    def gauge(self, *args, **kwargs):
        pass

    def timing_ns(self, *args, **kwargs):
        pass


class InMemoryMetrics:
    def __init__(self, alpha: float = 0.2):
        self.counters = defaultdict(int)  # (name, event) -> count
        self.gauges = {}  # str|tuple -> float
        self.ema = {}  # str|tuple -> float
        self.alpha = alpha

    def ring_event(
        self, name: str, event: Event, size: int = 0, fill: float = 0.0
    ) -> None:
        self.counters[(name, event)] += 1
        self.gauges[(name, "fill_pct")] = fill * 100.0
        self.gauges[(name, "last_size_bytes")] = float(size)

    def drain_event(
        self, name: str, event: Event, time: float | None = None
    ) -> None:
        if event is Event.DRAIN:
            self.counters[(name, event)] += 1
        elif event is Event.DRAIN_TIME:
            self.gauges[(name, "drain_ms")] = time

    def tick_event(self, event: Event, time: float) -> None:
        self.counters[event] += 1
        self.gauges["tick"] = time

    def gauge(self, name: str, value: float) -> None:
        self.gauges[name] = float(value)
        prev = self.ema.get(name, value)
        self.ema[name] = prev + self.alpha * (value - prev)

    def timing_ns(self, name: str, delta_ns: int) -> None:
        self.counters[(name, "count")] += 1
        last_ms = delta_ns / 1e6
        self.gauges[(name, "last_ms")] = last_ms
        prev = self.ema.get((name, "ema_ms"), last_ms)
        self.ema[(name, "ema_ms")] = prev + self.alpha * (last_ms - prev)

    def __repr__(self):
        counters = str(self.counters)
        gauges = str(self.gauges)
        return f"{counters}\n\n{gauges}"


class Timer:
    def __init__(self):
        self.start = time.perf_counter()
        self.lap_start = self.start

    def lap(self):
        lap = time.perf_counter()
        delta = lap - self.lap_start
        self.lap_start = lap
        return delta

    def delta(self):
        return time.perf_counter() - self.start
