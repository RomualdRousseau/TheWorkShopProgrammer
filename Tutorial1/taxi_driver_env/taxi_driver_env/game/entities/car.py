from typing import Optional

import numpy as np
import pyray as pr
import taxi_driver_env.resources as res
from taxi_driver_env.constants import GAMEPAD_AXIS_X, GAMEPAD_AXIS_Y, GAMEPAD_ID
from taxi_driver_env.game.entities import world
from taxi_driver_env.math import envelope
from taxi_driver_env.math.geom import (
    Point,
    Segment,
    cast_ray_segments,
    collision_circle_segment,
    distance,
    nearest_point_segment,
)
from taxi_driver_env.math.linalg import EPS, lst_2_vec, norm, normalize
from taxi_driver_env.physic.constants import C_G
from taxi_driver_env.physic.engine import euler_integrate
from taxi_driver_env.utils.bitbang import bit_set, bit_set_if, bit_unset, is_bit_set

MAX_LIFE = 100
MASS = 650.0  # kg
LENGTH = 5.0  # m
WIDTH = 2.0  # m
WHEEL_ANGLE_RATE = np.pi / 100  # rad
MAX_ENGINE_POWER = 200.0  # kN
MAX_SPEED = 125.0  # km.h-1
DRAG_ROAD = 0.9  # Concrete/Rubber
DRAG_ROLLING = 0.01  # Concrete/Rubber

FLAG_DAMAGED = 0
FLAG_OUT_OF_TRACK = 1

RAY_MAX_LEN = 25  # m
RAY_FOV = np.pi * 0.3

START_OFFSET = world.ROAD_WIDTH / 4  # m
MAX_VISITED_LOCATION = 10


class Car:
    def __init__(
        self,
        color: pr.Color,
        input_mode: str = "human",
        vin: int = 0,
        corridor: Optional[envelope.Envelope] = None,
    ) -> None:
        assert input_mode in ("human", "ai")
        self.vin = vin
        self.color = color
        self.input_mode = input_mode
        self.debug_mode = False

        self.corridor: envelope.Envelope = corridor if corridor is not None else world.get_random_corridor()
        self.spawn_location: envelope.Location = (
            self.corridor.skeleton[0],
            self.corridor.skeleton[0].start,
        )

        self.reset()

    def set_debug_mode(self, debug_mode: bool) -> None:
        self.debug_mode = debug_mode

    def set_corridor(self, corridor: envelope.Envelope) -> None:
        assert self.current_location[0] == corridor.skeleton[0]
        self.corridor = corridor

    def set_spawn_location(self, spawn_location: envelope.Location) -> None:
        self.spawn_location = spawn_location

    def get_total_distance_in_km(self) -> float:
        _, last_start = self.visited_location[-1]
        return (self.total_distance + distance(last_start, self.current_location[1])) * 0.001

    def get_average_speed_in_kmh(self) -> float:
        return (self.total_velocity / (self.total_tick + EPS)) * 3.6

    def get_speed_in_kmh(self) -> float:
        return norm(self.vel) * 3.6

    def get_spawn_location(self) -> envelope.Location:
        return self.visited_location[-1 if len(self.visited_location) <= 1 else -2]

    def turn_wheel(self, torque: float) -> None:
        self.wheel = float(np.interp(torque, [-1, 1], [-WHEEL_ANGLE_RATE, WHEEL_ANGLE_RATE]))

    def push_throttle(self, power: float) -> None:
        self.throttle = MAX_ENGINE_POWER * 1000 * power

    def is_alive(self) -> bool:
        return self.life > 0

    def hit(self, damage: int) -> None:
        self.life: float = max(0.0, self.life - damage)

    def reset(self) -> None:
        start_seg = self.spawn_location[0]
        start_pos, end_pos = (
            start_seg.closest_ep(self.spawn_location[1]).xy,
            start_seg.farest_ep(self.spawn_location[1]).xy,
        )
        start_pos = start_pos * 0.99 + end_pos * 0.01
        start_dir = normalize(end_pos - start_pos)
        start_off = lst_2_vec([-start_dir[1], start_dir[0]]) * START_OFFSET

        self.pos = start_pos + start_off
        self.vel = np.zeros(2, dtype=np.float64)
        self.mass = MASS
        self.head = start_dir

        self.life = MAX_LIFE
        self.wheel = 0.0
        self.throttle = 0.0
        self.flags = 0

        self.current_location = (start_seg, Point(start_pos))
        self.visited_location = [self.current_location]

        self.camera: list[Segment] = self._cast_rays()
        self.proximity: Optional[Segment] = None

        self.prev_pos = Point(self.pos.copy())
        self.curr_pos = self.prev_pos

        self.total_distance = 0.0
        self.total_velocity = 0.0
        self.total_tick = 0

    def update(self, dt: float) -> None:
        if self.input_mode == "human":
            self._input_human()
        self._update_physic(dt)

    def draw(self, layer: int = 1) -> None:
        if layer != 1:
            return

        if self.debug_mode:
            color: pr.Color = pr.YELLOW if not is_bit_set(self.flags, FLAG_DAMAGED | FLAG_OUT_OF_TRACK) else pr.RED  # type: ignore
            color = pr.color_alpha(color, 0.25)

            pr.draw_line_v(
                self.visited_location[-1][1].to_vec(),
                self.current_location[1].to_vec(),
                color,
            )

            for ray in self.camera:
                pr.draw_line_v(ray.start.to_vec(), ray.end.to_vec(), color)

            if self.proximity is not None:
                pr.draw_line_v(self.proximity.start.to_vec(), self.proximity.end.to_vec(), color)

        tex = res.load_texture("spritesheet")
        pr.draw_texture_pro(
            tex,
            pr.Rectangle(0, 0, 128, 128),
            pr.Rectangle(self.pos[0], self.pos[1], LENGTH, LENGTH),
            pr.Vector2(LENGTH * 0.5, LENGTH * 0.5),
            np.rad2deg(np.arctan2(self.head[1], self.head[0]) + np.pi / 2),
            pr.color_alpha(self.color, 1.0) if self.debug_mode else self.color,
        )

    def _input_human(self) -> None:
        # Gamepad

        self.turn_wheel(pr.get_gamepad_axis_movement(GAMEPAD_ID, GAMEPAD_AXIS_X) ** 3)
        self.push_throttle(-1.0 * pr.get_gamepad_axis_movement(GAMEPAD_ID, GAMEPAD_AXIS_Y) ** 3)

        # Keyboard

        if pr.is_key_down(pr.KeyboardKey.KEY_RIGHT):
            self.turn_wheel(0.5)
        if pr.is_key_down(pr.KeyboardKey.KEY_LEFT):
            self.turn_wheel(-0.5)
        if pr.is_key_down(pr.KeyboardKey.KEY_UP):
            self.push_throttle(0.5)
        if pr.is_key_down(pr.KeyboardKey.KEY_DOWN):
            self.push_throttle(-0.25)

    def _update_physic(self, dt: float) -> None:
        # Simple car modelisation (traction, drag road, drag rolling)

        forces = np.zeros(2)

        if self.wheel != 0:
            circ_radius = LENGTH / (np.sin(self.wheel))
            ang_vel = np.linalg.norm(self.vel) / circ_radius
            c, s = np.cos(ang_vel), np.sin(ang_vel)
            self.head = [[c, -s], [s, c]] @ self.head
        tract = self.head * self.throttle
        forces += tract

        drag_rd = self.vel * -DRAG_ROAD * self.mass * C_G
        forces += drag_rd

        drag_rr = self.vel * -DRAG_ROLLING * self.mass * C_G
        forces += drag_rr

        euler_integrate(self, forces, dt)

        # Collisions

        match self._collision():
            case None:
                self.flags = bit_unset(self.flags, FLAG_DAMAGED)
            case reaction:
                self.vel = self.vel * 0.5 + reaction
                self.pos += reaction
                self.head = normalize(self.vel)
                self.flags = bit_set(self.flags, FLAG_DAMAGED)

        self.prev_pos = self.curr_pos
        self.curr_pos = Point(self.pos.copy())

        # Sensors

        pos = Point(self.pos)

        self.camera = self._cast_rays()

        match nearest_point_segment(pos, self.visited_location[-1][0], True):
            case None:
                self.proximity = None
                self.flags = bit_unset(self.flags, FLAG_OUT_OF_TRACK)
            case Point() as nearest:
                self.proximity = Segment(pos, nearest)
                self.flags = bit_set_if(self.flags, FLAG_OUT_OF_TRACK, self.proximity.length < WIDTH * 0.75)

        # Localisation

        is_new_location_added = False
        self.current_location = self.corridor.get_nearest_location(pos)
        curr_loc_seg, curr_loc_pos = self.current_location
        if self.visited_location[-1][0] != curr_loc_seg:
            self.visited_location.append((curr_loc_seg, curr_loc_seg.closest_ep(curr_loc_pos)))
            if len(self.visited_location) > MAX_VISITED_LOCATION:
                self.visited_location.pop(0)
            is_new_location_added = True

        # Statistics

        self.total_distance += self.visited_location[-2][0].length if is_new_location_added else 0
        self.total_velocity += norm(self.vel)
        self.total_tick += 1

    def _cast_rays(
        self,
        length: float = RAY_MAX_LEN,
        fov: float = RAY_FOV,
        sampling: int = 16,
    ) -> list[Segment]:
        position = Point(self.pos)
        nearest_segments = envelope.get_nearest_segments(self.corridor, position, length)
        alpha = np.arctan2(self.head[1], self.head[0])
        rays = []

        for i in range(sampling):
            beta = np.interp(i / sampling, [0, 1], [alpha - fov, alpha + fov])
            direction = lst_2_vec([np.cos(beta), np.sin(beta)])
            rays.append(cast_ray_segments(position, direction, length, nearest_segments))

        return rays

    def _collision(self, radius: float = WIDTH * 0.5) -> Optional[np.ndarray]:
        position = Point(self.pos)
        nearest_segments = envelope.get_nearest_segments(self.corridor, position, radius)
        collide = lambda x: collision_circle_segment(position, radius, x)
        return next((x for x in map(collide, nearest_segments) if x is not None), None)
