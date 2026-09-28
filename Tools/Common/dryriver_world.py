# Southern Spear - Dry River world ground height, inside and beyond the playable terrain.
#
# Shared by Tools/Blender/dryriver_skirt.py (builds the outer ground mesh) and Tools/Unreal/expand_dryriver.py
# (places scatter on it). Inside the 260 x 180 m playable rectangle it is exactly terrain_height() of
# dryriver_spec.py; outside it blends into rolling hills and a distant rim. Metres, Blender axes
# (Unreal = x*100, -y*100, z*100).

import math

from dryriver_spec import PLAY_DEPTH, PLAY_WIDTH, terrain_height


# Session 041: the playable area grows past the 260 x 180 m terrain onto the skirt's dense 2.5 m band (it extends
# 60 m out, and the hills only start to rise ~40 m out), giving 340 x 240 m. Boundary volumes and the nav volume
# follow these numbers (Tools/Unreal/expand_dryriver.py).
PLAY_PAD_X, PLAY_PAD_Y = 40.0, 30.0
PLAY_HALF_X, PLAY_HALF_Y = PLAY_WIDTH / 2.0 + PLAY_PAD_X, PLAY_DEPTH / 2.0 + PLAY_PAD_Y


def outside_playable(x, y):
    """Metres outside the expanded playable rectangle (0 inside)."""
    return math.hypot(max(0.0, abs(x) - PLAY_HALF_X), max(0.0, abs(y) - PLAY_HALF_Y))


def outside_distance(x, y):
    """Metres outside the playable rectangle (0 inside)."""
    return math.hypot(max(0.0, abs(x) - PLAY_WIDTH / 2.0), max(0.0, abs(y) - PLAY_DEPTH / 2.0))


def smoothstep(a, b, v):
    t = max(0.0, min(1.0, (v - a) / (b - a)))
    return t * t * (3 - 2 * t)


def hills(x, y):
    # Deterministic layered sines at unrelated frequencies: low rolling country.
    return (6.0 * math.sin(x / 173.0 + 1.3) * math.cos(y / 211.0 - 0.7)
            + 3.5 * math.sin(x / 97.0 - y / 131.0 + 2.1)
            + 2.0 * math.sin(x / 53.0 + 0.4) * math.sin(y / 61.0 + 1.9))


def height(x, y):
    d = outside_distance(x, y)
    h = terrain_height(x, y)
    h += smoothstep(10.0, 300.0, d) * hills(x, y)
    h += smoothstep(500.0, 1400.0, d) * (55.0 + 25.0 * math.sin(math.atan2(y, x) * 3.0 + 0.8))  # distant rim
    return h
