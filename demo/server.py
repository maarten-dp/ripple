import sys
import time
import logging

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(sys.stdout))

from ripple import Address, UdpEndpointConfig
from ripple.connection import ReliableConnection
from ripple.core.server.extensions import ClientExtension
from ripple.ecs.world import World

from simulation import Simulation, ServerSnapshotExtension


def get_connection():
    local_addr = Address("127.0.0.1", 7001)
    remote_addr = Address("127.0.0.1", 7002)
    cfg = UdpEndpointConfig(
        local_addr=local_addr,
        remote_addr=remote_addr,
    )
    return ReliableConnection(
        cfg,
        mtu=1200,
        extenstions=[
            ClientExtension(),
            ServerSnapshotExtension(Simulation(World())),
        ],
    )


def run(tick=1 / 30):
    connection = get_connection()
    time.sleep(2)
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
