from dataclasses import dataclass
from functools import lru_cache

import pyray as pr
import taxi_driver_env.resources as res
from taxi_driver_env.render.effects.fade_inout import FadeInOut
from taxi_driver_env.render.widgets.screen import Screen

WAIT_TIME = 5  # s


@dataclass
class Context:
    state: int
    timer: float
    screen: Screen
    fade_out: FadeInOut


@lru_cache(1)
def get_singleton(name: str = "default") -> Context:
    return Context(0, 0.0, Screen("title"), FadeInOut(255, 0, 1, pr.WHITE))  # type: ignore


def reset() -> None:
    res.clear_caches()
    ctx = get_singleton()
    ctx.state = 0
    ctx.timer = 0.0
    ctx.screen.reset()
    ctx.fade_out.reset()


def update(dt: float) -> str:
    ctx = get_singleton()
    match ctx.state:
        case 0:
            ctx.timer += dt
            if pr.get_key_pressed() != 0 or ctx.timer > WAIT_TIME:
                ctx.state = 1
            return "title"

        case 1:
            ctx.fade_out.update(dt)
            if not ctx.fade_out.is_playing():
                ctx.state = 2
            return "title"

        case 2:
            return "loading"

        case _:
            return "title"


def draw() -> None:
    ctx = get_singleton()
    ctx.screen.draw()
    if ctx.state in (1, 2):
        ctx.fade_out.draw()
