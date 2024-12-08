from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

import numpy as np
import numpy.typing as npt
import pyray as pr
import taxi_driver_env.math.linalg as la
import taxi_driver_env.render.pyrayex as prx
from taxi_driver_env.constants import VIRTUAL_CELL, VIRTUAL_WIDTH

VIRTUAL_SIZE = VIRTUAL_WIDTH // VIRTUAL_CELL


@dataclass
class Point:
    xy: npt.NDArray[np.float64]

    def draw(self, thick: float, color: pr.Color) -> None:  # pragma: no cover
        pr.draw_circle_v(self.to_vec(), thick, color)

    def to_vec(self) -> pr.Vector2:
        return pr.Vector2(*self.xy)

    def almost(self, other: Point, eps=0.0001) -> bool:
        return np.allclose(self.xy, other.xy, 0.0, eps)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Point):
            return NotImplemented
        return np.array_equal(self.xy, other.xy)

    def __hash__(self) -> int:
        x, y = VIRTUAL_SIZE + self.xy // VIRTUAL_CELL
        return int(y * VIRTUAL_SIZE + x)


@dataclass
class Segment:
    start: Point
    end: Point

    @property
    def length(self) -> float:
        return distance(self.start, self.end)

    @property
    def middle(self) -> Point:
        return Point((self.start.xy + self.end.xy) * 0.5)

    @property
    def angle(self) -> float:
        x1, y1 = self.start.xy
        x2, y2 = self.end.xy
        return np.arctan2(y2 - y1, x2 - x1)

    def draw(
        self,
        thick: float,
        color: pr.Color,
        dashed: tuple[int, pr.Color] | None = None,
        rounded: bool = False,
    ) -> None:  # pragma: no cover
        if dashed:
            prx.draw_dashed_line(self.start.to_vec(), self.end.to_vec(), thick, color, dashed, rounded)
        else:
            prx.draw_line(self.start.to_vec(), self.end.to_vec(), thick, color, rounded)

    def farest_ep(self, p: Point) -> Point:
        return self.end if distance(p, self.start) < distance(p, self.end) else self.start

    def closest_ep(self, p: Point) -> Point:
        return self.start if distance(p, self.start) < distance(p, self.end) else self.end

    def almost(self, other: Segment, eps=0.0001) -> bool:
        return (
            self.start.almost(other.start, eps)
            and self.end.almost(other.end, eps)
            or self.end.almost(other.start, eps)
            and self.start.almost(other.end, eps)
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Segment):
            return NotImplemented
        return (
            self.start == other.start and self.end == other.end or self.end == other.start and self.start == other.end
        )


def distance(p1: Point, p2: Point) -> float:
    return la.norm(p2.xy - p1.xy)


def point_on_segment(p: Point, seg: Segment) -> bool:
    px, py = p.xy
    sx, sy = seg.start.xy
    ex, ey = seg.end.xy

    if not (min(sx, ex) <= px <= max(sx, ex) and min(sy, ey) <= py <= max(sy, ey)):
        return False

    return (ex - sx) * (py - sy) == (ey - sy) * (px - sx)


def point_in_polygon(point: Point, polygon: list[Point], strict: bool = True) -> bool:
    x, y = point.xy
    n = len(polygon)
    inside = False

    p1, (p1x, p1y) = polygon[0], polygon[0].xy
    for i in range(1, n + 1):
        p2, (p2x, p2y) = polygon[i % n], polygon[i % n].xy

        if point_on_segment(point, Segment(p1, p2)):
            inside = not strict
            break

        if min(p1y, p2y) < y <= max(p1y, p2y) and x <= max(p1x, p2x):
            xinters = np.interp((y - p1y) / (p2y - p1y), [0, 1], [p1x, p2x])
            if p1x == p2x or x < xinters:
                inside = not inside
        p1, (p1x, p1y) = p2, (p2x, p2y)

    return inside


def polygon_to_segments(polygon: list[Point], closed: bool = True) -> list[Segment]:
    segments = []
    n = len(polygon)
    p1 = polygon[0]
    for i in range(1, n + 1 if closed else n):
        p2 = polygon[i % n]
        segments.append(Segment(p1, p2))
        p1 = p2
    return segments


def intersect(seg1: Segment, seg2: Segment, strict: bool = True) -> Optional[Point]:
    x = la.intersect_jit(seg1.start.xy, seg1.end.xy, seg2.start.xy, seg2.end.xy, strict)
    return Point(x) if x is not None else None


def distance_point_segment(p: Point, seg: Segment, closest: bool = False) -> float:
    return la.distance_point_segment_jit(p.xy, seg.start.xy, seg.end.xy, closest)


def nearest_point_segment(p: Point, seg: Segment, closest: bool = False) -> Optional[Point]:
    x = la.nearest_point_segment_jit(p.xy, seg.start.xy, seg.end.xy, closest)
    return Point(x) if x is not None else None


def collision_circle_segment(center: Point, radius: float, seg: Segment) -> Optional[npt.NDArray[np.float64]]:
    return la.collision_circle_segment_jit(center.xy, radius, seg.start.xy, seg.end.xy)


def cast_ray_segments(
    position: Point,
    direction: npt.NDArray[np.float64],
    length: float,
    segments: Iterable[Segment],
    ordered: bool = True,
) -> Segment:
    target = Point(length * direction + position.xy)
    ray = Segment(position, target)
    intersect_with_ray = lambda x: intersect(ray, x, False)
    if ordered:
        point = next((x for x in map(intersect_with_ray, segments) if x is not None), target)
    else:
        closest = lambda x: distance(position, x)
        point = min(
            (x for x in map(intersect_with_ray, segments) if x is not None),
            key=closest,
            default=target,
        )
    return Segment(position, point)


def break_segment(seg1: Segment, seg2: Segment) -> list[Segment]:
    p = intersect(seg1, seg2, False)
    if p is not None and not seg2.start.almost(p) and not seg2.end.almost(p):
        return [Segment(seg2.start, p), Segment(p, seg2.end)]
    return [seg2]
