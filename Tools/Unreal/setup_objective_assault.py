# Build the Objective Assault experience assets and wire Dry River to them.
#
# Idempotent. Run after the level, dressing and navigation passes:
#
#   UnrealEditor-Cmd.exe SouthernSpear.uproject -nullrhi -unattended -nosplash -nosound -stdout ^
#     -ExecutePythonScript=Tools\Unreal\setup_objective_assault.py
#
# Creates (or updates):
#   /SSExp_ObjectiveAssault/SSExp_ObjectiveAssault             GameFeatureData
#       - scans /SSExp_ObjectiveAssault/Experiences for LyraExperienceDefinition
#       - adds Lyra's own two-team setup, team spawning rules, bot spawner and
#         character picker (the same components the Elimination experience uses)
#   /SSExp_ObjectiveAssault/Experiences/B_SS_ObjectiveAssault  LyraExperienceDefinition
#       - enables ShooterCore + SSExp_ObjectiveAssault, ShooterCore pawn and action sets
# and in /Game/Maps/L_DryRiver_01:
#   - one SSObjectiveActor per Objective row of the layout CSV, in CSV order
#   - one SSObjectiveAssaultDirector
#   - WorldSettings.DefaultGameplayExperience = B_SS_ObjectiveAssault
#
# Writes Build/objective_assault_setup.json. Nothing is hardcoded about the
# expected result; the report states what was found and done.

import csv
import json
import os
import traceback

import unreal
import sys

# does_asset_exist() misses Game Feature assets in a commandlet; see Tools/Unreal/ss_assets.py.
sys.path.insert(0, os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Tools", "Unreal"))
from ss_assets import asset_exists  # noqa: E402

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "objective_assault_setup.json")
LAYOUT = os.path.join(PROJECT_DIR, "Content", "Art", "Blockout", "SS_MAP_DryRiver_01_Layout.csv")
MAP = "/Game/Maps/L_DryRiver_01"

GF_ROOT = "/SSExp_ObjectiveAssault"
GFD_NAME = "SSExp_ObjectiveAssault"
EXP_DIR = GF_ROOT + "/Experiences"
EXP_NAME = "B_SS_ObjectiveAssault"

CAPTURE_RADIUS_CM = 1000.0

# Player-facing objective names, keyed by layout row. Identical for both teams.
OBJECTIVE_NAMES = {
    "SS_MAP_DryRiver_ObjA_WaterPoint": "Water Point",
    "SS_MAP_DryRiver_ObjB_Farmstead": "Farmstead",
}

report = {"ok": False, "steps": [], "errors": []}
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    unreal.log("[ObjectiveAssault] {} {} {}".format("OK  " if ok else "FAIL", name, detail))
    return bool(ok)


def load_class(path):
    cls = unreal.load_class(None, path)
    if cls is None:
        raise RuntimeError("class not found: " + path)
    return cls


def component_entry(actor_class, component_class, client, server):
    e = unreal.GameFeatureComponentEntry()
    e.set_editor_property("actor_class", actor_class)
    e.set_editor_property("component_class", component_class)
    e.set_editor_property("client_component", client)
    e.set_editor_property("server_component", server)
    return e


def ensure_game_feature_data():
    path = "{}/{}".format(GF_ROOT, GFD_NAME)
    gfd = eal.load_asset(path) if asset_exists(path) else None
    if gfd is None:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property("data_asset_class", unreal.GameFeatureData)
        gfd = asset_tools.create_asset(GFD_NAME, GF_ROOT, unreal.GameFeatureData, factory)
    if gfd is None:
        return step("game_feature_data", False, "could not create " + path)

    scan = unreal.PrimaryAssetTypeInfo()
    scan.set_editor_property("primary_asset_type", "LyraExperienceDefinition")
    scan.set_editor_property("asset_base_class", load_class("/Script/LyraGame.LyraExperienceDefinition"))
    scan.set_editor_property("has_blueprint_classes", True)
    scan.set_editor_property("directories", [unreal.DirectoryPath(path=EXP_DIR)])
    gfd.set_editor_property("primary_asset_types_to_scan", [scan])

    # FGameFeatureComponentEntry is not exposed to Python, so the entries are
    # written by SouthernSpearObjectivesEditor. These are the components Lyra's
    # own Elimination experience adds, minus its team kill scoring.
    grants = []
    for actor, comp in (
        ("/Script/LyraGame.LyraGameState", "/ShooterCore/Game/B_TeamSetup_TwoTeams.B_TeamSetup_TwoTeams_C"),
        # Team-side deployments (bridge) instead of Lyra's B_TeamSpawningRules, which mixes teams.
        ("/Script/LyraGame.LyraGameState", "/Script/SouthernSpearLyraBridge.SSDeploymentSpawningComponent"),
        ("/Script/LyraGame.LyraGameState", "/ShooterCore/Bot/B_ShooterBotSpawner.B_ShooterBotSpawner_C"),
        # Lyra's game state expects a music manager (on-screen warning every frame otherwise).
        ("/Script/LyraGame.LyraGameState", "/ShooterCore/Elimination/B_MusicManagerComponent_Elimination.B_MusicManagerComponent_Elimination_C"),
        # Per-player eliminations / deaths / assists stat tags (the scoreboard); the base
        # scorer only, not B_TeamDeathMatchScoring, whose kill limit would end the round.
        ("/Script/LyraGame.LyraGameState", "/ShooterCore/Game/B_ShooterGameScoring_Base.B_ShooterGameScoring_Base_C"),
        # Soldier bodies: ASSCharacter attaches B_SS_Soldier itself (Session 031); the Lyra
        # controller cosmetic-parts grant is no longer used.
    ):
        load_class(actor)
        load_class(comp)
        g = unreal.SSComponentGrant()
        g.set_editor_property("actor_class", unreal.SoftClassPath(actor))
        g.set_editor_property("component_class", unreal.SoftClassPath(comp))
        g.set_editor_property("client_component", False)
        g.set_editor_property("server_component", True)
        grants.append(g)
    written = unreal.SSObjectivesEditorLibrary.set_game_feature_component_grants(gfd, grants)
    step("component_grants", written == len(grants), "{} entr(ies)".format(written))
    # Respawn: grant ShooterCore's AbilitySet_Elimination (GA_AutoRespawn and the
    # leaderboard ability) to every player state. Lyra's FGameFeatureAbilitiesEntry
    # is not exposed to Python, so the list is written from text.
    abilities = unreal.new_object(load_class("/Script/LyraGame.GameFeatureAction_AddAbilities"), outer=gfd)
    text = ('((ActorClass="/Script/LyraGame.LyraPlayerState",'
            'GrantedAbilitySets=("/ShooterCore/Elimination/AbilitySet_Elimination.AbilitySet_Elimination")))')
    ok = unreal.SSObjectivesEditorLibrary.set_property_from_text(abilities, "AbilitiesList", text)
    actions = [a for a in gfd.get_editor_property("actions")
               if a.get_class().get_name() != "GameFeatureAction_AddAbilities"]
    gfd.set_editor_property("actions", actions + [abilities])
    step("respawn_abilities", ok, "AbilitySet_Elimination -> LyraPlayerState")

    saved = eal.save_loaded_asset(gfd, False)
    return step("game_feature_data", saved, path)


def ensure_experience():
    path = "{}/{}".format(EXP_DIR, EXP_NAME)
    bp = eal.load_asset(path) if asset_exists(path) else None
    if bp is None:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", load_class("/Script/LyraGame.LyraExperienceDefinition"))
        bp = asset_tools.create_asset(EXP_NAME, EXP_DIR, unreal.Blueprint, factory)
    if bp is None:
        return step("experience", False, "could not create " + path), None

    cdo = unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property("game_features_to_enable", ["ShooterCore", GFD_NAME])
    cdo.set_editor_property("default_pawn_data",
                            unreal.load_asset("/ShooterCore/Game/HeroData_ShooterGame.HeroData_ShooterGame"))
    cdo.set_editor_property("action_sets", [
        unreal.load_asset("/ShooterCore/Experiences/LAS_ShooterGame_SharedInput"),
        unreal.load_asset("/ShooterCore/Experiences/LAS_ShooterGame_StandardComponents"),
        # Lyra's StandardHUD is replaced by the Southern Spear HUD (setup_ui.py).
    ])
    saved = eal.save_loaded_asset(bp, False)
    step("experience", saved, path)
    return saved, bp.generated_class()


EXTRA_STARTS_PER_TEAM = 7
START_SPACING_CM = 400.0


def ground_z(world, x, y):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, 50000.0), unreal.Vector(x, y, -50000.0),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    if hit is None:
        return None
    hr = hit[1] if isinstance(hit, (list, tuple)) else hit
    return hr.to_dict()["impact_point"].z


def place_deployment_starts(world, actor_sub):
    """A line of extra LyraPlayerStarts beside each deployment's primary start,
    so a team does not spawn stacked on one point. Mirrored for both teams."""
    # Traces return nothing until the world has been through a nav/physics build.
    unreal.SystemLibrary.execute_console_command(world, "BUILDPATHS")
    starts = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart)
    for a in starts:
        if "_Extra" in a.get_actor_label():
            actor_sub.destroy_actor(a)
    primaries = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart)
                 if "_Extra" not in a.get_actor_label()]
    placed, missed = 0, 0
    for primary in primaries:
        base = primary.get_actor_location()
        rot = primary.get_actor_rotation()
        offsets = [(i // 2 + 1) * START_SPACING_CM * (1 if i % 2 == 0 else -1)
                   for i in range(EXTRA_STARTS_PER_TEAM)]
        for n, dx in enumerate(offsets):
            z = ground_z(world, base.x + dx, base.y)
            if z is None:
                missed += 1
                continue
            actor = actor_sub.spawn_actor_from_class(
                primary.get_class(), unreal.Vector(base.x + dx, base.y, z + 100.0), rot)
            if actor:
                actor.set_actor_label("{}_Extra{:02d}".format(primary.get_actor_label(), n + 1))
                placed += 1
    report["extra_starts"] = {"primaries": len(primaries), "placed": placed, "no_ground": missed}
    return step("deployment_starts", len(primaries) == 2 and missed == 0,
                "{} extra start(s) across {} deployment(s)".format(placed, len(primaries)))


def wire_map(experience_class):
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not world:
        return step("load_map", False, MAP)
    step("load_map", True, MAP)

    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    removed = 0
    for cls in (unreal.SSObjectiveActor, unreal.SSObjectiveAssaultDirector):
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, cls):
            actor_sub.destroy_actor(a)
            removed += 1
    report["removed_existing"] = removed

    with open(LAYOUT, "r", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["kind"] == "Objective"]
    report["objectives"] = []
    for index, row in enumerate(rows):
        # CSV is Blender metres; Unreal is centimetres with Y mirrored.
        loc = unreal.Vector(float(row["x"]) * 100.0, -float(row["y"]) * 100.0, float(row["z"]) * 100.0)
        actor = actor_sub.spawn_actor_from_class(unreal.SSObjectiveActor, loc, unreal.Rotator(roll=0, pitch=0, yaw=0))
        if actor is None:
            step("spawn_objective", False, row["name"])
            continue
        actor.set_actor_label(row["name"])
        actor.set_editor_property("sequence_index", index)
        actor.set_editor_property("objective_name", unreal.Text(OBJECTIVE_NAMES.get(row["name"], row["name"])))
        actor.get_component_by_class(unreal.SphereComponent).set_sphere_radius(CAPTURE_RADIUS_CM)
        report["objectives"].append({"label": row["name"], "sequence_index": index, "location_cm": [loc.x, loc.y, loc.z]})
    step("objectives_placed", len(report["objectives"]) == len(rows) and rows,
         "{}/{} objective(s)".format(len(report["objectives"]), len(rows)))

    place_deployment_starts(world, actor_sub)

    director = actor_sub.spawn_actor_from_class(unreal.SSObjectiveAssaultDirector, unreal.Vector(0, 0, 0),
                                                unreal.Rotator(roll=0, pitch=0, yaw=0))
    if director:
        director.set_actor_label("SS_ObjectiveAssault_Director")
    step("director_placed", director is not None)

    settings = world.get_world_settings()
    # DefaultGameplayExperience is EditDefaultsOnly, which Python refuses on an
    # instance; SouthernSpearObjectivesEditor sets it from text instead.
    class_path = experience_class.get_path_name()
    set_ok = unreal.SSObjectivesEditorLibrary.set_property_from_text(
        settings, "DefaultGameplayExperience", class_path)
    now = str(settings.get_editor_property("default_gameplay_experience"))
    step("world_experience", set_ok and EXP_NAME in now, now)

    saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
    return step("save_map", saved, MAP)


def main():
    try:
        ok = ensure_game_feature_data()
        exp_ok, exp_class = ensure_experience()
        ok = ok and exp_ok and exp_class is not None and wire_map(exp_class)
        report["ok"] = bool(ok) and all(s["ok"] for s in report["steps"])
    except Exception:  # noqa: BLE001
        report["errors"].append(traceback.format_exc())
        unreal.log_error("[ObjectiveAssault] raised:\n" + traceback.format_exc())
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    unreal.log("[ObjectiveAssault] result ok={} -> {}".format(report["ok"], REPORT))


# SS_OA_IMPORT_ONLY lets other scripts reuse ensure_game_feature_data() without
# re-wiring (and re-saving) the Dry River map.
if not os.environ.get("SS_OA_IMPORT_ONLY"):
    main()
