from typing import Dict

from ...utils import UInt8, UInt16, UInt32
from ...network.protocol.records import Hello, Welcome
from ...interfaces import ConnectionType, RecordType


class ClientExtension:
    def __init__(self, **options):
        self.connection: ConnectionType | None = None

    def init(self, connection: ConnectionType):
        self.connection = connection

    def on_tick(self):
        if self.connection is None:
            raise RuntimeError("Extension not initialised yet")

    def on_record(self, record: RecordType) -> bool:
        if self.connection is None:
            raise RuntimeError("Extension not initialised yet")

        if isinstance(record, Hello):
            self.connection.send_record(
                Welcome(
                    server_nonce=UInt32(0),
                    assigned_client_id=UInt16(0),
                    max_record_size=UInt16(self.connection.mtu),
                )
            )
        else:
            return False
        return True
