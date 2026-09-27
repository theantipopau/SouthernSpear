# Southern Spear - read-only probe of the wired-in soldier bodies (ADR-016, ADR-021).
#
# Reports the material slots on the friendly (3 ACR) and opposing (MAF) meshes
# and, for every distinct Fab master material they use, which texture
# parameters can be overridden. Nothing is modified or saved.
# Writes Build/character_materials.json.

import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "character_materials.json")

FRIENDLY = "/Game/QuantumCharacter/Mesh/SKM_QuantumCharacter"
OPPOSING = [
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Head",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Hands",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Sweater",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Pants_Military",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Shoes",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Armor_Small",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Beret",
]

# Candidate texture-parameter names seen across Fab/Fab-standard military packs,
# plus the ones implied by the texture asset names in each pack.
CANDIDATES = [
    "BaseColor", "Base Color", "BaseColorTexture", "Base_Color", "Albedo", "Diffuse",
    "Color", "Texture", "T_BC", "BC",
    "Normal", "NormalMap", "Normal_Texture", "T_Normal", "N",
    "ORM", "OcclusionRoughnessMetallic", "ORMTexture", "T_ORM",
    "Mask", "Masks", "Roughness", "Metallic", "Occlusion",
    "Emissive", "EmissiveColor",
]

report = {"ok": False, "meshes": {}, "masters": {}, "errors": []}


def mesh_slots(mesh):
    out = []
    try:
        mats = mesh.get_editor_property("materials")
    except Exception as exc:  # pragma: no cover - diagnostic path
        return [{"error": str(exc)}]
    for i, sm in enumerate(mats):
        mat = sm.get_editor_property("material_interface")
        out.append({
            "index": i,
            "slot": str(sm.get_editor_property("material_slot_name")),
            "material": mat.get_path_name() if mat else None,
        })
    return out


def probe_master(mat_path):
    """Find which candidate texture parameters this material actually exposes."""
    mat = unreal.load_asset(mat_path)
    if mat is None:
        return {"error": "load failed"}
    found = {}
    mel = unreal.MaterialEditingLibrary
    # Cheap attempt at a real enumeration, then fall back to trial assignment.
    for getter in ("get_material_texture_parameter_names",
                   "get_material_instance_texture_parameter_names"):
        fn = getattr(mel, getter, None)
        if fn is None:
            continue
        try:
            names = [str(n) for n in fn(mat)]
            if names:
                found["_enumerated_by"] = getter
                found["names"] = sorted(names)
                return found
        except Exception:
            pass
    return {"note": "no enumeration API; use trial assignment", "candidates": CANDIDATES}


def main():
    for path in [FRIENDLY] + OPPOSING:
        mesh = unreal.load_asset(path)
        if mesh is None:
            report["meshes"][path] = {"error": "load failed"}
            continue
        slots = mesh_slots(mesh)
        report["meshes"][path] = {"slots": slots}
        for s in slots:
            mp = s.get("material")
            if mp and mp not in report["masters"]:
                report["masters"][mp] = probe_master(mp)
    report["ok"] = True


try:
    main()
except Exception:
    report["errors"].append(traceback.format_exc())
os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[ProbeCharacters] ok={} masters={}".format(report["ok"], len(report["masters"])))
