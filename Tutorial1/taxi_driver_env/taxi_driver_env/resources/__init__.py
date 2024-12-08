from functools import cache
from importlib import resources as impresources
from typing import Callable

import pyray as pr

import taxi_driver_env.resources as res

RESOURCES = {
    "title": "screens/title.png",
    "loading": "screens/loading.png",
    "accept": "screens/dropoff.png",
    "pickup": "screens/dropoff.png",
    "dropoff": "screens/dropoff.png",
    "spritesheet": "sprites/spritesheet.png",
    "klaxon": "sounds/klaxon.ogg",
    "crash": "sounds/crash.ogg",
    "mono": "fonts/GelatinMono.ttf",
}

_gc: list[Callable[[], None]] = []


def clear_caches():
    [x() or True for x in _gc]
    load_texture.cache_clear()
    load_sound.cache_clear()
    load_font.cache_clear()


@cache
def load_texture(name: str) -> pr.Texture:
    texture = pr.load_texture(str(impresources.files(res) / RESOURCES[name]))
    _gc.append(lambda: pr.unload_texture(texture))
    return texture


@cache
def load_sound(name: str) -> pr.Sound:
    sound = pr.load_sound(str(impresources.files(res) / RESOURCES[name]))
    _gc.append(lambda: pr.unload_sound(sound))
    return sound


@cache
def load_font(name: str, size: int = 20) -> pr.Font:
    font = pr.load_font_ex(str(impresources.files(res) / RESOURCES[name]), size, None, 0)
    _gc.append(lambda: pr.unload_font(font))
    return font
