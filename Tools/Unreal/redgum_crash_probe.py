"""Isolate the audit crash: does BUILDPATHS kill the commandlet on Red Gum?

Phase 1 loads the map, counts actors and takes a few traces. Phase 2 calls the
same BUILDPATHS console command audit_map_playability.py calls. Set
SS_BUILDPATHS=1 to run phase 2; without it, phase 2 is skipped.

Read only. Writes Build/redgum_crash_probe.json.
"""
import json
import os

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
OUT = os.path.join(PROJECT_DIR, "Build", "redgum_crash_probe.json")
MAP = "/Game/Maps/L_RedGum_01"
RUN_BUILDPATHS = os.environ.get("SS_BUILDPATHS") == "1"

result = {"map": MAP, "phase": [], "buildpaths": RUN_BUILDPATHS}

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
result["phase"].append("loaded {}".format(world is not None))
if not world:
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    raise SystemExit(0)

actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
result["actor_count"] = len(actors)
result["phase"].append("actors {}".format(len(actors)))

hits = 0
for x in (-34000, 0, 34000):
    for y in (-28000, 0, 28000):
        res = unreal.SystemLibrary.line_trace_single(
            world, unreal.Vector(x, y, 50000.0), unreal.Vector(x, y, -50000.0),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [],
            unreal.DrawDebugTrace.NONE, True)
        hits += 1 if res else 0
result["traces_hit"] = hits
result["phase"].append("9 ground traces, {} hit".format(hits))

if RUN_BUILDPATHS:
    result["phase"].append("calling BUILDPATHS")
    unreal.SystemLibrary.execute_console_command(world, "BUILDPATHS")
    result["phase"].append("BUILDPATHS returned")

result["ok"] = True
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(result, fh, indent=2)
unreal.log("[RedGumCrashProbe] {}".format(result["phase"]))
