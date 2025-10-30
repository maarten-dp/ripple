from __future__ import annotations
from typing import Protocol, Any, Dict, Tuple
from io import BytesIO


class PackerType(Protocol):
    def pack(self, packable: Any) -> bytes: ...

    def unpack(cls, buffer: BytesIO) -> Tuple[Dict[str, Any], int]: ...
