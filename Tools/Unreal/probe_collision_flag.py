# Copyright Southern Spear. All Rights Reserved.
#
# One-off diagnostic, probe v2: determine per-element KAggregateGeom counts on
# the Dry River dressing assets.
#
# Probe v1 established that str(agg_geom) is an opaque pointer whether or not
# the struct is populated, so the existing report can never distinguish "the
# asset has no collision" from "the asset is fine". KAggregateGeom is a struct
# of element arrays, so counting them is the only way to tell.
#
# Also confirms that CTF_USE_DEFAULT is writable and reads back, which is the
# replacement for the nonexistent CTF_USE_SIMPLE_AS_SIMPLE.
#
# RESULT (5.8.3, 2026-09-26) - kept here because it bounds the R-10 investigation:
#   * enum members are only CTF_USE_DEFAULT, CTF_USE_COMPLEX_AS_SIMPLE,
#     CTF_USE_SIMPLE_AND_COMPLEX, CTF_USE_SIMPLE_AS_COMPLEX
#   * there is no capsule_elems or geom_elems on KAggregateGeom
#   * all six dressing meshes are ALREADY at CTF_USE_DEFAULT
#   * all six carry exactly one convex_elems entry, so they DO have simple
#     collision on disk, read back in a fresh editor with no import in play
# Therefore neither a missing nor a mis-set collision trace flag nor absent
# collision data explains R-10, and the cause is not in the mesh assets.
#
#   UnrealEditor-Cmd.exe SouthernSpear.uproject -nullrhi -unattended -nosplash \
#       -nosound -ExecutePythonScript=Tools/Unreal/probe_collision_flag.py

import json
import os

import unreal

PROJECT_DIR = unreal.Paths.project_dir()
MESH_DEST = "/Game/Art/Dressing"

ELEM_PROPS = (
    "box_elems",
    "sphere_elems",
    "convex_elems",
    "tapered_capsule_elems",
    "level_set_elems",
)

report = {"enum": [], "set_probe": {}, "assets": []}

try:
    report["enum"] = sorted(
        m for m in dir(unreal.CollisionTraceFlag) if not m.startswith("_")
    )
except Exception as exc:  # noqa: BLE001
    report["enum_error"] = str(exc)

# Does writing the intended value actually stick?
try:
    flag = unreal.CollisionTraceFlag.CTF_USE_DEFAULT
    report["set_probe"]["requested"] = str(flag)
except Exception as exc:  # noqa: BLE001
    report["set_probe"]["error"] = str(exc)


def agg_geom_counts(agg):
    """Count populated element arrays, so an empty struct is distinguishable."""
    counts = {}
    for prop in ELEM_PROPS:
        try:
            counts[prop] = len(agg.get_editor_property(prop))
        except Exception as exc:  # noqa: BLE001
            counts[prop] = "n/a: {}".format(exc)
    return counts


try:
    for name in sorted(unreal.EditorAssetLibrary.list_assets(MESH_DEST, recursive=True)):
        asset = unreal.EditorAssetLibrary.load_asset(name)
        if not isinstance(asset, unreal.StaticMesh):
            continue
        entry = {"asset": name, "elems": {}}
        try:
            body = asset.get_editor_property("body_setup")
            agg = body.get_editor_property("agg_geom")
            entry["trace_flag_before"] = str(body.get_editor_property("collision_trace_flag"))
            entry["elems"] = agg_geom_counts(agg)
            # Apply the correct flag and read it back.
            try:
                body.set_editor_property(
                    "collision_trace_flag",
                    unreal.CollisionTraceFlag.CTF_USE_DEFAULT,
                )
                entry["trace_flag_after"] = str(
                    body.get_editor_property("collision_trace_flag")
                )
            except Exception as exc:  # noqa: BLE001
                entry["set_error"] = str(exc)
        except Exception as exc:  # noqa: BLE001
            entry["body_error"] = str(exc)
        report["assets"].append(entry)
except Exception as exc:  # noqa: BLE001
    report["assets_error"] = str(exc)

path = os.path.join(PROJECT_DIR, "Build", "collision_flag_probe.json")
with open(path, "w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=2, sort_keys=True)
unreal.log("[Probe] wrote {}".format(path))
