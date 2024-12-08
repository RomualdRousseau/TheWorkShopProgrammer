import pyray as pr

BORDER = 20
ZOOM_RATE = 0.001


class CameraZoomer:
    def __init__(self, map_width: float, map_height: float, tex_width: float, tex_height: float) -> None:
        self.width = map_width
        self.height = map_height
        self.scale = pr.Vector2(map_width / tex_width, map_height / tex_height)
        self.camera = pr.Camera2D(
            pr.Vector2(tex_width // 2, tex_height // 2),
            pr.vector2_zero(),
            0,
            1,
        )

    def set_bound(self, bound: pr.Rectangle) -> None:
        self.bound = bound

    def reset(self) -> None:
        self.camera.target = pr.vector2_zero()
        self.camera.zoom = 1

    def update(self, dt: float) -> None:
        target = pr.Vector2(self.bound.x + self.bound.width // 2, self.bound.y + self.bound.height // 2)
        self.camera.target = pr.vector2_lerp(self.camera.target, target, 0.2)

        tl = self._to_screen_2d(
            pr.Vector2(
                self.bound.x - BORDER,
                self.bound.y - BORDER,
            )
        )
        br = self._to_screen_2d(
            pr.Vector2(
                self.bound.x + self.bound.width + BORDER,
                self.bound.y + self.bound.height + BORDER,
            )
        )
        self.camera.zoom += ZOOM_RATE * min(tl.x, self.width - br.x, tl.y, self.height - br.y)

    def draw(self) -> None:
        pass

    def _to_screen_2d(self, v: pr.Vector2) -> pr.Vector2:
        return pr.vector2_multiply(
            pr.get_world_to_screen_2d(v, self.camera),
            self.scale,
        )
