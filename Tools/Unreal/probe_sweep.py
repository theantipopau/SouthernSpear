# Probe: why does windmill_sweep not remove the SS_RA_Tree that windmill_clearance sees?
# Replicates both loops with per-actor detail near the windmill.
import json
import math
import os
import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = {"wm": None, "near": [], "sweep_would_remove": [], "errors": []}

unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/L_DryRiver_01")

wm = None
for a in actors.get_all_level_actors():
    if "Windmill" in a.get_actor_label():
        l = a.get_actor_location()
        wm = (l.x, l.y, a.get_actor_label())
        break
out["wm"] = wm
if not wm:
    json.dump(out, open(os.path.join(PROJECT_DIR, "Build", "probe_sweep.json"), "w"), indent=1)
    raise SystemExit

wx, wy = wm[0], wm[1]
for a in actors.get_all_level_actors():
    try:
        if not isinstance(a, unreal.StaticMeshActor):
            continue
        c = a.static_mesh_component
        if not c or not c.static_mesh:
            continue
        l = a.get_actor_location()
        d = math.hypot(l.x - wx, l.y - wy)
        if d > 4000.0:
            continue
        origin, ext = a.get_actor_bounds(False)
        lab = a.get_actor_label()
        name = c.static_mesh.get_name()
        out["near"].append({
            "lab": lab, "mesh": name, "d_m": round(d / 100.0, 2),
            "r_m": round((ext.x + ext.y) / 100.0, 2),
            "gap_clear": round(d / 100.0 - (ext.x + ext.y) / 100.0, 2),
            "gap_sweep": round(d / 100.0 - (ext.x + ext.y) / 200.0, 2),
            "tree_filter": ("tree" in name.lower() or lab.startswith("SS_RA_Tree")
                            or lab.startswith("SS_RA_Cover_Tree")),
            "cls": a.get_class().get_name(),
        })
        if d / 100.0 - (ext.x + ext.y) / 200.0 < 6.5 and "Creek_Water" not in lab \
                and "tree" in name.lower() or lab.startswith("SS_RA_Tree"):
            out["sweep_would_remove"].append(lab)
    except Exception as e:
        out["errors"].append(str(e))

json.dump(out, open(os.path.join(PROJECT_DIR, "Build", "probe_sweep.json"), "w"), indent=1)
unreal.log("[ProbeSweep] near={} would={}".format(len(out["near"]), out["sweep_would_remove"]))
