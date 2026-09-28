# Southern Spear - tactical movement content (ADR-024, LOCOMOTION_AUDIT §4 S1).
#
#   1. Input actions IA_SS_Sprint / Walk / Aim / LeanLeft / LeanRight and the mapping context
#      IMC_SS_Tactical (/SSExp_ObjectiveAssault/Input): Left Shift sprint (takes the key from Lyra's
#      dash), Left Alt walk, right mouse aim intent (shared with Lyra's ADS: not consumed),
#      Q / E lean (taking them from Lyra's grenade / melee), and Lyra's grenade on G, melee on V.
#   2. ADR-026 (Lyra departure): Lyra's B_Hero_Default reparented to ASSCharacter, so every Lyra hero
#      (players and bots) gets the tactical character and movement, and Lyra's own Blueprints that
#      identify the hero by class keep working.
#   3. The Objective Assault experience uses Lyra's HeroData_ShooterGame.
# Report: Build/tactical_movement_setup.json.

import json
import os
import traceback

import unreal
import sys

# does_asset_exist() misses Game Feature assets in a commandlet; see Tools/Unreal/ss_assets.py.
sys.path.insert(0, os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Tools", "Unreal"))
from ss_assets import asset_exists  # noqa: E402

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "tactical_movement_setup.json")
INPUT = "/SSExp_ObjectiveAssault/Input"
CHARS = "/SSExp_ObjectiveAssault/Characters"
EXPERIENCE = "/SSExp_ObjectiveAssault/Experiences/B_SS_ObjectiveAssault"
eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.SSObjectivesEditorLibrary
report = {"ok": False, "steps": [], "errors": []}


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def input_action(name, consume=True):
    path = INPUT + "/" + name
    ia = unreal.load_asset(path) if asset_exists(path) else tools.create_asset(name, INPUT, unreal.InputAction, unreal.InputAction_Factory())
    ia.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN)
    ia.set_editor_property("consume_input", consume)
    eal.save_loaded_asset(ia, False)
    return ia


def key(name):
    k = unreal.Key()
    k.set_editor_property("key_name", name)
    return k


def main():
    ours = {
        "IA_SS_Sprint": ("LeftShift", True),
        "IA_SS_Walk": ("LeftAlt", True),
        "IA_SS_Aim": ("RightMouseButton", False),
        "IA_SS_LeanLeft": ("Q", True),
        "IA_SS_LeanRight": ("E", True),
    }
    path = INPUT + "/IMC_SS_Tactical"
    if asset_exists(path):
        eal.delete_asset(path)
    imc = tools.create_asset("IMC_SS_Tactical", INPUT, unreal.InputMappingContext, unreal.InputMappingContext_Factory())
    for name, (k, consume) in ours.items():
        imc.map_key(input_action(name, consume), key(k))
    for lyra_name, k in (("/ShooterCore/Input/Actions/IA_Grenade", "G"), ("/ShooterCore/Input/Actions/IA_Melee", "V")):
        ia = unreal.load_asset(lyra_name)
        if ia:
            imc.map_key(ia, key(k))
    eal.save_loaded_asset(imc, False)
    step("input", True, "IMC_SS_Tactical: {} mappings".format(len(ours) + 2))

    # ADR-026: ASSCharacter goes UNDER Lyra's heroes: B_Hero_Default (parent of B_Hero_ShooterMannequin)
    # is reparented from LyraCharacter to SSCharacter. Copies of the hero broke Lyra Blueprints that
    # identify it by class (B_WeaponInstance_Base casts to B_Hero_ShooterMannequin: bots never fired).
    base = unreal.load_asset("/Game/Characters/Heroes/B_Hero_Default")
    unreal.BlueprintEditorLibrary.reparent_blueprint(base, unreal.load_class(None, "/Script/SouthernSpearLyraBridge.SSCharacter"))
    unreal.BlueprintEditorLibrary.compile_blueprint(base)
    step("hero_default_reparented", eal.save_loaded_asset(base, False), "B_Hero_Default -> SSCharacter")
    for old in ("B_SS_Hero", "B_SS_Hero_Default", "HeroData_SS"):
        if asset_exists(CHARS + "/" + old):
            eal.delete_asset(CHARS + "/" + old)

    exp = unreal.load_asset(EXPERIENCE)
    cdo = unreal.get_default_object(exp.generated_class())
    ok = lib.set_property_from_text(cdo, "DefaultPawnData", '"/ShooterCore/Game/HeroData_ShooterGame.HeroData_ShooterGame"')
    unreal.BlueprintEditorLibrary.compile_blueprint(exp)
    now = lib.get_property_as_text(cdo, "DefaultPawnData")
    step("experience_pawn_data", ok and "HeroData_ShooterGame" in now and eal.save_loaded_asset(exp, False), now)


try:
    main()
    report["ok"] = all(s["ok"] for s in report["steps"])
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[TacticalMovement] ok={} {}".format(report["ok"], json.dumps(report["steps"])))
