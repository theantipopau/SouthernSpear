# Southern Spear - Ravenshoe Crossing ground cover from the Namaqualand pack.
#
# The map's dressing is 424 cover actors from Scene_QuarrySlate and
# RuralAustralia - rock, trees, logs, fence - and 38 hand-placed props. What
# none of it provides is LOW GROUND COVER: scrub, litter and small succulents
# between the boulders. That absence is why the ridges read as bare heightfield.
#
# The pack is /Game/Namaqualand, a Karoo/Namaqualand dryland biome set. It is
# the only arid-country vegetation in the project. The alternatives were checked
# and rejected on look, not on licence:
#   Light_Foliage (Forest_A/B)                - temperate forest, wrong biome
#   Nanite_Plants_Sample_Collection           - Acer, Ophiopogon, Abelia;
#     ornamental Japanese and Chinese garden plants, wrong biome AND wrong
#     culture (ADR-016)
# Karoo succulent veld is genuinely close to Australian arid shrubland in
# habit - low, dense, drought-decorated - which is what the map needs.
#
# These arrive as ready StaticMeshAssets (72 low-poly, plus Nanite variants),
# so unlike the Fab props there is nothing to import, rescale, strip or
# decimate. They are referenced in place and never modified (ADR-029,
# L-0016b), and they KEEP THEIR OWN vendor materials rather than being put on
# an MI_SS_Raven_* override: unlike the props, which had to be unified onto one
# shader to sit together, ground cover is seen at arm's length in mixed
# clusters, and the pack's own material is what makes a dozen different plants
# read as a dozen different plants.
#
# Collision is OFF, per ADR-022. Low scrub that blocks an agent is a tripwire,
# and a few hundred small colliders fragment the navmesh for no gameplay gain.
#
# Idempotent: only its own SS_Raven_Ground_* actors are purged and replaced.
# Writes Build/ravenshoe_groundcover.json.

import json
import math
import os
import random
import sys
import traceback

import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "Common")))
import ravenshoe_spec as SPEC  # noqa: E402

PROJECT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
MAP = "/Game/Maps/L_Ravenshoe_01"
REPORT = os.path.join(PROJECT, "Build", "ravenshoe_groundcover.json")
PREFIX = "SS_Raven_Ground_"
PACK = "/Game/Namaqualand/Meshes/Foliage/LP/"

# A spread of forms rather than one plant repeated: rosette succulents,
# upright iceplants, and a couple of the debris pieces for ground litter.
MESHES = [
    "SM_cheiridopsis_succulent_a_LP", "SM_cheiridopsis_succulent_c_LP",
    "SM_cheiridopsis_succulent_f_LP", "SM_cheiridopsis_succulent_i_LP",
    "SM_crystalline_iceplant_a_LP", "SM_crystalline_iceplant_c_LP",
    "SM_crystalline_iceplant_f_LP",
]

# Where scrub belongs. The creek bed is the second lane and is deliberately the
# most open, so it gets the lightest touch; the ridges and the road shoulder
# carry the bulk. z always comes from the spec's own ground_z, never from a
# traced hit, because -nullrhi ray casts cannot see StaticMeshActors.
#   (x, y, count, jitter_m, scale_lo, scale_hi)
CLUSTERS = [
    # Creek bed - sparse, so the bed stays traversable and readable.
    (-18, -8, 14, 5.0, 0.8, 1.4),
    (16, 6, 14, 5.0, 0.8, 1.4),
    (0, 20, 10, 4.0, 0.8, 1.3),
    # Road shoulders on both approaches, where scrub actually grows.
    (-9, -60, 18, 4.0, 0.7, 1.2),
    (10, -74, 16, 4.0, 0.7, 1.2),
    (8, 60, 16, 4.0, 0.7, 1.2),
    (-11, 76, 18, 4.0, 0.7, 1.2),
    # Ridge tops, the highest and driest ground.
    (44, 104, 22, 9.0, 0.9, 1.6),
    (-52, 118, 22, 9.0, 0.9, 1.6),
    (68, -108, 20, 9.0, 0.9, 1.6),
    (-60, -96, 18, 9.0, 0.9, 1.6),
]

report = {"ok": False, "placed": 0, "meshes": {}, "clusters": [],
          "errors": [], "warnings": []}


def main():
    rng = random.Random(20260928)
    if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
        report["errors"].append("could not open " + MAP)
        return
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.EditorLevelLibrary.get_editor_world()

    # Load the pack meshes. Missing ones are skipped, not fatal: a partial
    # ground cover is still better than an aborted pass.
    meshes = []
    for name in MESHES:
        asset = unreal.load_asset(PACK + name)
        if isinstance(asset, unreal.StaticMesh):
            meshes.append((name, asset))
        else:
            report["warnings"].append("no mesh " + name)
    report["meshes"] = {n: m.get_path_name() for n, m in meshes}
    if not meshes:
        report["errors"].append("no Namaqualand meshes resolved")
        return

    removed = 0
    for a in sub.get_all_level_actors():
        if a.get_actor_label().startswith(PREFIX):
            sub.destroy_actor(a)
            removed += 1
    report["removed_existing"] = removed

    placed = 0
    for cx, cy, count, jitter, lo, hi in CLUSTERS:
        before = placed
        for i in range(count):
            x = cx + rng.uniform(-jitter, jitter)
            y = cy + rng.uniform(-jitter, jitter)
            z = SPEC.ground_z(x, y)
            _name, mesh = meshes[rng.randrange(len(meshes))]
            scale = rng.uniform(lo, hi)
            actor = sub.spawn_actor_from_class(
                unreal.StaticMeshActor,
                unreal.Vector(x * 100.0, -y * 100.0, z * 100.0),
                unreal.Rotator(roll=rng.uniform(-4, 4), pitch=0.0,
                               yaw=rng.uniform(0, 360)))
            if actor is None:
                continue
            actor.set_actor_label("{}{:03d}".format(PREFIX, placed))
            comp = actor.get_component_by_class(unreal.StaticMeshComponent)
            if comp is None:
                sub.destroy_actor(actor)
                continue
            comp.set_static_mesh(mesh)
            actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
            # Collision off: ADR-022. Small scrub that blocks an agent is a
            # tripwire and fragments the navmesh for nothing.
            #
            # The enum spelling differs between builds - 5.8 has no
            # CollisionEnabled.NoCollision - so the name is resolved rather than
            # hardcoded, and the actor-level toggle is set regardless because
            # that one is stable.
            for candidate in ("NO_COLLISION", "NoCollision", "NONE"):
                mode = getattr(unreal.CollisionEnabled, candidate, None)
                if mode is not None:
                    comp.set_collision_enabled(mode)
                    break
            else:
                report["warnings"].append(
                    "no CollisionEnabled no-collision value on this build; "
                    "used the actor toggle only")
            actor.set_actor_enable_collision(False)
            placed += 1
        report["clusters"].append({
            "centre_xy": [cx, cy], "requested": count,
            "placed": placed - before, "jitter_m": jitter,
        })

    report["placed"] = placed
    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP)

    # Verify from the saved level rather than trusting the spawn count.
    found = [a for a in sub.get_all_level_actors()
             if a.get_actor_label().startswith(PREFIX)]
    report["verified_in_level"] = len(found)
    report["ok"] = not report["errors"] and len(found) == placed


try:
    main()
except Exception:  # noqa: BLE001
    report["errors"].append(traceback.format_exc())
finally:
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, default=str)
