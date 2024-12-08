import numpy as np
from taxi_driver_env.math.geom import (
    Point,
    Segment,
    break_segment,
    cast_ray_segments,
    collision_circle_segment,
    intersect,
    polygon_to_segments,
)
from taxi_driver_env.math.linalg import lst_2_vec


def test_segment_not_equals_different_types():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    e = Segment(a, b)
    assert e != "a string"


def test_segment_length():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    e = Segment(a, b)
    assert e.length == np.sqrt(2)


def test_segment_middle():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    e = Segment(a, b)
    assert e.middle == Point(lst_2_vec([1.5, 1.5]))


def test_segment_angle():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    e = Segment(a, b)
    assert e.angle == np.pi / 4


def test_segment_farest_ep():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    c = Point(lst_2_vec([1.1, 1.1]))
    d = Point(lst_2_vec([1.9, 1.9]))
    e = Segment(a, b)
    assert e.farest_ep(c) == b
    assert e.farest_ep(d) == a


def test_segment_closest_ep():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    c = Point(lst_2_vec([1.1, 1.1]))
    d = Point(lst_2_vec([1.9, 1.9]))
    e = Segment(a, b)
    assert e.closest_ep(c) == a
    assert e.closest_ep(d) == b


def test_segment_almost():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    c = Point(lst_2_vec([2.01, 2.01]))
    e = Segment(a, b)
    f = Segment(a, c)
    assert e.almost(f, 0.5)


def test_segment_not_almost():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    c = Point(lst_2_vec([2.6, 2.6]))
    e = Segment(a, b)
    f = Segment(a, c)
    assert not e.almost(f, 0.5)


def test_segments_equals():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    e1 = Segment(a, b)
    e2 = Segment(a, b)
    assert e1 == Segment(a, b)
    assert e2 == Segment(a, b)
    assert e1 == e2


def test_segments_not_equals():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    c = Point(lst_2_vec([3, 3]))
    e1 = Segment(a, b)
    e2 = Segment(a, c)
    assert e1 == Segment(a, b)
    assert e2 == Segment(a, c)
    assert e1 != e2


def test_segments_non_directed():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    e1 = Segment(a, b)
    e2 = Segment(b, a)
    assert e1 == Segment(a, b)
    assert e2 == Segment(b, a)
    assert e1 == e2


def test_intersect():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([3, 3]))
    c = Point(lst_2_vec([1, 3]))
    d = Point(lst_2_vec([3, 1]))
    e1 = Segment(a, b)
    e2 = Segment(c, d)
    p = intersect(e1, e2)
    assert p and p.almost(Point(lst_2_vec([2, 2])))
    p = intersect(e2, e1)
    assert p and p.almost(Point(lst_2_vec([2, 2])))


def test_intersect_horiz():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([3, 3]))
    c = Point(lst_2_vec([1, 2]))
    d = Point(lst_2_vec([3, 2]))
    e1 = Segment(a, b)
    e2 = Segment(c, d)
    p = intersect(e1, e2)
    assert p and p.almost(Point(lst_2_vec([2, 2])))
    p = intersect(e2, e1)
    assert p and p.almost(Point(lst_2_vec([2, 2])))


def test_intersect_verti():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([3, 3]))
    c = Point(lst_2_vec([2, 3]))
    d = Point(lst_2_vec([2, 1]))
    e1 = Segment(a, b)
    e2 = Segment(c, d)
    p = intersect(e1, e2)
    assert p and p.almost(Point(lst_2_vec([2, 2])))
    p = intersect(e2, e1)
    assert p and p.almost(Point(lst_2_vec([2, 2])))


def test_intersect_parallel():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([3, 3]))
    c = Point(lst_2_vec([1, 2]))
    d = Point(lst_2_vec([3, 4]))
    e1 = Segment(a, b)
    e2 = Segment(c, d)
    p = intersect(e1, e2)
    assert p is None
    p = intersect(e2, e1)
    assert p is None


def test_not_intersect():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([3, 3]))
    c = Point(lst_2_vec([4, 5]))
    d = Point(lst_2_vec([5, 3]))
    e1 = Segment(a, b)
    e2 = Segment(c, d)
    p = intersect(e1, e2)
    assert p is None
    p = intersect(e2, e1)
    assert p is None


def test_segment_collision_circle():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([3, 3]))
    c = Point(lst_2_vec([1, 3]))
    e = Segment(a, b)
    assert collision_circle_segment(c, 3, e) is not None


def test_segment_not_collision_circle():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([3, 3]))
    x = Point(lst_2_vec([1, 3]))
    e = Segment(a, b)
    assert collision_circle_segment(x, 1, e) is None


def test_cast_ray_segments_intersect():
    n = lst_2_vec([1, -1]) / np.sqrt(2)
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    c = Point(lst_2_vec([1, 2]))
    d = Point(lst_2_vec([2, 0]))
    e = Point(lst_2_vec([6, 4]))
    x = Point(lst_2_vec([1.5, 1.5]))
    e1 = Segment(a, b)
    e2 = Segment(d, e)
    assert cast_ray_segments(c, n, 2, [e1, e2]) == Segment(c, x)
    assert cast_ray_segments(c, n, 2, [e1, e2], ordered=False) == Segment(c, x)


def test_cast_ray_segments_not_intersect():
    n = lst_2_vec([-1, 0])
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    c = Point(lst_2_vec([1, 2]))
    x = Point(lst_2_vec([-1, 2]))
    e = Segment(a, b)
    assert cast_ray_segments(c, n, 2, [e]) == Segment(c, x)
    assert cast_ray_segments(c, n, 2, [e], ordered=False) == Segment(c, x)


def test_polygon_to_segments_closed():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 1]))
    c = Point(lst_2_vec([2, 2]))
    d = Point(lst_2_vec([1, 2]))
    assert polygon_to_segments([a, b, c, d]) == [
        Segment(a, b),
        Segment(b, c),
        Segment(c, d),
        Segment(d, a),
    ]


def test_polygon_to_segments_not_closed():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 1]))
    c = Point(lst_2_vec([2, 2]))
    d = Point(lst_2_vec([1, 2]))
    assert polygon_to_segments([a, b, c, d], False) == [
        Segment(a, b),
        Segment(b, c),
        Segment(c, d),
    ]


def test_segment_break():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 1]))
    c = Point(lst_2_vec([2, 2]))
    d = Point(lst_2_vec([1, 2]))
    x = Point(lst_2_vec([1.5, 1.5]))
    e1 = Segment(a, c)
    e2 = Segment(b, d)
    assert break_segment(e1, e2) == [
        Segment(b, x),
        Segment(x, d),
    ]


def test_segment_not_break():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 1]))
    c = Point(lst_2_vec([0, 0]))
    d = Point(lst_2_vec([1, 2]))
    e1 = Segment(a, c)
    e2 = Segment(b, d)
    assert break_segment(e1, e2) == [e2]
