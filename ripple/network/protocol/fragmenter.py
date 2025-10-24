import zlib
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from ...utils import monotonic, UInt8, UInt16, UInt32
from .headers import FragmentHeader


@dataclass
class Fragment:
    payload: bytes = field(default_factory=bytes)
    reliable: bool = False


class Fragmenter:
    def __init__(self, mtu: int):
        self.mtu = mtu
        self.fragment_size = mtu - FragmentHeader.size()
        self._msg_id = UInt16(0)
        self._fragments: List[Fragment] = []

    def _get_msg_id(self):
        msg_id = self._msg_id
        self._msg_id = self._msg_id + 1
        return msg_id

    def fragment(
        self,
        payload: bytes,
        reliable: bool = False,
    ):
        payload_len = len(payload)
        size = UInt16(payload_len)
        crc32 = UInt32(zlib.crc32(payload))

        buffer = memoryview(payload)
        msg_id = self._get_msg_id()

        fragments = []
        for start in range(0, payload_len, self.fragment_size):
            end = start + self.fragment_size
            fragment_payload = buffer[start:end]
            fragments.append(bytes(fragment_payload))

        count = UInt8(len(fragments))
        for idx, fragment in enumerate(fragments):
            header = FragmentHeader(
                msg_id=msg_id,
                index=UInt8(idx),
                count=count,
                total_len=size,
                msg_crc32=crc32,
            )
            self._fragments.append(
                Fragment(
                    payload=header.pack() + fragment,
                    reliable=reliable,
                )
            )

    def finish(self) -> List[Fragment]:
        if self._fragments:
            fragments = self._fragments
            self._fragments = []
            return fragments
        return []


class FragmentBucket:
    @monotonic
    def __init__(self, now):
        self.fragments: List[memoryview] = []
        self.crc32 = UInt32(0)
        self.created_at = now
        self.received = 0

    def add_fragment(self, header: FragmentHeader, fragment: memoryview):
        if not self.fragments:
            self.fragments = [memoryview(b"")] * int(header.count)
            self.crc32 = header.msg_crc32
        if self.crc32 != header.msg_crc32:
            raise ValueError("crc32 mismatch!")
        self.received += 1
        self.fragments[int(header.index)] = fragment

    @property
    def can_reconstruct(self):
        return self.received == len(self.fragments)

    def reconstruct(self) -> bytes:
        if not self.can_reconstruct:
            raise ValueError("Bucket not ready yet")
        payload_array = bytearray()
        [payload_array.extend(f) for f in self.fragments]
        payload = bytes(payload_array)
        if not self.crc32 == zlib.crc32(payload):
            raise ValueError("Given crc32 and calculated crc32 do not match")
        return payload


class Defragmenter:
    def __init__(self, capacity: int = 128, ttl: float = 5.0):
        self.capacity = capacity
        self.ttl = ttl
        self._buckets: Dict[UInt16, FragmentBucket] = {}
        self._reconstructed: List[bytes] = []

    @monotonic
    def _expire(self, now):
        for idx, bucket in self._buckets.items():
            if now - bucket.created_at > self.ttl:
                self._buckets.pop(idx)

    def _evict(self):
        if len(self._buckets) <= self.capacity:
            return
        oldest_key, _ = min(
            self._buckets.items(),
            key=lambda kv: kv[1].created_at,
        )
        self._buckets.pop(oldest_key, None)

    def register_fragment(self, fragment: bytes) -> Optional[bytes]:
        self._expire()

        buffer = memoryview(fragment)
        header = FragmentHeader.unpack(buffer)
        payload = buffer[FragmentHeader.size() :]
        bucket = self._buckets.get(header.msg_id)
        if bucket is None:
            bucket = FragmentBucket()
            self._buckets[header.msg_id] = bucket
            self._evict()

        bucket.add_fragment(header, payload)
        if bucket.can_reconstruct:
            self._buckets.pop(header.msg_id)
            self._reconstructed.append(bucket.reconstruct())

    def finish(self) -> List[bytes]:
        if self._reconstructed:
            records = self._reconstructed
            self._reconstructed = []
            return records
        return []
