import socket
from typing import List, Tuple, Any
from functools import cached_property

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional


class DropPolicy(Enum):
    OLDEST = auto()
    NEWEST = auto()


@dataclass
class Address:
    host: str
    port: int

    @cached_property
    def family(self) -> socket.AddressFamily:
        family = socket.AF_INET
        if ":" in self.host:
            family = socket.AF_INET6
        return family

    @property
    def bind_address(self):
        return (self.host, self.port)


@dataclass
class DatagramConfig:
    # bytes
    max_size: int = 1200
    # max entries in the ring
    capacity: int = 256
    drop_policy: DropPolicy = DropPolicy.NEWEST


@dataclass
class UdpEndpointConfig:
    local_addr: Address
    remote_addr: Optional[Address] = None

    rx: DatagramConfig = DatagramConfig(drop_policy=DropPolicy.OLDEST)
    tx: DatagramConfig = DatagramConfig()

    # reserved for later
    dscp: Optional[int] = None
    ipv6_only: bool = False
    reuse_addr: bool = True

    def get_local_socket_options(self) -> List[Tuple[int, int, Any]]:
        options = []
        if self.reuse_addr:
            options.append((socket.SOL_SOCKET, socket.SO_REUSEADDR, 1))
        if self.local_addr.family == socket.AF_INET6 and self.ipv6_only:
            options.append((socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1))
        return options
