# Southern Spear - soldier bodies (ADR-003, ADR-016, ADR-021, ADR-042).
#
# B_SS_Soldier (ASSCharacterPartActor): the viewer's own team is shown with the
# Fab "Quantum" military character on its own skeleton (3 ACR look, ADR-042:
# the producer's choice; the G3/Modern-Insurgent mix read as assembled rather
# than worn), retargeted per tick from the pawn mesh's evaluated pose by
# ASSCharacterPartActor. The ADFRC vest and helmet stay Manny-rigged and follow
# by leader pose, layered over the Quantum body. The other team keeps the
# Fab "Modern Insurgent 7" parts chosen for a conventional uniform (MAF look:
# no balaclava, beard or irregular gear; ADR-016), which follow by leader pose.
# The ADFRC camo materials are applied as FriendlyMaterialOverrides (R-91: the mesh assets'
# slots are read-only from Python), from setup_quantum_proto.py's saved instances.
# B_SS_CharacterParts (Lyra controller character-parts component) adds it to
# every pawn, and the Game Feature grants it in place of B_PickRandomCharacter.
# Idempotent. Writes Build/soldiers_setup.json.

import json
import os
import traceback

import unreal
import sys

# does_asset_exist() misses Game Feature assets in a commandlet; see Tools/Unreal/ss_assets.py.
sys.path.insert(0, os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Tools", "Unreal"))
from ss_assets import asset_exists  # noqa: E402

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "soldiers_setup.json")
DEST = "/SSExp_ObjectiveAssault/Characters"
# 3 ACR (ADR-042): the Quantum character on its own skeleton (duplicated with the
# ADFRC camo already applied by setup_quantum_proto.py, never reparented to the
# mannequin), plus the ADFRC vest and helmet which stay on the mannequin skeleton
# and follow by leader pose. The shirt's rolled sleeves end at the forearm, so
# SKM_Arms carries the hands.
FRIENDLY_RETARGET = ["/SSExp_ObjectiveAssault/Characters/QuantumProto/" + n
                     for n in ("SKM_Shirt_RolledUp_Blue", "SKM_Jeans", "SKM_Arms", "SKM_Head")]
FRIENDLY_LEADER = ["/SSExp_ObjectiveAssault/Characters/ADF/" + n
                   for n in ("SK_ADF_Vest_TBAS", "SK_ADF_Helmet_OpsCore")]
MAF = "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/"
# MAF (ADR-016: a conventional force): the same fitted uniform in a green palette, a PASGT helmet and a
# Peacekeeper plate vest (setup_adf_soldier.py), with the conventional head.
ADF = "/SSExp_ObjectiveAssault/Characters/ADF/"
OPPOSING = [MAF + "SK_Head", ADF + "SK_ADF_Uniform_G3", ADF + "SK_MAF_Vest_Peacekeeper", ADF + "SK_MAF_Helmet_PASGT"]

eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.SSObjectivesEditorLibrary
report = {"ok": False, "steps": [], "errors": []}


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def blueprint(name, parent):
    path = DEST + "/" + name
    if asset_exists(path):
        return unreal.load_asset(path)
    f = unreal.BlueprintFactory()
    f.set_editor_property("parent_class", parent)
    return tools.create_asset(name, DEST, unreal.Blueprint, f)


def main():
    retarget = [unreal.load_asset(p) for p in FRIENDLY_RETARGET]
    leader = [unreal.load_asset(p) for p in FRIENDLY_LEADER]
    opposing = [unreal.load_asset(p) for p in OPPOSING]
    step("meshes", all(retarget) and all(leader) and all(opposing),
         "{} friendly retarget, {} friendly leader-pose, {} opposing".format(
             len(retarget), len(leader), len(opposing)))

    # The camo instances from setup_quantum_proto.py (R-91: mesh-asset slots are read-only
    # from Python, so the camo rides on the character-part components as overrides).
    shirt_camo = unreal.load_asset("/SSExp_ObjectiveAssault/Characters/QuantumProto/MI_SS_ADFRC_Camo_Shirt")
    jeans_camo = unreal.load_asset("/SSExp_ObjectiveAssault/Characters/QuantumProto/MI_SS_ADFRC_Camo_Jeans")

    def overrides_for(mesh, camo):
        """One inner override array per mesh: the camo instance on every slot (each garment
        module is single-slot), so the vendor blue never reaches the component."""
        slots = []
        if mesh is not None:
            slots = [camo for _ in mesh.get_editor_property("materials")]
        wrap = unreal.SSPartMaterialOverride()
        wrap.set_editor_property("slots", slots)
        return wrap

    by_name = {p.rsplit("/", 1)[-1]: m for p, m in zip(FRIENDLY_RETARGET, retarget)}
    friendly_overrides = [
        overrides_for(by_name.get("SKM_Shirt_RolledUp_Blue"), shirt_camo),
        overrides_for(by_name.get("SKM_Jeans"), jeans_camo),
        unreal.SSPartMaterialOverride(),  # arms: authored material
        unreal.SSPartMaterialOverride(),  # head: authored materials
    ]
    step("camo_overrides", shirt_camo is not None and jeans_camo is not None,
         "shirt={} jeans={}".format(shirt_camo.get_path_name() if shirt_camo else None,
                                    jeans_camo.get_path_name() if jeans_camo else None))

    soldier = blueprint("B_SS_Soldier", unreal.SSCharacterPartActor)
    cdo = unreal.get_default_object(soldier.generated_class())
    cdo.set_editor_property("friendly_parts", [m for m in retarget if m])
    cdo.set_editor_property("friendly_leader_pose_parts", [m for m in leader if m])
    cdo.set_editor_property("retarget_friendly_pose", True)
    cdo.set_editor_property("opposing_parts", [m for m in opposing if m])
    cdo.set_editor_property("friendly_material_overrides", friendly_overrides)
    # MAF: the uniform (part 1) in the green palette, from setup_adf_soldier.py's report.
    adf = json.load(open(os.path.join(PROJECT_DIR, "Build", "adf_soldier_setup.json")))
    green = unreal.SSPartMaterialOverride()
    green.set_editor_property("slots", [unreal.load_asset(p) for p in adf["maf_uniform_slots"]])
    cdo.set_editor_property("opposing_material_overrides", [unreal.SSPartMaterialOverride(), green])
    unreal.BlueprintEditorLibrary.compile_blueprint(soldier)
    step("soldier", eal.save_loaded_asset(soldier), soldier.generated_class().get_path_name())

    parts = blueprint("B_SS_CharacterParts",
                      unreal.load_class(None, "/Script/LyraGame.LyraControllerComponent_CharacterParts"))
    pcdo = unreal.get_default_object(parts.generated_class())
    text = '((Part=(PartClass="{}",CollisionMode=NoCollision)))'.format(soldier.generated_class().get_path_name())
    ok = lib.set_property_from_text(pcdo, "CharacterParts", text)
    unreal.BlueprintEditorLibrary.compile_blueprint(parts)
    report["character_parts"] = lib.get_property_as_text(pcdo, "CharacterParts")
    step("character_parts", ok and "B_SS_Soldier" in report["character_parts"] and eal.save_loaded_asset(parts),
         report["character_parts"])


try:
    main()
    report["ok"] = all(s["ok"] for s in report["steps"])
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[Soldiers] ok={}".format(report["ok"]))
