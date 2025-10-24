from __future__ import annotations
from dataclasses import dataclass
from functools import partial
import struct

from ....utils.int_types import UInt8, UInt16, UInt32

_ENDIAN = ">"
_MSG_ID = "H"
_INDEX = "B"
_COUNT = "B"
_TOTAL_LEN = "H"
_CRC32 = "I"

_FRAGMENT_HEADER_FMT = f"{_ENDIAN}{_MSG_ID}{_INDEX}{_COUNT}{_TOTAL_LEN}{_CRC32}"
_FRAGMENT_HEADER_SIZE = struct.calcsize(_FRAGMENT_HEADER_FMT)
pack = partial(struct.pack, _FRAGMENT_HEADER_FMT)
unpack = partial(struct.unpack_from, _FRAGMENT_HEADER_FMT)


@dataclass(frozen=True)
class FragmentHeader:
    msg_id: UInt16
    index: UInt8
    count: UInt8
    total_len: UInt16
    msg_crc32: UInt32

    def pack(self) -> bytes:
        return pack(
            int(self.msg_id),
            int(self.index),
            int(self.count),
            int(self.total_len),
            int(self.msg_crc32),
        )

    @classmethod
    def unpack(cls, buffer: memoryview) -> FragmentHeader:
        if len(buffer) < _FRAGMENT_HEADER_SIZE:
            raise ValueError("buffer too small for header")
        msg_id, index, count, total_len, msg_crc32 = unpack(buffer)
        return cls(
            msg_id=UInt16(msg_id),
            index=UInt8(index),
            count=UInt8(count),
            total_len=UInt16(total_len),
            msg_crc32=UInt32(msg_crc32),
        )

    @staticmethod
    def size() -> int:
        return _FRAGMENT_HEADER_SIZE
