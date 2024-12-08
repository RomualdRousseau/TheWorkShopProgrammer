import pyray as pr
from taxi_driver_env.constants import WINDOW_HEIGHT, WINDOW_WIDTH
from taxi_driver_env.game.entities import car

ZOOM_DEFAULT = 20
ZOOM_ACCELERATION_COEF = 0.1


class CameraFollower:
    def __init__(self, acar: car.Car) -> None:
        self.camera = pr.Camera2D(
            pr.Vector2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2),
            acar.curr_pos.to_vec(),
            0,
            ZOOM_DEFAULT,
        )
        self.car = acar

    def set_target(self, acar: car.Car) -> None:
        self.car = acar

    def reset(self) -> None:
        pr.set_mouse_cursor(pr.MouseCursor.MOUSE_CURSOR_ARROW)
        pr.hide_cursor()
        self.camera.zoom = ZOOM_DEFAULT
        self.camera.target = self.car.curr_pos.to_vec()

    def update(self, dt: float) -> None:
        self.camera.target = pr.vector2_lerp(self.camera.target, self.car.curr_pos.to_vec(), 0.2)
        self.camera.zoom = 0.8 * self.camera.zoom + 0.2 * (
            max(
                1,
                ZOOM_DEFAULT - self.car.get_speed_in_kmh() * ZOOM_ACCELERATION_COEF,
            )
        )

    def draw(self) -> None:
        pass
