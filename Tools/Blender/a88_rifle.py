# Southern Spear - A88 rifle, first pass (ADR-016, ADR-020).
#
# An original, fictional bullpup built from primitives: angular polymer shell,
# flat-top rail with a separate compact optic, vertical foregrip, magazine
# behind the pistol grip. Not traced from, or dimensioned after, any real
# weapon. Placeholder quality by design; later passes add detail.
#
# Axes: +X muzzle, +Z up, metres. Origin = top of the pistol grip, where the
# right hand holds it. An empty named SOCKET_Muzzle becomes a mesh socket on
# import.
#
# Run:  blender --background --factory-startup --python Tools/Blender/a88_rifle.py
# Out:  Art/Weapons/A88/SM_A88.fbx, Art/Weapons/A88/A88.blend,
#       Build/a88_report.json (dimensions, triangle count)

import json
import math
import os

import bpy
import bmesh

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "Art", "Weapons", "A88")
REPORT = os.path.join(ROOT, "Build", "a88_report.json")

# Flat colours for the preview .blend only; Unreal assigns its own materials
# per slot (slot names are the contract).
SLOTS = {
    "Polymer": (0.21, 0.22, 0.16, 1.0),
    "Metal": (0.05, 0.05, 0.05, 1.0),
    "Glass": (0.10, 0.18, 0.16, 1.0),
}


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for name, colour in SLOTS.items():
        m = bpy.data.materials.new(name)
        m.diffuse_color = colour


def box(name, x0, x1, y_half, z0, z1, slot="Polymer", bevel=0.004, taper_top=0.0):
    """Axis-aligned box from x0..x1, -y_half..y_half, z0..z1. taper_top narrows the top face."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    yt = y_half - taper_top
    verts = [
        (x0, -y_half, z0), (x1, -y_half, z0), (x1, y_half, z0), (x0, y_half, z0),
        (x0, -yt, z1), (x1, -yt, z1), (x1, yt, z1), (x0, yt, z1),
    ]
    v = [bm.verts.new(p) for p in verts]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([v[i] for i in f])
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(bpy.data.materials[slot])
    if bevel > 0:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
    return obj


def slanted(name, x_top0, x_top1, x_bot0, x_bot1, y_half, z_top, z_bot, slot="Polymer", bevel=0.003):
    """Quad prism whose top and bottom edges differ in X (grips, magazine)."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    pts = [
        (x_bot0, -y_half, z_bot), (x_bot1, -y_half, z_bot), (x_bot1, y_half, z_bot), (x_bot0, y_half, z_bot),
        (x_top0, -y_half, z_top), (x_top1, -y_half, z_top), (x_top1, y_half, z_top), (x_top0, y_half, z_top),
    ]
    v = [bm.verts.new(p) for p in pts]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([v[i] for i in f])
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(bpy.data.materials[slot])
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = bevel
    mod.segments = 2
    return obj


def cylinder(name, x0, x1, radius, z, slot="Metal", vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=x1 - x0,
                                        location=((x0 + x1) / 2, 0, z), rotation=(0, math.pi / 2, 0))
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(bpy.data.materials[slot])
    return obj


def build():
    parts = []
    # Receiver shell: long, low, angular; butt at the rear (bullpup).
    parts.append(box("Receiver", -0.31, 0.16, 0.030, -0.030, 0.062, taper_top=0.008, bevel=0.006))
    parts.append(slanted("Butt", -0.33, -0.30, -0.335, -0.30, 0.031, 0.060, -0.075, bevel=0.006))
    parts.append(box("ButtPad", -0.345, -0.333, 0.032, -0.078, 0.062, slot="Metal", bevel=0.003))
    # Lower shell under the action, ahead of the butt, carrying the magazine well.
    parts.append(box("LowerShell", -0.30, -0.06, 0.028, -0.075, -0.030, bevel=0.005))
    # Pistol grip (origin sits at its top), raked back.
    parts.append(slanted("PistolGrip", -0.012, 0.022, -0.040, -0.008, 0.016, -0.028, -0.125))
    # Trigger guard: a flat loop from grip to lower shell.
    parts.append(box("TriggerGuard", 0.020, 0.075, 0.008, -0.058, -0.050, slot="Metal", bevel=0.002))
    parts.append(box("TriggerGuardFront", 0.068, 0.078, 0.008, -0.058, -0.030, slot="Metal", bevel=0.002))
    # Magazine behind the grip, slight forward curve approximated by a slant.
    parts.append(slanted("Magazine", -0.175, -0.110, -0.190, -0.128, 0.013, -0.070, -0.185, slot="Metal"))
    # Handguard with vent slots suggested by stepped blocks.
    parts.append(box("Handguard", 0.16, 0.36, 0.026, -0.022, 0.052, taper_top=0.006, bevel=0.005))
    for i in range(4):
        x = 0.19 + i * 0.04
        parts.append(box("Vent{}".format(i), x, x + 0.022, 0.0275, 0.012, 0.030, slot="Metal", bevel=0.001))
    # Flat-top rail across receiver and handguard.
    parts.append(box("Rail", -0.12, 0.35, 0.011, 0.062, 0.074, slot="Metal", bevel=0.0015))
    for i in range(22):
        x = -0.115 + i * 0.021
        parts.append(box("RailTooth{}".format(i), x, x + 0.010, 0.011, 0.074, 0.079, slot="Metal", bevel=0.0))
    # Compact optic: mount block, housing, lens caps.
    parts.append(box("OpticMount", -0.02, 0.06, 0.012, 0.079, 0.090, slot="Metal", bevel=0.002))
    parts.append(box("OpticBody", -0.035, 0.085, 0.018, 0.090, 0.128, slot="Metal", bevel=0.004))
    parts.append(cylinder("OpticLensRear", -0.040, -0.034, 0.013, 0.109, slot="Glass"))
    parts.append(cylinder("OpticLensFront", 0.084, 0.090, 0.015, 0.109, slot="Glass"))
    # Barrel, gas block and muzzle device.
    parts.append(cylinder("Barrel", 0.34, 0.50, 0.0110, 0.030))
    parts.append(box("GasBlock", 0.355, 0.385, 0.012, 0.022, 0.050, slot="Metal", bevel=0.002))
    parts.append(cylinder("Muzzle", 0.495, 0.545, 0.0150, 0.030, vertices=8))
    # Vertical foregrip.
    parts.append(slanted("Foregrip", 0.255, 0.290, 0.258, 0.286, 0.015, -0.022, -0.105))
    # Charging handle stub and ejection-port cover on the right side.
    parts.append(box("ChargingHandle", 0.05, 0.075, 0.042, 0.030, 0.045, slot="Metal", bevel=0.002))
    parts.append(box("EjectionCover", -0.22, -0.12, 0.033, 0.000, 0.035, slot="Metal", bevel=0.002))

    # Join into one mesh with modifiers applied.
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    for p in parts:
        bpy.context.view_layer.objects.active = p
        for m in list(p.modifiers):
            bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    rifle = bpy.context.active_object
    rifle.name = "SM_A88"
    rifle.data.name = "SM_A88"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.shade_auto_smooth(angle=math.radians(35))

    muzzle = bpy.data.objects.new("SOCKET_Muzzle", None)
    muzzle.location = (0.545, 0.0, 0.030)
    bpy.context.collection.objects.link(muzzle)
    muzzle.parent = rifle
    return rifle


def main():
    reset_scene()
    rifle = build()
    os.makedirs(OUT_DIR, exist_ok=True)
    fbx = os.path.join(OUT_DIR, "SM_A88.fbx")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                             axis_forward="-Y", axis_up="Z", mesh_smooth_type="FACE", add_leaf_bones=False)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "A88.blend"))

    dims = list(rifle.dimensions)
    tris = sum(len(p.vertices) - 2 for p in rifle.data.polygons)
    report = {"ok": 0.6 < dims[0] < 0.95 and tris < 20000, "dimensions_m": dims, "triangles": tris,
              "material_slots": [m.name for m in rifle.data.materials], "fbx": fbx}
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w") as fh:
        json.dump(report, fh, indent=2)
    print("[A88] ok={} dims={} tris={}".format(report["ok"], [round(d, 3) for d in dims], tris))


main()
