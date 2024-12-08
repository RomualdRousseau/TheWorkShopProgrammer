import pyray as pr
import taxi_driver_env.render.pyrayex as prx
import taxi_driver_env.resources as res


class Screen:
    def __init__(self, texture_name: str):
        self.texture_name = texture_name

    def get_bound(self) -> pr.Rectangle:
        return prx.SCREEN

    def reset(self) -> None:
        self.surface = res.load_texture(self.texture_name)

    def update(self, _: float) -> None:
        pass

    def draw(self):
        pr.draw_texture_pro(
            self.surface,
            pr.Rectangle(0, 0, self.surface.width, self.surface.height),
            self.get_bound(),
            pr.vector2_zero(),
            0,
            pr.WHITE,  # type: ignore
        )
