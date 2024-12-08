import numpy as np
from taxi_driver_env.math.linalg import EPS, lst_2_vec, normalize


def test_normalize():
    a = lst_2_vec([1, 1])
    b = lst_2_vec([np.cos(np.pi / 4), np.sin(np.pi / 4)])
    assert np.allclose(normalize(a), b, 0.0, EPS)
