"""
Southern Spear - Red Gum Station homestead generator (class F, original work).

WHY THIS EXISTS

Red Gum's centre objective is labelled "Homestead" and nothing stands on it. The
Rural Australia pack has trees, logs, rocks, fences and signs but no building
mesh, and the only other installed packs are the wrong continent or the wrong
culture. So the station is modelled here, from scratch, by us: that keeps the
map's originality intact (ADR-013, ADR-021) and costs no licence work.

The compound is the map's hard-cover anchor. Objective B sits at the centre of
a 720 x 600 m play space, and a 1 km paddock map with only trees and wire is a
shooting gallery: the farmhouse and shearing shed give the centre objective
something to fight around, break the long axial sightline, and give players a
landmark they can navigate by from either deployment.

WHAT IT EXPORTS

One FBX per structure, each authored at the ORIGIN with transforms applied, so
every placement decision lives in the CSV and the import can never bake a
transform into the mesh. Plus the .blend source, which is the authoritative
artwork per ADR-009 (the FBX is a derivative).

    Content/Art/Environment/RedGum/SS_RedGum_Homestead.blend
    Content/Art/Environment/RedGum/SS_RedGum_<Structure>.fbx
    Content/Art/Environment/RedGum/SS_RedGum_Homestead_Layout.csv

CSV columns: name,structure,x_m,y_m,yaw_deg,scale
    x_m, y_m are Blender-space METRES relative to the objective-B capture
    point; Tools/Unreal/import_redgum_homestead.py converts to UE centimetres
    and negates Y, following the same handedness rule as the Dry River dressing
    pass (the FBX is Z-up Blender, the engine is Z-up left-handed).

MATERIAL SLOTS

Five slots, named, and mapped to authored UE materials at import:
    Wall    - painted weatherboard cladding
    Roof    - corrugated iron, red oxide
    Timber  - posts, rails, trims, decking
    Glass   - windows
    Metal   - galvanised: tank, windmill, chimney cowl

DIMENSIONS TRACE TO GAMEPLAY

Every dimension is a gameplay number, not taste:
    farmhouse 12.0 x 8.0 m, 2.7 m eaves - two rooms, verandah deep enough to
        stand in and shoot from, which is the whole point of a homestead
        objective; a verandah you cannot stand in is a wall.
    verandah 2.6 m deep, 1.0 m above grade - chest-high cover on the open
        side, head-high on the enclosed side. Both are readable as cover.
    shearing shed 16.0 x 9.0 m, 4.5 m - the tall hard cover on the compound's
        north side; 16 m so it screens the homestead from the north paddock
        approach but not from every angle.
    stock pens rails at 0.55 m and 1.05 m - the Dry River post-and-rail
        heights, so the cover classification already measured on that map
        carries over instead of inventing a new number.
    water tank 3.0 m diameter on a 2.0 m stand - a landmark visible over the
        tree lines from both deployments, which is what makes a 1 km map
        navigable without a minimap.

Run headless:
    blender -b --factory-startup --python Tools/Blender/redgum_homestead.py

Standards (TECHNICAL_DESIGN_DOCUMENT.md 12.2):
    Metric units, +Y forward, +Z up, transforms applied, SS_ naming.
"""

import math
import os
import random

import bpy

OUT_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                 "Content", "Art", "Environment", "RedGum"))

RNG = random.Random(20260928)  # fixed seed: the station must be reproducible

# Slot names, in the order they are created. The import maps by name, but a
# stable order means a slot mismatch is visible in the mesh rather than silent.
SLOTS = ("Wall", "Roof", "Timber", "Glass", "Metal")
MAT = {name: None for name in SLOTS}

# The compound layout, in metres relative to objective B's capture point.
# +Y is "north" in Blender space. The farmhouse faces east onto the yard, the
# shed's open front faces south into it, so the two hard-cover masses make an
# L that fights the centre objective from two sides instead of one.
LAYOUT = [
    # name,                  structure,      x,     y,   yaw,   scale
    ("Farmhouse",            "farmhouse",   -7.5,   6.0,  12.0,  1.00),
    ("ShearingShed",         "shedding_shed", 11.0, -5.0, -8.0,  1.00),
    ("StockPens",            "stock_pens",   1.0,   0.5,   0.0,  1.00),
    ("WaterTank",            "water_tank",  -1.5,  -6.5,   0.0,  1.00),
    ("Windmill",             "windmill",     1.5,  -6.5,   0.0,  1.00),
    ("Hut_North",            "hut",        -14.0,-168.0, 25.0,  0.95),
    ("Hut_South",            "hut",         18.0, 152.0,-15.0,  0.95),
]

# Keeping dressing off the structures. The dressing pass reads this so a rerun
# cannot drop a gum tree through the shearing shed roof.
PROTECTED = [
    ("homestead yard", -9.0, 7.0, 13.0, 11.0, 6.0),   # name, x, y, half_x, half_y, pad
    ("hut north", -14.0, -168.0, 5.0, 5.0, 6.0),
    ("hut south", 18.0, 152.0, 5.0, 5.0, 6.0),
]


# ---------------------------------------------------------------------------
# Scene helpers
# ---------------------------------------------------------------------------

def reset_scene():
    """Clear the default scene so the script is idempotent."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.meshes):
        bpy.data.meshes.remove(block)
    for block in list(bpy.data.materials):
        bpy.data.materials.remove(block)


def make_materials():
    for name in SLOTS:
        mat = bpy.data.materials.new("SS_RedGum_" + name)
        mat.use_nodes = True
        # Flat viewport colour so the .blend is readable without UVs; the real
        # look is the authored UE material assigned at import.
        mat.diffuse_color = {
            "Wall": (0.62, 0.63, 0.55, 1.0),
            "Roof": (0.45, 0.22, 0.14, 1.0),
            "Timber": (0.36, 0.30, 0.24, 1.0),
            "Glass": (0.05, 0.07, 0.08, 1.0),
            "Metal": (0.55, 0.57, 0.58, 1.0),
        }[name]
        MAT[name] = mat


def apply(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return obj


def tag(obj, slot):
    """Assign one material slot to every face of obj."""
    obj.data.materials.clear()
    obj.data.materials.append(MAT[slot])
    for poly in obj.data.polygons:
        poly.material_index = 0
        poly.use_smooth = False  # flat shade: this is low-poly station geometry
    return obj


def box(name, size, loc, slot, rot=(0.0, 0.0, 0.0)):
    """Axis-aligned box by FULL dimensions in metres, then applied."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    return apply(tag(obj, slot))


def cylinder(name, radius, depth, loc, slot, rot=(0.0, 0.0, 0.0), verts=16):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    return apply(tag(obj, slot))


def gable(name, length_x, half_depth, height, loc, slot):
    """A right-triangle prism, ridge along X. Used for roof ends and hut gables."""
    d, h = half_depth, height
    verts = [
        (-length_x / 2.0, -d, 0.0), (length_x / 2.0, -d, 0.0),
        (length_x / 2.0, 0.0, h), (-length_x / 2.0, 0.0, h),
        (-length_x / 2.0, d, 0.0), (length_x / 2.0, d, 0.0),
    ]
    faces = [(0, 1, 2, 3), (3, 2, 5, 4), (0, 4, 5, 1), (0, 3, 4), (1, 5, 2)]
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = loc
    return apply(tag(obj, slot))


def join(objects, name):
    """Join a structure's parts into one mesh, origin at the world origin."""
    objects = [o for o in objects if o is not None]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name + "_Mesh"
    # The import scales the actor, so any residual non-uniform scale here would
    # compound with it. Apply everything.
    return apply(obj)


# ---------------------------------------------------------------------------
# Structures
# ---------------------------------------------------------------------------

def build_farmhouse():
    """Weatherboard farmhouse with a deep verandah. Returns a list of parts."""
    L, W, EAVE = 12.0, 8.0, 2.7
    VER_D, VER_H = 2.6, 1.0
    RIDGE = EAVE + 1.9
    VERAND = (-1.0, W / 2.0 + VER_D / 2.0)  # verandah on the +Y face
    parts = []

    # Floor slab, so the house is not a floating box on uneven ground.
    parts.append(box("RG_Farmhouse_Slab", (L, W, 0.35), (0, 0, 0.17), "Wall"))
    parts.append(box("RG_Farmhouse_Deck", (L, VER_D, VER_D * 0.06 + 0.15),
                     (0, VERAND[1], VER_H - 0.1), "Timber"))

    # Walls, as four separate slabs so the interior is hollow and the windows
    # can be recessed. Solid walls would be cheaper and would read as a bunker.
    t = 0.15
    parts.append(box("RG_Farmhouse_Wall_S", (L, t, EAVE), (0, -W / 2.0, EAVE / 2.0), "Wall"))
    parts.append(box("RG_Farmhouse_Wall_N", (L, t, EAVE - VER_H), (0, W / 2.0, (EAVE + VER_H) / 2.0), "Wall"))
    parts.append(box("RG_Farmhouse_Wall_W", (t, W, EAVE), (-L / 2.0, 0, EAVE / 2.0), "Wall"))
    parts.append(box("RG_Farmhouse_Wall_E", (t, W, EAVE), (L / 2.0, 0, EAVE / 2.0), "Wall"))

    # Gable ends above the eaves.
    for i, x in enumerate((-L / 2.0, L / 2.0)):
        parts.append(gable("RG_Farmhouse_Gable_%d" % i, t + 0.02, W / 2.0, RIDGE - EAVE,
                           (x, 0, EAVE), "Wall"))

    # Two roof planes. Slight overhang past the walls is what makes a roof read
    # as a roof at a distance rather than as a wedge.
    pitch = math.atan2(RIDGE - EAVE, W / 2.0)
    slope_len = math.hypot(RIDGE - EAVE, W / 2.0) + 0.45
    for sign in (1.0, -1.0):
        parts.append(box("RG_Farmhouse_Roof_%s" % ("N" if sign > 0 else "S"),
                         (L + 0.7, slope_len, 0.12),
                         (0.0, sign * (W / 4.0), (EAVE + RIDGE) / 2.0),
                         "Roof", rot=(sign * pitch, 0.0, 0.0)))
    # Verandah roof, a shallower single fall away from the wall.
    v_pitch = math.atan2(VER_H + 0.35, VER_D)
    parts.append(box("RG_Farmhouse_Verandah_Roof", (L + 0.7, math.hypot(VER_H + 0.35, VER_D) + 0.3, 0.12),
                     (0.0, W / 2.0 + VER_D / 2.0, EAVE + (VER_H + 0.35) / 2.0),
                     "Roof", rot=(v_pitch, 0.0, 0.0)))

    # Verandah posts, set back from the deck edge so they do not block the
    # sightline a player is meant to have from the deck.
    for x in (-L / 2.0 + 0.5, -L / 4.0, L / 4.0, L / 2.0 - 0.5):
        parts.append(box("RG_Farmhouse_Post_%0.0f" % (x * 100), (0.18, 0.18, EAVE + 0.5),
                         (x, VERAND[1] + VER_D / 2.0 - 0.3, (EAVE + 0.5) / 2.0), "Timber"))
    parts.append(box("RG_Farmhouse_Beam", (L + 0.3, 0.2, 0.28),
                     (0, VERAND[1] + VER_D / 2.0 - 0.3, EAVE + 0.36), "Timber"))

    # Chimney: hard cover on the roof, and the only vertical above the ridge.
    parts.append(box("RG_Farmhouse_Chimney", (0.9, 0.9, RIDGE + 1.1),
                     (L / 2.0 - 1.8, -1.2, (RIDGE + 1.1) / 2.0), "Wall"))
    parts.append(box("RG_Farmhouse_Chimney_Cowl", (1.15, 1.15, 0.14),
                     (L / 2.0 - 1.8, -1.2, RIDGE + 1.17), "Metal"))

    # Windows and a door, inset into the wall line. A window flush with the
    # cladding is a decal; inset with a sill, it reads as an opening.
    win = (1.3, 0.12, 1.2)
    sill = 0.95
    for i, x in enumerate((-4.0, -1.3, 1.4, 4.1)):
        parts.append(box("RG_Farmhouse_Win_S_%d" % i, win, (x, -W / 2.0 - 0.02, sill + win[2] / 2.0), "Glass"))
        parts.append(box("RG_Farmhouse_Sill_S_%d" % i, (win[0] + 0.3, 0.3, 0.1),
                         (x, -W / 2.0 - 0.14, sill - 0.05), "Timber"))
    for i, x in enumerate((-3.0, 0.0, 3.2)):
        parts.append(box("RG_Farmhouse_Win_N_%d" % i, win, (x, W / 2.0 + 0.02, VER_H + 0.75 + win[2] / 2.0), "Glass"))
    # Front door, off-centre so the wall is not symmetrical.
    parts.append(box("RG_Farmhouse_Door", (1.0, 0.12, 2.05), (2.3, W / 2.0 + 0.02, VER_H + 1.03), "Timber"))
    # Steps up to the verandah deck.
    for i in range(3):
        parts.append(box("RG_Farmhouse_Step_%d" % i, (1.6, 0.34, 0.3),
                         (2.3, W / 2.0 + VER_D - 0.2 - i * 0.34, VER_H - 0.15 - i * 0.3), "Timber"))
    return parts


def build_shearing_shed():
    """Tall open-front shed. The tall mass that screens the yard from the north."""
    L, W, EAVE = 16.0, 9.0, 4.5
    RIDGE = EAVE + 1.6
    t = 0.18
    parts = [
        box("RG_Shed_Slab", (L, W, 0.3), (0, 0, 0.15), "Wall"),
        box("RG_Shed_Wall_N", (L, t, EAVE), (0, W / 2.0, EAVE / 2.0), "Wall"),
        box("RG_Shed_Wall_W", (t, W, EAVE), (-L / 2.0, 0, EAVE / 2.0), "Wall"),
        box("RG_Shed_Wall_E", (t, W, EAVE), (L / 2.0, 0, EAVE / 2.0), "Wall"),
    ]
    # Front wall with two open bays: a shed you cannot enter is a blockout, and
    # two openings make the south approach a fight rather than a corridor.
    for i, x in enumerate((-L / 2.0, 0.0, L / 2.0)):
        width = 1.6 if i == 1 else 2.2
        parts.append(box("RG_Shed_Pier_%d" % i, (width, t, EAVE),
                         (x, -W / 2.0, EAVE / 2.0), "Wall"))
    parts.append(box("RG_Shed_Lintel", (L, t, 0.7), (0, -W / 2.0, EAVE - 0.35), "Timber"))
    for i, x in enumerate((-L / 2.0, L / 2.0)):
        parts.append(gable("RG_Shed_Gable_%d" % i, t + 0.02, W / 2.0, RIDGE - EAVE,
                           (x, 0, EAVE), "Wall"))
    pitch = math.atan2(RIDGE - EAVE, W / 2.0)
    slope_len = math.hypot(RIDGE - EAVE, W / 2.0) + 0.5
    for sign in (1.0, -1.0):
        parts.append(box("RG_Shed_Roof_%s" % ("N" if sign > 0 else "S"),
                         (L + 0.8, slope_len, 0.14),
                         (0.0, sign * (W / 4.0), (EAVE + RIDGE) / 2.0),
                         "Roof", rot=(sign * pitch, 0.0, 0.0)))
    # Sliding door track on the open face, and a lean-to along the west wall.
    parts.append(box("RG_Shed_Door_Track", (3.2, 0.16, 0.16), (0, -W / 2.0 - 0.12, 2.35), "Metal"))
    parts.append(box("RG_Shed_Leanto_Roof", (6.0, 2.2, 0.12), (-L / 2.0 + 3.0, -W / 2.0 - 1.0, 2.5),
                     "Roof", rot=(0.32, 0.0, 0.0)))
    for i, y in enumerate((-W / 2.0 - 1.9, -W / 2.0 - 0.2)):
        parts.append(box("RG_Shed_Leanto_Post_%d" % i, (0.16, 0.16, 2.45),
                         (-L / 2.0 + 0.4, y, 1.22), "Timber"))
    parts.append(box("RG_Shed_Leanto_Post_C", (0.16, 0.16, 2.45),
                     (-L / 2.0 + 5.6, -W / 2.0 - 1.0, 1.22), "Timber"))
    return parts


def build_stock_pens():
    """Post-and-rail pens at the Dry River rail heights (0.55 m, 1.05 m)."""
    parts = []
    RAILS = (0.55, 1.05)
    SPACING = 2.5
    post = 0.12
    runs = [
        ((-9.0, -6.5), (9.0, -6.5)),
        ((-9.0, 6.5), (9.0, 6.5)),
        ((-9.0, -6.5), (-9.0, 6.5)),
    ]
    for r, (a, b) in enumerate(runs):
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(2, int(round(length / SPACING)) + 1)
        yaw = math.atan2(b[1] - a[1], b[0] - a[0])
        for i in range(n):
            t = i / float(n - 1)
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            parts.append(box("RG_Pen_Post_%d_%d" % (r, i), (post, post, 1.35),
                             (x, y, 0.675), "Timber"))
        for i in range(n - 1):
            t = (i + 0.5) / float(n - 1)
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            for h in RAILS:
                parts.append(box("RG_Pen_Rail_%d_%d_%d" % (r, i, int(h * 100)),
                                 (length / (n - 1) + 0.1, 0.08, 0.16),
                                 (x, y, h), "Timber", rot=(0.0, 0.0, yaw)))
    # A gate gap on the south run, with the gate swung open, so the pen is
    # enterable and reads as working infrastructure.
    parts.append(box("RG_Pen_Gate", (2.6, 0.1, 1.0), (-3.0, -6.5, 0.8), "Timber",
                     rot=(0.0, 0.0, 0.55)))
    return parts


def build_water_tank():
    """Galvanised tank on a timber stand. The map's long-range landmark."""
    parts = [
        cylinder("RG_Tank_Body", 1.5, 3.0, (0, 0, 3.6), "Metal", verts=20),
        cylinder("RG_Tank_Lid", 1.56, 0.12, (0, 0, 5.16), "Metal", verts=20),
        cylinder("RG_Tank_Outlet", 0.12, 0.9, (0, -1.4, 2.2), "Metal", verts=8),
    ]
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        parts.append(box("RG_Tank_Leg_%d" % i, (0.16, 0.16, 2.1),
                         (sx * 1.15, sy * 1.15, 1.05), "Timber"))
    parts.append(box("RG_Tank_Stand_Deck", (2.9, 2.9, 0.14), (0, 0, 2.1), "Timber"))
    for i, h in enumerate((2.4, 4.2)):
        parts.append(box("RG_Tank_Band_%d" % i, (3.1, 3.1, 0.08), (0, 0, h), "Metal"))
    return parts


def build_windmill():
    """Lattice tower, hub and a fan of blades. Read as a silhouette only."""
    parts = []
    h, top = 9.0, 0.9
    legs = 8
    for i in range(legs):
        ang = 2.0 * math.pi * i / legs
        parts.append(box("RG_Windmill_Leg_%d" % i, (0.1, 0.1, h),
                         (math.cos(ang) * top / 2.0, math.sin(ang) * top / 2.0, h / 2.0),
                         "Metal", rot=(0.0, 0.0, ang)))
    for ring, z in enumerate((2.4, 4.8, 7.2)):
        r = top * (1.0 - z / h) + 0.25
        for i in range(legs):
            a0 = 2.0 * math.pi * i / legs
            a1 = 2.0 * math.pi * (i + 1) / legs
            mx, my = (math.cos(a0) + math.cos(a1)) * r / 2.0, (math.sin(a0) + math.sin(a1)) * r / 2.0
            ang = math.atan2(my, mx)
            length = math.hypot(math.cos(a1) * r - math.cos(a0) * r, math.sin(a1) * r - math.sin(a0) * r)
            parts.append(box("RG_Windmill_Ring_%d_%d" % (ring, i), (length, 0.06, 0.06),
                             (mx, my, z), "Metal", rot=(0.0, 0.0, ang)))
    parts.append(box("RG_Windmill_Head", (0.5, 0.5, 0.9), (0, 0, h - 0.3), "Metal"))
    # Fan, facing -Y so it looks back over the yard from the paddocks.
    parts.append(cylinder("RG_Windmill_Hub", 0.16, 0.3, (0, -0.55, h + 0.35), "Metal",
                          rot=(math.pi / 2.0, 0.0, 0.0), verts=10))
    for i in range(10):
        ang = 2.0 * math.pi * i / 10.0
        r = 1.5
        parts.append(box("RG_Windmill_Blade_%d" % i, (0.22, 0.05, 1.25),
                         (math.sin(ang) * r, -0.7, h + 0.35 + math.cos(ang) * r),
                         "Metal", rot=(-ang, 0.0, 0.0)))
    return parts


def build_hut():
    """Small stockman's hut: 3.2 x 2.8 m, one room, no verandah.

    Placed off each paddock objective so those objectives have something to
    fight around that is not a tree, without competing with the homestead for
    the centre. A stockman's hut rather than a second house: two houses on one
    station reads as a village.
    """
    L, W, EAVE = 3.2, 2.8, 2.3
    RIDGE = EAVE + 0.9
    t = 0.12
    parts = [
        box("RG_Hut_Floor", (L, W, 0.2), (0, 0, 0.1), "Timber"),
        box("RG_Hut_Wall_S", (L, t, EAVE), (0, -W / 2.0, EAVE / 2.0), "Wall"),
        box("RG_Hut_Wall_N", (L, t, EAVE), (0, W / 2.0, EAVE / 2.0), "Wall"),
        box("RG_Hut_Wall_W", (t, W, EAVE), (-L / 2.0, 0, EAVE / 2.0), "Wall"),
        box("RG_Hut_Wall_E", (t, W, EAVE), (L / 2.0, 0, EAVE / 2.0), "Wall"),
        box("RG_Hut_Door", (0.85, 0.1, 1.9), (0.5, -W / 2.0 - 0.02, 0.95), "Timber"),
        box("RG_Hut_Win", (0.9, 0.1, 0.8), (-0.8, -W / 2.0 - 0.02, 1.5), "Glass"),
    ]
    for i, x in enumerate((-L / 2.0, L / 2.0)):
        parts.append(gable("RG_Hut_Gable_%d" % i, t + 0.02, W / 2.0, RIDGE - EAVE, (x, 0, EAVE), "Wall"))
    pitch = math.atan2(RIDGE - EAVE, W / 2.0)
    slope = math.hypot(RIDGE - EAVE, W / 2.0) + 0.35
    for sign in (1.0, -1.0):
        parts.append(box("RG_Hut_Roof_%s" % ("N" if sign > 0 else "S"), (L + 0.5, slope, 0.1),
                         (0.0, sign * (W / 4.0), (EAVE + RIDGE) / 2.0),
                         "Roof", rot=(sign * pitch, 0.0, 0.0)))
    # A short stove pipe, so the hut reads as lived in at a distance.
    parts.append(cylinder("RG_Hut_Pipe", 0.09, 1.0, (L / 2.0 - 0.5, 0.4, RIDGE + 0.2), "Metal", verts=8))
    return parts


BUILDERS = {
    "farmhouse": build_farmhouse,
    "shedding_shed": build_shearing_shed,
    "stock_pens": build_stock_pens,
    "water_tank": build_water_tank,
    "windmill": build_windmill,
    "hut": build_hut,
}


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_fbx(obj, filename):
    path = os.path.join(OUT_DIR, filename)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    # Box-projected UVs (2 m per unit) so the import can use textured materials.
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cube_project(cube_size=2.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.export_scene.fbx(
        filepath=path,
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
    return path


def world_extents(obj):
    """Half-extents and base height of a joined structure, in metres.

    The base height is the important one: the import pass places a structure
    with its actor origin at the traced ground, which is only correct if the
    mesh is authored base-at-origin. Emitting the measured value lets the
    importer assert that convention instead of assuming it - a structure whose
    base is not at 0 would otherwise be buried or floating by its own height
    with nothing in the logs to say why.
    """
    import mathutils
    corners = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
    return (
        max(abs(c.x) for c in corners),
        max(abs(c.y) for c in corners),
        min(c.z for c in corners),
        max(c.z for c in corners),
    )


def main():
    reset_scene()
    make_materials()
    os.makedirs(OUT_DIR, exist_ok=True)

    rows = []
    for name, structure, x, y, yaw, scale in LAYOUT:
        parts = BUILDERS[structure]()
        obj = join(parts, "SS_RedGum_" + name)
        half_x, half_y, base_z, top_z = world_extents(obj)
        fbx = export_fbx(obj, "SS_RedGum_%s.fbx" % name)
        rows.append((name, structure, x, y, yaw, scale, half_x, half_y, base_z, top_z,
                     len(obj.data.polygons)))

    blend = os.path.join(OUT_DIR, "SS_RedGum_Homestead.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)

    csv_path = os.path.join(OUT_DIR, "SS_RedGum_Homestead_Layout.csv")
    with open(csv_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("name,structure,x_m,y_m,yaw_deg,scale,half_x_m,half_y_m,base_z_m,top_z_m,faces\n")
        for r in rows:
            fh.write("%s,%s,%.3f,%.3f,%.1f,%.3f,%.3f,%.3f,%.4f,%.3f,%d\n" % r)

    for name, structure, _x, _y, _yaw, _s, half_x, half_y, base_z, top_z, faces in rows:
        print("EXPORTED %-14s %-14s faces=%-5d footprint=%.1fx%.1f base_z=%+.3f top=%.2f" % (
            name, structure, faces, half_x * 2.0, half_y * 2.0, base_z, top_z))
    print("EXPORTED_BLEND=%s" % blend)
    print("EXPORTED_CSV=%s" % csv_path)
    print("STRUCTURES=%d TRIS~%d" % (len(rows), sum(r[-1] for r in rows) * 2))


if __name__ == "__main__":
    main()
