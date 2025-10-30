import sys
import time
import logging

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(sys.stdout))

from ripple import Address, UdpEndpointConfig
from ripple.connection import ReliableConnection
from ripple.network.protocol.records import Hello
from ripple.utils import UInt8, UInt32


def get_connection():
    local_addr = Address("127.0.0.1", 7002)
    remote_addr = Address("127.0.0.1", 7001)
    cfg = UdpEndpointConfig(
        local_addr=local_addr,
        remote_addr=remote_addr,
    )
    return ReliableConnection(cfg, mtu=1200)


def run(tick=1 / 30):
    connection = get_connection()
    hello = Hello(
        protocol_version=UInt8(0),
        client_nonce=UInt32(0),
        app_id=UInt32(0),
    )
    connection.send_record(hello)
    while True:
        try:
            t1 = time.monotonic()
            connection.tick()
            delta = time.monotonic() - t1
            if (sleep := tick - delta) > 0:
                time.sleep(sleep)
        except KeyboardInterrupt:
            print("stopping")
            break


run(1)
