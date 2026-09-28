# Southern Spear - Ravenshoe Crossing deployments as Lyra player starts.
#
#   UnrealEditor-Cmd ... -ExecutePythonScript=E:/SouthernSpear/Tools/Unreal/fix_ravenshoe_starts.py
#
# import_ravenshoe.py placed plain PlayerStarts. Lyra's spawning manager only uses ALyraPlayerStart, so with none
# every pawn spawned at the world origin - in the gorge under the deck (first play test: 270 failed bot spawns).
# Replaces each deployment start with a LyraPlayerStart facing the bridge, plus a line of extras either side so
# a team does not stack on one point. Idempotent. Report: Build/ravenshoe_starts.json.

import json
import math
import os
import sys

import unreal

ROOT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
sys.path.insert(0, os.path.join(ROOT, "Tools", "Common"))
import ravenshoe_spec as spec  # noqa: E402

MAP = "/Game/Maps/L_Ravenshoe_01"
EXTRAS = 7
SPACING_CM = 150.0
report = {"ok": False, "starts": [], "errors": []}

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lyra_start = unreal.load_class(None, "/Script/LyraGame.LyraPlayerStart")

deploys = {}
for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart):
    label = a.get_actor_label()
    if label.startswith("SS_MAP_Ravenshoe_Deploy"):
        base = label.split("_Extra")[0]
        if "_Extra" not in label:
            deploys[base] = a.get_actor_location()
        actor_sub.destroy_actor(a)

for label, loc in sorted(deploys.items()):
    yaw = math.degrees(math.atan2(-loc.y, -loc.x)) if abs(loc.x) + abs(loc.y) > 1 else 0.0
    offsets = [0.0] + [(i // 2 + 1) * SPACING_CM * (1 if i % 2 == 0 else -1) for i in range(EXTRAS)]
    for n, dx in enumerate(offsets):
        x, y = loc.x + dx, loc.y
        z = spec.ground_z(x / 100.0, -y / 100.0) * 100.0 + 100.0
        actor = actor_sub.spawn_actor_from_class(lyra_start, unreal.Vector(x, y, z), unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
        if not actor:
            report["errors"].append("spawn failed " + label)
            continue
        actor.set_actor_label(label if n == 0 else "{}_Extra{:02d}".format(label, n))
        report["starts"].append([actor.get_actor_label(), round(x), round(y), round(z), round(yaw)])

report["ok"] = len(deploys) == 2 and not report["errors"]
if report["ok"]:
    unreal.EditorLoadingAndSavingUtils.save_current_level()
with open(os.path.join(ROOT, "Build", "ravenshoe_starts.json"), "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[FixRavenshoeStarts] ok={} starts={}".format(report["ok"], len(report["starts"])))
