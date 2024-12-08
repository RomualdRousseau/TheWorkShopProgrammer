from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from functools import lru_cache

import pyray as pr
from taxi_driver_env.constants import WINDOW_HEIGHT
from taxi_driver_env.game.entities import world


@dataclass
class Context:
    executor = ThreadPoolExecutor(max_workers=1)
    progress = 0.0
    done = False


@lru_cache(1)
def get_singleton(name: str = "default") -> Context:
    return Context()


def reset() -> None:
    ctx = get_singleton()

    def progress_callback(progress: float) -> None:
        ctx.progress = progress

    def done_callback(_: Future) -> None:
        ctx.done = True

    world.add_progress_callback(progress_callback)
    ctx.executor.submit(world.get_singleton).add_done_callback(done_callback)


def update(_: float) -> str:
    ctx = get_singleton()
    return "gameplay" if ctx.done else "loading"


def draw() -> None:
    pr.clear_background(pr.WHITE)  # type: ignore
    pr.draw_rectangle_lines(100, WINDOW_HEIGHT // 2, (WINDOW_HEIGHT - 200) + 4, 14, pr.BLACK)  # type: ignore
    pr.draw_rectangle(102, WINDOW_HEIGHT // 2 + 2, int(get_singleton().progress * (WINDOW_HEIGHT - 200)), 10, pr.BLACK)  # type: ignore
