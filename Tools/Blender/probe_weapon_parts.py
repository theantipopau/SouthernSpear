# Southern Spear - list a converted Arma MLOD's named parts (W5: can the magazine come off?).
#
# Arma animates a reload through the weapon model: the "magazine" named selection is hidden and swapped
# at magazineReloadSwitchPhase. Arma3ObjectBuilder imports named selections as vertex groups, so this
# lists every mesh object's vertex groups with their vertex counts and the memory points, as JSON.
#
# Run: blender --background --factory-startup --python Tools/Blender/probe_weapon_parts.py -- <src.blend> <out.json>

import json
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=SRC)

report = {"source": SRC, "objects": [], "magazine_groups": []}
for obj in bpy.data.objects:
    if obj.type != "MESH":
        continue
    counts = {}
    for vertex in obj.data.vertices:
        for element in vertex.groups:
            counts[element.group] = counts.get(element.group, 0) + 1
    groups = {g.name: counts.get(g.index, 0) for g in obj.vertex_groups}
    collections = [c.name for c in obj.users_collection]
    report["objects"].append({"name": obj.name, "collections": collections, "vertices": len(obj.data.vertices),
                              "materials": [m.name for m in obj.data.materials if m], "vertex_groups": groups})
    for name, count in groups.items():
        if "mag" in name.lower() and count:
            report["magazine_groups"].append({"object": obj.name, "collections": collections, "group": name, "vertices": count})
with open(OUT, "w") as fh:
    json.dump(report, fh, indent=1)
print("[probe parts]", SRC, "magazine groups:", json.dumps(report["magazine_groups"]))
