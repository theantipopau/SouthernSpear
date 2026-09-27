# Southern Spear - tactical movement content (ADR-024, LOCOMOTION_AUDIT §4 S1).
#
#   1. Input actions IA_SS_Sprint / Walk / Aim / LeanLeft / LeanRight and the mapping context
#      IMC_SS_Tactical (/SSExp_ObjectiveAssault/Input): Left Shift sprint (takes the key from Lyra's
#      dash), Left Alt walk, right mouse aim intent (shared with Lyra's ADS: not consumed),
#      Q / E lean (taking them from Lyra's grenade / melee), and Lyra's grenade on G, melee on V.
#   2. B_SS_Hero_Default (copy of Lyra's B_Hero_Default, reparented to ASSCharacter) and B_SS_Hero (copy
#      of B_Hero_ShooterMannequin, reparented to B_SS_Hero_Default): Lyra's chain with our character at
#      the root; Lyra's assets are untouched. HeroData_SS: a copy of HeroData_ShooterGame using B_SS_Hero.
#   3. The Objective Assault experience's pawn data -> HeroData_SS (players and bots).
# Report: Build/tactical_movement_setup.json.

import json
import os
import traceback

import unreal

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
    ia = unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset(name, INPUT, unreal.InputAction, unreal.InputAction_Factory())
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
    if eal.does_asset_exist(path):
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

    # Lyra's chain is B_Hero_ShooterMannequin -> B_Hero_Default -> LyraCharacter, and B_Hero_Default
    # holds components (character parts among them). Mirror it: B_SS_Hero_Default (copy of
    # B_Hero_Default) -> SSCharacter, and B_SS_Hero (copy of the shooter hero) -> B_SS_Hero_Default.
    base_path = CHARS + "/B_SS_Hero_Default"
    if not eal.does_asset_exist(base_path):
        eal.duplicate_asset("/Game/Characters/Heroes/B_Hero_Default", base_path)
    base = unreal.load_asset(base_path)
    unreal.BlueprintEditorLibrary.reparent_blueprint(base, unreal.load_class(None, "/Script/SouthernSpearLyraBridge.SSCharacter"))
    unreal.BlueprintEditorLibrary.compile_blueprint(base)
    step("hero_default", eal.save_loaded_asset(base, False), base.generated_class().get_name())
    hero_path = CHARS + "/B_SS_Hero"
    if not eal.does_asset_exist(hero_path):
        eal.duplicate_asset("/ShooterCore/Game/B_Hero_ShooterMannequin", hero_path)
    hero = unreal.load_asset(hero_path)
    unreal.BlueprintEditorLibrary.reparent_blueprint(hero, base.generated_class())
    unreal.BlueprintEditorLibrary.compile_blueprint(hero)
    step("hero", eal.save_loaded_asset(hero, False), hero.generated_class().get_name())

    data_path = CHARS + "/HeroData_SS"
    if not eal.does_asset_exist(data_path):
        eal.duplicate_asset("/ShooterCore/Game/HeroData_ShooterGame", data_path)
    data = unreal.load_asset(data_path)
    data.set_editor_property("pawn_class", hero.generated_class())
    step("pawn_data", eal.save_loaded_asset(data, False), data.get_editor_property("pawn_class").get_path_name())

    exp = unreal.load_asset(EXPERIENCE)
    cdo = unreal.get_default_object(exp.generated_class())
    ok = lib.set_property_from_text(cdo, "DefaultPawnData", '"{}"'.format(data.get_path_name()))
    unreal.BlueprintEditorLibrary.compile_blueprint(exp)
    now = lib.get_property_as_text(cdo, "DefaultPawnData")
    step("experience_pawn_data", ok and "HeroData_SS" in now and eal.save_loaded_asset(exp, False), now)


try:
    main()
    report["ok"] = all(s["ok"] for s in report["steps"])
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[TacticalMovement] ok={} {}".format(report["ok"], json.dumps(report["steps"])))
