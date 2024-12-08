import random
from dataclasses import dataclass
from functools import lru_cache, reduce
from typing import Any, Callable, Iterable

import numpy as np
from taxi_driver_env.constants import VIRTUAL_WIDTH
from taxi_driver_env.math import graph
from taxi_driver_env.math.geom import (
    Point,
    Segment,
    break_segment,
    distance,
    distance_point_segment,
    nearest_point_segment,
    point_in_polygon,
    polygon_to_segments,
)
from taxi_driver_env.math.linalg import lst_2_vec, normalize
from tqdm import tqdm, trange

Location = tuple[Segment, Point]
ProgressCallBack = Callable[[float], None]


@dataclass
class Envelope:
    segments: list[Segment]
    skeleton: list[Segment]
    width: int

    @property
    def points(self) -> list[Point]:
        return [s.start for s in self.segments]

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Envelope):
            return NotImplemented
        return self is other

    def __hash__(self) -> int:
        return id(self)

    def get_nearest_location(self, position: Point) -> Location:
        nearest_location = lambda x: (x, nearest_point_segment(position, x, True))
        closest_distance = lambda x: distance(position, x[1])
        location = min(map(nearest_location, self.skeleton), key=closest_distance)
        return location  # type: ignore

    def get_random_location(self) -> Location:
        s = random.choice(self.skeleton)
        t = random.random()
        return s, Point(s.start.xy * (1 - t) + s.end.xy * t)


@lru_cache(256)
def get_nearest_segments(envelope: Envelope, position: Point, radius: int) -> list[Segment]:
    radius = max(radius, VIRTUAL_WIDTH)
    nearest_distance = lambda x: distance_point_segment(position, x, True)
    return sorted(
        (x for x in envelope.segments if nearest_distance(x) < radius),
        key=nearest_distance,
    )


def generare_borders_from_spatial_graph(
    agraph: graph.SpatialGraph, width: int, progress_callbacks: list[ProgressCallBack]
) -> tuple[Envelope, list[Point]]:
    with tqdm(
        total=4,
        desc="Generating envelope",
        ncols=80,
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
    ) as pbar:
        envelopes = [_generate_envelope(e, width) for e in agraph.edges]
        _pbar_update_and_call(pbar, progress_callbacks)
        anchors = _generate_anchors(envelopes)
        _pbar_update_and_call(pbar, progress_callbacks)
        envelopes = _break_envelopes(envelopes)
        _pbar_update_and_call(pbar, progress_callbacks)
        envelope = _union_envelopes(envelopes)
        _pbar_update_and_call(pbar, progress_callbacks)
    return envelope, anchors


def generare_corridor_from_spatial_graph(
    agraph: graph.SpatialGraph, width: int, progress_callbacks: list[ProgressCallBack]
) -> Envelope:
    with tqdm(
        total=3,
        desc="Generating envelope",
        ncols=80,
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
    ) as pbar:
        envelopes = [_generate_envelope(e, width) for e in agraph.edges]
        _pbar_update_and_call(pbar, progress_callbacks)
        envelopes = _break_envelopes(envelopes)
        _pbar_update_and_call(pbar, progress_callbacks)
        envelope = _union_envelopes(envelopes)
        _pbar_update_and_call(pbar, progress_callbacks)
    return envelope


def _generate_envelope(edge: graph.SpatialEdge, width: int, slices: int = 10) -> Envelope:
    x1, y1 = edge.start.point.xy
    x2, y2 = edge.end.point.xy
    vx, vy = normalize(lst_2_vec([x2 - x1, y2 - y1]))

    points = []
    points.append(Point(lst_2_vec([x1 - vy * width * 0.5, y1 + vx * width * 0.5])))
    points.append(Point(lst_2_vec([x2 - vy * width * 0.5, y2 + vx * width * 0.5])))

    b = np.arctan2(vx, -vy)
    for i in range(slices):
        a = b - np.pi * i / slices
        c, s = np.cos(a), np.sin(a)
        points.append(Point(lst_2_vec([x2 + c * width * 0.5, y2 + s * width * 0.5])))

    points.append(Point(lst_2_vec([x2 + vy * width * 0.5, y2 - vx * width * 0.5])))
    points.append(Point(lst_2_vec([x1 + vy * width * 0.5, y1 - vx * width * 0.5])))

    b = np.arctan2(-vx, vy)
    for i in range(slices):
        a = b - np.pi * i / slices
        c, s = np.cos(a), np.sin(a)
        points.append(Point(lst_2_vec([x1 + c * width * 0.5, y1 + s * width * 0.5])))

    segments = polygon_to_segments(points)

    return Envelope(segments, [edge.segment], width)


def _generate_anchors(envelopes: list[Envelope], step: int = 20):
    def anchors() -> Iterable[Point]:
        for i in range(-VIRTUAL_WIDTH, VIRTUAL_WIDTH + 1, step):
            for j in range(-VIRTUAL_WIDTH, VIRTUAL_WIDTH + 1, step):
                yield Point(lst_2_vec([j, i]))

    anchor_in_polygon = lambda x, y: point_in_polygon(x, y.points)
    anchor_in_polygons = lambda x: not any((anchor_in_polygon(x, y) for y in envelopes))
    return [x for x in anchors() if anchor_in_polygons(x)]


def _break_envelopes(envelopes: list[Envelope]) -> list[Envelope]:
    def break_envelope(e: Envelope, s: Segment) -> Envelope:
        segments: list[Segment] = reduce(lambda a, x: [*a, *x], (break_segment(s, x) for x in e.segments), [])
        return Envelope(segments, e.skeleton, e.width)

    def break_two_envelopes(e1: Envelope, e2: Envelope) -> tuple[Envelope, Envelope]:
        return (
            reduce(break_envelope, e2.segments, e1),
            reduce(break_envelope, e1.segments, e2),
        )

    result = envelopes
    n = len(envelopes)

    for i in trange(n, desc="Break", ncols=80, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}"):
        head, acc = result[i], []
        for j in range(i + 1, n):
            head, tail = break_two_envelopes(head, result[j])
            acc.append(tail)
        result = [*result[:i], head, *acc]
    return result


def _union_envelopes(envelopes: list[Envelope]) -> Envelope:
    segments_to_keep: list[Segment] = []
    skeleton = [e.skeleton[0] for e in envelopes]
    width = envelopes[0].width

    segment_in_polygon = lambda y: lambda x: point_in_polygon(y.middle, x.points)

    for e in tqdm(
        envelopes,
        desc="Union",
        ncols=80,
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
    ):
        for s in e.segments:
            inside = any(
                map(
                    segment_in_polygon(s),
                    filter(lambda x: x != e, envelopes),
                )
            )
            if not (inside or s.start.almost(s.end) or any((x.almost(s) for x in segments_to_keep))):
                segments_to_keep.append(s)

    return Envelope(segments_to_keep, skeleton, width)


def _pbar_update_and_call(pbar: tqdm, progress_callbacks: list[ProgressCallBack]):
    pbar.update(1)
    for progress_callback in progress_callbacks:
        progress_callback(pbar.n / pbar.total)
