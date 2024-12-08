import pyray as pr
import taxi_driver_env.resources as res
from taxi_driver_env.constants import WINDOW_HEIGHT, WINDOW_WIDTH
from taxi_driver_env.game.cameras.camera_zoomer import CameraZoomer
from taxi_driver_env.game.entities import world
from taxi_driver_env.game.entities.taxi_driver import TaxiDriver

BORDER = 0.01 * WINDOW_WIDTH
BOUND_WIDTH = 0.128 * WINDOW_WIDTH
BOUND_HEIGHT = 0.256 * WINDOW_HEIGHT
MAP_WIDTH = 0.109 * WINDOW_WIDTH
MAP_HEIGHT = 0.199 * WINDOW_HEIGHT
MAP_RATIO = MAP_WIDTH / MAP_HEIGHT


class Minimap:
    def __init__(self, player: TaxiDriver) -> None:
        self.player = player

    def get_bound(self) -> pr.Rectangle:
        return pr.Rectangle(
            WINDOW_WIDTH - (BOUND_WIDTH + BORDER),
            WINDOW_HEIGHT - (BOUND_HEIGHT + BORDER),
            BOUND_WIDTH,
            BOUND_HEIGHT,
        )

    def get_map_bound(self) -> pr.Rectangle:
        return pr.Rectangle(
            WINDOW_WIDTH - BOUND_WIDTH // 2 - BORDER - MAP_WIDTH // 2 - 1,
            WINDOW_HEIGHT - BOUND_HEIGHT // 2 - BORDER - MAP_HEIGHT // 2 - 1,
            MAP_WIDTH,
            MAP_HEIGHT,
        )

    def get_corridor_bound(self) -> pr.Rectangle:
        x1 = int(min((p.xy[0] for p in self.player.car.corridor.points)))
        y1 = int(min((p.xy[1] for p in self.player.car.corridor.points)))
        x2 = int(max((p.xy[0] for p in self.player.car.corridor.points)))
        y2 = int(max((p.xy[1] for p in self.player.car.corridor.points)))
        return pr.Rectangle(x1, y1, x2 - x1, y2 - y1)

    def reset(self) -> None:
        self.frame_buffer = pr.load_render_texture(int(WINDOW_WIDTH * MAP_RATIO), WINDOW_HEIGHT)
        self.camera = CameraZoomer(
            self.get_map_bound().width,
            self.get_map_bound().height,
            self.frame_buffer.texture.width,
            self.frame_buffer.texture.height,
        )

    def update(self, dt: float) -> None:
        self.camera.set_bound(self.get_corridor_bound())
        self.camera.update(dt)

    def draw(self) -> None:
        pr.begin_texture_mode(self.frame_buffer)
        pr.clear_background(pr.WHITE)
        pr.begin_mode_2d(self.camera.camera)

        for bone in world.get_singleton().borders.skeleton:
            bone.draw(5, pr.GRAY)

        for bone in self.player.car.corridor.skeleton:
            bone.draw(10, pr.BLUE)

        self.player.car.curr_pos.draw(15, pr.YELLOW)

        pr.end_mode_2d()
        pr.end_texture_mode()

        tex = self.frame_buffer.texture
        pr.draw_texture_pro(
            tex,
            pr.Rectangle(0, 0, tex.width, -tex.height),
            self.get_map_bound(),
            pr.Vector2(0, 0),
            0,
            pr.WHITE,
        )

        tex = res.load_texture("spritesheet")
        pr.draw_texture_pro(
            tex,
            pr.Rectangle(512, 256, 128, 256),
            self.get_bound(),
            pr.Vector2(0, 0),
            0,
            pr.WHITE,
        )
