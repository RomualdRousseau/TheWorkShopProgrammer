import pyray as pr
from taxi_driver_env.constants import FRAME_RATE
from taxi_driver_env.math.linalg import EPS
from taxi_driver_env.render.types import Widget


class OpenHorizontal:
    def __init__(self, widget: Widget, duration: float, color: pr.Color):
        self.duration = duration
        self.widget = widget
        self.color = color

    def get_bound(self) -> pr.Rectangle:
        t = self.timer / (self.duration + EPS)
        width = int(pr.clamp(self.widget.get_bound().width * t, 0, self.widget.get_bound().width))
        return pr.Rectangle(
            self.widget.get_bound().x + (self.widget.get_bound().width - width) / 2,
            self.widget.get_bound().y,
            width,
            self.widget.get_bound().height,
        )

    def is_playing(self, latency: float = 0.1) -> bool:
        return self.timer < self.duration + latency

    def reset(self) -> None:
        self.timer = 0.0

    def update(self, dt: float):
        self.timer = self.timer + min(dt, 1 / FRAME_RATE)
        if not self.is_playing():
            self.widget.update(dt)

    def draw(self):
        if not self.is_playing():
            self.widget.draw()
        else:
            bound = self.get_bound()
            if bound.width > 0:
                pr.draw_rectangle_rec(bound, self.color)
