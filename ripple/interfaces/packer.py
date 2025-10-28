from __future__ import annotations
from typing import Protocol, Any, Dict, Tuple


class PackerType(Protocol):
    @property
    def size(self) -> int: ...

    def pack(self, packable: Any) -> bytes: ...

    def unpack(cls, buffer: memoryview) -> Tuple[Dict[str, Any], int]: ...
