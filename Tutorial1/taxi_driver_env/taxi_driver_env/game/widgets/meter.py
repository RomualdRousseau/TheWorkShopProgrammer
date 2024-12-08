import pyray as pr
import taxi_driver_env.render.pyrayex as prx
import taxi_driver_env.resources as res
from taxi_driver_env.constants import WINDOW_HEIGHT, WINDOW_WIDTH
from taxi_driver_env.game.entities.taxi_driver import TaxiDriver

BORDER = 0.01 * WINDOW_WIDTH
BOUND_WIDTH = 0.128 * WINDOW_WIDTH
BOUND_HEIGHT = 0.088 * WINDOW_HEIGHT
LCD_OFFX = 0.018 * WINDOW_WIDTH
LCD_OFFY = 0.040 * WINDOW_HEIGHT
FONT_SIZE = 0.025 * WINDOW_WIDTH
FONT_COLOR = pr.Color(51, 51, 49, 255)


class Meter:
    def __init__(self, player: TaxiDriver) -> None:
        self.player = player

    def get_bound(self) -> pr.Rectangle:
        return pr.Rectangle(
            BORDER,
            BORDER,
            BOUND_WIDTH,
            BOUND_HEIGHT,
        )

    def reset(self) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self) -> None:
        tex = res.load_texture("spritesheet")
        pr.draw_texture_pro(
            tex,
            pr.Rectangle(640, 256, 128, 88),
            self.get_bound(),
            pr.Vector2(0, 0),
            0,
            pr.WHITE,
        )

        pos = pr.Vector2(BORDER + LCD_OFFX, BORDER + LCD_OFFY)
        font = res.load_font("mono", int(FONT_SIZE))
        prx.draw_text("$000000", pos, int(FONT_SIZE), pr.color_alpha(FONT_COLOR, 0.1), font=font)
        prx.draw_text(f"${self.player.money:-6}", pos, int(FONT_SIZE), FONT_COLOR, font=font)
