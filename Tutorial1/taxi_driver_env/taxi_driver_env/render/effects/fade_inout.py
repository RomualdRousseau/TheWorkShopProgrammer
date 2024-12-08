import pyray as pr
import taxi_driver_env.render.pyrayex as prx
from taxi_driver_env.constants import FRAME_RATE
from taxi_driver_env.math.linalg import EPS, clamp


class FadeInOut:
    def __init__(self, min: int, max: int, duration: float, color: pr.Color) -> None:
        self.duration = duration
        self.timer = 0.0
        self.min = min
        self.max = max
        self.color = color

    def get_bound(self) -> pr.Rectangle:
        return prx.SCREEN

    def is_playing(self, latency: float = 0.1) -> bool:
        return self.timer < self.duration + latency

    def reset(self) -> None:
        self.timer = 0.0

    def update(self, dt: float) -> None:
        self.timer = self.timer + min(dt, 1 / FRAME_RATE)

    def draw(self) -> None:
        t = self.timer / (self.duration + EPS)
        alpha = float(clamp(self.max * (1.0 - t) + self.min * t, 0, 255))
        if alpha > 0:
            pr.draw_rectangle_rec(self.get_bound(), pr.fade(self.color, alpha / 255.0))
