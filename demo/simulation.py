from typing import Dict
from dataclasses import dataclass
import arcade

from ripple.utils import UInt8, UInt16, UInt32
from ripple.network.protocol.records import Input, Delta, Snapshot as Snap
from ripple.interfaces import ConnectionType, RecordType
from ripple.ecs.world import World
from ripple.utils import UInt16
from ripple.ecs.snapshot import Snapshot, DeltaSnapshot


UP = 0
DOWN = 1


@dataclass
class Position:
    x: UInt16 = UInt16(0)
    y: UInt16 = UInt16(0)


@dataclass
class Velocity:
    dx: UInt16 = UInt16(0)
    dy: UInt16 = UInt16(0)


class Simulation:
    def __init__(self, world):
        self.world = world

    def on_tick(self):
        for entity, (pos, vel) in WORLD.get_components(Position, Velocity):
            pos.x += vel.dx
            pos.y += vel.dy

    def on_key_up(self, key, modifiers):
        for entity, (vel,) in self.world.get_components(Velocity):
            if key == arcade.key.UP:
                vel.dy = MOVEMENT_SPEED
            elif key == arcade.key.DOWN:
                vel.dy = -MOVEMENT_SPEED
            elif key == arcade.key.LEFT:
                vel.dx = -MOVEMENT_SPEED
            elif key == arcade.key.RIGHT:
                vel.dx = MOVEMENT_SPEED

    def on_key_down(self, key, modifiers):
        for entity, (vel,) in self.world.get_components(Velocity):
            if key == arcade.key.UP or key == arcade.key.DOWN:
                vel.dy = 0
            elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
                vel.dx = 0


class SimulationExtension:
    def __init__(self, Simulation, **options):
        self.connection: ConnectionType | None = None
        self.simulation = simulation

    def init(self, connection: ConnectionType):
        self.connection = connection

    def on_tick(self):
        if self.connection is None:
            raise RuntimeError("Extension not initialised yet")
        self.simulation.on_tick()

    def on_record(self, record: RecordType) -> bool:
        if self.connection is None:
            raise RuntimeError("Extension not initialised yet")

        if isinstance(record, Input):
            if record.up_down == UP:
                self.simulation.on_key_up(record.key, record.modifiers)
            elif record.up_down == DOWN:
                self.simulation.on_key_down(record.key, record.modifiers)
            else:
                raise ValueError(f"{record.up_down} not valid")
        else:
            return False
        return True


class ServerSnapshotExtension:
    def __init__(self, simulation, **options):
        self.connection: ConnectionType | None = None
        self.simulation = simulation
        self.deltas = 0
        self.last_snapshot = None

    def init(self, connection: ConnectionType):
        self.connection = connection

    def on_tick(self):
        if self.connection is None:
            raise RuntimeError("Extension not initialised yet")
        snapshot = Snapshot.from_world(self.simulation.world)
        if self.last_snapshot is None:
            record = Snap(snapshot=snapshot)
        elif self.deltas < 5:
            delta = snapshot.get_delta_from(self.last_snapshot)
            record = Delta(snapshot=delta)
            self.deltas += 1
        else:
            self.deltas = 0
            record = Snap(snapshot=snapshot)
        self.last_snapshot = snapshot
        self.connection.send_record(record)

    def on_record(self, record: RecordType) -> bool:
        return False


class ClientSnapshotExtension:
    def __init__(self, simulation, **options):
        self.connection: ConnectionType | None = None
        self.simulation = simulation
        self.last_snapshot = Snapshot(id=UInt16(-1))

    def init(self, connection: ConnectionType):
        self.connection = connection

    def on_tick(self):
        pass

    def on_record(self, record: RecordType) -> bool:
        if self.connection is None:
            raise RuntimeError("Extension not initialised yet")

        delta = None
        if isinstance(record, Snap):
            snapshot = record.snapshot
            delta = snapshot.get_delta_from(self.last_snapshot)
        elif isinstance(record, Delta):
            if self.last_snapshot is None:
                raise ValueError("No available snapshot")
            snapshot = self.last_snapshot.apply_delta(record.snapshot)
            if snapshot is None:
                snapshot = self.last_snapshot
            delta = record.snapshot
        else:
            return False

        self.last_snapshot = snapshot
        if delta is not None:
            self.simulation.world.apply_delta(delta)

        return True
