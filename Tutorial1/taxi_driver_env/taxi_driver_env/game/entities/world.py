from __future__ import annotations

import random
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import pyray as pr
import taxi_driver_env.resources as res
from taxi_driver_env.math import envelope, graph
from taxi_driver_env.math.geom import (
    Point,
    Segment,
    distance,
    distance_point_segment,
    nearest_point_segment,
)
from taxi_driver_env.math.linalg import normalize

GRASS_COLOR = pr.Color(157, 176, 84, 255)
BASE_COLOR = pr.Color(111, 111, 111, 255)
ROAD_COLOR = pr.Color(60, 60, 60, 255)
BORDER1_COLOR = pr.Color(255, 255, 255, 255)
BORDER2_COLOR = pr.Color(255, 0, 0, 255)

ROAD_WIDTH = 10  # m
START_OFFSET = 2  # m

HOUSE_DENSITY = 0.9
HOUSE_DISTANCE = 10  # m
HOUSE_SIZES = {
    "house1": (544, 0, 192, 192, 16, 16, 1),
    "house2": (800, 0, 192, 192, 16, 16, 2),
    "house3": (0, 256, 256, 192, 32, 24, 3),
    "house4": (256, 256, 256, 192, 32, 24, 4),
}
HOUSE_TYPES = list(HOUSE_SIZES.keys())
HOUSE_REAL_ESTATE = 0.5

TREE_DENSITY = 0.5
TREE_DISTANCE = 25  # m
TREE_SIZES = {
    "tree1": (256, 0, 128, 128, 16, 16, 1),
    "tree2": (384, 0, 128, 128, 16, 16, 1),
    "tree3": (256, 128, 128, 128, 16, 16, 0.5),
}
TREE_TYPES = list(TREE_SIZES.keys())
TREE_OFFSET = 5  # m


@dataclass
class House:
    position: Point
    segment: Segment
    type: str

    def __post_init__(self):
        self.angle = self.segment.angle
        path_end = nearest_point_segment(self.position, self.segment)
        if path_end:
            u = normalize(path_end.xy - self.position.xy) * (HOUSE_DISTANCE * 0.75 + TREE_DISTANCE * 0.25)
            self.position = Point(path_end.xy - u)
            self.path = Segment(self.position, path_end)

    def is_overlap(self, other: House) -> bool:
        p1, r1 = self.position, HOUSE_SIZES[self.type][4] * HOUSE_REAL_ESTATE
        p2, r2 = other.position, HOUSE_SIZES[other.type][4] * HOUSE_REAL_ESTATE
        return distance(p1, p2) < r1 + r2


@dataclass
class Tree:
    position: Point
    angle: float
    type: str


@dataclass
class World:
    roads: graph.SpatialGraph
    borders: envelope.Envelope
    houses: list[House]
    trees: list[Tree]


_progress_callback: list[envelope.ProgressCallBack] = []


@lru_cache(1)
def get_singleton(name: str = "default") -> World:
    pr.trace_log(pr.TraceLogLevel.LOG_INFO, "WORLD: Initialize singleton")

    roads = graph.generate_random()

    borders, anchors = envelope.generare_borders_from_spatial_graph(roads, ROAD_WIDTH, _progress_callback)

    houses: list[House] = []
    for anchor in anchors:
        dist, seg = min(
            ((distance_point_segment(anchor, seg), seg) for seg in borders.segments),
            key=lambda x: x[0],
        )
        if HOUSE_DISTANCE <= dist <= TREE_DISTANCE and random.random() < HOUSE_DENSITY:
            house = House(anchor, seg, random.choice(HOUSE_TYPES))
            if not any(x.is_overlap(house) for x in houses):
                houses.append(house)

    trees = [
        Tree(
            Point(
                anchor.xy
                + [
                    random.randint(-TREE_OFFSET, TREE_OFFSET),
                    random.randint(-TREE_OFFSET, TREE_OFFSET),
                ]
            ),
            random.random() * np.pi / 2,
            random.choice(TREE_TYPES),
        )
        for anchor in anchors
        if min((distance_point_segment(anchor, x, True) for x in borders.segments)) > TREE_DISTANCE
        and random.random() < TREE_DENSITY
    ]

    return World(roads, borders, houses, trees)


def add_progress_callback(progress_callback: envelope.ProgressCallBack):
    _progress_callback.append(progress_callback)


def remove_progress_callback(progress_callback: envelope.ProgressCallBack):
    _progress_callback.remove(progress_callback)


def get_random_corridor():
    roads = get_singleton().roads
    start = random.choice(roads.vertice)
    stop = max(roads.vertice, key=lambda x: distance(start.point, x.point))
    return envelope.generare_corridor_from_spatial_graph(roads.get_shortest_path(start, stop), ROAD_WIDTH, [])


def get_corridor_from_a_to_b(a: envelope.Location, b: envelope.Location) -> envelope.Envelope:
    roads = get_singleton().roads

    start = min(roads.vertice, key=lambda x: distance(a[0].closest_ep(a[1]), x.point))
    stop = min(roads.vertice, key=lambda x: distance(b[0].closest_ep(b[1]), x.point))
    shortest_path = roads.get_shortest_path(start, stop)

    if shortest_path.edges[0].segment != a[0]:
        shortest_path.prepend_vertex(graph.SpatialVertex(a[0].farest_ep(a[1])))

    if shortest_path.edges[-1].segment != b[0]:
        shortest_path.append_vertex(graph.SpatialVertex(b[0].farest_ep(b[1])))

    return envelope.generare_corridor_from_spatial_graph(shortest_path, ROAD_WIDTH, [])


def is_alive() -> bool:
    return True


def hit(damage: int) -> None:
    pass


def reset() -> None:
    pass


def update(dt: float) -> None:
    pass


def draw(layer: int = 1) -> None:
    world = get_singleton()

    def draw_bg():
        pr.clear_background(GRASS_COLOR)
        for bone in world.borders.skeleton:
            bone.draw(world.borders.width + TREE_DISTANCE * 0.5, BASE_COLOR, None, True)
        for house in world.houses:
            _, _, _, _, sx, _, _ = HOUSE_SIZES[house.type]
            house.path.draw(sx * (1 + HOUSE_REAL_ESTATE), BASE_COLOR)
        for bone in world.borders.skeleton:
            bone.draw(world.borders.width, ROAD_COLOR, None, True)
        for bone in world.borders.skeleton:
            bone.draw(0.25, BORDER1_COLOR, (2, ROAD_COLOR), False)
        for segment in world.borders.segments:
            segment.draw(0.5, BORDER1_COLOR, None, True)

    def draw_fg():
        tex = res.load_texture("spritesheet")
        for tree in world.trees:
            tx, ty, tw, th, sx, sy, sh = TREE_SIZES[tree.type]
            pr.draw_texture_pro(
                tex,
                pr.Rectangle(tx, ty, tw, th),
                pr.Rectangle(tree.position.xy[0] - sh, tree.position.xy[1] + sh, sx, sy),
                pr.Vector2(sx * 0.5, sy * 0.5),
                np.rad2deg(tree.angle),
                pr.Color(0, 0, 0, 64),
            )
            pr.draw_texture_pro(
                tex,
                pr.Rectangle(tx, ty, tw, th),
                pr.Rectangle(tree.position.xy[0], tree.position.xy[1], sx, sy),
                pr.Vector2(sx * 0.5, sy * 0.5),
                np.rad2deg(tree.angle),
                pr.WHITE,  # type: ignore
            )
        for house in world.houses:
            tx, ty, tw, th, sx, sy, sh = HOUSE_SIZES[house.type]
            pr.draw_texture_pro(
                tex,
                pr.Rectangle(tx, ty, tw, th),
                pr.Rectangle(house.position.xy[0] - sh, house.position.xy[1] + sh, sx, sy),
                pr.Vector2(sx * 0.5, sy * 0.5),
                np.rad2deg(house.angle),
                pr.Color(0, 0, 0, 64),
            )
            pr.draw_texture_pro(
                tex,
                pr.Rectangle(tx, ty, tw, th),
                pr.Rectangle(house.position.xy[0], house.position.xy[1], sx, sy),
                pr.Vector2(sx * 0.5, sy * 0.5),
                np.rad2deg(house.angle),
                pr.WHITE,  # type: ignore
            )

    [draw_bg, draw_fg][layer]()
