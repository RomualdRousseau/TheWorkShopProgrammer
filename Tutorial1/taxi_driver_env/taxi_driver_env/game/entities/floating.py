import pyray as pr
from taxi_driver_env.math.geom import Point
from taxi_driver_env.math.linalg import lst_2_vec

COLOR = pr.Color(255, 255, 255, 255)
SPEED = -60.0  # m.s-1
MAX_LIFE = 120
FONT_SIZE = 20


class Floating:
    def __init__(self, pos: Point, camera: pr.Camera2D, text: str) -> None:
        xy = pr.get_world_to_screen_2d(pos.to_vec(), camera)
        self.pos = lst_2_vec([xy.x, xy.y])
        self.vel = lst_2_vec([0.0, SPEED])
        self.text = text
        self.life = MAX_LIFE

    def is_alive(self) -> bool:
        return self.life > 0

    def reset(self) -> None:
        self.life = MAX_LIFE

    def hit(self, damage: int) -> None:
        pass

    def update(self, dt: float) -> None:
        self.pos = self.pos + self.vel * dt
        self.life = max(0, self.life - 1)

    def draw(self, layer: int = 1) -> None:
        if layer != 1:
            return

        pr.draw_text(
            self.text,
            int(self.pos[0]),
            int(self.pos[1]),
            FONT_SIZE,
            pr.color_alpha(COLOR, (self.life / MAX_LIFE) * (COLOR.a / 256)),
        )
