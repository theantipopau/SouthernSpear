# Southern Spear - what the soldier blueprint actually says.
#
# The class-select preview, the in-game friendly body and the opposing body all read B_SS_Soldier's
# CDO arrays. A missing helmet is invisible in every report that only counts steps, so this probe
# prints the configured meshes, their per-part material overrides, and each mesh's own slot
# assignments with the BaseColorMap each ADF/MAF material instance resolved to.
#
# Report: Build/soldier_parts_probe.json. Run with:
#   UnrealEditor-Cmd.exe <project> -run=pythonscript -script=Tools/Unreal/probe_soldier_parts.py \
#     -nullrhi -unattended -nosplash -nop4

import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "soldier_parts_probe.json")
DEST = "/SSExp_ObjectiveAssault/Characters"
PARTS = ["SK_ADF_Uniform_G3", "SK_ADF_Vest_TBAS", "SK_ADF_Helmet_OpsCore",
         "SK_MAF_Vest_Peacekeeper", "SK_MAF_Helmet_PASGT"]
report = {"ok": False, "errors": []}


def name_of(asset):
    return asset.get_path_name() if asset else None


def slots_of(override):
    return [name_of(s) for s in (override.get_editor_property("slots") or [])]


def texture_of(mi, param="BaseColorMap"):
    if mi is None:
        return None
    try:
        t = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mi, param)
    except Exception:
        return "raise"
    return name_of(t)


try:
    # Without this scan the Game Feature paths answer None in a commandlet; see probe_load_routes.py.
    unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous(
        ["/SSExp_ObjectiveAssault"], force_rescan=True)
    soldier = unreal.load_asset(DEST + "/B_SS_Soldier")
    report["blueprint"] = name_of(soldier)
    if soldier is None:
        raise RuntimeError("B_SS_Soldier did not load")
    cdo = unreal.get_default_object(soldier.generated_class())
    for prop in ("friendly_parts", "friendly_leader_pose_parts", "opposing_parts"):
        arr = cdo.get_editor_property(prop) or []
        report[prop] = [name_of(m) for m in arr]
    report["retarget_friendly_pose"] = bool(cdo.get_editor_property("retarget_friendly_pose"))
    for prop in ("friendly_material_overrides", "opposing_material_overrides"):
        report[prop] = [slots_of(o) for o in (cdo.get_editor_property(prop) or [])]

    # Each gear mesh's own slot assignments: this is what renders when no component override applies.
    for part in PARTS:
        mesh = unreal.load_asset(DEST + "/ADF/" + part)
        entry = {"loaded": mesh is not None, "slots": []}
        if mesh:
            for sm in (mesh.get_editor_property("materials") or []):
                mat = sm.get_editor_property("material_interface")
                entry["slots"].append({
                    "slot": str(sm.get_editor_property("material_slot_name")),
                    "material": name_of(mat),
                    "base_colour": texture_of(mat),
                })
        report[part] = entry

    report["ok"] = True
except Exception:
    report["errors"].append(traceback.format_exc())

with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[SoldierParts] ok={}".format(report["ok"]))
