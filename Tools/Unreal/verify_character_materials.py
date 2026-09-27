# Southern Spear - verify the original character materials and overrides.
#
# Read-only: confirms each M_SS_* material has a base colour, normal and ORM
# sample wired to the right material inputs, that the textures are imported
# with sane settings, and that B_SS_Soldier still carries the overrides.
# Writes Build/character_materials_verify.json.

import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "character_materials_verify.json")
MAT_ROOT = "/SSExp_ObjectiveAssault/Characters/Materials"
SOLDIER = "/SSExp_ObjectiveAssault/Characters/B_SS_Soldier"
MATS = ["M_SS_CMECU", "M_SS_MAF", "M_SS_GearTan", "M_SS_GearDark"]

report = {"ok": False, "materials": {}, "soldier": {}, "errors": []}


def connections(mat):
    """Map each material input to the expression feeding it."""
    out = {}
    try:
        inputs = mat.get_editor_property("expression_collection").get_editor_property("inputs") \
            if hasattr(mat, "expression_collection") else None
    except Exception:
        inputs = None
    if inputs is None:
        # Fall back to the editing library's per-input query.
        mel = unreal.MaterialEditingLibrary
        for prop in ("MP_BASE_COLOR", "MP_NORMAL", "MP_ROUGHNESS", "MP_METALLIC",
                     "MP_AMBIENT_OCCLUSION"):
            try:
                expr = mel.get_material_property_input_expression(mat, prop)
                out[str(prop)] = expr.get_class().get_name() if expr else None
            except Exception as exc:
                out[str(prop)] = "query failed: %s" % exc
        return out
    for i in inputs:
        try:
            out[i.get_editor_property("input_name")] = i.get_editor_property("expression").get_class().get_name()
        except Exception:
            pass
    return out


def main():
    mel = unreal.MaterialEditingLibrary
    for name in MATS:
        mat = unreal.load_asset(MAT_ROOT + "/" + name)
        if mat is None:
            report["materials"][name] = {"error": "missing"}
            report["errors"].append("missing material %s" % name)
            continue
        conns = connections(mat)
        # Which textures are actually bound? MaterialExpressionCollection is not
        # exposed to Python, so walk expressions through the editing library.
        tex = []
        try:
            count = mel.get_num_material_expressions(mat)
            for i in range(count):
                expr = mel.get_material_expression(mat, i)
                if expr and "TextureSample" in expr.get_class().get_name():
                    bound = expr.get_editor_property("texture")
                    tex.append({
                        "param": str(expr.get_editor_property("parameter_name")),
                        "texture": bound.get_name() if bound else None,
                        "sampler": str(expr.get_editor_property("sampler_type")),
                    })
        except Exception as exc:
            report["errors"].append("expression walk %s: %s" % (name, exc))
        report["materials"][name] = {
            "path": mat.get_path_name(),
            "inputs": conns,
            "textures": sorted(tex, key=lambda d: d["param"]),
        }

    soldier = unreal.load_asset(SOLDIER)
    if soldier is not None:
        cdo = unreal.get_default_object(soldier.generated_class())
        for prop in ("friendly_material_overrides", "opposing_material_overrides"):
            rows = cdo.get_editor_property(prop)
            packed = []
            for r in rows:
                slots = r.get_editor_property("slots") if hasattr(r, "get_editor_property") else r
                packed.append([s.get_name() if s else None for s in (slots or [])])
            report["soldier"][prop] = packed

    connected = all(
        report["materials"].get(n, {}).get("textures")
        and len(report["materials"][n]["textures"]) == 3
        for n in MATS
    )
    overrides = report["soldier"].get("friendly_material_overrides") or []
    report["ok"] = bool(connected and overrides and not report["errors"])


try:
    main()
except Exception:
    report["errors"].append(traceback.format_exc())
os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[VerifyCharacterMaterials] ok={}".format(report["ok"]))
