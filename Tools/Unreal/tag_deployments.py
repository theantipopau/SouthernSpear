# Southern Spear - tag each map's deployment starts by team (USSDeploymentSpawningComponent).
#
# Splits a map's player starts into two clusters (2-means on position); the
# cluster nearer objective A deploys Team One ("TeamOne"), the other Team Two.
# Sets APlayerStart::PlayerStartTag and saves. Idempotent.
# Writes Build/deployment_tags.json.

import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "deployment_tags.json")
MAPS = ["/Game/Maps/L_RedGum_01", "/Game/Maps/L_DryRiver_01", "/Game/Maps/L_Saltbush_01", "/Game/Maps/L_SelatCanal_01"]
report = {"ok": False, "maps": {}, "errors": []}


def two_means(points):
    a, b = min(points, key=lambda p: p.x + p.y), max(points, key=lambda p: p.x + p.y)
    for _ in range(12):
        ga = [p for p in points if (p - a).length() <= (p - b).length()]
        gb = [p for p in points if (p - a).length() > (p - b).length()]
        if not ga or not gb:
            break
        a = sum(ga, unreal.Vector()) / len(ga)
        b = sum(gb, unreal.Vector()) / len(gb)
    return a, b


def tag_map(path):
    world = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if not world:
        return {"error": "load failed"}
    starts = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart)
    objs = sorted(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SSObjectiveActor),
                  key=lambda o: o.get_editor_property("sequence_index"))
    if len(starts) < 2 or not objs:
        return {"error": "starts={} objectives={}".format(len(starts), len(objs))}
    ca, cb = two_means([s.get_actor_location() for s in starts])
    first = objs[0].get_actor_location()
    one, two = (ca, cb) if (ca - first).length() <= (cb - first).length() else (cb, ca)
    counts = {"TeamOne": 0, "TeamTwo": 0}
    for s in starts:
        loc = s.get_actor_location()
        tag = "TeamOne" if (loc - one).length() <= (loc - two).length() else "TeamTwo"
        s.set_editor_property("player_start_tag", tag)
        counts[tag] += 1
    saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
    return {"counts": counts, "separation_m": round((one - two).length() / 100), "saved": saved}


try:
    for m in MAPS:
        report["maps"][m] = tag_map(m)
    report["ok"] = all(r.get("saved") and min(r["counts"].values()) >= 2 for r in report["maps"].values())
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[DeploymentTags] ok={}".format(report["ok"]))
