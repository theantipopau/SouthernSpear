# Probe: do the SS_Overhaul_Creek_Water_* segments exist in the saved map, with which material, where?
import json
import math
import os
import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
out = {"segments": [], "material_path": None, "errors": []}
unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/L_DryRiver_01")
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in actors.get_all_level_actors():
    if not a.get_actor_label().startswith("SS_Overhaul_Creek_Water"):
        continue
    c = a.static_mesh_component
    m = c.get_material(0) if c else None
    l = a.get_actor_location()
    s = a.get_actor_scale3d()
    out["segments"].append({
        "label": a.get_actor_label(),
        "pos_cm": [round(l.x), round(l.y), round(l.z)],
        "scale": [round(s.x, 2), round(s.y, 2), round(s.z, 2)],
        "material": m.get_path_name() if m else None,
        "mesh": c.static_mesh.get_name() if c and c.static_mesh else None,
    })
    if m:
        out["material_path"] = m.get_path_name()
out["count"] = len(out["segments"])
# ground truth at creek centre x=0: bed z vs water z
sys_mod = __import__("sys")
sys_mod.path.insert(0, os.path.join(PROJECT_DIR, "Tools", "Common"))
from dryriver_world import height
out["bed_z_at_x0_cm"] = height(0.0, 0.0) * 100.0
with open(os.path.join(PROJECT_DIR, "Build", "probe_water_state.json"), "w") as fh:
    json.dump(out, fh, indent=1)
unreal.log("[ProbeWater] count={}".format(out["count"]))
