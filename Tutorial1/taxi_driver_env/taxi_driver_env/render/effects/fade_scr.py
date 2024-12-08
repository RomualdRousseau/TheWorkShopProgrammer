import pyray as pr
import taxi_driver_env.render.pyrayex as prx
from taxi_driver_env.constants import FRAME_RATE
from taxi_driver_env.math.linalg import EPS, clamp


class FadeScr:
    def __init__(self, duration: float) -> None:
        self.duration = duration

    def get_bound(self) -> pr.Rectangle:
        return prx.SCREEN

    def is_playing(self, latency: float = 0.1) -> bool:
        return self.timer < self.duration + latency

    def reset(self) -> None:
        self.timer = 0.0
        self.snapshot = self._take_screen_snapshot()

    def update(self, dt: float) -> None:
        self.timer = self.timer + min(dt, 1 / FRAME_RATE)

    def draw(self) -> None:
        t = self.timer / (self.duration + EPS)
        alpha = clamp(255 * (1.0 - t), 0, 255)
        if alpha > 0:
            pr.draw_texture(self.snapshot, 0, 0, pr.fade(pr.WHITE, alpha / 255.0))  # type: ignore
        elif self.snapshot is not None:
            pr.unload_texture(self.snapshot)
            self.snapshot = None

    def _take_screen_snapshot(self) -> pr.Texture:
        image = pr.load_image_from_screen()
        texture = pr.load_texture_from_image(image)
        pr.unload_image(image)
        return texture
