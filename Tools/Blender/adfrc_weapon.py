# Southern Spear - ADFRC weapon to game mesh (L-0021; ADR-016 naming).
#
# Input: an Arma MLOD converted to .blend (Art/ADFRC_BLEND/<addon>/<model>_MLOD.blend).
# Output: Art/Weapons/<NAME>/ADFRC/SM_<NAME>.fbx and a texture manifest for
# Tools/Unreal/setup_weapons.py.
#
# - Keeps LOD0 of each visual part: in the view_R0 collection each part appears
#   once per LOD (per material); the first occurrence is the highest detail.
# - Drops identification decals (tag, ruid, patch, flag, logo): no real
#   insignia or unit markings (ADR-016).
# - Material slots are named after their colour texture stem (e.g.
#   adfrc_ef88_co); the manifest maps each slot to the extracted PNG
#   (Art/ADFRC/Textures/**, colour _co and normal _nohq).
# - Orientation from the Arma memory LOD: muzzle_pos to +X, origin at
#   trigger_axis (the gripping hand), SOCKET_Muzzle at muzzle_pos. Without
#   memory points: thinner end to +X, bounding-box centre. Metres.
# - Optional third argument: an optic FBX merged on the sight line (eye point).
#
# Run: blender --background --factory-startup --python Tools/Blender/adfrc_weapon.py -- <src.blend> <NAME> [optic.fbx]

import json
import math
import os
import re
import sys

import bpy
import mathutils

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEXTURES = os.path.join(ROOT, "Art", "ADFRC", "Textures")
DROP = re.compile(r"(tag|ruid|patch|flag|logo|insignia)", re.I)

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, NAME = argv[0], argv[1]
OPTIC = os.path.abspath(argv[2]) if len(argv) > 2 else None  # optional optic FBX merged on the rail
OUT_DIR = os.path.join(ROOT, "Art", "Weapons", NAME, "ADFRC")
os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(SRC))

# PNG index by lower-case stem.
index = {}
for dirpath, _, files in os.walk(TEXTURES):
    for f in files:
        if f.lower().endswith(".png"):
            index.setdefault(os.path.splitext(f)[0].lower(), os.path.join(dirpath, f))


def texture_stem(material_name):
    # "P3D: adfrc_ef88_co.paa :: adfrc_ef88_poly.rvmat" -> "adfrc_ef88_co"
    m = re.search(r"([\w\-]+)\.paa", material_name or "", re.I)
    return m.group(1).lower() if m else None


# Arma memory LOD points (named vertex groups): muzzle, trigger, sight eye.
memory = {}
mem = bpy.data.objects.get("Memory")
if mem:
    for g in mem.vertex_groups:
        pts = [v.co.copy() for v in mem.data.vertices if any(e.group == g.index for e in v.groups)]
        if pts:
            memory[g.name] = sum(pts, mathutils.Vector()) / len(pts)

view = bpy.data.collections.get("view_R0") or bpy.data.collections.get("LODs")
candidates = [o for o in (view.all_objects if view else bpy.data.objects) if o.type == "MESH"]
seen, keep, dropped = set(), [], []
for o in sorted(candidates, key=lambda o: o.name):
    base = re.sub(r"\.\d+$", "", o.name)
    mat = o.data.materials[0].name if o.data.materials and o.data.materials[0] else ""
    key = (base, mat)
    if key in seen:
        continue
    seen.add(key)
    if DROP.search(base) or DROP.search(mat):
        dropped.append(base)
        continue
    if not texture_stem(mat):
        dropped.append(base + " (no texture)")
        continue
    keep.append(o)

for o in bpy.data.objects:
    o.select_set(False)
parts = []
for o in keep:
    c = o.copy()
    c.data = o.data.copy()
    bpy.context.scene.collection.objects.link(c)
    parts.append(c)
for o in list(bpy.data.objects):
    if o not in parts:
        bpy.data.objects.remove(o, do_unlink=True)
for o in parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
obj = bpy.context.active_object
obj.name = obj.data.name = "SM_" + NAME
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Slots named after their colour texture.
manifest = {}
for slot in obj.material_slots:
    stem = texture_stem(slot.material.name if slot.material else "")
    if not stem:
        continue
    mat = bpy.data.materials.get(stem) or bpy.data.materials.new(stem)
    slot.material = mat
    colour = index.get(stem)
    normal = index.get(re.sub(r"_(co|ca)$", "_nohq", stem))
    manifest[stem] = {"colour": colour, "normal": normal}

# Placement. Points are kept in step with the mesh through every transform.
points = dict(memory)


def transform(fn):
    for v in obj.data.vertices:
        v.co = fn(v.co)
    for k in points:
        points[k] = fn(points[k])


dims = obj.dimensions
if dims.y > dims.x and dims.y >= dims.z:
    transform(lambda c: mathutils.Vector((c.y, -c.x, c.z)))
length = max(v.co.x for v in obj.data.vertices) - min(v.co.x for v in obj.data.vertices)


def end_height(sign):
    xs = [v.co.x for v in obj.data.vertices]
    lo_x, hi_x = min(xs), max(xs)
    edge = hi_x if sign > 0 else lo_x
    band = [v.co for v in obj.data.vertices if abs(v.co.x - edge) < length * 0.1]
    return (max(v.z for v in band) - min(v.z for v in band)) if band else 0.0


# Muzzle to +X: from the memory point when present, else the thinner end.
if "muzzle_pos" in points and "trigger_axis" in points:
    flip = points["muzzle_pos"].x < points["trigger_axis"].x
else:
    flip = end_height(-1) < end_height(+1)
if flip:
    transform(lambda c: mathutils.Vector((-c.x, -c.y, c.z)))

# Origin at the trigger (the gripping hand), else the bounding-box centre.
if "trigger_axis" in points:
    origin = points["trigger_axis"].copy()
else:
    vs = [v.co for v in obj.data.vertices]
    origin = mathutils.Vector(((min(v.x for v in vs) + max(v.x for v in vs)) / 2, 0.0,
                               (min(v.z for v in vs) + max(v.z for v in vs)) / 2))
transform(lambda c: c - origin)

if "muzzle_pos" in points:
    muzzle = points["muzzle_pos"].copy()
else:
    front = max(v.co.x for v in obj.data.vertices)
    tip = [v.co for v in obj.data.vertices if v.co.x > front - 0.01]
    muzzle = mathutils.Vector((front, sum(v.y for v in tip) / len(tip), sum(v.z for v in tip) / len(tip)))

# Optional optic on the rail: sight axis at the iron-sight eye height, centred
# between the trigger and the eye point.
optic_report = None
if OPTIC and os.path.exists(OPTIC):
    before = set(bpy.data.objects)
    if OPTIC.lower().endswith(".blend"):
        # Arma optic converted with Tools/Blender/p3d_to_blend.py: take the most
        # detailed visual LOD ("Resolution N", lowest N).
        with bpy.data.libraries.load(OPTIC, link=False) as (src, dst):
            lods = sorted((n for n in src.objects if n.startswith("Resolution")),
                          key=lambda n: float(re.sub(r"[^0-9.]", "", n) or 0))
            dst.objects = lods[:1]
        for o in dst.objects:
            bpy.context.scene.collection.objects.link(o)
    else:
        bpy.ops.import_scene.fbx(filepath=OPTIC)
    new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    if new:
        for o in bpy.data.objects:
            o.select_set(o in new)
        bpy.context.view_layer.objects.active = new[0]
        if len(new) > 1:
            bpy.ops.object.join()
        opt = bpy.context.active_object
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        d = opt.dimensions
        if d.y > d.x and d.y >= d.z:
            for v in opt.data.vertices:
                v.co = mathutils.Vector((v.co.y, -v.co.x, v.co.z))
        ovs = [v.co for v in opt.data.vertices]
        o_lo = mathutils.Vector((min(v.x for v in ovs), min(v.y for v in ovs), min(v.z for v in ovs)))
        o_hi = mathutils.Vector((max(v.x for v in ovs), max(v.y for v in ovs), max(v.z for v in ovs)))
        eye = points.get("eye", mathutils.Vector((-0.15, 0.0, 0.08)))
        target = mathutils.Vector(((eye.x + 0.0) / 2, 0.0, eye.z))  # optic centre on the sight line
        shift = target - (o_lo + o_hi) / 2
        for v in opt.data.vertices:
            v.co += shift
        for slot in opt.material_slots:
            stem = texture_stem(slot.material.name if slot.material else "")
            if stem:  # textured Arma optic: keep a slot per texture
                slot.material = bpy.data.materials.get(stem) or bpy.data.materials.new(stem)
                manifest[stem] = {"colour": index.get(stem), "normal": index.get(re.sub(r"_(co|ca)$", "_nohq", stem))}
            else:
                slot.material = bpy.data.materials.get("optic") or bpy.data.materials.new("optic")
        for o in bpy.data.objects:
            o.select_set(o in (obj, opt))
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.join()
        optic_report = {"source": OPTIC, "centre_m": list(target), "size_m": list(o_hi - o_lo)}
        manifest.setdefault("optic", {"colour": None, "normal": None})

sock = bpy.data.objects.new("SOCKET_Muzzle", None)
sock.location = muzzle
bpy.context.scene.collection.objects.link(sock)
sock.parent = obj

fbx = os.path.join(OUT_DIR, "SM_" + NAME + ".fbx")
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                         axis_forward="-Y", axis_up="Z", mesh_smooth_type="FACE", add_leaf_bones=False)
report = {"source": SRC, "fbx": fbx, "dimensions_m": list(obj.dimensions),
          "triangles": sum(len(p.vertices) - 2 for p in obj.data.polygons), "parts": len(keep),
          "dropped": sorted(set(dropped)), "textures": manifest, "muzzle_m": list(muzzle),
          "memory_points": sorted(memory), "origin": "trigger_axis" if "trigger_axis" in memory else "bbox centre",
          "optic": optic_report}
with open(os.path.join(OUT_DIR, "manifest.json"), "w") as fh:
    json.dump(report, fh, indent=1)
print("[ADFRC weapon]", NAME, json.dumps({k: report[k] for k in ("dimensions_m", "triangles", "parts", "dropped")}))
