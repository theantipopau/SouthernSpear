# Southern Spear - read-only probe of what the class-select preview pawn is actually made of.
#
# The FrontEnd capture (L_SS_FrontEnd, -SSShotAt=14) shows a flat grey-sage surface on the torso
# between the webbing and the waist, on the forearms below the elbow, and on the shoulder. This
# probe loads that level, walks every pawn's mesh components, and for each material slot resolves
# the BaseColorMap the instance actually has bound, plus the texture's pixel size, so a flat
# fallback (the 64x64 T_ADF_Olive / T_ADF_Coyote) can be told from a real ADFRC sheet.
# Nothing is modified or saved. Writes Build/probe_soldier_render.json.

import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "probe_soldier_render.json")
LEVEL = "/Game/Maps/L_SS_FrontEnd"

report = {"ok": False, "level": LEVEL, "actors": [], "errors": []}
seen_materials = {}


def describe_texture(tex):
    if tex is None:
        return None
    try:
        w, h = tex.blueprint_get_size_x(), tex.blueprint_get_size_y()
    except Exception:
        try:
            w, h = tex.get_editor_property("imported_size")
        except Exception:
            w = h = -1
    try:
        max_size = tex.get_editor_property("max_texture_size")
    except Exception:
        max_size = None
    return {"asset": tex.get_path_name(), "size": [w, h], "max_texture_size": max_size}


def describe_material(mat):
    """BaseColorMap / NormalMap / SMDIMap as actually bound on this instance, else on its parents."""
    if mat is None:
        return {"error": "no material"}
    out = {"asset": mat.get_path_name(), "class": mat.get_class().get_name()}
    mel = unreal.MaterialEditingLibrary
    chain, node = [mat], mat
    while node is not None and len(chain) < 8:
        chain.append(node)
        try:
            node = node.get_editor_property("parent")
        except Exception:
            node = None
    for param in ("BaseColorMap", "NormalMap", "SMDIMap"):
        found = None
        for node in chain:
            tex = None
            if isinstance(node, unreal.MaterialInstanceConstant):
                tex = mel.get_material_instance_texture_parameter_value(node, param)
            else:
                tex = mel.get_material_default_texture_parameter_value(node, param)
            if tex is not None:
                found = describe_texture(tex)
                found["from"] = node.get_path_name()
                break
        out[param] = found
    return out


def describe_mesh(comp):
    try:
        mats = comp.get_editor_property("override_materials")
    except Exception:
        mats = []
    try:
        mats = comp.get_materials()
    except Exception:
        pass
    slots = []
    for i, mat in enumerate(mats):
        entry = {"index": i}
        if mat is None:
            entry["material"] = None
            entry["error"] = "EMPTY SLOT - renders with the CDO default (flat grey)"
        else:
            entry["material"] = mat.get_path_name()
            key = mat.get_path_name()
            if key not in seen_materials:
                seen_materials[key] = describe_material(mat)
        slots.append(entry)
    try:
        skel = comp.get_editor_property("skeletal_mesh")
    except Exception:
        skel = None
    return {
        "component": comp.get_name(),
        "mesh": skel.get_path_name() if skel else None,
        "hidden": comp.is_visible() if hasattr(comp, "is_visible") else None,
        "slots": slots,
    }


def walk(actor):
    entry = {"actor": actor.get_name(), "class": actor.get_class().get_name(), "meshes": []}
    try:
        comps = actor.get_components_by_class(unreal.SkeletalMeshComponent)
    except Exception as exc:
        entry["error"] = str(exc)
        return entry
    for comp in comps:
        if comp.get_name() in ("", "None"):
            continue
        try:
            entry["meshes"].append(describe_mesh(comp))
        except Exception as exc:
            entry["meshes"].append({"component": comp.get_name(), "error": str(exc)})
    return entry


try:
    unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        name = actor.get_name()
        cls = actor.get_class().get_name()
        interesting = any(k in cls for k in ("Pawn", "Character", "Display", "Preview", "Hero"))
        if not interesting and not any(k in name for k in ("Preview", "Hero", "Pawn", "SS_")):
            continue
        report["actors"].append(walk(actor))
    report["materials"] = seen_materials
    report["ok"] = True
except Exception:
    report["errors"].append(traceback.format_exc())
    report["materials"] = seen_materials

with open(REPORT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=1)
unreal.log("SS_PROBE_DONE {}".format(REPORT))
