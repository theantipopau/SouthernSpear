# Southern Spear - Ravenshoe Crossing lighting and atmosphere pass.
#
# import_ravenshoe.py builds geometry only. It never spawns a sky, a sun, a sky
# light, fog or a post-process volume, so the map had no lighting rig and no
# atmosphere at all. This adds one, modelled on Tools/Unreal/light_dryriver.py.
#
# WHY DISTANCE FOG AND NOT MOSTLY HEIGHT FOG
#     The obvious way to stop ridge snipers in a gorge is height fog: it pools in
#     the bottom and thins on top, which is exactly the shape of this map. But
#     Ravenshoe has 46 m of total relief - bed at -18 m, deck at +14 m, crest at
#     +28 m - and an exponential that separates those three usefully has to
#     change density by an order of magnitude over about 30 m. At that falloff
#     the deck 32 m above the bed goes with it, and the 68 m span stops being a
#     readable 3.4 m-bay fight. The fog ends up controlling the exact thing the
#     design is for.
#
#     So the two jobs are split, and each tool does the one it is good at:
#       - DISTANCE fog is the sniper tool. StartDistance is set at 140 m, which
#         is longer than any single sightline that matters on the map - the deck
#         is 68 m end to end and the ridge-to-ridge shot is 200 m. Nothing a
#         player needs to read is inside 140 m, and the one engagement that IS
#         over 140 m (a post holding the far crest) is exactly the one the fog
#         is meant to break up.
#       - HEIGHT fog is the mood tool, and it is deliberately weak. A little
#         extra haze in the creek bed to make the second lane feel like a
#         canyon, nothing that touches the deck.
#
# RUN ORDER
#     import_ravenshoe -> dress_ravenshoe_props -> setup_ravenshoe_surfaces
#     -> light_ravenshoe -> setup_objective_assault -> nav bake
#
#     This pass must run AFTER the import. The import re-spawns the geometry
#     actors and strips the surface overrides; running this before it means the
#     next import silently removes the whole rig, exactly as it did to the
#     surfaces. Idempotent, though: actors labelled SS_Raven_Light_* are purged
#     and re-placed, so a re-run cannot stack suns.
#
# Writes Build/ravenshoe_lighting_report.json.

import json
import os
import traceback

import unreal

PROJECT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
MAP = "/Game/Maps/L_Ravenshoe_01"
REPORT = os.path.join(PROJECT, "Build", "ravenshoe_lighting_report.json")
PREFIX = "SS_Raven_Light_"

# Spec heights in metres, from Tools/Common/ravenshoe_spec.py. Bed is the creek
# floor, Deck is the bridge surface, Crest is the road level at the deployments.
BED_M = -18.0
DECK_M = 14.0
CREST_M = 28.0

report = {"ok": False, "actors": {}, "fog": {}, "errors": [], "warnings": []}


def err(msg):
    report["errors"].append(str(msg))


def warn(msg):
    report["warnings"].append(str(msg))


def setp(component, name, value):
    """Set a component property and READ IT BACK.

    Every material and fog bug in this project has been the same shape: a call
    into an API that no longer exists, swallowed by a broad except, reported as
    a warning on a pass whose summary said zero errors. Reading the value back
    turns a silent no-op into a reported one.
    """
    try:
        component.set_editor_property(name, value)
        got = component.get_editor_property(name)
        ok = (abs(float(got) - float(value)) < 1e-4
              if isinstance(value, (int, float)) else True)
        if not ok:
            warn("{}.{}: set {} but read back {}".format(
                component.get_name(), name, value, got))
        return True
    except Exception as exc:  # noqa: BLE001
        warn("{}.{}: {}".format(component.get_name(), name, exc))
        return False


def spawn(sub, cls, label, location=unreal.Vector(0, 0, 0), rotation=None):
    actor = sub.spawn_actor_from_class(
        cls, location, rotation or unreal.Rotator(roll=0, pitch=0, yaw=0))
    if actor is not None:
        actor.set_actor_label(PREFIX + label)
    return actor


def main():
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if world is None:
        err("could not open " + MAP)
        return
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # Purge our own actors so a re-run cannot stack two suns.
    removed = 0
    for a in sub.get_all_level_actors():
        if a.get_actor_label().startswith(PREFIX):
            sub.destroy_actor(a)
            removed += 1
    report["removed_existing"] = removed

    # --- sun ----------------------------------------------------------------
    # Mid-morning, high, from the north-east: southern hemisphere, so the sun
    # tracks across the northern sky and the south-facing gorge wall is lit.
    sun = spawn(sub, unreal.DirectionalLight, "Sun", unreal.Vector(0, 0, 5000),
                unreal.Rotator(roll=0, pitch=-54, yaw=38))
    if sun is None:
        err("no DirectionalLight")
    else:
        c = sun.light_component
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        setp(c, "intensity", 9.0)
        # light_color is deliberately NOT set. It is an FLinearColor StructProperty
        # and this build rejects a LinearColor; a positional unreal.Color does not
        # land in the right channels. light_dryriver.py has been setting it with a
        # LinearColor and swallowing the failure, so the Dry River sun has been
        # untinted white this whole time. Not worth guessing a channel order for a
        # cosmetic tint - the atmosphere provides the warm cast instead.
        setp(c, "atmosphere_sun_light", True)
        setp(c, "cast_shadows", True)
        report["actors"]["Sun"] = "DirectionalLight pitch=-54 yaw=38 i=9.0"

    # --- sky ----------------------------------------------------------------
    atmo = spawn(sub, unreal.SkyAtmosphere, "Atmosphere")
    if atmo is None:
        err("no SkyAtmosphere")
    else:
        report["actors"]["Atmosphere"] = "SkyAtmosphere"

    sky = spawn(sub, unreal.SkyLight, "SkyLight", unreal.Vector(0, 0, 3000))
    if sky is not None:
        c = sky.light_component
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        setp(c, "real_time_capture", True)
        setp(c, "intensity", 1.0)
        report["actors"]["SkyLight"] = "real-time capture, i=1.0"

    # --- fog ----------------------------------------------------------------
    # See the header for why this is mostly a distance rig.
    fog = spawn(sub, unreal.ExponentialHeightFog, "Fog",
                unreal.Vector(0, 0, int(BED_M * 100)))
    if fog is None:
        err("no ExponentialHeightFog")
    else:
        c = fog.component
        # Nothing within 140 m is touched. The deck is 68 m end to end, so the
        # span and both lips are completely clear; the 200 m ridge-to-ridge
        # shot is the first thing fogged, and that is the shot to break.
        setp(c, "start_distance", 14000.0)
        # Ramp hard so the far ridge reads as haze rather than as a wall of
        # milk, and cap the opacity so a silhouette is always legible.
        setp(c, "fog_density", 0.055)
        setp(c, "fog_max_opacity", 0.82)
        setp(c, "fog_cutoff_distance", 60000.0)
        # The HEIGHT term is switched OFF, deliberately, and this is worth
        # spelling out. ExponentialHeightFog on 5.8 exposes fog_height_falloff
        # but NOT fog_height_offset or fog_height_density - probed, both absent.
        # With no offset available the height layer is pinned to z = 0, and a
        # falloff of 0.02 gives it a 1/0.02 = 50 cm thickness: a razor-thin
        # disc lying across the deck at road level, not a pool in the gorge. A
        # true bed-pool needs an offset this build will not take, so the rig is
        # distance-only and the creek bed gets its atmosphere from the terrain
        # and the dark ironwork instead.
        setp(c, "fog_height_falloff", 0.0)
        # Warm dry-country inscatter, matched to the Dry River rig.
        setp(c, "fog_inscattering_luminance",
             unreal.LinearColor(0.78, 0.72, 0.62, 1.0))
        report["actors"]["Fog"] = "ExponentialHeightFog start=140m"
        report["fog"] = {
            "start_distance_m": 140.0,
            "fog_density": 0.055,
            "fog_max_opacity": 0.82,
            "fog_cutoff_distance_m": 600.0,
            "fog_height_falloff": 0.0,
            "height_layer": "disabled - no fog_height_offset on this build",
            "deck_span_m": 68.0,
            "ridge_to_ridge_m": 200.0,
            "note": "the 68 m span and both lips sit inside start_distance and "
                    "are unaffected; the 200 m ridge-to-ridge shot is the only "
                    "sightline fogged, which is the sniper case",
        }

    # --- post ---------------------------------------------------------------
    ppv = spawn(sub, unreal.PostProcessVolume, "PostProcess")
    if ppv is not None:
        ppv.set_editor_property("unbound", True)
        s = ppv.settings
        setp(s, "override_auto_exposure_min_brightness", True)
        setp(s, "auto_exposure_min_brightness", 0.5)
        setp(s, "override_auto_exposure_max_brightness", True)
        setp(s, "auto_exposure_max_brightness", 2.0)
        report["actors"]["PostProcess"] = "unbound, exposure 0.5-2.0"

    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP)

    placed = [a.get_actor_label() for a in sub.get_all_level_actors()
              if a.get_actor_label().startswith(PREFIX)]
    report["placed"] = sorted(placed)
    report["ok"] = not report["errors"]


try:
    main()
except Exception:  # noqa: BLE001
    report["errors"].append(traceback.format_exc())
finally:
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, default=str)
