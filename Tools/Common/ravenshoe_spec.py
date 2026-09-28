"""
Southern Spear - Ravenshoe Crossing layout spec (class F, original work).

This module is the SINGLE SOURCE OF TRUTH for the Ravenshoe Crossing layout.
It has no `bpy` dependency on purpose: the CI validator and the blockout
generator must agree on every dimension, and Blender is not available in CI.
This is the pattern Tools/Common/dryriver_spec.py already established, and
duplicating these numbers into a second file is exactly the bug that pattern
exists to prevent.

Every constant below is a GAMEPLAY number with a reason, recorded in
Docs/MAPS_RAVENSHOE.md. If you cannot state the gameplay reason for a number,
do not add it.

COORDINATES
    +X east, +Y north, +Z up, metres. North is +Y.
    The road runs north-south; the gorge cuts east-west across it; the bridge
    spans it north-south. That orientation is chosen so the map's signature
    axial lane is the long axis and both flanking routes must leave the road
    entirely and come back to it.

GEOMETRY SUMMARY
    Map            200 m (E-W) x 300 m (N-S)
    Gorge          68 m wide, bed at -18 m, road/deck at +14 m
    Bridge         20 bays of 3.4 m, 7.5 m deck, 21 uprights per side
    Objectives     A at mid-span (y=0), B in the gatehouse passage (y=+62)
    Deployments    equidistant at 130 m from A, the fairness property that the
                   whole layout is built around. See check_spec().

WHY OBJECTIVE A IS AT MID-SPAN
    A bridgehead objective sits 96 m from one deployment and 164 m from the
    other - a 68 m positional gift that no amount of terrain dressing repairs.
    Mid-span splits it exactly, and sequential A->B order (Dry River 6.1) is
    what stops the northern team skipping straight to B and taking the round.
"""

import math

# ---------------------------------------------------------------------------
# Map extents
# ---------------------------------------------------------------------------

MAP_HALF_X = 100.0          # -100..100 -> 200 m wide
MAP_N = 150.0               # north edge
MAP_S = -150.0              # south edge
MAP_CENTER = (0.0, 0.0)

# ---------------------------------------------------------------------------
# Vertical
# ---------------------------------------------------------------------------

BED_Z = -18.0               # creek bed, the second lane's floor
DECK_Z = 14.0               # road and bridge deck level
RIDGE_Z = 28.0              # ridge crest outside the road corridor
CREST_LEVEL = 22.0          # road level out at the deployments

# ---------------------------------------------------------------------------
# The gorge
# ---------------------------------------------------------------------------

GORGE_N = 34.0              # north lip
GORGE_S = -34.0             # south lip
SPAN = GORGE_N - GORGE_S    # 68 m
GORGE_DEPTH = DECK_Z - BED_Z   # 32 m

# How fast the wall falls away from the lip. Higher = steeper. At 2.2 the wall
# transitions between |y|=34 and |y|=26, i.e. 8 m of run for 32 m of drop
# (~76 degrees). Steep enough to read as a gorge, shallow enough that the rock
# is walkable in two or three places, which is what stops the bed being a
# sealed channel nobody uses.
GORGE_WALL = 2.2

ROAD_HALF = 5.0             # 10 m road corridor
ROAD_BLEND = 12.0           # terrain rises to meet the road over this band

# ---------------------------------------------------------------------------
# The bridge
# ---------------------------------------------------------------------------

DECK_W = 7.5                # wide enough to fight and fall back along
DECK_T = 0.45               # deck slab thickness
PARAPET_H = 1.05            # the Dry River rail height: crouch cover, and it
                            # makes the deck a firing step rather than a lane
PARAPET_T = 0.35

N_BAYS = 20
BAY = SPAN / N_BAYS         # 3.4 m
N_UPRIGHT = N_BAYS + 1      # 21 per side

# Lamp standards every 5th upright = every 17 m: 5 per side, and the two at the
# abutments are shared pairs, so 9 distinct standards on the deck.
LAMP_STRIDE = 5
LAMP_R = 0.11
LAMP_H = 3.6
LAMP_PER_SIDE = 5           # at uprights 0, 5, 10, 15, 20 on each side

TRUSS_DEPTH = 5.2           # top chord above deck
TRUSSOUT = 0.30             # the lattice frame stands this far outboard of the
                            # deck edge, so it does not share space with the
                            # parapet. In a through truss the deck passes
                            # THROUGH the frame; a truss drawn on the same line
                            # as the parapet is two structures in one place.
                            # Must exceed CHORD_T/2 or the chord's inner face
                            # lands on the parapet's outer face; check_spec
                            # fails the build on that.
CHORD_T = 0.34              # member section
DIAG_T = 0.16

ABUT_X = 3.2                # abutment half-thickness along the road
ABUT_HALF_W = 7.0           # abutment half-width across the road

# ---------------------------------------------------------------------------
# The gatehouse (objective B)
# ---------------------------------------------------------------------------

GATE_X = 0.0                # on the road centreline
GATE_Y = 62.0
GATE_W = 9.0                # across the road
GATE_D = 6.2                # along the road
GATE_EAVES = 4.6            # wall top. Passage crown at 3.6, so 1.0 m of
                            # spandrel: that is what a 3.4 m granite span
                            # actually needs, and the building reads as a
                            # gatehouse rather than a viaduct
GATE_PARAPET_H = 1.2
GATE_H = GATE_EAVES + GATE_PARAPET_H    # 5.8 m overall
GATE_WALL_T = 0.85
PASSAGE_W = 3.4             # 3.4 m wide road passage through the building
PASSAGE_H = 3.6
ARCH_RISE = 1.0             # segmental, not semicircular: a 3.4 m span at this
                            # rise is what would actually be built in granite
ARCH_SPRING_Z = PASSAGE_H - ARCH_RISE   # 2.6
N_VOUSSOIR = 17             # odd, so one keystone lands on the crown
VOUSSOIR_T = 0.45           # radial thickness of the visible arch ring
RING_T = 0.50               # how far the ring stands proud of each face

# ---------------------------------------------------------------------------
# Objectives and deployments
# ---------------------------------------------------------------------------

OBJ_A_XY = (0.0, 0.0)       # mid-span, on the deck
OBJ_B_XY = (GATE_X, GATE_Y)  # in the passage
OBJ_A_R = 6.0               # capture radius
OBJ_B_R = 5.0

DEPLOY_S_XY = (0.0, -130.0)
DEPLOY_N_XY = (0.0, 130.0)
DEPLOY_HALF_X = 45.0
DEPLOY_HALF_Y = 15.0

# The verifier fails the build if the two approach distances differ by more
# than this. It is the one fairness property this layout is built around.
SYMMETRY_TOL = 0.5

# ---------------------------------------------------------------------------
# Flank routes - the second lane
# ---------------------------------------------------------------------------

# Both ramps branch off the road at the south abutment and traverse the gorge
# wall. The shape of these two polylines is the result of measuring, not taste.
#
# The first attempt ran east to x=60 and dropped 32 m in 91 m of run, and the
# verifier measured 1.54 m steps over 2 m samples - a 38-degree pitch, which no
# player climbs. The cause is arithmetic: the gorge is 32 m deep with 76-degree
# walls, so a ramp that heads straight for the deep centre has almost no
# horizontal run available to it. The fix is to use the map's WIDTH, which the
# first attempt ignored. Running out along the wall - where the ground is
# high, so the track is a cutting rather than a 15 m embankment - buys the run.
#
# Every control-point pitch is now under 23 degrees, which leaves headroom for
# the corner-cutting below to make the curve slightly tighter without it ever
# becoming a cliff. An earlier pass designed to 31 degrees and looked fine on
# paper; Chaikin then cut those corners and pushed the mesh back to 47.
#
# The west ramp reaches further out and runs ~135 m against the east's ~124 m,
# and its foot sits in the open, so the two flanks are not interchangeable.
RAMP_EAST = [
    (5.0, -34.0, DECK_Z),
    (26.0, -34.0, DECK_Z),
    (52.0, -32.0, 8.0),
    (76.0, -28.0, 2.0),
    (92.0, -22.0, -5.0),
    (84.0, -16.0, -9.0),
    (66.0, -13.0, -13.0),
    (46.0, -10.0, BED_Z),
]

RAMP_WEST = [
    (-5.0, -34.0, DECK_Z),
    (-28.0, -34.0, DECK_Z),
    (-56.0, -32.0, 8.0),
    (-82.0, -28.0, 2.0),
    (-98.0, -22.0, -5.0),
    (-90.0, -16.0, -9.0),
    (-70.0, -13.0, -13.0),
    (-48.0, -10.0, BED_Z),
]

def _chaikin_xy(pts, iterations=3):
    """Corner-cutting subdivision of the PLAN geometry only. Endpoints pinned."""
    out = [(p[0], p[1]) for p in pts]
    for _ in range(iterations):
        nxt = [out[0]]
        for a, b in zip(out, out[1:]):
            nxt.append((a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25))
            nxt.append((a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75))
        nxt.append(out[-1])
        out = nxt
    return out


def _grade_along(xy, z_start, z_end, max_grade_deg, flat_start, flat_end):
    """Lay a constant grade along a smoothed plan path.

    Smoothing the plan and grading the height separately is the whole trick.
    Smoothing the 3D polyline directly - which two earlier passes did - cuts
    the corner at the turnaround, and there the plan direction reverses so the
    horizontal run cancels while the drop does not. The apex came out at 40
    degrees on a path whose control points never exceeded 23, and no amount of
    hand-tuning the control points fixed it because the curve was doing the
    damage, not the points.

    Grading against arc length instead makes the steepest pitch a property of
    the design (max_grade_deg) rather than a side effect of where the corners
    fall. The first and last few metres are flat so the track meets the road at
    the abutment level and arrives at the bed floor level rather than diving
    into it.
    """
    cum = [0.0]
    for a, b in zip(xy, xy[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = cum[-1]
    run = max(1e-6, total - flat_start - flat_end)
    drop = z_start - z_end
    grade = math.atan2(drop, run)
    cap = math.radians(max_grade_deg)
    pts = []
    for (x, y), s in zip(xy, cum):
        d = min(max(0.0, s - flat_start), run)
        pts.append((x, y, z_start - math.tan(grade) * d))
    return pts, math.degrees(grade)


RAMP_GRADE_MAX = 22.0
_E, _GE = _grade_along(_chaikin_xy(RAMP_EAST), DECK_Z, BED_Z,
                        RAMP_GRADE_MAX, 22.0, 10.0)
_W, _GW = _grade_along(_chaikin_xy(RAMP_WEST), DECK_Z, BED_Z,
                        RAMP_GRADE_MAX, 22.0, 10.0)
RAMP_EAST = _E
RAMP_WEST = _W

RAMP_HALF_W = 1.8           # the track itself

# How far the terrain is graded to meet the track. This number is the whole
# walkability of the flank routes, and it is not a free choice.
#
# The gorge is 32 m deep with 76-degree walls, and the bed is at its lowest in
# the middle. A ramp leaving the south lip at +14 m therefore passes over
# ground that is 16 m below it, so the corridor has to BUILD fill up to the
# track, and the batter slope of that fill is (height difference) / RAMP_BLEND.
# At 5 m the batter was 73 degrees and the verifier measured 1.62 m steps over
# a 2 m sample - impassable. The track is a constructed ledge and embankment,
# which is what a gorge access road actually is, so the blend is set wide
# enough that the batter is a slope rather than a cliff. Widening it to 16 m
# only moved the worst step from 1.62 m to 1.54 m, which is the clue that the
# batter was never the cause: the cause was the ramp's own pitch, fixed above.
RAMP_BLEND = 12.0

# The bed route, from each ramp foot to mid-span, is appended to each ramp
# polyline in COVER_ROUTES below. The bed is 34 m of open ground from either
# foot, which is deliberately worse than the 68 m of trussed deck above it:
# more exposure, no lamp rhythm, boulders not uprights.

# ---------------------------------------------------------------------------
# Small maths
# ---------------------------------------------------------------------------


def clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def dist_xy(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def polyline_length(pts):
    total = 0.0
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        total += math.hypot(b[0] - a[0], b[1] - a[1])
    return total


def polyline_resample(pts, spacing):
    """Walk a polyline at fixed arc-length steps.

    Returns [(x, y, z, heading_deg), ...]. Heading is the 2D direction of
    travel, so callers can offset to the left or right of the track.
    """
    out = []
    carry = 0.0
    for i in range(len(pts) - 1):
        ax, ay, az = pts[i][0], pts[i][1], pts[i][2]
        bx, by, bz = pts[i + 1][0], pts[i + 1][1], pts[i + 1][2]
        seg = math.hypot(bx - ax, by - ay)
        if seg < 1e-6:
            continue
        head = math.degrees(math.atan2(by - ay, bx - ax))
        t = carry
        while t < seg:
            f = t / seg
            out.append((ax + (bx - ax) * f, ay + (by - ay) * f,
                        az + (bz - az) * f, head))
            t += spacing
        carry = t - seg
    return out


def _nearest_on_polyline(x, y, pts):
    """Return (distance_to_centreline, interpolated_z) for the closest segment."""
    best_d = 1e18
    best_z = 0.0
    for i in range(len(pts) - 1):
        ax, ay, az = pts[i][0], pts[i][1], pts[i][2]
        bx, by, bz = pts[i + 1][0], pts[i + 1][1], pts[i + 1][2]
        dx, dy = bx - ax, by - ay
        seg_sq = dx * dx + dy * dy
        if seg_sq < 1e-9:
            continue
        t = ((x - ax) * dx + (y - ay) * dy) / seg_sq
        t = clamp(t, 0.0, 1.0)
        px, py = ax + dx * t, ay + dy * t
        d = math.hypot(x - px, y - py)
        if d < best_d:
            best_d = d
            best_z = az + (bz - az) * t
    return best_d, best_z


def _corridor(x, y, z, pts, half_width, blend):
    """Pull terrain onto a corridor's centreline, flat across the track itself
    and easing back to natural ground across the blend band."""
    d, zr = _nearest_on_polyline(x, y, pts)
    if d > blend:
        return z
    t = 1.0 - smoothstep((d - half_width) / max(1e-6, blend - half_width))
    return lerp(z, zr, t)


# ---------------------------------------------------------------------------
# The road
# ---------------------------------------------------------------------------

def _longitudinal(y):
    """Road-level profile along the map, before the gorge is cut."""
    ay = abs(y)
    if ay <= 40.0:
        return DECK_Z
    t = smoothstep((ay - 40.0) / 90.0)
    return lerp(DECK_Z, CREST_LEVEL, t)


# The road is a corridor in its own right rather than a function of the
# longitudinal profile, because the same code then has to carve the ramps, and
# one mechanism is easier to keep honest than two. It is SAMPLED FROM
# _longitudinal rather than authored by hand: an earlier version hard-coded
# four points and let the corridor interpolate them linearly, which put the
# road at 15.96 m where the terrain said 15.20 m. Two profiles disagreeing by
# three quarters of a metre is exactly the class of bug this module exists to
# make impossible, so the corridor is now derived from the profile.
def _road_polyline():
    pts = []
    for y in (-130.0, -110.0, -95.0, -80.0, -68.0, -58.0, -50.0, -44.0, -40.0,
              40.0, 44.0, 50.0, 58.0, 68.0, 80.0, 95.0, 110.0, 130.0):
        pts.append((0.0, y, _longitudinal(y)))
    return pts


ROAD = _road_polyline()


# ---------------------------------------------------------------------------
# Terrain
# ---------------------------------------------------------------------------


def _cross_slope(ax, long_z):
    """Ground rises away from the road corridor to the ridge."""
    if ax <= ROAD_HALF:
        return long_z
    t = smoothstep((ax - ROAD_HALF) / (MAP_HALF_X - ROAD_HALF))
    return lerp(long_z, RIDGE_Z, t)


def _carve_gorge(z, y):
    """Cut the gorge between the lips, with a steep wall."""
    ay = abs(y)
    if ay >= GORGE_N:
        return z
    tg = 1.0 - (ay / GORGE_N)
    carve = smoothstep(tg * GORGE_WALL)
    return lerp(z, BED_Z, carve)


def ground_z(x, y):
    """Terrain height in metres at (x, y). This is the ground every placement
    script must agree with - the same discipline dryriver_spec.py enforces."""
    ay = abs(y)
    z = _cross_slope(abs(x), _longitudinal(y))
    z = _carve_gorge(z, y)

    # Ramps: cut into the wall, inside the gorge as well as outside it.
    z = _corridor(x, y, z, RAMP_EAST, RAMP_HALF_W, RAMP_BLEND)
    z = _corridor(x, y, z, RAMP_WEST, RAMP_HALF_W, RAMP_BLEND)

    # The road, but only outside the gorge. Inside the gorge the terrain is the
    # gorge, because the bridge spans it: blending the road back in there would
    # fill the chasm the whole map is built around.
    if ay >= GORGE_N:
        z = _corridor(x, y, z, ROAD, ROAD_HALF, ROAD_BLEND)
    return z


# ---------------------------------------------------------------------------
# Cover markers
# ---------------------------------------------------------------------------

# Spacing along a route. Dry River's cover rule is one object per 12 m of
# intended route. Markers sit OFF the route line, offset to alternating sides,
# so the spacing that actually matters is the diagonal between markers on
# opposite sides, not the along-route step. At 8 m the worst point on a route
# is sqrt(4^2 + 4.5^2) = 6.0 m from a marker centre, which after the marker
# radius is inside COVER_REACH. Spacing this out to 13 m leaves a 6.8 m hole
# mid-way between markers, which the 20 m rule does not permit.
COVER_SPACING = 8.0
COVER_OFFSET = 4.5

# How far from the route line a player may be and still be considered to have
# cover in reach. A boulder 4.5 m off the track is cover a player can use; it
# is not open ground. This is the number the 20 m rule is measured against,
# and the first version of this file conflated it with the marker radius, which
# made every offset marker read as a gap.
COVER_REACH = 6.0

# Route legs that must be cover-to-cover walkable. The deck is excluded on
# purpose: the truss uprights and lamp standards ARE the cover there, and they
# are part of the bridge mesh rather than scattered dressing.
COVER_ROUTES = [
    ("south_approach", [(0.0, -130.0, CREST_LEVEL), (0.0, -44.0, DECK_Z)]),
    ("north_road", [(0.0, 44.0, DECK_Z), (0.0, 130.0, CREST_LEVEL)]),
    ("ramp_east", RAMP_EAST),
    ("ramp_west", RAMP_WEST),
    ("bed_east", RAMP_EAST[-1:] + [OBJ_A_XY[0:2] + (DECK_Z,)]),
    ("bed_west", RAMP_WEST[-1:] + [OBJ_A_XY[0:2] + (DECK_Z,)]),
]


def cover_markers():
    """Deterministic cover placements along every route leg.

    Returns [(name, x, y, kind, half_r), ...]. Kind is the dressing class the
    Unreal import should spawn: 'rock' uses Scene_QuarrySlate, 'bush' uses
    Namaqualand. Generated here rather than in the blockout so that
    verify_ravenshoe.py can measure the 20 m rule against the same list the
    geometry is built from - a verifier that reads a different list than the
    builder is a verifier that proves nothing.
    """
    import random
    rng = random.Random(20260928)  # same fixed-seed discipline as Red Gum
    out = []
    for route_name, pts in COVER_ROUTES:
        steps = polyline_resample(pts, COVER_SPACING)
        for i, (x, y, z, head) in enumerate(steps):
            # Alternate sides of the track, with a deterministic jitter so the
            # line does not read as a ruler.
            side = 1.0 if (i % 2 == 0) else -1.0
            rad = math.radians(head + 90.0 * side)
            off = COVER_OFFSET + rng.uniform(-1.2, 1.2)
            cx = x + math.cos(rad) * off
            cy = y + math.sin(rad) * off
            if not (MAP_S + 6.0 <= cy <= MAP_N - 6.0 and
                    -MAP_HALF_X + 6.0 <= cx <= MAP_HALF_X - 6.0):
                continue
            # Never inside the gatehouse: the passage IS objective B, and a
            # boulder in it would block the capture volume as well as the
            # fight. check_spec() fails the build on this, but the generator
            # skips the placement rather than emitting it and complaining.
            if (abs(cx - GATE_X) < GATE_W / 2.0 + 1.5 and
                    abs(cy - GATE_Y) < GATE_D / 2.0 + 1.5):
                continue
            kind = "rock" if rng.random() < 0.62 else "bush"
            half_r = rng.uniform(0.75, 1.45)
            out.append(("%s_%02d" % (route_name, i), cx, cy, kind, half_r))
    return out


# ---------------------------------------------------------------------------
# The verification the CI runs
# ---------------------------------------------------------------------------

# The intent routes the 20 m rule is measured along: the legs a player
# actually walks, not every straight line on the map.
INTENT_ROUTES = [
    ("south_approach", [(0.0, -130.0), (0.0, -44.0)]),
    ("north_road", [(0.0, 44.0), (0.0, 130.0)]),
    ("ramp_east", [(p[0], p[1]) for p in RAMP_EAST]),
    ("ramp_west", [(p[0], p[1]) for p in RAMP_WEST]),
    ("bed_east", [(RAMP_EAST[-1][0], RAMP_EAST[-1][1]), OBJ_A_XY]),
    ("bed_west", [(RAMP_WEST[-1][0], RAMP_WEST[-1][1]), OBJ_A_XY]),
]

# Hard cover that is not a scattered marker. The gatehouse is the important
# one: the road runs straight through it, so the stretch of north road it
# occupies is covered by the building rather than by boulders, and the
# generator correctly refuses to drop a rock inside objective B. Without this
# list the 20 m rule reports a 66 m hole that is in fact a 9 m stone building.
#
# Entries are (name, cx, cy, half_x, half_y). Counted as cover out to
# COVER_REACH beyond the box face.
HARD_COVER = [
    ("gatehouse", GATE_X, GATE_Y, GATE_W / 2.0, GATE_D / 2.0),
    ("south_abutment", 0.0, GORGE_S, ABUT_HALF_W, 3.0),
    ("north_abutment", 0.0, GORGE_N, ABUT_HALF_W, 3.0),
]

MAX_OPEN_CROSSING = 20.0    # Dry River 5, carried over unchanged


def _gap_to_cover(x, y, marks):
    """Smallest surface gap from (x, y) to any cover: scattered marker or
    hard-cover volume. Hard cover is axis-aligned and read as a box, so its
    edge distance is exact rather than an approximation from a radius."""
    best = 1e18
    for _n, mx, my, _k, mr in marks:
        d = math.hypot(x - mx, y - my) - mr
        if d < best:
            best = d
    for _n, cx, cy, hx, hy in HARD_COVER:
        dx = max(0.0, abs(x - cx) - hx)
        dy = max(0.0, abs(y - cy) - hy)
        d = math.hypot(dx, dy)
        if d < best:
            best = d
    return best


def route_max_gap(name, pts, marks, step=1.0):
    """Longest stretch of an intent route with no cover within reach."""
    worst = 0.0
    worst_at = None
    run_start = None
    prev_ok = True
    for a, b in zip(pts, pts[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(seg / step))
        for k in range(n + 1):
            f = k / float(n)
            x = lerp(a[0], b[0], f)
            y = lerp(a[1], b[1], f)
            ok = _gap_to_cover(x, y, marks) <= COVER_REACH
            if ok and not prev_ok:
                run_start = (x, y)
            elif not ok and prev_ok and run_start is not None:
                g = math.hypot(x - run_start[0], y - run_start[1])
                if g > worst:
                    worst, worst_at = g, run_start
            prev_ok = ok
    if not prev_ok and run_start is not None:
        g = math.hypot(pts[-1][0] - run_start[0], pts[-1][1] - run_start[1])
        if g > worst:
            worst, worst_at = g, run_start
    return worst, worst_at


def check_spec():
    """Run every check the spec can prove without the engine. Returns a list
    of (severity, message). severity is 'FAIL' or 'WARN'."""
    issues = []

    d_s = dist_xy(*DEPLOY_S_XY, *OBJ_A_XY)
    d_n = dist_xy(*DEPLOY_N_XY, *OBJ_A_XY)
    if abs(d_s - d_n) > SYMMETRY_TOL:
        issues.append(("FAIL", "deployment asymmetry %.2f m (S=%.2f N=%.2f), "
                      "tolerance %.2f" % (abs(d_s - d_n), d_s, d_n, SYMMETRY_TOL)))
    if d_s > 220.0:
        issues.append(("FAIL", "approach %.2f m exceeds the 220 m sightline ceiling" % d_s))

    a_b = dist_xy(*OBJ_A_XY, *OBJ_B_XY)
    if a_b < 30.0:
        issues.append(("WARN", "objective leg A->B is only %.1f m" % a_b))

    # The deck is the map's one sanctioned exception to the 20 m rule, and the
    # spec is only allowed to claim that exception while the mitigation exists.
    if N_UPRIGHT * 2 < 30:
        issues.append(("FAIL", "only %d uprights: the deck mitigation is too thin"
                      % N_UPRIGHT))
    if BAY > 4.0:
        issues.append(("FAIL", "bay %.2f m exceeds 4 m; the deck loses its cover rhythm"
                      % BAY))
    if DECK_W < 6.0:
        issues.append(("FAIL", "deck %.1f m is too narrow to fight or fall back along"
                      % DECK_W))
    # The parapet and the truss frame must not share space. This is the check
    # for the specific overlap that shipped in the first bridge.
    parapet_outer = DECK_W / 2.0
    truss_inner = DECK_W / 2.0 + TRUSSOUT - CHORD_T / 2.0
    if truss_inner <= parapet_outer:
        issues.append(("FAIL", "truss frame starts at x=%.2f but the parapet "
                      "reaches x=%.2f; they overlap" % (truss_inner, parapet_outer)))

    # Ramps must be walkable, not just present. Both the average and the WORST
    # SINGLE PITCH are checked: an average hides a cliff, and a cliff is what
    # actually stops a player or an agent.
    for label, pts in (("east", RAMP_EAST), ("west", RAMP_WEST)):
        run = polyline_length(pts)
        drop = pts[0][2] - pts[-1][2]
        grade = math.degrees(math.atan2(drop, run))
        if grade > 32.0:
            issues.append(("FAIL", "%s ramp averages %.1f deg over %.1f m; too steep "
                          "to walk or navigate" % (label, grade, run)))
        for a, b in zip(pts, pts[1:]):
            seg = math.hypot(b[0] - a[0], b[1] - a[1])
            if seg < 1e-6:
                continue
            pitch = math.degrees(math.atan2(abs(b[2] - a[2]), seg))
            if pitch > 32.0:
                issues.append(("FAIL", "%s ramp has a %.1f deg pitch from "
                              "(%.0f,%.0f) to (%.0f,%.0f); a cliff, not a track"
                              % (label, pitch, a[0], a[1], b[0], b[1])))

    marks = cover_markers()
    if len(marks) < 40:
        issues.append(("FAIL", "only %d cover markers" % len(marks)))
    for name, pts in INTENT_ROUTES:
        gap, at = route_max_gap(name, pts, marks)
        if gap > MAX_OPEN_CROSSING:
            issues.append(("FAIL", "route %s has a %.1f m uncovered run at %s; "
                          "the 20 m rule allows 20" % (name, gap, at)))

    # Nothing may be dropped inside the gatehouse passage, or the objective
    # volume itself would be blocked.
    for name, mx, my, _k, _r in marks:
        if abs(mx - GATE_X) < GATE_W / 2.0 + 1.0 and abs(my - GATE_Y) < GATE_D / 2.0 + 1.0:
            issues.append(("FAIL", "cover marker %s sits in the gatehouse" % name))

    return issues


if __name__ == "__main__":
    problems = check_spec()
    for sev, msg in problems:
        print("%s  %s" % (sev, msg))
    print("spec checks: %d issue(s)" % len(problems))
