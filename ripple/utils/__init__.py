import time
from typing import Callable

from .int_types import UInt8, UInt16, UInt32
from .packable import FreeFormField


def clamp(value, lowest, highest):
    return min(highest, max(value, lowest))


def monotonic(fn: Callable):
    def _monotonic(*args, **kwargs):
        now = kwargs.get("now")
        kwargs["now"] = time.monotonic() if now is None else now
        return fn(*args, **kwargs)

    return _monotonic


__all__ = [
    "UInt8",
    "UInt16",
    "UInt32",
    "FreeFormField",
    "clamp",
    "monotonic",
]
