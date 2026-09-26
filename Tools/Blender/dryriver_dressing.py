"""
Southern Spear - Dry River dressing generator.

Dressing is the layer ON TOP of the structural blockout: scrub, vehicle wrecks,
crates, barrels, and fence runs. The blockout (dryriver_blockout.py) is the
playable shape; this is the stuff that makes a lane a lane. Keeping them
separate is what lets the blockout be replaced with real art later without
re-authoring a single placement.

THE POINT OF THIS TOOL IS THE CSV, NOT THE MESHES.

    Content/Art/Blockout/SS_MAP_DryRiver_02_Dressing.csv   point dressing
    Content/Art/Blockout/SS_MAP_DryRiver_02_Fences.csv      fence runs

Those two text files are the source of truth for dressing. Tools/Unreal/
dress_dryriver.py reads them and nothing else, so moving a fence or deleting
a wreck is a one-line diff that a level designer makes without opening the
editor. The meshes below are interchangeable greyboxes.

Existing CSVs are NEVER overwritten. Re-running this regenerates the mesh
library and leaves hand-placed dressing alone. Pass --force to discard edits
and start the layout over.

Run headless:
    blender -b --factory-startup --python Tools/Blender/dryriver_dressing.py
    blender -b --factory-startup --python Tools/Blender/dryriver_dressing.py -- --force

Outputs (relative to this file, ../../Content/Art/Blockout/):
    SS_Dressing_*.fbx     - one mesh per dressing type, each authored at the
                             ORIGIN so that all placement comes from the CSVs
                             and the FBX import can never bake in a transform
    SS_MAP_DryRiver_02_Dressing.csv / _Fences.csv - placement data

Standards (TECHNICAL_DESIGN_DOCUMENT.md 12.2):
    Metric units, +Y forward, +Z up, transforms applied, SS_ naming.
"""

import math
import os
import random
import sys

import bpy

# The terrain function, the playable extents and the protected zones live in a
# shared pure-Python module. Importing rather than copying is a correctness
# requirement, not tidiness: if dressing carried its own terrain_height() the
# two would drift and the symptom would be dressing floating above the ground,
# which is invisible in a screenshot and tedious to find later. The same module
# is what Tools/verify_dressing.py uses in CI, where Blender does not exist.
sys.path.insert(
    0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Common"))
)
import dryriver_spec as spec  # noqa: E402

RNG_SEED = 20260927          # one day past the blockout seed; never reuse it
RNG = random.Random(RNG_SEED)

# ---------------------------------------------------------------------------
# Placement rules. Every number here is a gameplay constraint, not taste.
# ---------------------------------------------------------------------------

EDGE_INSET = 8.0             # m, keep dressing off the map edge
MIN_SPACING = 3.0            # m, dressing must not clump into a blob

# Clearance from a protected zone, by type. A wreck is a sight-line breaker and
# must not be allowed to seal an objective; scrub can sit much closer because it
# conceals without blocking.
CLEARANCE = {
    "wreck": 14.0,
    "crate": 9.0,
    "barrel": 8.0,
    "scrub": 2.0,
}
DEFAULT_CLEARANCE = 6.0

# Solid dressing must not stand where a fence rail will be. The level pass snaps
# every height with a downward ray, so a crate on a fence line would be built on
# top of the rail. Must match FENCE_DRESSING_CLEARANCE in Tools/verify_dressing.py.
FENCE_DRESSING_CLEARANCE = 1.5

# Fence runs: a run is a straight line of posts with rails. Runs are authored
# explicitly, never scattered, because a fence is a long object and random
# placement produces walls that bisect the map.
FENCE_MAX_LENGTH = 45.0      # m, longer than this and it stops being a fence
FENCE_MIN_LENGTH = 8.0
FENCE_POST_SPACING = 2.5     # m
FENCE_RAIL_HEIGHTS = (0.55, 1.05)   # m, two rails, post-and-rail

# Counts are deliberately modest. Dry River is a small map (260 x 180 m) and
# the blockout already carries ~90 cover objects; piling on more would make it
# unreadable and untestable rather than richer.
SCRUB_COUNT = 46
WRECK_COUNT = 3
CRATE_COUNT = 8
BARREL_COUNT = 10

DRESSING_CSV = "SS_MAP_DryRiver_02_Dressing.csv"
FENCES_CSV = "SS_MAP_DryRiver_02_Fences.csv"

# ---------------------------------------------------------------------------
# Fence runs. Authored, not generated, with the reason for each one.
# ---------------------------------------------------------------------------

FENCE_RUNS = [
    # Farm paddock, east of the farmstead. OBJ B sits 38 m west of this line so
    # attackers must cross open ground before they can use the fence for cover.
    ("SS_DryRiver_Fence_PaddockEast", 78.0, 34.0, 78.0, 74.0),
    # Paddock return, closing the corner so the run is not a lone line.
    ("SS_DryRiver_Fence_PaddockNorth", 78.0, 74.0, 100.0, 74.0),
    # Creek-side boundary, west of the water point. Breaks the long west lane
    # that would otherwise let Bravo flank OBJ A without crossing cover.
    ("SS_DryRiver_Fence_CreekWest", -74.0, -34.0, -74.0, 6.0),
    # North-east boundary. Well clear of the Bravo deployment circle, whose 70 m
    # radius reaches most of the way across the northern half of the map.
    ("SS_DryRiver_Fence_NorthEastBoundary", 100.0, 70.0, 122.0, 70.0),
    # Creek-bank run on the central band. Sits where the ground is walkable
    # between the two deployment circles, so it crosses no protected zone.
    ("SS_DryRiver_Fence_CreekBankSouth", 6.0, 10.0, 18.0, 10.0),
    # West mid-line. Cuts the long western approach to OBJ A, which would
    # otherwise let one team arrive with no contact at all.
    ("SS_DryRiver_Fence_WestMidLine", -96.0, -12.0, -96.0, 12.0),
    # South bank, east of centre.
    ("SS_DryRiver_Fence_SouthBankEast", 60.0, -14.0, 78.0, -14.0),
]

# Wrecks are placed by hand for the same reason fences are: each one has to
# serve a specific sight line, and random placement cannot be reasoned about.
# They are NOT exempt from the clearance rules - the first version of this file
# hand-placed them without checking, and Tools/verify_dressing.py failed CI with
# two wrecks inside a deployment zone. Hand placement overrides WHERE, never
# WHETHER, and the check below runs on every wreck exactly as it does on scatter.
WRECKS = [
    ("SS_DryRiver_Wreck_WestBank", -52.0, -8.0, 20.0),
    ("SS_DryRiver_Wreck_EastRise", 64.0, 20.0, 118.0),
    ("SS_DryRiver_Wreck_CreekNorth", -44.3, 13.5, 62.0),
]


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def seg_point_distance(ax, ay, bx, by, px, py):
    """Re-exported from the shared spec so callers of this module have one place
    to look. The implementation lives there, not here."""
    return spec.seg_point_distance(ax, ay, bx, by, px, py)


def run_clears_protected(name, ax, ay, bx, by, extra=0.0):
    ok, why = spec.run_clears_protected(ax, ay, bx, by, extra=extra)
    if not ok:
        return False, "{} {}".format(name, why)
    return True, ""


def inside_play_area(x, y, inset=EDGE_INSET):
    return spec.inside_play_area(x, y, inset)


def clear_of_protected(x, y, clearance):
    for px, py, pr in spec.PROTECTED:
        if math.hypot(x - px, y - py) < pr + clearance:
            return False
    return True


def new_box(name, size, location):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.scale = size
    return obj


def new_cylinder(name, radius, depth, location, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12, radius=radius, depth=depth, location=location, rotation=rotation
    )
    return bpy.context.active_object


def new_ico(name, radius, location, subdivisions=1):
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=subdivisions, radius=radius, location=location
    )
    return bpy.context.active_object


def join_objects(name, objs):
    """Join parts into one mesh, then collapse the result to the origin.

    Every dressing mesh is authored AT THE ORIGIN on purpose. If a mesh carried
    a baked-in world position, the FBX import would apply a transform we then
    have to reason about, and the CSV would no longer be the only source of
    placement truth. Origin-only meshes make that impossible to get wrong.
    """
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name + "_Mesh"

    # Bake scale and rotation, then move the origin to (0,0,0) with the
    # geometry relative to it.
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="BOUNDS")
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
    return obj


def export_single(obj, filepath):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=filepath,
        use_selection=True,
        apply_unit_scale=True,
        global_scale=1.0,
        apply_scale_options="FBX_SCALE_NONE",
        axis_forward="-Z",
        axis_up="Y",
        object_types={"MESH"},
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        path_mode="COPY",
    )


# ---------------------------------------------------------------------------
# Mesh library
# ---------------------------------------------------------------------------


def make_fence_post():
    """A 1.4 m square post. Base sits on the ground, so local origin is the
    foot of the post; z = height/2 keeps it that way."""
    h = 1.4
    return join_objects("SS_Dressing_FencePost", [new_box("post", (0.12, 0.12, h), (0, 0, h / 2))])


def make_fence_rail():
    """A 1.0 m rail segment along +X, authored at unit length.

    The level pass scales X by the gap it actually needs, so post spacing stays
    a data decision instead of being baked into the mesh.
    """
    return join_objects("SS_Dressing_FenceRail", [new_box("rail", (1.0, 0.05, 0.09), (0, 0, 0))])


def make_wreck():
    """A stripped vehicle: body, cabin, and two wheels. Deliberately anonymous —
    a recognisable real-world vehicle would be a trademark problem, and the
    opposing force is fictional anyway (see LICENCE_REGISTER.md)."""
    parts = [
        new_box("body", (4.60, 1.90, 0.85), (0, 0, 0.70)),
        new_box("cabin", (1.90, 1.75, 0.80), (-0.55, 0, 1.50)),
        new_cylinder("wheel_fl", 0.42, 0.30, (1.45, 0.95, 0.42), (math.pi / 2, 0, 0)),
        new_cylinder("wheel_fr", 0.42, 0.30, (1.45, -0.95, 0.42), (math.pi / 2, 0, 0)),
        new_cylinder("wheel_rl", 0.42, 0.30, (-1.45, 0.95, 0.42), (math.pi / 2, 0, 0)),
        new_cylinder("wheel_rr", 0.42, 0.30, (-1.45, -0.95, 0.42), (math.pi / 2, 0, 0)),
    ]
    return join_objects("SS_Dressing_Wreck", parts)


def make_scrub():
    """Low scrub. Conveys ground, breaks up sight lines at ankle height, and
    never fully blocks movement — which is why it can sit close to objectives."""
    parts = [
        new_ico("s0", 0.62, (0.00, 0.00, 0.34), 1),
        new_ico("s1", 0.44, (0.52, 0.18, 0.26), 1),
        new_ico("s2", 0.38, (-0.40, -0.30, 0.22), 1),
    ]
    return join_objects("SS_Dressing_Scrub", parts)


def make_crate():
    return join_objects("SS_Dressing_Crate", [new_box("crate", (0.90, 0.90, 0.90), (0, 0, 0.45))])


def make_barrel():
    return join_objects(
        "SS_Dressing_Barrel", [new_cylinder("barrel", 0.29, 0.88, (0, 0, 0.44), (0, 0, 0))]
    )


MESH_BUILDERS = [
    ("FencePost", make_fence_post),
    ("FenceRail", make_fence_rail),
    ("Wreck", make_wreck),
    ("Scrub", make_scrub),
    ("Crate", make_crate),
    ("Barrel", make_barrel),
]


# ---------------------------------------------------------------------------
# Placement data
# ---------------------------------------------------------------------------


def clear_of_fence_lines(x, y, kind):
    """Scrub is exempt: it is non-colliding and low, so it neither obstructs a
    fence nor intercepts the height ray. Everything solid must stand clear."""
    if kind == "scrub":
        return True
    for _name, ax, ay, bx, by in FENCE_RUNS:
        if seg_point_distance(ax, ay, bx, by, x, y) < FENCE_DRESSING_CLEARANCE:
            return False
    return True


def scatter(kind, count, placed):
    """Seeded rejection sampling with per-type clearance and minimum spacing.

    Rejection is deterministic given the seed, and every candidate is rejected
    for a stated reason, so a run that comes up short says why instead of
    silently under-filling the map.
    """
    clearance = CLEARANCE.get(kind, DEFAULT_CLEARANCE)
    results = []
    tries = 0
    while len(results) < count and tries < count * 400:
        tries += 1
        x = RNG.uniform(-spec.PLAY_WIDTH / 2 + EDGE_INSET, spec.PLAY_WIDTH / 2 - EDGE_INSET)
        y = RNG.uniform(-spec.PLAY_DEPTH / 2 + EDGE_INSET, spec.PLAY_DEPTH / 2 - EDGE_INSET)

        if not clear_of_protected(x, y, clearance):
            continue
        if not clear_of_fence_lines(x, y, kind):
            continue
        if any(math.hypot(x - px, y - py) < MIN_SPACING for _, px, py in placed):
            continue
        # The farmstead is already modelled by the blockout; keep dressing off
        # the building footprint so nothing intersects the shed or the house.
        if math.hypot(x - spec.FARM_POS[0], y - spec.FARM_POS[1]) < 16.0:
            continue

        rot_y = RNG.uniform(0.0, 360.0)
        scale = 1.0 if kind != "scrub" else RNG.uniform(0.8, 1.35)
        z = spec.terrain_height(x, y)
        results.append(
            {
                "name": "SS_DryRiver_{}_{:02d}".format(kind.capitalize(), len(results) + 1),
                "type": kind,
                "x": round(x, 3),
                "y": round(y, 3),
                "z": round(z, 3),
                "rot_y": round(rot_y, 2),
                "scale": round(scale, 3),
            }
        )
        placed.append((results[-1]["name"], x, y))

    if len(results) < count:
        print(
            "  NOTE {} placed {} of {} requested after {} tries "
            "(clearance {:.1f}m / spacing {:.1f}m)".format(
                kind, len(results), count, tries, clearance, MIN_SPACING
            )
        )
    return results


def build_dressing_rows():
    placed = []
    rows = []

    rows.extend(scatter("scrub", SCRUB_COUNT, placed))
    rows.extend(scatter("crate", CRATE_COUNT, placed))
    rows.extend(scatter("barrel", BARREL_COUNT, placed))

    for name, x, y, rot in WRECKS:
        # Hand-placed wreck, still law-abiding. Refuse rather than emit, so a
        # bad hand edit fails here with a reason instead of reaching the CSV.
        need = CLEARANCE.get("wreck", DEFAULT_CLEARANCE)
        if not clear_of_protected(x, y, need):
            print("  REJECT {} at ({:.1f},{:.1f}): inside a protected zone (needs {:.1f}m)".format(
                name, x, y, need))
            continue
        if not inside_play_area(x, y):
            print("  REJECT {} at ({:.1f},{:.1f}): outside the playable area".format(name, x, y))
            continue
        if not clear_of_fence_lines(x, y, "wreck"):
            print("  REJECT {} at ({:.1f},{:.1f}): too close to a fence line".format(name, x, y))
            continue
        z = spec.terrain_height(x, y)
        rows.append(
            {
                "name": name,
                "type": "wreck",
                "x": round(x, 3),
                "y": round(y, 3),
                "z": round(z, 3),
                "rot_y": round(rot, 2),
                "scale": 1.0,
            }
        )
        placed.append((name, x, y))

    return rows


def validate_fence_runs():
    """Reject any run that is too long, too short, or crosses a protected zone.

    This is the check that stops a fence from quietly becoming a wall across the
    map. It runs at generation time AND again in Tools/verify_dressing.py, so
    hand-edited CSVs get the same protection as generated ones.
    """
    good = []
    for name, ax, ay, bx, by in FENCE_RUNS:
        length = math.hypot(bx - ax, by - ay)
        if length > FENCE_MAX_LENGTH:
            print("  REJECT {}: {:.1f}m exceeds the {:.1f}m limit".format(name, length, FENCE_MAX_LENGTH))
            continue
        if length < FENCE_MIN_LENGTH:
            print("  REJECT {}: {:.1f}m is below the {:.1f}m minimum".format(name, length, FENCE_MIN_LENGTH))
            continue
        ok, why = run_clears_protected(name, ax, ay, bx, by, extra=4.0)
        if not ok:
            print("  REJECT {}".format(why))
            continue
        good.append((name, ax, ay, bx, by, length))
    return good


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def output_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "..", "Content", "Art", "Blockout"))


def write_dressing_csv(rows, path):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("name,type,x,y,z,rot_y,scale\n")
        for r in rows:
            fh.write(
                "{name},{type},{x:.3f},{y:.3f},{z:.3f},{rot_y:.2f},{scale:.3f}\n".format(**r)
            )


def write_fences_csv(runs, path):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("name,x1,y1,x2,y2,post_spacing\n")
        for name, ax, ay, bx, by, _length in runs:
            fh.write(
                "{},{:.3f},{:.3f},{:.3f},{:.3f},{:.2f}\n".format(
                    name, ax, ay, bx, by, FENCE_POST_SPACING
                )
            )


def main():
    force = "--force" in sys.argv
    out = output_dir()
    os.makedirs(out, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    coll = bpy.data.collections.new("SS_Dressing")
    bpy.context.scene.collection.children.link(coll)

    print("BUILDING MESHES")
    total_faces = 0
    for name, builder in MESH_BUILDERS:
        obj = builder()
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        coll.objects.link(obj)
        export_single(obj, os.path.join(out, "SS_Dressing_{}.fbx".format(name)))
        faces = len(obj.data.polygons)
        total_faces += faces
        print("  SS_Dressing_{}.fbx  faces={}".format(name, faces))

    blend = os.path.join(out, "SS_Dressing_HI.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)

    print("VALIDATING FENCE RUNS")
    runs = validate_fence_runs()
    for name, ax, ay, bx, by, length in runs:
        print("  OK {} {:.1f}m".format(name, length))

    rows = build_dressing_rows()
    print("DRESSING ROWS={}".format(len(rows)))
    by_kind = {}
    for r in rows:
        by_kind[r["type"]] = by_kind.get(r["type"], 0) + 1
    print("BY_TYPE={}".format(sorted(by_kind.items())))
    print("FENCE_RUNS={}".format(len(runs)))
    print("TOTAL_FACES={}".format(total_faces))

    dpath = os.path.join(out, DRESSING_CSV)
    fpath = os.path.join(out, FENCES_CSV)

    # Placement data is the source of truth and is never silently clobbered.
    for path, writer, payload, label in (
        (dpath, write_dressing_csv, rows, DRESSING_CSV),
        (fpath, write_fences_csv, runs, FENCES_CSV),
    ):
        if os.path.isfile(path) and not force:
            print("KEPT EXISTING {} (pass --force to regenerate)".format(label))
        else:
            writer(payload, path)
            print("WROTE {}".format(label))

    print("BLEND={}".format(blend))


if __name__ == "__main__":
    main()
