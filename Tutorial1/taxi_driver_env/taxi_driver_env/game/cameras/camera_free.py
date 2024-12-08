import pyray as pr
from taxi_driver_env.constants import WINDOW_HEIGHT, WINDOW_WIDTH
from taxi_driver_env.math.geom import Point

ZOOM_DEFAULT = 20
ZOOM_ACCELERATION_COEF = 0.1


class CameraFree:
    def __init__(self, initial_position: Point) -> None:
        self.camera = pr.Camera2D(
            pr.Vector2(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2),
            initial_position.to_vec(),
            0,
            ZOOM_DEFAULT,
        )

    def reset(self) -> None:
        pr.set_mouse_cursor(pr.MouseCursor.MOUSE_CURSOR_RESIZE_ALL)
        pr.show_cursor()
        self.camera.zoom = ZOOM_DEFAULT

    def update(self, dt: float) -> None:
        if pr.is_mouse_button_down(pr.MouseButton.MOUSE_BUTTON_LEFT):
            self.camera.target = pr.vector2_lerp(
                self.camera.target,
                pr.vector2_subtract(self.camera.target, pr.get_mouse_delta()),
                0.2,
            )
        self.camera.zoom = max(1, self.camera.zoom + pr.get_mouse_wheel_move() * 0.5)

    def draw(self) -> None:
        pass
