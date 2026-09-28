"""
Ravenshoe Crossing - layout and geometry verifier (class F, original work).

The counterpart to Tools/Blender/verify_dryriver.py. It runs in two modes:

    python Tools/Blender/verify_ravenshoe.py
        Spec checks only. No bpy, no Blender. This is the CI mode, and it is
        the one that matters for every rule the design is built on.

    blender -b --factory-startup Content/Art/Blockout/SS_MAP_Ravenshoe_01_HI.blend \
            --python Tools/Blender/verify_ravenshoe.py
        Spec checks PLUS functional probes of the geometry that was actually
        built, by ray-casting the meshes rather than by re-reading the numbers
        that produced them.

Why the second mode exists
    Re-asserting that the spec says 3.4 m bays proves only that the spec still
    says 3.4 m bays. It does not prove the generator honoured it, and it does
    not prove the arch is actually a hole. A voussoir sweep angle computed with
    asin instead of atan2 put the arch ring 0.44 m below grade while every
    number in the spec stayed correct; only a ray cast through the passage
    found it. So the geometry gets probed as a functional object: can a player
    actually walk, stand and shoot through what was built?

Exit code is 0 on success, 1 on any FAIL. WARN does not fail the build.
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "Common")))
import ravenshoe_spec as S  # noqa: E402

TOL = 0.05          # metres, geometry vs spec
RESULTS = []


def check(ok, label, detail=""):
    RESULTS.append((bool(ok), label, detail))
    return bool(ok)


def near(a, b, tol=TOL):
    return abs(a - b) <= tol


# ---------------------------------------------------------------------------
# Mode 1 - the spec. Runs everywhere, including CI.
# ---------------------------------------------------------------------------

def verify_spec():
    for sev, msg in S.check_spec():
        check(sev != "FAIL", "spec: %s" % msg, sev)

    # Rotation distances, reported as measurements rather than assumptions.
    d_s = S.dist_xy(*S.DEPLOY_S_XY, *S.OBJ_A_XY)
    d_n = S.dist_xy(*S.DEPLOY_N_XY, *S.OBJ_A_XY)
    check(near(d_s, d_n), "deployments equidistant to OBJ A",
          "S=%.2f m N=%.2f m delta=%.2f m" % (d_s, d_n, abs(d_s - d_n)))

    d_ab = S.dist_xy(*S.OBJ_A_XY, *S.OBJ_B_XY)
    check(d_ab <= 220.0, "OBJ A -> OBJ B within sightline ceiling",
          "%.1f m" % d_ab)

    # The deck is the sanctioned exception; record it so it stays visible.
    print("INFO  deck is %.0f m against a %.0f m rule; mitigation is %d "
          "uprights/side at %.1f m, %d lamps, %.2f m parapet, %.1f m deck"
          % (S.SPAN, S.MAX_OPEN_CROSSING, S.N_UPRIGHT, S.BAY,
             S.LAMP_PER_SIDE * 2, S.PARAPET_H, S.DECK_W))


# ---------------------------------------------------------------------------
# Mode 2 - the built geometry. Only under Blender.
# ---------------------------------------------------------------------------

def verify_geometry():
    import bpy
    import mathutils

    bridge = bpy.data.objects.get("SS_Raven_Bridge")
    gate = bpy.data.objects.get("SS_Raven_Gatehouse")
    terrain = bpy.data.objects.get("SS_MAP_Ravenshoe_01_Terrain")
    check(bridge is not None, "bridge mesh present")
    check(gate is not None, "gatehouse mesh present")
    check(terrain is not None, "terrain mesh present")
    if not (bridge and gate and terrain):
        return

    def cast(obj, origin, direction, dist=500.0):
        """World-space ray cast against obj. Returns hit point or None."""
        inv = obj.matrix_world.inverted()
        o = inv @ mathutils.Vector(origin)
        d = (inv.to_3x3() @ mathutils.Vector(direction)).normalized()
        hit, loc, _nrm, _idx = obj.ray_cast(o, d, distance=dist)
        if not hit:
            return None
        return obj.matrix_world @ loc

    down = (0.0, 0.0, -1.0)
    north = (0.0, 1.0, 0.0)

    # --- the deck is a continuous walkable surface at the authored level ----
    # Probes start at z=2.0, which is ABOVE the parapet and the bottom chord
    # but BELOW the top chord and the lateral bracing at 5.2. A ray dropped
    # from z=60 down the centreline hits the lateral bracing first, because
    # the bracing crosses the deck at every upright - which is correct
    # geometry and a badly designed probe.
    probe_from = 2.0
    for y in (-30.0, -17.0, 0.0, 17.0, 30.0):
        p = cast(bridge, (0.0, y, probe_from), down, dist=10.0)
        check(p is not None and near(p.z, S.DECK_T, 0.02),
              "deck top at %.2f m at y=%+.0f" % (S.DECK_T, y),
              "hit z=%.3f" % (p.z if p else float("nan")))

    # --- nothing solid over the gorge beyond the abutments -----------------
    for y in (42.0, 60.0):
        p = cast(bridge, (0.0, y, probe_from), down, dist=10.0)
        check(p is None, "no bridge structure over open ground y=%+.0f" % y,
              "hit z=%.3f" % (p.z if p else float("nan")))

    # --- the parapet is chest-high cover, not a railing --------------------
    p = cast(bridge, (S.DECK_W / 2.0 - S.PARAPET_T / 2.0, 0.0, probe_from),
             down, dist=10.0)
    check(p is not None and near(p.z, S.DECK_T + S.PARAPET_H, 0.02),
          "parapet top at %.2f m" % (S.DECK_T + S.PARAPET_H),
          "hit z=%.3f" % (p.z if p else float("nan")))

    # --- the passage is a real hole you can stand in and shoot through -----
    # Cast north along the road axis at standing height: must pass clean
    # through both faces, because the arch is the objective. The gatehouse
    # stands at y = GATE_Y, so the probes start south of it - the first
    # version cast from y=-40 assuming a building at the origin and silently
    # proved nothing once the building was moved to its design position.
    gate_ground = S.ground_z(S.GATE_X, S.GATE_Y)
    approach = S.GATE_Y - 22.0

    p = cast(gate, (0.0, approach, gate_ground + 1.0), north, dist=100.0)
    check(p is None, "road passage is clear end to end at z=1.0",
          "blocked at y=%.2f" % (p.y if p else float("nan")))

    # Head height through the crown.
    p = cast(gate, (0.0, approach, gate_ground + S.PASSAGE_H - 0.25),
             north, dist=100.0)
    check(p is None, "road passage is clear just under the crown z=%.2f"
          % (S.PASSAGE_H - 0.25),
          "blocked at y=%.2f" % (p.y if p else float("nan")))

    # Above the crown must be SOLID, or the building is a pair of walls.
    p = cast(gate, (0.0, approach, gate_ground + S.PASSAGE_H + 0.4),
             north, dist=100.0)
    check(p is not None, "spandrel solid above the arch crown",
          "no hit - the gatehouse has a hole in its roof")

    # The piers either side of the opening must be solid.
    for sx in (-1.0, 1.0):
        p = cast(gate, (sx * (S.PASSAGE_W / 2.0 + 0.5), approach, gate_ground + 1.0),
                 north, dist=100.0)
        check(p is not None, "pier solid at x=%+.1f" % (sx * (S.PASSAGE_W / 2.0 + 0.5)),
              "no hit - the passage is wider than PASSAGE_W")

    # --- it stands where the layout row says, and on the road --------------
    zs = [(gate.matrix_world @ v.co).z for v in gate.data.vertices]
    check(near(min(zs), gate_ground, 0.02),
          "gatehouse base sits on the measured road surface",
          "lowest vertex z=%.3f want=%.3f" % (min(zs), gate_ground))
    ys = [(gate.matrix_world @ v.co).y for v in gate.data.vertices]
    check(near((min(ys) + max(ys)) / 2.0, S.GATE_Y, 0.02),
          "gatehouse centred on objective B",
          "centre y=%.3f want=%.1f" % ((min(ys) + max(ys)) / 2.0, S.GATE_Y))

    # --- the gorge actually exists, and is 32 m deep -----------------------
    # Probed only where the surface is genuinely flat, i.e. the bed floor and
    # the lip. Probing mid-wall compares the ray against a smooth function
    # while the 2 m terrain grid linearly interpolates across it, so the two
    # legitimately differ by most of half a metre. The wall is checked instead
    # by the monotone descent probe below.
    for y, label in ((-6.0, "creek bed south"), (0.0, "mid-span floor"),
                     (6.0, "creek bed north")):
        p = cast(terrain, (0.0, y, 90.0), down)
        check(p is not None and near(p.z, S.BED_Z, 0.1),
              "terrain at %s (y=%+.0f) is %.1f m" % (label, y, S.BED_Z),
              "z=%.2f want=%.2f" % (p.z if p else float("nan"), S.BED_Z))

    for y, label in ((-34.0, "south lip"), (34.0, "north lip")):
        p = cast(terrain, (0.0, y, 90.0), down)
        check(p is not None and near(p.z, S.DECK_Z, 0.1),
              "terrain at %s (y=%+.0f) is road level" % (label, y),
              "z=%.2f want=%.2f" % (p.z if p else float("nan"), S.DECK_Z))

    # The wall must descend monotonically from lip to bed.
    zs = []
    y = -33.0
    while y <= -5.0:
        p = cast(terrain, (0.0, y, 90.0), down)
        zs.append(p.z if p else float("nan"))
        y += 2.0
    drops = sum(1 for a, b in zip(zs, zs[1:]) if b > a + 0.01)
    check(drops == 0, "south gorge wall descends monotonically",
          "%d of %d steps went uphill" % (drops, len(zs) - 1))
    check(near(zs[-1], S.BED_Z, 0.2) and near(zs[0], S.DECK_Z, 1.0),
          "south wall runs lip to bed",
          "top=%.2f bottom=%.2f" % (zs[0], zs[-1]))

    # --- the road is continuous from each deployment to the bridge --------
    # Even y only: every even y is a terrain grid sample, so the ray lands on
    # a vertex and compares exactly rather than against an interpolated face.
    for y in (-130.0, -94.0, -58.0, -42.0, 42.0, 58.0, 94.0, 130.0):
        p = cast(terrain, (0.0, y, 90.0), down)
        want = S.ground_z(0.0, y)
        check(p is not None and near(p.z, want, 0.1),
              "road surface at y=%+.0f" % y,
              "z=%.2f want=%.2f" % (p.z if p else float("nan"), want))

    # --- the ramps are walkable -------------------------------------------
    # Measured along the SURFACE at 2 m intervals, not between the control
    # points. The control points are 14 m apart with an 8 m drop between two
    # of them; that is the ramp, not a step, and comparing them directly
    # reported an 8 m "step" that does not exist on the ground.
    # --- the ramps are walkable -------------------------------------------
    # Measured along the SURFACE, and graded at the terrain grid's own 2.0 m
    # resolution. Sampling finer than the grid is meaningless: the first
    # attempt sampled every 1.0 m and reported a 52-degree pitch that existed
    # only in the difference between two rays landing either side of a grid
    # cell. The exact grade property is asserted on the spec in
    # check_spec(), where it is grid-independent; this test is about whether
    # the BUILT surface follows that spec, not about re-deriving the grade.
    for label, pts in (("east", S.RAMP_EAST), ("west", S.RAMP_WEST)):
        samples = S.polyline_resample(pts, 2.0)
        worst_off = 0.0
        worst_step = 0.0
        prev = None
        misses = 0
        for x, y, z, _h in samples:
            p = cast(terrain, (x, y, 90.0), down)
            if p is None:
                misses += 1
                continue
            worst_off = max(worst_off, abs(p.z - z))
            if prev is not None:
                worst_step = max(worst_step, abs(p.z - prev))
            prev = p.z
        check(misses == 0, "%s ramp is a continuous surface" % label,
              "%d of %d samples missed the terrain" % (misses, len(samples)))
        # 1.25 m per 2.0 m of run is 32 degrees, the spec's own ceiling.
        check(worst_step <= 1.25, "%s ramp grade stays under 32 deg on the mesh" % label,
              "worst %.2f m per 2.0 m run" % worst_step)
        check(worst_off <= 1.0, "%s ramp surface follows the spec line" % label,
              "worst deviation %.2f m" % worst_off)

    verify_bridge_metrics(bridge, cast, down, mathutils)


def verify_bridge_metrics(bridge, cast, down, mathutils):
    """Measure the BUILT bridge and report it against the spec.

    The spec-mode checks assert the numbers. These assert that the geometry
    generated from them actually has those numbers. A box the spec calls 2.0 m
    tall can be 1.0 m on the mesh, and every spec check still passes; only a
    cast finds it.

    Everything here is in the bridge's own local frame, where the deck top is
    z = DECK_T and the span runs along y. Probes start BELOW the lateral
    bracing and the sway frames, which cross the lane overhead, so a ray meant
    for the deck does not stop on a member 5 m above it.
    """
    half = S.SPAN / 2.0
    deck = S.DECK_T
    chord_z = deck + S.CHORD_T / 2.0
    top_z = deck + S.TRUSS_DEPTH
    truss_x = S.DECK_W / 2.0 + S.TRUSSOUT
    parapet_x = S.DECK_W / 2.0 - S.PARAPET_T / 2.0

    # --- the running surface, the parapets and the chords, at their heights --
    # Mid-bay in y, so no lateral or sway member is overhead.
    y_probe = -half + S.BAY * 0.5
    p = cast(bridge, (0.0, y_probe, deck + 0.6), down, dist=20.0)
    check(p is not None and near(p.z, deck),
          "bridge deck top is at DECK_T",
          "z=%.3f want=%.3f" % (p.z if p else float("nan"), deck))

    for sx in (-1.0, 1.0):
        p = cast(bridge, (sx * parapet_x, y_probe, top_z + 1.0), down, dist=20.0)
        want = deck + S.PARAPET_H
        check(p is not None and near(p.z, want),
              "parapet top is %.2f m above the deck (x=%+.1f)" % (S.PARAPET_H, sx * parapet_x),
              "z=%.3f want=%.3f" % (p.z if p else float("nan"), want))

        p = cast(bridge, (sx * truss_x, y_probe, top_z + 2.0), down, dist=20.0)
        want = top_z + S.CHORD_T / 2.0
        check(p is not None and near(p.z, want),
              "top chord centre is TRUSS_DEPTH up (x=%+.1f)" % (sx * truss_x),
              "z=%.3f want=%.3f" % (p.z if p else float("nan"), want))

    # --- the running surface is its own material slot ----------------------
    # The deck slab is one box, so the split has to be done by reassigning the
    # top polygons. If that silently did nothing the whole slab would render
    # as road surface on its fascia and soffit, which is exactly the fault the
    # slot exists to prevent - and it would not be visible from the deck.
    slots = [m.name if m else "" for m in bridge.data.materials]
    road_idx = next((i for i, n in enumerate(slots) if n.endswith("_Road")), None)
    check(road_idx is not None, "bridge has a Road material slot",
          "slots: %s" % ", ".join(slots))
    if road_idx is not None:
        road_faces = [f for f in bridge.data.polygons
                      if f.material_index == road_idx]
        area = sum(f.area for f in road_faces)
        want = S.DECK_W * S.SPAN
        tilted = [f for f in road_faces if abs(f.normal.z) < 0.5]
        check(abs(area - want) < 1.0,
              "Road slot covers the running surface only",
              "area=%.1f m2 want=%.1f m2" % (area, want))
        check(not tilted,
              "Road slot has no fascia or soffit faces",
              "%d of %d road faces are not horizontal" % (len(tilted), len(road_faces)))

    # --- the counts the cover rhythm depends on ---------------------------
    # Measured off the vertices rather than re-derived from the spec: if the
    # generator dropped every other upright the mesh would say so here.
    #
    # The predicates have to separate members that share a plane. On the truss
    # line sit the chords (0.34 square, corners at +/-0.17 from the frame), the
    # uprights (0.28 square, corners at +/-0.14), the diagonals (0.16 square,
    # corners at +/-0.08) and the outriggers, all on the same x. A loose
    # tolerance counted 138 y positions per side instead of 21 - diagonals and
    # sway frames contributed their corners. The upright band is therefore the
    # gap between the diagonal and chord corner offsets, which only the
    # uprights land in.
    def distinct_y(pred):
        seen = set()
        for v in bridge.data.vertices:
            if pred(v.co):
                seen.add(round(v.co.y, 2))
        return len(seen)

    for sx in (-1.0, 1.0):
        # Snap each corner to its bay index rather than counting distinct y:
        # one upright is a box, so it contributes corners at y-0.14 and y+0.14
        # and a distinct-y count returns 42 for 21 uprights. Snapping also makes
        # the check stronger - it confirms each upright is at a SPECIFIED bay,
        # not merely that 21 somethings are out there.
        bays = set()
        for v in bridge.data.vertices:
            c = v.co
            if 0.10 <= abs(abs(c.x) - truss_x) <= 0.15:
                bays.add(int(round((c.y + half) / S.BAY)))
        n = len(bays)
        check(n == S.N_UPRIGHT and min(bays) == 0 and max(bays) == S.N_UPRIGHT - 1,
              "uprights on the %s frame" % ("+x" if sx > 0 else "-x"),
              "%d bays %d..%d, spec says %d bays 0..%d"
              % (n, min(bays), max(bays), S.N_UPRIGHT, S.N_UPRIGHT - 1))

    # Lamp heads stand on the parapet line at +/-3.575, inboard of the truss at
    # 4.05, and their tops are above the lateral bracing. Filtering on height
    # alone also catches the bracing, the portal heads and the sway frames.
    lamps = distinct_y(lambda c: c.z > deck + S.PARAPET_H + S.LAMP_H
                       and abs(abs(c.x) - parapet_x) < 0.3)
    check(lamps == S.LAMP_PER_SIDE * 2,
          "lamp standards on the deck",
          "%d found, spec says %d" % (lamps, S.LAMP_PER_SIDE * 2))

    # --- clear headroom over the lane --------------------------------------
    # The lowest members crossing overhead are the sway frames, not the
    # lateral bracing, so this is the height a player actually gets.
    up = (0.0, 0.0, 1.0)
    head = None
    for k in range(0, S.N_BAYS + 1, 3):
        p = cast(bridge, (0.0, -half + k * S.BAY, deck + 0.05), up, dist=20.0)
        if p is not None:
            h = p.z - deck
            head = h if head is None else min(head, h)
    check(head is not None and head >= 4.0,
          "clear headroom over the lane is at least 4 m",
          "%.2f m" % (head if head is not None else float("nan")))


# ---------------------------------------------------------------------------

def main():
    # The bridge's governing table, printed every run. A metric nobody reads is
    # a metric nobody maintains, and these are the numbers the design argument
    # actually rests on.
    print("=" * 78)
    print("%-14s %-42s %10s %s" % ("KEY", "BRIDGE METRIC", "VALUE", "UNIT"))
    for _k, label, value, unit in S.bridge_metrics():
        print("%-14s %-42s %10.3f %s" % (_k, label, value, unit))
    print("=" * 78)

    verify_spec()
    try:
        import bpy  # noqa: F401
        verify_geometry()
        mode = "spec + geometry"
    except ImportError:
        mode = "spec only (no bpy)"

    fails = [r for r in RESULTS if not r[0]]
    warns = [r for r in RESULTS if "WARN" in r[2]]
    for ok, label, detail in RESULTS:
        if not ok or "WARN" in detail:
            print("%s  %-52s %s" % ("PASS" if ok else "FAIL", label, detail))
    print("=" * 78)
    print("MODE   %s" % mode)
    print("CHECKS %d passed, %d failed, %d warn" % (
        len(RESULTS) - len(fails), len(fails), len(warns)))
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
