# Southern Spear - shared helpers for script-built weapons (ADR-020).
#
# Conventions for every weapon: +X muzzle, +Z up, metres, origin at the top of
# the pistol grip (right-hand hold point). Material slots are named Polymer,
# Metal and Glass (Tools/Unreal/setup_weapons.py assigns finishes by name).
# An empty SOCKET_Muzzle becomes the mesh's Muzzle socket on import.

import json
import math
import os

import bpy
import bmesh

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SLOTS = {
    "Polymer": (0.21, 0.22, 0.16, 1.0),
    "Metal": (0.05, 0.05, 0.05, 1.0),
    "Glass": (0.10, 0.18, 0.16, 1.0),
}

_parts = []


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _parts.clear()
    for name, colour in SLOTS.items():
        bpy.data.materials.new(name).diffuse_color = colour


def _prism(name, pts, slot, bevel):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in pts]
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
    _parts.append(obj)
    return obj


def box(name, x0, x1, y_half, z0, z1, slot="Polymer", bevel=0.004, taper_top=0.0):
    yt = y_half - taper_top
    return _prism(name, [(x0, -y_half, z0), (x1, -y_half, z0), (x1, y_half, z0), (x0, y_half, z0),
                         (x0, -yt, z1), (x1, -yt, z1), (x1, yt, z1), (x0, yt, z1)], slot, bevel)


def slanted(name, x_top0, x_top1, x_bot0, x_bot1, y_half, z_top, z_bot, slot="Polymer", bevel=0.003):
    return _prism(name, [(x_bot0, -y_half, z_bot), (x_bot1, -y_half, z_bot), (x_bot1, y_half, z_bot), (x_bot0, y_half, z_bot),
                         (x_top0, -y_half, z_top), (x_top1, -y_half, z_top), (x_top1, y_half, z_top), (x_top0, y_half, z_top)],
                  slot, bevel)


def cylinder(name, x0, x1, radius, z, slot="Metal", vertices=16, y=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=x1 - x0,
                                        location=((x0 + x1) / 2, y, z), rotation=(0, math.pi / 2, 0))
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(bpy.data.materials[slot])
    _parts.append(obj)
    return obj


def rod(name, start, end, radius, slot="Metal", vertices=8):
    """Cylinder between two points (bipod legs, carry handles)."""
    sx, sy, sz = start
    ex, ey, ez = end
    dx, dy, dz = ex - sx, ey - sy, ez - sz
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=length,
                                        location=((sx + ex) / 2, (sy + ey) / 2, (sz + ez) / 2))
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    from mathutils import Vector
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(Vector((dx, dy, dz)))
    obj.data.materials.append(bpy.data.materials[slot])
    _parts.append(obj)
    return obj


def rail(x0, x1, z, half=0.011, pitch=0.021):
    box("Rail", x0, x1, half, z, z + 0.012, slot="Metal", bevel=0.0015)
    n = int((x1 - x0 - 0.01) / pitch)
    for i in range(n):
        x = x0 + 0.005 + i * pitch
        box("RailTooth{}".format(i), x, x + 0.010, half, z + 0.012, z + 0.017, slot="Metal", bevel=0.0)


def finish(name, muzzle_xz, out_rel_dir, ok_length):
    """Join parts, add the muzzle socket, export FBX + .blend, write a report."""
    for p in _parts:
        bpy.context.view_layer.objects.active = p
        for m in list(p.modifiers):
            bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.ops.object.select_all(action="DESELECT")
    for p in _parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = _parts[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = obj.data.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.shade_auto_smooth(angle=math.radians(35))

    muzzle = bpy.data.objects.new("SOCKET_Muzzle", None)
    muzzle.location = (muzzle_xz[0], 0.0, muzzle_xz[1])
    bpy.context.collection.objects.link(muzzle)
    muzzle.parent = obj

    out_dir = os.path.join(ROOT, out_rel_dir)
    os.makedirs(out_dir, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    fbx = os.path.join(out_dir, name + ".fbx")
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                             axis_forward="-Y", axis_up="Z", mesh_smooth_type="FACE", add_leaf_bones=False)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, name.replace("SM_", "") + ".blend"))

    dims = list(obj.dimensions)
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    report = {"ok": ok_length[0] < dims[0] < ok_length[1] and tris < 20000, "dimensions_m": dims, "triangles": tris,
              "material_slots": [m.name for m in obj.data.materials], "fbx": fbx}
    path = os.path.join(ROOT, "Build", name.lower() + "_report.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(report, fh, indent=2)
    print("[{}] ok={} dims={} tris={}".format(name, report["ok"], [round(d, 3) for d in dims], tris))
    return report
