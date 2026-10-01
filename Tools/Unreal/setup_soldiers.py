# Southern Spear - soldier bodies (ADR-003, ADR-016, ADR-021, ADR-042).
#
# B_SS_Soldier (ASSCharacterPartActor): the friendly look uses the ADFRC G3
# uniform, TBAS vest and OpsCore helmet on Manny's skeleton, with the Quantum
# head retargeted from the animated pawn pose. The G3 uniform carries its
# ADFRC-authored AMC/AMCU shirt and trouser material slots; keep those source
# materials rather than the prototype's generated DPC tile on Quantum clothing.
# This is the producer's requested ADFRC model/texture assembly, replacing the
# visually rejected Quantum outfit. MAF stays on its separate conventional look.
# R-91 still applies only to component overrides: no mesh asset material array
# is written by Python here.

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
# Game Feature content does not resolve in a -run=pythonscript commandlet until the asset registry
# has scanned it: the first load returns a quiet None (measured 2026-10-01, Build/load_route_probe.json)
# and this script then hard-fails on a mesh that is present on disk.
unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous(
    ["/SSExp_ObjectiveAssault"], force_rescan=True)
REPORT = os.path.join(PROJECT_DIR, "Build", "soldiers_setup.json")
DEST = "/SSExp_ObjectiveAssault/Characters"
# Friendly ADFRC assembly requested by the producer: the Quantum head remains
# independently retargeted, while the complete ADFRC G3 body and fitted gear
# share the Manny skeleton and follow the same evaluated 3rd-person pose.
FRIENDLY_RETARGET = ["/SSExp_ObjectiveAssault/Characters/QuantumProto/SKM_Head"]
FRIENDLY_LEADER = ["/SSExp_ObjectiveAssault/Characters/ADF/" + n
                   for n in ("SK_ADF_Uniform_G3", "SK_ADF_Vest_TBAS", "SK_ADF_Helmet_OpsCore")]
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
    if not all(retarget) or not all(leader):
        raise RuntimeError("required ADFRC friendly mesh/head failed to load")

    # The Quantum head keeps its authored face/eye materials. Clothing and gear
    # use their ADFRC SkeletalMesh material assignments, including the G3's
    # source AMC/AMCU texture maps, so no generated camo is injected on top.
    friendly_overrides = [unreal.SSPartMaterialOverride()]
    step("friendly_assembly", len(retarget) == 1 and len(leader) == 3,
         "Quantum head retarget + ADFRC G3 uniform/TBAS vest/OpsCore helmet leader pose")

    soldier = blueprint("B_SS_Soldier", unreal.SSCharacterPartActor)
    cdo = unreal.get_default_object(soldier.generated_class())
    cdo.set_editor_property("friendly_parts", [m for m in retarget if m])
    cdo.set_editor_property("friendly_leader_pose_parts", [m for m in leader if m])
    cdo.set_editor_property("retarget_friendly_pose", True)
    # The retargeted head is a different-proportioned rig; align it to the mannequin's head bone, which
    # is where the ADFRC helmet the head has to sit inside is fitted (see FriendlyRetargetAnchor).
    cdo.set_editor_property("friendly_retarget_anchor", "head")
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
