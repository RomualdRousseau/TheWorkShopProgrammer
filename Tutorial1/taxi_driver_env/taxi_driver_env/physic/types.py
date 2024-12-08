from typing import Protocol

import numpy as np


class Integrable(Protocol):
    pos: np.ndarray
    vel: np.ndarray
    head: np.ndarray
    mass: float


class Entity(Protocol):
    def is_alive(self) -> bool: ...

    def hit(self, damage: int) -> None: ...

    def reset(self) -> None: ...

    def update(self, dt: float) -> None: ...

    def draw(self, layer: int = 1) -> None: ...
