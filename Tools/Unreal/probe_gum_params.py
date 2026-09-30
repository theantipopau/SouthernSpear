# Probe: QuarrySlate water MI parameter names + water mesh slots (for the Dry River harvest water pass).
import json
import os
import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
out = {"params": [], "scalars": [], "vectors": [], "mi_parent": None, "mesh_slots": [], "mesh_bounds": None}
mi = unreal.load_asset("/Game/Scene_QuarrySlate/Materials/MaterialInstances/MI_Qua_Sla_Water_01")
if isinstance(mi, unreal.MaterialInterface):
    out["mi_parent"] = mi.get_editor_property("parent").get_path_name() if mi.get_editor_property("parent") else None
    ump = unreal.MaterialEditingLibrary
    try:
        out["params"] = [str(p) for p in ump.get_material_instance_texture_parameter_names(mi)]
        out["scalars"] = [str(p) for p in ump.get_material_instance_scalar_parameter_names(mi)]
        out["vectors"] = [str(p) for p in ump.get_material_instance_vector_parameter_names(mi)]
    except Exception as e:
        out["probe_error"] = str(e)
else:
    out["probe_error"] = "MI not found"

mesh = unreal.load_asset("/Game/Scene_QuarrySlate/Assets/Custom/Qua_Sla_Water_01/SM_Qua_Sla_Water_01")
if isinstance(mesh, unreal.StaticMesh):
    b = mesh.get_bounds().box_extent * 2.0
    out["mesh_bounds"] = [round(b.x, 1), round(b.y, 1), round(b.z, 1)]
    out["mesh_slots"] = [str(sm.material_slot_name) for sm in mesh.get_editor_property("static_materials")]
    body = mesh.get_editor_property("body_setup")
    out["has_body"] = body is not None
else:
    out["probe_error"] = out.get("probe_error", "") + " mesh not found"

gum = unreal.load_asset("/Game/Art/Environment/Fab/TH_Complete_Full_Ghoast_Gum")
out["gum_slots"] = ([str(sm.material_slot_name) for sm in gum.get_editor_property("static_materials")]
                    if isinstance(gum, unreal.StaticMesh) else None)

with open(os.path.join(PROJECT_DIR, "Build", "probe_gum_params.json"), "w") as fh:
    json.dump(out, fh, indent=1)
unreal.log("[ProbeGum] done")
