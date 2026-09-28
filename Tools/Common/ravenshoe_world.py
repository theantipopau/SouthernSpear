# Southern Spear - Ravenshoe Crossing world ground height, inside and beyond the playable terrain.
#
# Shared by Tools/Blender/ravenshoe_skirt.py (builds the outer ground mesh) and any placement pass that
# needs a height off the playable edge. Inside the 200 x 300 m playable rectangle it is exactly
# ground_z() of ravenshoe_spec.py - the single definition of the ground, the discipline Dry River
# established with dryriver_world.py. Outside it blends into rolling high country and rises into a
# distant rim, so the map ends in ground and not in sky (the horizon band the first play test found).
# Metres, Blender axes (Unreal = x*100, -y*100, z*100).

import math

from ravenshoe_spec import MAP_HALF_X, MAP_N, MAP_S, ground_z

# The skirt extends this far from the centre before the rim takes over.
EXTENT_X = 1600.0   # m east/west of the centre
EXTENT_Y = 1700.0   # m north/south of the centre


def outside_distance(x, y):
    """Metres outside the playable rectangle (0 inside)."""
    return math.hypot(max(0.0, abs(x) - MAP_HALF_X), max(0.0, abs(y) - max(abs(MAP_N), abs(MAP_S))))


def smoothstep(a, b, v):
    t = max(0.0, min(1.0, (v - a) / (b - a)))
    return t * t * (3 - 2 * t)


def hills(x, y):
    """Deterministic layered sines at unrelated frequencies: rolling alpine country."""
    return (7.0 * math.sin(x / 181.0 + 0.9) * math.cos(y / 223.0 - 1.1)
            + 4.0 * math.sin(x / 101.0 - y / 143.0 + 2.4)
            + 2.2 * math.sin(x / 57.0 + 0.6) * math.sin(y / 67.0 - 1.7))


def height(x, y):
    """Ground height in metres at (x, y), inside the playable terrain and beyond it."""
    d = outside_distance(x, y)
    h = ground_z(x, y)
    h += smoothstep(10.0, 300.0, d) * hills(x, y)
    # A high-country rim: the gorge reads as cut into a plateau, not a ridge in an infinite plain.
    h += smoothstep(500.0, 1500.0, d) * (70.0 + 30.0 * math.sin(math.atan2(y, x) * 3.0 + 1.2))
    return h
