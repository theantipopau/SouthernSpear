"""
Southern Spear - Dry River map specification (pure Python, no bpy).

The single source of truth for the Dry River layout: playable extents, the
analytic terrain, and the zones that must stay clear.

This module deliberately has NO bpy import. That is the entire point of it:

    Tools/Blender/dryriver_blockout.py  needs bpy, so it runs only in Blender
    Tools/Blender/dryriver_dressing.py  needs bpy, so it runs only in Blender
    Tools/verify_dressing.py            runs in CI, where Blender is absent

Dressing and blockout must never disagree about where the ground is or which
areas are protected. Sharing the terrain function is not tidiness — it is
correctness. A copy of terrain_height() in two files is a copy that will drift,
and the symptom of drift is dressing floating above the ground or a fence
bisecting an objective, neither of which is obvious in a screenshot.

Nothing here may import anything from the project. It is pure maths.
"""

import math

# ---------------------------------------------------------------------------
# Layout constants. Each carries the gameplay reason it has that value; these
# are restated in Docs/MAPS_DRYRIVER.md and must stay in step with it.
# ---------------------------------------------------------------------------

PLAY_WIDTH = 260.0          # m, x extent. Small enough to polish.
PLAY_DEPTH = 180.0          # m, y extent.
VERTICAL_RELIEF = 14.0      # m. Enough that elevation matters.
DEPLOY_ZONE_DEPTH = 15.0    # m, depth of each spawn band.
DEPLOY_OFFSET = 85.0        # m, spawn band centre from map centre.

OBJ_A_POS = (-15.0, 0.0)    # Water Point - first contact, map centre in Y so
                            # both teams reach it at an equal distance
OBJ_B_POS = (40.0, 52.0)    # Farmstead   - the round's pivot

CREEK_MEAN_Y = 0.0          # m, creek runs east-west through the centre
CREEK_DEPTH = 2.5           # m, cut into the terrain
CREEK_HALF_WIDTH = 5.5      # m, meanders +/-2.5 about this
CREEK_MEANDER = 2.5         # m, lateral sine amplitude

FARM_POS = (40.0, 52.0)     # same as OBJ B

# Zones that must stay clear of scatter: (x, y, radius).
# The deployment radii are large because a spawn must never be shootable from
# or obstructed on the way out.
PROTECTED = [
    (OBJ_A_POS[0], OBJ_A_POS[1], 18.0),
    (OBJ_B_POS[0], OBJ_B_POS[1], 26.0),
    (0.0, -DEPLOY_OFFSET, 70.0),
    (0.0, DEPLOY_OFFSET, 70.0),
]


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------


def terrain_height(x, y):
    """Analytic terrain height. Two ridges, a creek cut, and gentle roll.

    The creek is cut rather than raised so that a player inside it is concealed
    from the ridge but must climb out to shoot - the map's central tactical
    trade (MAPS_DRYRIVER.md 4.3).
    """
    h = 0.0

    # Northern ridge - the map's only strong elevation.
    ridge = math.exp(-((y - 78.0) ** 2) / (2.0 * 22.0 ** 2))
    h += VERTICAL_RELIEF * ridge

    # A low rise on the eastern third, to break the long north-south lane.
    h += 4.5 * math.exp(-((x - 85.0) ** 2 + (y + 30.0) ** 2) / (2.0 * 34.0 ** 2))

    # Gentle roll so the ground is not a table.
    h += 1.1 * math.sin(x / 38.0) * math.cos(y / 47.0)
    h += 0.55 * math.sin(x / 17.0 + y / 23.0)

    # Creek channel.
    centre = CREEK_MEAN_Y + CREEK_MEANDER * math.sin(x / 45.0)
    d = abs(y - centre)
    if d < CREEK_HALF_WIDTH:
        t = 1.0 - (d / CREEK_HALF_WIDTH) ** 2
        h -= CREEK_DEPTH * t

    return h


def is_protected(x, y, clearance=6.0):
    for px, py, pr in PROTECTED:
        if math.hypot(x - px, y - py) < pr + clearance:
            return True
    return False


def inside_play_area(x, y, inset=0.0):
    return (
        -PLAY_WIDTH / 2 + inset <= x <= PLAY_WIDTH / 2 - inset
        and -PLAY_DEPTH / 2 + inset <= y <= PLAY_DEPTH / 2 - inset
    )


def seg_point_distance(ax, ay, bx, by, px, py):
    """Shortest distance from point P to segment AB, in the XY plane.

    Fence runs are lines, and testing only their endpoints would let a run pass
    straight through an objective between them. This is the check that prevents
    a fence quietly becoming a wall across the map.
    """
    abx, aby = bx - ax, by - ay
    apx, apy = px - ax, py - ay
    denom = abx * abx + aby * aby
    if denom < 1e-9:
        return math.hypot(apx, apy)
    t = max(0.0, min(1.0, (apx * abx + apy * aby) / denom))
    return math.hypot(apx - abx * t, apy - aby * t)


def run_clears_protected(ax, ay, bx, by, extra=0.0):
    """(ok, reason). Reason names the offending zone so the failure is actionable."""
    for px, py, pr in PROTECTED:
        d = seg_point_distance(ax, ay, bx, by, px, py)
        if d < pr + extra:
            return False, "segment passes {:.1f}m from protected zone ({:.0f},{:.0f}); needs {:.1f}m".format(
                d, px, py, pr + extra
            )
    return True, ""
