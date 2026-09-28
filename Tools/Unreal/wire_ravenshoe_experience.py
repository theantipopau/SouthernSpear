# Southern Spear - wire Ravenshoe Crossing to the Objective Assault experience.
#
# setup_objective_assault.py builds the GameFeatureData and the
# LyraExperienceDefinition, and wires Dry River to them. Both assets already
# exist and are committed, and neither is map-specific, so this script does NOT
# rebuild them - it only does the level half for Ravenshoe:
#
#   - one SSObjectiveActor per Objective row of the Ravenshoe layout CSV, in
#     CSV order, with sequence_index and a player-facing name
#   - one SSObjectiveAssaultDirector
#   - WorldSettings.DefaultGameplayExperience = B_SS_ObjectiveAssault
#
# setup_objective_assault.py is left alone deliberately: it is Dry River's
# script with Dry River's paths hardcoded, and Dry River depends on it. Note
# also that the two layout CSVs do NOT share a column order - Dry River is
# name,x,y,z,kind and Ravenshoe is name,kind,x,y,z,... - so sharing one parser
# would have been a silent-corruption bug, not a saving.
#
# Until this ran, Ravenshoe had two correctly-placed objective actors and two
# equidistant PlayerStarts and no experience bound, so a match launched on it
# had nothing driving the sequence.
#
# RUN ORDER: after import/dress/surfaces/light, before the nav bake.
# Writes Build/ravenshoe_experience_wiring.json.

import csv
import json
import os
import traceback

import unreal

PROJECT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT, "Build", "ravenshoe_experience_wiring.json")
MAP = "/Game/Maps/L_Ravenshoe_01"
LAYOUT = os.path.join(PROJECT, "Content", "Art", "Blockout",
                      "SS_MAP_Ravenshoe_01_Layout.csv")
EXP_ASSET = "/SSExp_ObjectiveAssault/Experiences/B_SS_ObjectiveAssault"
EXP_NAME = "B_SS_ObjectiveAssault"
CAPTURE_RADIUS_CM = 1000.0

# Player-facing names. The raw row names are engineering labels; these are what
# the HUD prints, so they name the thing rather than the coordinate.
OBJECTIVE_NAMES = {
    "SS_MAP_Ravenshoe_ObjA_Span": "The Span",
    "SS_MAP_Ravenshoe_ObjB_GravelGate": "Gravel Gate",
}

report = {"ok": False, "steps": [], "errors": []}


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return bool(ok)


def main():
    # The experience is a Blueprint, so the class comes from generated_class().
    # load_class() on the asset path returns None here - the BP path and the
    # _C class path are different objects, and DefaultGameplayExperience wants
    # the class.
    exp_bp = unreal.EditorAssetLibrary.load_asset(EXP_ASSET)
    exp_class = exp_bp.generated_class() if exp_bp is not None else None
    if not step("experience_class", exp_class is not None, EXP_ASSET):
        report["errors"].append("experience not found: " + EXP_ASSET)
        return
    report["experience_class_path"] = exp_class.get_path_name()
    step("experience_class", True, exp_class.get_path_name())

    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not step("load_map", world is not None, MAP):
        report["errors"].append("could not open " + MAP)
        return

    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # Purge and rebuild. import_ravenshoe.py already spawns an SSObjectiveActor
    # per Objective row, but without sequence_index or objective_name, so
    # leaving them would mean half-configured actors with no capture radius.
    removed = 0
    for cls in (unreal.SSObjectiveActor, unreal.SSObjectiveAssaultDirector):
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, cls):
            sub.destroy_actor(a)
            removed += 1
    report["removed_existing"] = removed

    with open(LAYOUT, "r", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["kind"] == "Objective"]
    report["layout_objective_rows"] = len(rows)
    if not step("layout_rows", len(rows) == 2, "{} objective row(s)".format(len(rows))):
        report["errors"].append("expected 2 objective rows, found %d" % len(rows))
        return

    placed = []
    for index, row in enumerate(rows):
        # CSV is Blender metres; Unreal is centimetres with Y mirrored.
        loc = unreal.Vector(float(row["x_m"]) * 100.0,
                            -float(row["y_m"]) * 100.0,
                            float(row["z_m"]) * 100.0)
        actor = sub.spawn_actor_from_class(
            unreal.SSObjectiveActor, loc, unreal.Rotator(roll=0, pitch=0, yaw=0))
        if actor is None:
            step("spawn_objective", False, row["name"])
            continue
        actor.set_actor_label(row["name"])
        actor.set_editor_property("sequence_index", index)
        actor.set_editor_property(
            "objective_name",
            unreal.Text(OBJECTIVE_NAMES.get(row["name"], row["name"])))
        sphere = actor.get_component_by_class(unreal.SphereComponent)
        if sphere is not None:
            sphere.set_sphere_radius(CAPTURE_RADIUS_CM)
        placed.append({"label": row["name"],
                       "sequence_index": index,
                       "player_name": OBJECTIVE_NAMES.get(row["name"], row["name"]),
                       "radius_cm": CAPTURE_RADIUS_CM,
                       "location_cm": [loc.x, loc.y, loc.z]})
    report["objectives"] = placed
    step("objectives_placed", len(placed) == 2, "%d/2" % len(placed))

    director = sub.spawn_actor_from_class(
        unreal.SSObjectiveAssaultDirector, unreal.Vector(0, 0, 0),
        unreal.Rotator(roll=0, pitch=0, yaw=0))
    if director is not None:
        director.set_actor_label("SS_ObjectiveAssault_Director")
    step("director_placed", director is not None)

    # DefaultGameplayExperience is EditDefaultsOnly, which Python refuses to set
    # on an instance; the objectives editor library sets it from text. Reading it
    # back is the only way to know it took.
    settings = world.get_world_settings()
    set_ok = unreal.SSObjectivesEditorLibrary.set_property_from_text(
        settings, "DefaultGameplayExperience", exp_class.get_path_name())
    now = str(settings.get_editor_property("default_gameplay_experience"))
    report["default_gameplay_experience"] = now
    bound = step("world_experience", set_ok and EXP_NAME in now, now)
    if not bound:
        report["errors"].append("experience did not bind: " + now)

    saved = unreal.EditorLoadingAndSavingUtils.save_map(world, MAP)
    step("save_map", saved, MAP)

    # Re-count from the saved level, because a spawn that reports success and a
    # save that reports success is still not evidence that either stuck.
    actors = [a for a in sub.get_all_level_actors()]
    objs = [a for a in actors if isinstance(a, unreal.SSObjectiveActor)]
    dirs = [a for a in actors if isinstance(a, unreal.SSObjectiveAssaultDirector)]
    starts = [a for a in actors if isinstance(a, unreal.PlayerStart)]
    report["verified"] = {
        "ss_objective_actors": len(objs),
        "directors": len(dirs),
        "player_starts": len(starts),
    }
    step("verified_objectives", len(objs) == 2, str(len(objs)))
    step("verified_director", len(dirs) == 1, str(len(dirs)))
    step("verified_starts", len(starts) == 2, str(len(starts)))

    report["ok"] = all(s["ok"] for s in report["steps"]) and not report["errors"]


try:
    main()
except Exception:  # noqa: BLE001
    report["errors"].append(traceback.format_exc())
finally:
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, default=str)
