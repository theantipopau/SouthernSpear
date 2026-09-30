# Author M_SS_CreekWater: the Dry River creek water (D-DR-05). Translucent, dark green-brown body,
# fresnel-lifted opacity/roughness, animated wave normal (WaterPlane T_MediumWaves_N). Idempotent:
# recreates the material each run, then the water segments pick it up on the next harvest_dryriver run.
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
OUT = os.path.join(PROJECT_DIR, "Build", "author_water_report.json")
MAT_PATH = "/Game/Art/Environment/DryRiver/M_SS_CreekWater"
NORMAL_TEX = "/Game/WaterPlane/Lake/Textures/T_MediumWaves_N"
report = {"ok": False, "steps": [], "errors": []}


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def mk(material, cls):
    # 5.8 wrapper: extra positionals map to node_pos_x/y, so create unnamed nodes.
    return unreal.MaterialEditingLibrary.create_material_expression(material, cls)


def const(material, value):
    e = mk(material, unreal.MaterialExpressionConstant)
    e.set_editor_property("r", float(value))
    return e


def const3(material, r, g, b):
    e = mk(material, unreal.MaterialExpressionConstant3Vector)
    e.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
    return e


def main():
    mel = unreal.MaterialEditingLibrary
    at = unreal.AssetToolsHelpers.get_asset_tools()
    if unreal.EditorAssetLibrary.does_asset_exist(MAT_PATH):
        unreal.EditorAssetLibrary.delete_asset(MAT_PATH)
        step("delete_old", True)
    mat = at.create_asset("M_SS_CreekWater", "/Game/Art/Environment/DryRiver", unreal.Material,
                          unreal.MaterialFactoryNew())
    if not step("create_material", isinstance(mat, unreal.Material), MAT_PATH):
        return
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)

    dark = const3(mat, 0.012, 0.022, 0.020)        # dark green-brown creek body
    edge = const3(mat, 0.045, 0.075, 0.085)        # sky-lifted edge colour
    fres = mk(mat, unreal.MaterialExpressionFresnel)
    body_lerp = mk(mat, unreal.MaterialExpressionLinearInterpolate)
    mel.connect_material_expressions(dark, "", body_lerp, "A")
    mel.connect_material_expressions(edge, "", body_lerp, "B")
    mel.connect_material_expressions(fres, "", body_lerp, "Alpha")
    step("base_color", mel.connect_material_property(body_lerp, "", unreal.MaterialProperty.MP_BASE_COLOR))

    rough_lo = const(mat, 0.06)
    rough_hi = const(mat, 0.30)
    rough_lerp = mk(mat, unreal.MaterialExpressionLinearInterpolate)
    mel.connect_material_expressions(rough_lo, "", rough_lerp, "A")
    mel.connect_material_expressions(rough_hi, "", rough_lerp, "B")
    mel.connect_material_expressions(fres, "", rough_lerp, "Alpha")
    step("roughness", mel.connect_material_property(rough_lerp, "", unreal.MaterialProperty.MP_ROUGHNESS))

    op_lo = const(mat, 0.60)
    op_hi = const(mat, 0.94)
    op_lerp = mk(mat, unreal.MaterialExpressionLinearInterpolate)
    mel.connect_material_expressions(op_lo, "", op_lerp, "A")
    mel.connect_material_expressions(op_hi, "", op_lerp, "B")
    mel.connect_material_expressions(fres, "", op_lerp, "Alpha")
    step("opacity", mel.connect_material_property(op_lerp, "", unreal.MaterialProperty.MP_OPACITY))

    tex = unreal.load_asset(NORMAL_TEX)
    step("normal_tex", isinstance(tex, unreal.Texture), NORMAL_TEX)
    if tex:
        panner = mk(mat, unreal.MaterialExpressionPanner)
        try:
            panner.set_editor_property("speed", unreal.Vector2D(0.016, 0.006))
        except Exception as exc:
            report["warnings"] = report.get("warnings", []) + ["panner speed: %s" % exc]
        texcoord = mk(mat, unreal.MaterialExpressionTextureCoordinate)
        mel.connect_material_expressions(texcoord, "", panner, "Coordinate")
        sample = mk(mat, unreal.MaterialExpressionTextureSample)
        sample.set_editor_property("texture", tex)
        mel.connect_material_expressions(panner, "", sample, "UVs")
        step("normal", mel.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_NORMAL))

    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    step("saved", unreal.EditorAssetLibrary.does_asset_exist(MAT_PATH))


try:
    main()
    report["ok"] = all(s["ok"] for s in report["steps"])
except Exception:
    report["errors"].append(traceback.format_exc())
with open(OUT, "w") as fh:
    json_dump = __import__("json").dump(report, fh, indent=1)
unreal.log("[AuthorWater] ok={}".format(report["ok"]))
