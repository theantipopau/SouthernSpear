# Probe: why is the kangaroo grey, and where is the bed across each water segment's width?
import json
import os
import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
out = {"kangaroo": [], "water": [], "errors": []}
WORLD = unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/L_DryRiver_01")
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def trace_z(x_cm, y_cm, ignore=None):
    hit = unreal.SystemLibrary.line_trace_single(
        WORLD, unreal.Vector(x_cm, y_cm, 500000.0), unreal.Vector(x_cm, y_cm, -500000.0),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore or [], unreal.DrawDebugTrace.NONE, True)
    return None if hit is None else round(hit.to_dict()["impact_point"].z, 1)

# 1. Kangaroo ground truth
for a in actors.get_all_level_actors():
    if not a.get_actor_label().startswith("SS_EasterEgg_Kangaroo"):
        continue
    c = a.static_mesh_component
    info = {"label": a.get_actor_label(), "cls": a.get_class().get_name(),
            "loc": [round(v) for v in (a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z)],
            "slots": [], "trace_bed": trace_z(a.get_actor_location().x, a.get_actor_location().y, [a])}
    for i in range(c.get_num_materials()):
        m = c.get_material(i)
        e = {"slot": i, "mat": m.get_path_name() if m else None}
        if m and m.get_path_name().endswith("MI_SS_Kangaroo"):
            try:
                tv = m.get_editor_property("texture_parameter_values")
                e["tex_params"] = [(t.parameter_name, t.value.get_path_name() if t.value else None)
                                   for t in tv][:6]
            except Exception as exc:
                e["tex_params_err"] = str(exc)
            try:
                e["parent"] = m.get_editor_property("parent").get_path_name() if m.get_editor_property("parent") else None
            except Exception as exc:
                e["parent_err"] = str(exc)
        info["slots"].append(e)
    out["kangaroo"].append(info)

# 2. Water segments: bed height at centre and +-8 m across (perpendicular ~ Y here)
for a in actors.get_all_level_actors():
    if not a.get_actor_label().startswith("SS_Overhaul_Creek_Water"):
        continue
    l = a.get_actor_location()
    s = a.get_actor_scale3d()
    rec = {"label": a.get_actor_label(), "z": round(l.z, 1),
           "bed_c": trace_z(l.x, l.y),
           "bed_n8": trace_z(l.x, l.y + 800.0),
           "bed_s8": trace_z(l.x, l.y - 800.0),
           "bed_n4": trace_z(l.x, l.y + 400.0),
           "bed_s4": trace_z(l.x, l.y - 400.0),
           "yaw": round(a.get_actor_rotation().yaw, 1)}
    out["water"].append(rec)

with open(os.path.join(PROJECT_DIR, "Build", "probe_kanga_water.json"), "w") as fh:
    json.dump(out, fh, indent=1)
unreal.log("[ProbeKW] kanga={} water={}".format(len(out["kangaroo"]), len(out["water"])))
