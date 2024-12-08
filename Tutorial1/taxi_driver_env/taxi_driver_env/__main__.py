import random

import numpy as np
import pyray as pr

import taxi_driver_env.render.pyrayex as prx
from taxi_driver_env.constants import (
    APP_NAME,
    FRAME_RATE,
    GAME_SEED,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from taxi_driver_env.game.scenes import first_scene, next_scene


def main():
    random.seed(GAME_SEED)
    np.random.seed(GAME_SEED)

    pr.set_config_flags(pr.ConfigFlags.FLAG_MSAA_4X_HINT)
    pr.init_window(WINDOW_WIDTH, WINDOW_HEIGHT, APP_NAME)
    pr.set_target_fps(FRAME_RATE)
    pr.hide_cursor()
    pr.init_audio_device()
    prx.init_gamepad()

    scene = first_scene("title")

    while not pr.window_should_close():
        next = scene.update(pr.get_frame_time())
        pr.begin_drawing()
        scene.draw()
        pr.end_drawing()
        scene = next_scene(scene, next)

    pr.close_window()


if __name__ == "__main__":
    main()
