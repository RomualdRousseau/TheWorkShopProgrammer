from __future__ import annotations

import heapq
import random
from dataclasses import dataclass
from random import choice
from typing import Iterable

import numpy as np
import pyray as pr
from taxi_driver_env.constants import VIRTUAL_WIDTH
from taxi_driver_env.math.geom import (
    Point,
    Segment,
    distance,
    intersect,
)
from taxi_driver_env.math.linalg import lst_2_vec

EDGE_COLOR = pr.Color(0, 0, 0, 128)
VERTEX_COLOR = pr.Color(0, 0, 255, 128)


@dataclass
class SpatialVertex:
    point: Point

    def draw(self, color=VERTEX_COLOR):
        self.point.draw(5.0, color)

    def __lt__(self, other):
        return distance(self.point, other.point) < 0

    def __hash__(self) -> int:
        return self.point.__hash__()


@dataclass
class SpatialEdge:
    start: SpatialVertex
    end: SpatialVertex

    @property
    def segment(self):
        return Segment(self.start.point, self.end.point)

    def draw(self, color=EDGE_COLOR):
        self.segment.draw(1.0, color)


@dataclass
class SpatialGraph:
    vertice: list[SpatialVertex]
    edges: list[SpatialEdge]

    def get_edges_from_vextex(self, v: SpatialVertex) -> Iterable[tuple[SpatialEdge, SpatialVertex]]:
        is_neighboor = lambda x: v in (x.start, x.end)
        other_vertex = lambda x: (x, x.end if x.start == v else x.start)
        return map(other_vertex, filter(is_neighboor, self.edges))

    def get_shortest_path(self, start: SpatialVertex, stop: SpatialVertex) -> SpatialGraph:
        weight = lambda x: x[0]
        distances = {x: 0.0 if x == start else np.inf for x in self.vertice}
        unvisited = sorted(((distances[x], x) for x in self.vertice), key=weight)
        prev = {}

        while unvisited:
            dist_u, u = heapq.heappop(unvisited)
            if u == stop:
                break
            for e, v in self.get_edges_from_vextex(u):
                alt = dist_u + e.segment.length
                if alt < distances[v]:
                    prev[v] = u
                    distances[v] = alt
                    heapq.heappush(unvisited, (alt, v))

        vertice: list[SpatialVertex] = []
        u = stop
        while prev.get(u) and u != start:
            vertice = [u, *vertice]
            u = prev[u]
        vertice = [start, *vertice]

        edges: list[SpatialEdge] = []
        for i in range(len(vertice) - 1):
            edges.append(SpatialEdge(vertice[i], vertice[i + 1]))

        return SpatialGraph(vertice, edges)

    def prepend_vertex(self, v: SpatialVertex):
        new_edge = SpatialEdge(v, self.vertice[0])
        self.vertice.insert(0, v)
        self.edges.insert(0, new_edge)

    def append_vertex(self, v: SpatialVertex):
        new_edge = SpatialEdge(self.vertice[-1], v)
        self.vertice.append(v)
        self.edges.append(new_edge)

    def draw(self):
        for seg in self.edges:
            seg.draw()
        for vertex in self.vertice:
            vertex.draw()


def generate_random():
    def generate_vertice(num: int, min: int) -> list[SpatialVertex]:
        rand = lambda: random.randrange(-VIRTUAL_WIDTH, VIRTUAL_WIDTH)
        vertice: list[SpatialVertex] = []
        n = 0

        is_valid = lambda x, y: distance(x.point, y.point) > min

        while n < num:
            v = SpatialVertex(Point(lst_2_vec([rand(), rand()])))
            if all((is_valid(v, x) for x in vertice)):
                vertice.append(v)
                n += 1
        return vertice

    def generate_edges(vertice: list[SpatialVertex], num: int, k: int = 3):
        edges: list[SpatialEdge] = []
        n = 0

        is_valid = lambda x, y: x.segment != y.segment and not intersect(x.segment, y.segment)

        while n < num:
            e = generate_edge(vertice, k)
            if all((is_valid(e, x) for x in edges)):
                edges.append(e)
                n += 1
        return edges

    def generate_edge(vertice: list[SpatialVertex], k: int) -> SpatialEdge:
        start = choice(vertice)
        distance_to_start = lambda x: distance(start.point, x.point)
        choices = sorted((x for x in vertice if x != start), key=distance_to_start)
        end = choice(choices[:k])
        return SpatialEdge(start, end)

    vertice = generate_vertice(20, 100)
    edges = generate_edges(vertice, 25, 3)
    return SpatialGraph(vertice, edges)
