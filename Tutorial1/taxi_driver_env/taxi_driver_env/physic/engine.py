import numpy as np
from taxi_driver_env.physic.types import Integrable


def euler_integrate(object: Integrable, forces: np.ndarray, dt: float):
    # Second Newton law

    acc = forces / object.mass

    # Simple Euler integration

    object.vel += acc * dt
    object.pos += object.vel * dt
