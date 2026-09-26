"""
Southern Spear - Dry River vertical-slice blockout generator.

Generates the playable blockout described in Docs/MAPS_DRYRIVER.md.
Every dimension here traces to a gameplay requirement documented in that
spec; nothing is arbitrary.

This is a GREYBOX. It deliberately uses untextured primitives. A greybox
that looks finished stops being treated as one.

Run headless:
    blender -b --factory-startup --python Tools/Blender/dryriver_blockout.py

Outputs (relative to this file, ../../Content/Art/Blockout/):
    SS_MAP_DryRiver_01_HI.blend   - source, version controlled in LFS
    SS_MAP_DryRiver_01.fbx        - game import mesh
    SS_MAP_DryRiver_01_Layout.csv - gameplay marker positions for UE

Standards (TECHNICAL_DESIGN_DOCUMENT.md 12.2):
    Metric units, +Y forward, +Z up, transforms applied, SS_ naming.
"""

import math
import os
import random
import sys

import bpy
from mathutils import Vector

# The layout spec and the terrain function live in a pure-Python module with no
# bpy dependency, because the CI validator needs to check dressing against the
# same ground the blockout is built on and Blender is not available there. See
# Tools/Common/dryriver_spec.py for why this must not be duplicated.
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Common")))
from dryriver_spec import (  # noqa: E402
    PLAY_WIDTH,
    PLAY_DEPTH,
    VERTICAL_RELIEF,
    DEPLOY_ZONE_DEPTH,
    DEPLOY_OFFSET,
    OBJ_A_POS,
    OBJ_B_POS,
    CREEK_MEAN_Y,
    CREEK_DEPTH,
    CREEK_HALF_WIDTH,
    CREEK_MEANDER,
    FARM_POS,
    PROTECTED,
    terrain_height,
    is_protected,
)

# ---------------------------------------------------------------------------
# Blockout-only constants. Anything the dressing layer also needs to know lives
# in dryriver_spec.py instead.
# ---------------------------------------------------------------------------

SHED_SIZE = (18.0, 10.0, 6.0)
HOUSE_SIZE = (12.0, 9.0, 4.0)

FENCE_X = 10.0              # m, post-and-rail runs north-south
FENCE_FROM_Y = -60.0
FENCE_TO_Y = 60.0

ROCK_COUNT = 40
TREE_COUNT = 20
SCRUB_COUNT = 30
COVER_PER_ROUTE = 1 / 12.0  # one object per 12 m of intended route

RNG = random.Random(20260926)  # Fixed seed: the map must be reproducible.

COLLECTIONS = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def reset_scene():
    """Clear the default scene so the script is idempotent."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.meshes:
        bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        bpy.data.materials.remove(block)


def make_collection(name):
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    COLLECTIONS[name] = coll
    return coll


def link(obj, coll_name):
    """Move an object into a named collection."""
    for coll in list(obj.users_collection):
        coll.objects.unlink(obj)
    COLLECTIONS[coll_name].objects.link(obj)
    return obj


def emit(obj, name, coll_name):
    """Name an object, apply its transform, and file it."""
    obj.name = name
    if obj.data is not None:
        obj.data.name = f"{name}_Mesh"
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return link(obj, coll_name)


def new_box(name, size, location, coll_name, collection_name):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.scale = size
    emit(obj, name, coll_name)
    return obj


# ---------------------------------------------------------------------------
# Terrain
# ---------------------------------------------------------------------------

def build_terrain():
    """Subdivided grid, displaced by terrain_height. Flat shaded (greybox)."""
    cols, rows = 104, 72          # 2.5 m resolution
    sx, sy = PLAY_WIDTH, PLAY_DEPTH

    verts, faces = [], []
    for j in range(rows + 1):
        for i in range(cols + 1):
            u = i / cols
            v = j / rows
            x = -sx / 2.0 + u * sx
            y = -sy / 2.0 + v * sy
            verts.append((x, y, terrain_height(x, y)))

    def vid(i, j):
        return j * (cols + 1) + i

    for j in range(rows):
        for i in range(cols):
            a, b = vid(i, j), vid(i + 1, j)
            c, d = vid(i + 1, j + 1), vid(i, j + 1)
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new("SS_MAP_DryRiver_Terrain_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    obj = bpy.data.objects.new("SS_MAP_DryRiver_Terrain", mesh)
    bpy.context.scene.collection.objects.link(obj)

    for poly in mesh.polygons:
        poly.use_smooth = False          # flat shade: unmistakably a greybox
    emit(obj, "SS_MAP_DryRiver_Terrain", "SS_Terrain")
    return obj


# ---------------------------------------------------------------------------
# Farmstead
# ---------------------------------------------------------------------------

def build_farm():
    make_collection("SS_ObjB_Farmstead")
    fx, fy = FARM_POS

    shed = new_box(
        "SS_MAP_DryRiver_Farm_Shed", SHED_SIZE,
        (fx, fy, SHED_SIZE[2] / 2.0), "SS_ObjB_Farmstead", "SS_ObjB_Farmstead")

    hx, hy = fx - 22.0, fy + 9.0
    house = new_box(
        "SS_MAP_DryRiver_Farm_Residence", HOUSE_SIZE,
        (hx, hy, HOUSE_SIZE[2] / 2.0), "SS_ObjB_Farmstead", "SS_ObjB_Farmstead")

    # Stock pens - post-and-rail, chest high: soft cover that blocks
    # movement but not fire.
    for i in range(4):
        px = fx + 26.0 + i * 7.0
        rail = new_box(
            f"SS_MAP_DryRiver_Farm_Pens_Rail_{i:02d}", (7.0, 0.25, 1.15),
            (px, fy - 4.0, 0.6), "SS_ObjB_Farmstead", "SS_ObjB_Farmstead")
    return shed, house


# ---------------------------------------------------------------------------
# Objective markers and deployments (exported to CSV for Unreal)
# ---------------------------------------------------------------------------

LAYOUT_ROWS = []


def record(name, x, y, z, kind):
    LAYOUT_ROWS.append((name, x, y, z, kind))


def build_markers():
    make_collection("SS_LayoutMarkers")
    for nm, pos, kind in [
        ("SS_MAP_DryRiver_ObjA_WaterPoint", OBJ_A_POS, "Objective"),
        ("SS_MAP_DryRiver_ObjB_Farmstead", OBJ_B_POS, "Objective"),
        ("SS_MAP_DryRiver_DeployAlpha", (0.0, -DEPLOY_OFFSET), "Deployment"),
        ("SS_MAP_DryRiver_DeployBravo", (0.0, DEPLOY_OFFSET), "Deployment"),
    ]:
        x, y = pos
        z = terrain_height(x, y)
        new_box(nm, (2.0, 2.0, 0.3), (x, y, z + 0.15),
                "SS_LayoutMarkers", "SS_LayoutMarkers")
        record(nm, x, y, z, kind)


# ---------------------------------------------------------------------------
# Cover scatter
# ---------------------------------------------------------------------------

def scatter_points(count, avoid_farm=True):
    """Deterministic points inside the playable area, clear of key locations."""
    pts = []
    tries = 0
    while len(pts) < count and tries < count * 200:
        tries += 1
        x = RNG.uniform(-PLAY_WIDTH / 2 + 6, PLAY_WIDTH / 2 - 6)
        y = RNG.uniform(-PLAY_DEPTH / 2 + 6, PLAY_DEPTH / 2 - 6)
        if is_protected(x, y):
            continue
        if avoid_farm and math.hypot(x - FARM_POS[0], y - FARM_POS[1]) < 34.0:
            continue
        pts.append((x, y))
    return pts


def build_cover():
    make_collection("SS_Cover_Rocks")
    make_collection("SS_Cover_Trees")
    make_collection("SS_Cover_Scrub")

    for i, (x, y) in enumerate(scatter_points(ROCK_COUNT)):
        z = terrain_height(x, y)
        s = RNG.uniform(0.9, 2.4)
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=1, radius=s,
            location=(x, y, z + s * 0.45))
        o = bpy.context.active_object
        o.scale = (1.0, RNG.uniform(0.7, 1.3), RNG.uniform(0.5, 0.9))
        o.rotation_euler = (RNG.uniform(0, 0.4), RNG.uniform(0, 0.4),
                            RNG.uniform(0, math.tau))
        emit(o, f"SS_MAP_DryRiver_Cover_Rock_{i:03d}", "SS_Cover_Rocks")

    for i, (x, y) in enumerate(scatter_points(TREE_COUNT)):
        z = terrain_height(x, y)
        h = RNG.uniform(4.0, 7.0)
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=6, radius=0.22, depth=h, location=(x, y, z + h / 2))
        emit(bpy.context.active_object,
             f"SS_MAP_DryRiver_Cover_TreeTrunk_{i:03d}", "SS_Cover_Trees")
        bpy.ops.mesh.primitive_cone_add(
            vertices=7, radius1=RNG.uniform(1.3, 2.1), radius2=0.0,
            depth=h * 0.8, location=(x, y, z + h * 0.95))
        emit(bpy.context.active_object,
             f"SS_MAP_DryRiver_Cover_TreeCanopy_{i:03d}", "SS_Cover_Trees")

    for i, (x, y) in enumerate(scatter_points(SCRUB_COUNT)):
        z = terrain_height(x, y)
        bpy.ops.mesh.primitive_plane_add(
            size=RNG.uniform(1.8, 3.4), location=(x, y, z + 0.35))
        o = bpy.context.active_object
        o.rotation_euler = (0, 0, RNG.uniform(0, math.tau))
        emit(o, f"SS_MAP_DryRiver_Cover_Scrub_{i:03d}", "SS_Cover_Scrub")


def build_fence():
    make_collection("SS_Fence")
    span = FENCE_TO_Y - FENCE_FROM_Y
    segs = int(span / 6.0)
    for i in range(segs):
        y = FENCE_FROM_Y + i * 6.0 + 3.0
        z = terrain_height(FENCE_X, y)
        new_box(f"SS_MAP_DryRiver_Fence_Rail_{i:03d}", (0.14, 6.0, 1.1),
                (FENCE_X, y, z + 0.55), "SS_Fence", "SS_Fence")
    for i in range(segs + 1):
        y = FENCE_FROM_Y + i * 6.0
        z = terrain_height(FENCE_X, y)
        new_box(f"SS_MAP_DryRiver_Fence_Post_{i:03d}", (0.2, 0.2, 1.35),
                (FENCE_X, y, z + 0.65), "SS_Fence", "SS_Fence")


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def output_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "..", "Content", "Art", "Blockout"))


def export_all():
    out = output_dir()
    os.makedirs(out, exist_ok=True)

    blend = os.path.join(out, "SS_MAP_DryRiver_01_HI.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)

    fbx = os.path.join(out, "SS_MAP_DryRiver_01.fbx")
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.export_scene.fbx(
        filepath=fbx,
        use_selection=False,
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

    csv = os.path.join(out, "SS_MAP_DryRiver_01_Layout.csv")
    with open(csv, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("name,x,y,z,kind\n")
        for name, x, y, z, kind in LAYOUT_ROWS:
            fh.write(f"{name},{x:.3f},{y:.3f},{z:.3f},{kind}\n")

    print(f"EXPORTED_BLEND={blend}")
    print(f"EXPORTED_FBX={fbx}")
    print(f"EXPORTED_CSV={csv}")
    print(f"MARKERS={len(LAYOUT_ROWS)}")


def main():
    reset_scene()
    make_collection("SS_Terrain")

    build_terrain()
    build_farm()
    build_markers()
    build_cover()
    build_fence()

    objs = [o for o in bpy.data.objects if o.type == "MESH"]
    tris = sum(len(o.data.polygons) for o in objs)
    print(f"OBJECTS={len(objs)}")
    print(f"FACES={tris}")
    export_all()


if __name__ == "__main__":
    main()
