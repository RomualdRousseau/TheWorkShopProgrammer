from taxi_driver_env.game.scenes import gameplay, loading, title, trainer
from taxi_driver_env.render.types import Scene

SCENES = {"title": title, "loading": loading, "gameplay": gameplay, "trainer": trainer}


def first_scene(next: str) -> Scene:
    scene = SCENES[next]
    scene.reset()
    return scene


def next_scene(scene: Scene, next: str) -> Scene:
    if scene != SCENES[next]:
        scene = SCENES[next]
        scene.reset()
    return scene
