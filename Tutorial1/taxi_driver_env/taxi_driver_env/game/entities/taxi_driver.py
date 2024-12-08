from typing import Optional

import pyray as pr
from taxi_driver_env.game.entities import car, world
from taxi_driver_env.game.entities.marker import Marker
from taxi_driver_env.math import envelope
from taxi_driver_env.math.geom import Point

CAR_COLOR = pr.Color(255, 255, 255, 255)
CORRIDOR_COLOR = pr.Color(255, 255, 0, 64)
WAIT_TIMER = 3600  # s


class TaxiDriver:
    STATE_INIT = 0
    STATE_WAITING_CALL = 1
    STATE_ACCEPTING_CALL = 2
    STATE_ACCEPT_CALL = 3
    STATE_GOING_TO_PICKUP = 4
    STATE_PICKUP = 5
    STATE_PICKUP_WAIT = 6
    STATE_GOING_TO_DROPOFF = 7
    STATE_DROPOFF = 8
    STATE_DROPOFF_WAIT = 9

    def __init__(self, input_mode: str, debug_mode: bool = False) -> None:
        self.state = TaxiDriver.STATE_INIT
        self.car = car.Car(CAR_COLOR, input_mode)
        self.car.set_debug_mode(debug_mode)
        self.pickup: Optional[Marker] = None
        self.dropoff: Optional[Marker] = None
        self.money = 1000

    def get_previous_pos(self) -> Point:
        return self.car.prev_pos

    def get_current_pos(self) -> Point:
        return self.car.curr_pos

    def on_enter(self, marker: Marker) -> None:
        if self.state == TaxiDriver.STATE_GOING_TO_PICKUP and marker is self.pickup and self.dropoff is not None:
            self.state = TaxiDriver.STATE_PICKUP
        if self.state == TaxiDriver.STATE_GOING_TO_DROPOFF and marker is self.dropoff:
            self.state = TaxiDriver.STATE_DROPOFF

    def on_leave(self, marker: Marker) -> None:
        pass

    def accept_call(self, pickup: envelope.Location, dropoff: envelope.Location):
        if self.state != TaxiDriver.STATE_WAITING_CALL:
            return

        self.pickup = Marker(pickup, world.ROAD_WIDTH * 0.5, 2)
        self.pickup.add_listener(self)
        self.dropoff = Marker(dropoff, world.ROAD_WIDTH * 0.5, 2)
        self.dropoff.add_listener(self)
        self.state = TaxiDriver.STATE_ACCEPTING_CALL

    def is_alive(self) -> bool:
        return self.car.is_alive()

    def reset(self) -> None:
        self.state = TaxiDriver.STATE_WAITING_CALL
        self.pickup = None
        self.dropoff = None
        self.money = 1000
        self.car.reset()

    def hit(self, damage: int) -> None:
        self.car.hit(damage)

    def update(self, dt: float) -> None:
        match self.state:
            case TaxiDriver.STATE_INIT:
                pass

            case TaxiDriver.STATE_WAITING_CALL:
                self.timer = 0.0
                pass

            case TaxiDriver.STATE_ACCEPTING_CALL:
                self.timer += dt
                if self.timer > WAIT_TIMER:
                    self.state = TaxiDriver.STATE_ACCEPT_CALL
                return

            case TaxiDriver.STATE_ACCEPT_CALL:
                assert self.pickup is not None
                self.car.set_corridor(world.get_corridor_from_a_to_b(self.car.current_location, self.pickup.location))
                self.state = TaxiDriver.STATE_GOING_TO_PICKUP

            case TaxiDriver.STATE_GOING_TO_PICKUP:
                pass

            case TaxiDriver.STATE_PICKUP:
                self.timer = 0.0
                self.state = TaxiDriver.STATE_PICKUP_WAIT

            case TaxiDriver.STATE_PICKUP_WAIT:
                self.timer += dt
                if self.timer > WAIT_TIMER:
                    assert self.dropoff is not None
                    self.car.set_corridor(
                        world.get_corridor_from_a_to_b(self.car.current_location, self.dropoff.location)
                    )
                    self.state = TaxiDriver.STATE_GOING_TO_DROPOFF
                return

            case TaxiDriver.STATE_GOING_TO_DROPOFF:
                pass

            case TaxiDriver.STATE_DROPOFF:
                self.timer = 0
                self.state = TaxiDriver.STATE_DROPOFF_WAIT

            case TaxiDriver.STATE_DROPOFF_WAIT:
                self.timer += dt
                if self.timer > WAIT_TIMER:
                    assert self.dropoff is not None
                    self.pickup = None
                    self.dropoff = None
                    self.state = TaxiDriver.STATE_WAITING_CALL
                return

        if self.pickup is not None:
            self.pickup.update(dt)

        if self.dropoff is not None:
            self.dropoff.update(dt)

        self.car.update(dt)

    def draw(self, layer: int = 1) -> None:
        if self.pickup is not None:
            self.pickup.draw(layer)

        if self.dropoff is not None:
            self.dropoff.draw(layer)

        if layer == 0 and self.car.debug_mode and self.car.corridor is not None:
            for segment in self.car.corridor.segments:
                segment.draw(1, CORRIDOR_COLOR, None, True)

        self.car.draw(layer)
