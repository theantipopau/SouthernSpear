# Southern Spear - Dry River lighting pass.
#
# The level pass builds geometry only, so the map rendered black. This places
# an outdoor daylight rig: sun (atmosphere sun light), sky atmosphere, real-time
# sky light, height fog and a post-process volume with bounded exposure. All
# movable, so no light build is needed and Lumen handles bounce light.
#
# Idempotent: actors labelled SS_Light_* are removed and re-placed each run.
# Run after dressing and before setup_objective_assault / nav (see
# Docs/MAPS_DRYRIVER.md). Writes Build/dryriver_lighting_report.json.

import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "dryriver_lighting_report.json")
MAP = "/Game/Maps/L_DryRiver_01"
PREFIX = "SS_Light_"

report = {"ok": False, "steps": [], "errors": []}


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def spawn(actor_sub, cls, label, location=unreal.Vector(0, 0, 0), rotation=None):
    actor = actor_sub.spawn_actor_from_class(cls, location, rotation or unreal.Rotator(roll=0, pitch=0, yaw=0))
    if actor:
        actor.set_actor_label(PREFIX + label)
    step("spawn_" + label, actor is not None, cls.__name__ if hasattr(cls, "__name__") else cls)
    return actor


def main():
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not step("load_map", world is not None, MAP):
        return False
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    removed = 0
    for a in actor_sub.get_all_level_actors():
        if a.get_actor_label().startswith(PREFIX):
            actor_sub.destroy_actor(a)
            removed += 1
    report["removed_existing"] = removed

    # Late-morning inland sun: high, warm, from the north-east (southern hemisphere).
    sun = spawn(actor_sub, unreal.DirectionalLight, "Sun", unreal.Vector(0, 0, 5000),
                unreal.Rotator(roll=0, pitch=-52, yaw=35))
    if sun:
        c = sun.light_component
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_intensity(10.0)
        c.set_light_color(unreal.LinearColor(1.0, 0.95, 0.86, 1.0))
        c.set_editor_property("atmosphere_sun_light", True)
        c.set_editor_property("cast_shadows", True)

    spawn(actor_sub, unreal.SkyAtmosphere, "Atmosphere")

    sky = spawn(actor_sub, unreal.SkyLight, "SkyLight", unreal.Vector(0, 0, 3000))
    if sky:
        c = sky.light_component
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_editor_property("real_time_capture", True)
        c.set_intensity(1.0)

    fog = spawn(actor_sub, unreal.ExponentialHeightFog, "HeightFog")
    if fog:
        c = fog.component
        c.set_editor_property("fog_density", 0.01)
        c.set_editor_property("fog_inscattering_luminance", unreal.LinearColor(0.75, 0.68, 0.58, 1.0))

    ppv = spawn(actor_sub, unreal.PostProcessVolume, "PostProcess")
    if ppv:
        ppv.set_editor_property("unbound", True)
        s = ppv.settings
        s.set_editor_property("override_auto_exposure_min_brightness", True)
        s.set_editor_property("auto_exposure_min_brightness", 0.5)
        s.set_editor_property("override_auto_exposure_max_brightness", True)
        s.set_editor_property("auto_exposure_max_brightness", 2.0)
        ppv.set_editor_property("settings", s)

    placed = [a.get_actor_label() for a in actor_sub.get_all_level_actors() if a.get_actor_label().startswith(PREFIX)]
    report["placed"] = placed
    step("placed_all", len(placed) == 5, "{}/5".format(len(placed)))
    return step("save_map", unreal.EditorLoadingAndSavingUtils.save_current_level(), MAP)


try:
    ok = main()
    report["ok"] = bool(ok) and all(s["ok"] for s in report["steps"])
except Exception:
    report["errors"].append(traceback.format_exc())
os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=2)
unreal.log("[DryRiverLighting] result ok={} -> {}".format(report["ok"], REPORT))
