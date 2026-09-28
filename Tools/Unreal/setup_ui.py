# Southern Spear - UI content (SouthernSpearUI plugin).
#
# 1. Imports Docs/images/loadingscreen.png as /SouthernSpearUI/Textures/T_SS_KeyArt
#    (loading screen and front-end background).
# 2. Creates /Game/Maps/L_SS_FrontEnd: an empty level whose game mode is
#    ASSFrontEndGameMode (the title menu). Config/DefaultEngine.ini boots into it.
# 3. Drops Lyra's LAS_ShooterGame_StandardHUD from B_SS_ObjectiveAssault: the
#    Southern Spear HUD (SouthernSpearUI + SouthernSpearObjectivesUI) replaces it.
# Idempotent. Writes Build/ui_setup.json.

import json
import os
import traceback

import unreal
import sys

# does_asset_exist() misses Game Feature assets in a commandlet; see Tools/Unreal/ss_assets.py.
sys.path.insert(0, os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Tools", "Unreal"))
from ss_assets import asset_exists  # noqa: E402

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "ui_setup.json")
KEY_ART = os.path.join(PROJECT_DIR, "Docs", "images", "loadingscreen.png")
TEX_DIR = "/SouthernSpearUI/Textures"
FRONT_END = "/Game/Maps/L_SS_FrontEnd"
EXPERIENCE = "/SSExp_ObjectiveAssault/Experiences/B_SS_ObjectiveAssault"

eal = unreal.EditorAssetLibrary
report = {"ok": False, "steps": [], "errors": []}


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def import_key_art(source=None, name="T_SS_KeyArt"):
    task = unreal.AssetImportTask()
    task.filename = source or KEY_ART
    task.destination_path = TEX_DIR
    task.destination_name = name
    task.replace_existing = True
    task.automated = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = unreal.load_asset(TEX_DIR + "/" + name)
    if tex:
        tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
        tex.set_editor_property("never_stream", True)
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        eal.save_loaded_asset(tex)
    step("key_art_" + name, tex is not None, TEX_DIR + "/" + name)


def front_end_map():
    if asset_exists(FRONT_END):
        eal.delete_asset(FRONT_END)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ok = les.new_level(FRONT_END)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ws = world.get_world_settings()
    mode = unreal.load_class(None, "/Script/SouthernSpearUI.SSFrontEndGameMode")
    ws.set_editor_property("default_game_mode", mode)
    saved = les.save_current_level()
    step("front_end_map", ok and mode is not None and saved, "{} mode={}".format(FRONT_END, mode))


def drop_lyra_hud():
    bp = unreal.load_asset(EXPERIENCE)
    cdo = unreal.get_default_object(bp.generated_class())
    sets = list(cdo.get_editor_property("action_sets"))
    kept = [s for s in sets if s and "StandardHUD" not in s.get_name()]
    cdo.set_editor_property("action_sets", kept)
    saved = eal.save_loaded_asset(bp, False)
    step("experience_hud", saved and len(kept) == len(sets) - 1 or len(kept) == len(sets),
         [s.get_name() for s in kept])


try:
    import_key_art()
    import_key_art(os.path.join(PROJECT_DIR, "Docs", "images", "mainmenu.png"), "T_SS_MainMenu")
    import_key_art(os.path.join(PROJECT_DIR, "Docs", "images", "logo.png"), "T_SS_Logo")
    drop_lyra_hud()
    front_end_map()
    report["ok"] = all(s["ok"] for s in report["steps"])
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[UI] ok={}".format(report["ok"]))
