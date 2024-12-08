from typing import Optional

import numpy as np
import numpy.typing as npt
from numba import njit

EPS = 1e-7


def lst_2_vec(a: npt.ArrayLike) -> npt.NDArray[np.float64]:
    return np.array(a, dtype=np.float64)


def clamp(n: float, minn: float, maxn: float) -> float:
    return max(min(maxn, n), minn)


@njit
def det(a: npt.ArrayLike) -> float:
    return np.linalg.det(np.array(a))


@njit
def norm(v: npt.NDArray[np.float64]) -> float:
    return np.sqrt(np.sum(v**2))


@njit
def normalize(v: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    return v / (norm(v) + EPS)


@njit(cache=True)
def intersect_jit(
    a: npt.NDArray[np.float64],
    b: npt.NDArray[np.float64],
    c: npt.NDArray[np.float64],
    d: npt.NDArray[np.float64],
    strict: bool = True,
) -> Optional[npt.NDArray[np.float64]]:
    x1, y1 = a
    x2, y2 = b
    x3, y3 = c
    x4, y4 = d
    atol = -EPS if strict else 0
    match det([[x1 - x2, y1 - y2], [x3 - x4, y3 - y4]]):
        case dd if dd != 0:
            match -det([[x1 - x2, y1 - y2], [x1 - x3, y1 - y3]]) / dd:
                case u if abs(u - 0.5) <= (atol + 0.5):
                    match det([[x1 - x3, y1 - y3], [x3 - x4, y3 - y4]]) / dd:
                        case t if abs(t - 0.5) <= (atol + 0.5):
                            return np.array(
                                [
                                    np.interp(t, [0, 1], [x1, x2]),
                                    np.interp(t, [0, 1], [y1, y2]),
                                ]
                            )
    return None


@njit
def distance_point_segment_jit(
    p: npt.NDArray[np.float64],
    a: npt.NDArray[np.float64],
    b: npt.NDArray[np.float64],
    closest: bool = False,
) -> float:
    u = p - a
    v = b - a
    v_l = norm(v)
    v = v / (v_l + EPS)
    x = float(np.dot(u, v))
    if x < 0:
        return norm(a - p) if closest else np.inf
    elif x > v_l:
        return norm(b - p) if closest else np.inf
    else:
        return norm(a + v * x - p)


@njit
def nearest_point_segment_jit(
    p: npt.NDArray[np.float64],
    a: npt.NDArray[np.float64],
    b: npt.NDArray[np.float64],
    closest: bool = False,
) -> Optional[npt.NDArray[np.float64]]:
    u = p - a
    v = b - a
    v_l = norm(v)
    v = v / (v_l + EPS)
    x = float(np.dot(u, v))
    if x < 0:
        return a if closest else None
    elif x > v_l:
        return b if closest else None
    else:
        return a + v * x


@njit
def collision_circle_segment_jit(
    center: npt.NDArray[np.float64],
    radius: float,
    a: npt.NDArray[np.float64],
    b: npt.NDArray[np.float64],
) -> Optional[npt.NDArray[np.float64]]:
    x = nearest_point_segment_jit(center, a, b, True)
    if x is not None:
        w = center - x
        w_l = norm(w)
        if w_l <= radius:
            return w * (radius - w_l + EPS) / (w_l + EPS)
    return None


def compile_all_jits():
    normalize(np.zeros(2))
    intersect_jit(np.zeros(2), np.zeros(2), np.zeros(2), np.zeros(2), False)
    collision_circle_segment_jit(np.zeros(2), 0.0, np.zeros(2), np.zeros(2))


compile_all_jits()
