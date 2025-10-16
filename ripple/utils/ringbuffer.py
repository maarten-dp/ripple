from ..core.models import DropPolicy
from ..core.metrics import MetricsSink, NoOpMetrics, Event


class RingBuffer:
    def __init__(
        self,
        name: str,
        capacity: int,
        drop_policy: DropPolicy,
        metrics: MetricsSink | None = None,
    ):
        self.name = name
        self._buf = [None] * capacity
        self._capacity = capacity
        self._head = 0
        self._tail = 0
        self._size = 0
        self.drop_policy = drop_policy
        self.metrics = metrics or NoOpMetrics()

    @property
    def full(self):
        return self._size == self._capacity

    @property
    def empty(self):
        return self._size == 0

    def __len__(self):
        return self._size

    def fill_ratio(self):
        return self._size / self._capacity

    def push(self, item):
        if self.full:
            if self.drop_policy == DropPolicy.NEWEST:
                self.metrics.ring_event(self.name, Event.ENQUEUE_DROP_NEWEST)
                return False
            self._move_head()
            self.metrics.ring_event(self.name, Event.ENQUEUE_DROP_OLDEST)
        self._buf[self._tail] = item
        self._move_tail()
        self.metrics.ring_event(self.name, Event.ENQUEUE_OK)
        return True

    def pop(self):
        if self.empty:
            self.metrics.ring_event(self.name, Event.DEQUEUE_EMPTY)
            return None
        item = self._buf[self._head]
        self._buf[self._head] = None
        self._move_head()
        self.metrics.ring_event(self.name, Event.DEQUEUE_OK)
        return item

    def _move_head(self):
        self._head = (self._head + 1) % self._capacity
        self._size -= 1

    def _move_tail(self):
        self._tail = (self._tail + 1) % self._capacity
        self._size += 1
