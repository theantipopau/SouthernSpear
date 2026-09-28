# Southern Spear - read-only: can the soldier pivot to the Quantum modular character?
#
# The pack is modular (Content/QuantumCharacter/Mesh/Modules/SKM_*) and carries its own skeleton,
# SK_Military_Character_Skeleton. The decisive question is whether that skeleton is Manny's, or a
# different one: if the bones resolve against Lyra's mannequin the modules can be character parts
# under leader pose, and if not, the whole soldier moves off Manny and Lyra's animations have to
# retarget. This reports both, plus each module's vertex count and slot count.
import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "probe_quantum_modules.json")
ROOT = "/Game/QuantumCharacter"
MODULES = ["SKM_Head", "SKM_Arms", "SKM_Shirt_RolledUp_Blue", "SKM_Jeans",
           "SKM_Bulletproof_Bege", "SKM_Holster_Hard_Bege", "SKM_Drops_1_Bege", "SKM_Patch_Back"]
ASSEMBLED = [ROOT + "/Mesh/SKM_QuantumCharacter", ROOT + "/Mesh/SKM_QuantumCharacter_NoHead"]

report = {"ok": False, "manny": {}, "quantum_skeleton": {}, "modules": {}, "assembled": {},
          "errors": []}


def bones(skeleton):
    """Bone names off a Skeleton asset, via the one route that works in UE 5.8."""
    try:
        return {str(n) for n in skeleton.get_reference_pose().get_bone_names()}
    except Exception as exc:
        report["errors"].append(str(exc))
        return set()


def describe(path):
    mesh = unreal.load_asset(path)
    if mesh is None:
        return {"error": "load failed"}
    skel = mesh.get_editor_property("skeleton")
    out = {"asset": path, "skeleton": skel.get_path_name()}
    try:
        out["lods"] = mesh.get_num_lods()
    except Exception:
        pass
    try:
        out["verts_lod0"] = len(mesh.get_editor_property("lod0_skeleton").get_bone_names()) and None
    except Exception:
        pass
    for prop, key in (("imported_lod0_vertices", "verts"),):
        try:
            out[key] = int(mesh.get_editor_property(prop))
        except Exception:
            pass
    try:
        mats = mesh.get_editor_property("materials")
        out["slots"] = [{"slot": str(m.get_editor_property("material_slot_name")),
                         "material": (m.get_editor_property("material_interface").get_path_name()
                                      if m.get_editor_property("material_interface") else None)}
                        for m in mats]
    except Exception as exc:
        out["slots_error"] = str(exc)
    return out


try:
    manny = unreal.load_asset("/Game/Characters/Heroes/Mannequin/Meshes/SK_Mannequin")
    manny_bones = bones(manny)
    report["manny"] = {"bones": len(manny_bones)}

    qskel = unreal.load_asset(ROOT + "/Mesh/SK_Military_Character_Skeleton")
    if qskel is None:
        report["quantum_skeleton"] = {"error": "did not load"}
    else:
        q_bones = bones(qskel)
        only_q = sorted(q_bones - manny_bones)
        report["quantum_skeleton"] = {
            "asset": qskel.get_path_name(),
            "bones": len(q_bones),
            "shared_with_manny": len(q_bones & manny_bones),
            "only_in_quantum": only_q,
            "only_in_quantum_count": len(only_q),
            "usable_as_leader_pose": len(only_q) == 0,
        }

    for name in MODULES:
        report["modules"][name] = describe(ROOT + "/Mesh/Modules/" + name)
    for path in ASSEMBLED:
        report["assembled"][path] = describe(path)
    report["ok"] = True
except Exception:
    report["errors"].append(traceback.format_exc())

with open(REPORT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=1)
unreal.log("SS_PROBE_DONE")
