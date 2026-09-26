# Southern Spear - soldier bodies (ADR-003, ADR-016, ADR-021).
#
# B_SS_Soldier (ASSCharacterPartActor): the viewer's own team is shown with the
# Fab "Quantum" military character (3 ACR look), the other team with Fab
# "Modern Insurgent 7" parts chosen for a conventional uniform (MAF look: no
# balaclava, beard or irregular gear; ADR-016). Both packs use UE-mannequin bone
# names, so the meshes follow Lyra's animated mannequin by leader pose.
# B_SS_CharacterParts (Lyra controller character-parts component) adds it to
# every pawn, and the Game Feature grants it in place of B_PickRandomCharacter.
# Idempotent. Writes Build/soldiers_setup.json.

import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "soldiers_setup.json")
DEST = "/SSExp_ObjectiveAssault/Characters"
FRIENDLY = ["/Game/QuantumCharacter/Mesh/SKM_QuantumCharacter"]
MAF = "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/"
OPPOSING = [MAF + n for n in ("SK_Head", "SK_Hands", "SK_Sweater", "SK_Pants_Military", "SK_Shoes",
                              "SK_Armor_Small", "SK_Beret")]

eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.SSObjectivesEditorLibrary
report = {"ok": False, "steps": [], "errors": []}


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def blueprint(name, parent):
    path = DEST + "/" + name
    if eal.does_asset_exist(path):
        return unreal.load_asset(path)
    f = unreal.BlueprintFactory()
    f.set_editor_property("parent_class", parent)
    return tools.create_asset(name, DEST, unreal.Blueprint, f)


def main():
    friendly = [unreal.load_asset(p) for p in FRIENDLY]
    opposing = [unreal.load_asset(p) for p in OPPOSING]
    step("meshes", all(friendly) and all(opposing), "{} friendly, {} opposing".format(len(friendly), len(opposing)))

    soldier = blueprint("B_SS_Soldier", unreal.SSCharacterPartActor)
    cdo = unreal.get_default_object(soldier.generated_class())
    cdo.set_editor_property("friendly_parts", [m for m in friendly if m])
    cdo.set_editor_property("opposing_parts", [m for m in opposing if m])
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
