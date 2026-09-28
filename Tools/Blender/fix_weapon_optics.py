"""Move the mounted optics on the exported weapon FBX files.

The scopes on the A4, A416 and A25 were exported over the buffer tube and the
stock, and the EF88's Spectr sat off the back of the rail. adfrc_weapon.py
placed an optic at eye.x / 2 - the midpoint of the trigger (the mesh origin)
and the REAR sight - and the rule has since been corrected. The optic source
blends (Art/ADFRC_BLEND/adfrc_optics_ss/) are no longer on disk, so the fix is
applied to the exported meshes instead of re-running the exporter: the optic's
faces are separated by material, translated onto the sight line, and joined
back with the exporter's own FBX settings.

The new centre comes from the model, not from a hand-tuned offset: the
midpoint of the Arma memory points front_sight_axis and rear_sight_axis at eye
height (Build/audit/sight_points.py replays the exporter's transform to get
them). The EF88 has no iron sights, so its scope is centred in the gap between
the two rail sections.

Run: blender --background --factory-startup -P Tools/Blender/fix_weapon_optics.py
"""
import json
import os

import bpy
import mathutils

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# name -> (delta x, delta z, note)
MOVES = {
    "A88": (0.131, 0.0, "Spectr onto the bullpup rail, between the rail sections"),
    "A4": (0.3054, 0.0, "TA31 between the M4's front and rear sights"),
    "A416": (0.2446, 0.0, "TA31 between the HK416's front and rear sights"),
    "A25": (0.3091, 0.0, "TA648 between the SR25's front and rear sights"),
}

OPTIC_HINTS = ("ta31", "ta648", "acog", "spectr", "optic", "glass", "ret")


def optic_slots(meshes):
    return {m.name for ob in meshes for m in ob.data.materials if m
            and any(h in m.name.lower() for h in OPTIC_HINTS)}


def slot_bounds(ob, names):
    mesh = ob.data
    order = [m.name if m else "" for m in mesh.materials]
    cache = {}
    lo = hi = None
    tris = 0
    for poly in mesh.polygons:
        name = order[poly.material_index] if poly.material_index < len(order) else ""
        if name not in names:
            continue
        tris += poly.loop_total - 2
        for vi in poly.vertices:
            co = cache.get(vi)
            if co is None:
                co = ob.matrix_world @ mesh.vertices[vi].co
                cache[vi] = co
            lo = co.copy() if lo is None else Vector_min(lo, co)
            hi = co.copy() if hi is None else Vector_max(hi, co)
    return lo, hi, tris


def Vector_min(a, b):
    return mathutils.Vector((min(a[i], b[i]) for i in range(3)))


def Vector_max(a, b):
    return mathutils.Vector((max(a[i], b[i]) for i in range(3)))


def fix(name, dx, dz, note):
    folder = os.path.join(ROOT, "Art", "Weapons", name, "ADFRC")
    fbx = os.path.join(folder, "SM_" + name + ".fbx")
    if not os.path.isfile(fbx):
        print("SKIP", name, "(no FBX)")
        return

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fbx)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    targets = optic_slots(meshes)
    if not targets:
        print("SKIP", name, "(no optic slots)")
        return
    before_lo, before_hi, tris = slot_bounds(meshes[0], targets)

    # Split the mesh per material so the optic can move on its own.
    bpy.ops.object.select_all(action="DESELECT")
    for ob in meshes:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="MATERIAL")
    bpy.ops.object.mode_set(mode="OBJECT")

    moved = 0
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH":
            continue
        names = {m.name for m in ob.data.materials if m}
        if names & targets:
            ob.location = ob.location + mathutils.Vector((dx, 0.0, dz))
            moved += 1

    bpy.ops.object.select_all(action="DESELECT")
    parts = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    for ob in parts:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active

    after_lo, after_hi, _ = slot_bounds(obj, targets)
    obj.dimensions  # refresh

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, apply_unit_scale=True,
                             apply_scale_options="FBX_SCALE_UNITS", axis_forward="-Y",
                             axis_up="Z", mesh_smooth_type="FACE", add_leaf_bones=False)

    # Keep the manifest honest: it records the optic centre and the mesh size.
    mpath = os.path.join(folder, "manifest.json")
    if os.path.isfile(mpath):
        with open(mpath, encoding="utf-8") as fh:
            report = json.load(fh)
        if report.get("optic"):
            centre = list(report["optic"]["centre_m"])
            report["optic"]["centre_m"] = [centre[0] + dx, centre[1], centre[2] + dz]
            report["optic"]["placement"] = note
        report["dimensions_m"] = list(obj.dimensions)
        with open(mpath, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1)

    print(f"FIXED {name}: {moved} optic part(s) moved by ({dx:+.4f}, 0, {dz:+.4f}) - {note}")
    print(f"       optic x {before_lo.x:+.3f}..{before_hi.x:+.3f} -> "
          f"{after_lo.x:+.3f}..{after_hi.x:+.3f}   ({tris} tris)")


if __name__ == "__main__":
    for name, (dx, dz, note) in MOVES.items():
        fix(name, dx, dz, note)
    print("done")
