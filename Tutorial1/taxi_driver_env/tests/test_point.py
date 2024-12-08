import numpy as np
import pyray as pr
from taxi_driver_env.math.geom import (
    Point,
    Segment,
    distance,
    distance_point_segment,
    nearest_point_segment,
    point_in_polygon,
    point_on_segment,
)
from taxi_driver_env.math.linalg import EPS, lst_2_vec


def test_point_to_vector2():
    a = Point(lst_2_vec([1, 1]))
    assert pr.vector2_equals(a.to_vec(), pr.Vector2(1, 1))


def test_point_hash():
    a = Point(lst_2_vec([1, 1]))
    b = 650
    assert a.__hash__() == b


def test_point_equals():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([1, 1]))
    assert a == b


def test_point_not_equals():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    assert a != b


def test_point_not_equals_different_types():
    a = Point(lst_2_vec([1, 1]))
    assert a != "a string"


def test_point_almost():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([0.9, 0.9]))
    assert a.almost(b, 0.1)


def test_point_not_almost():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([0.9, 0.9]))
    assert not a.almost(b, 0.01)


def test_point_distance():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    assert distance(a, b) == np.sqrt(2)


def test_point_on_segment():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    c = Point(lst_2_vec([1.5, 1.5]))
    e = Segment(a, b)
    assert point_on_segment(c, e)


def test_point_not_on_segment_within_bounding_box():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    c = Point(lst_2_vec([1, 2]))
    e = Segment(a, b)
    assert not point_on_segment(c, e)


def test_point_not_on_segment_out_of_bounding_box():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    c = Point(lst_2_vec([4, 4]))
    e = Segment(a, b)
    assert not point_on_segment(c, e)


def test_point_in_polygon_strict():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 1]))
    c = Point(lst_2_vec([2, 2]))
    d = Point(lst_2_vec([1, 2]))
    x = Point(lst_2_vec([1.5, 1.5]))
    assert point_in_polygon(x, [a, b, c, d])


def test_point_not_in_polygon_strict():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 1]))
    c = Point(lst_2_vec([2, 2]))
    d = Point(lst_2_vec([1, 2]))
    x = Point(lst_2_vec([1, 1.5]))
    assert not point_in_polygon(x, [a, b, c, d])


def test_point_in_polygon_not_strict():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 1]))
    c = Point(lst_2_vec([2, 2]))
    d = Point(lst_2_vec([1, 2]))
    x = Point(lst_2_vec([1, 1.5]))
    assert point_in_polygon(x, [a, b, c, d], False)


def test_point_not_in_polygon_not_strict():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 1]))
    c = Point(lst_2_vec([2, 2]))
    d = Point(lst_2_vec([1, 2]))
    x = Point(lst_2_vec([0, 0]))
    assert not point_in_polygon(x, [a, b, c, d], False)


def test_point_distance_with_segment():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    c = Point(lst_2_vec([1, 2]))
    e = Segment(a, b)
    assert np.allclose(distance_point_segment(c, e), np.sqrt(2) / 2, 0.0, EPS)


def test_point_distance_out_of_segment():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    c = Point(lst_2_vec([0, 0]))
    e = Segment(a, b)
    assert distance_point_segment(c, e) == np.inf


def test_point_distance_out_of_segment_but_non_strict():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    c = Point(lst_2_vec([0, 0]))
    d = Point(lst_2_vec([3, 3]))
    e = Segment(a, b)
    assert distance_point_segment(c, e, True) == np.sqrt(2)
    assert distance_point_segment(d, e, True) == np.sqrt(2)


def test_point_nearest_with_segment():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    c = Point(lst_2_vec([1, 2]))
    e = Segment(a, b)
    x = nearest_point_segment(c, e)
    assert x is not None
    assert x.almost(Point(lst_2_vec([1.5, 1.5])))


def test_point_nearest_out_of_segment():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    c = Point(lst_2_vec([0, 0]))
    e = Segment(a, b)
    assert nearest_point_segment(c, e) is None


def test_point_nearest_out_of_segment_but_non_strict():
    a = Point(lst_2_vec([1, 1]))
    b = Point(lst_2_vec([2, 2]))
    c = Point(lst_2_vec([0, 0]))
    d = Point(lst_2_vec([3, 3]))
    e = Segment(a, b)
    x = nearest_point_segment(c, e, True)
    assert x is not None
    assert x.almost(Point(lst_2_vec([1, 1])))
    x = nearest_point_segment(d, e, True)
    assert x is not None
    assert x.almost(Point(lst_2_vec([2, 2])))
