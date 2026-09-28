"""Probe: which level-creation and gameplay-actor APIs exist in UE 5.8 Python.

Writes to a JSON file rather than printing: in this commandlet neither
print() nor unreal.log() reaches the log file, so a probe that reports on
stdout reports nothing at all. The import pass discovered this the hard way -
its first run returned None from two level-creation calls with no warning
recorded, because the warnings went to the same place.
"""
import json
import os

import unreal

out = {"level_apis": {}, "classes": {}, "docs": {}}

for holder in ("EditorLevelUtils", "EditorLevelLibrary", "LevelEditorSubsystem",
               "EditorActorSubsystem", "EditorLoadingAndSavingUtils",
               "EditorStaticMeshLibrary"):
    obj = getattr(unreal, holder, None)
    if obj is None:
        out["level_apis"][holder] = "ABSENT"
        continue
    names = sorted(n for n in dir(obj)
                   if any(k in n.lower() for k in
                          ("new_level", "new_map", "create_level", "new_empty",
                           "load_map", "save_current", "level", "world")))
    out["level_apis"][holder] = names

for cls in ("SSObjectiveActor", "PlayerStart", "NavMeshBoundsVolume", "Brush",
            "BrushType", "StaticMeshActor", "MaterialFactoryNew",
            "MaterialEditingLibrary", "MaterialProperty", "LinearColor",
            "CollisionTraceFlag", "EditorAssetLibrary", "AssetToolsHelpers"):
    out["classes"][cls] = hasattr(unreal, cls)

if hasattr(unreal, "BrushType"):
    out["BrushType"] = [n for n in dir(unreal.BrushType) if not n.startswith("_")]

for holder, fn in (("EditorLevelUtils", "new_level"),
                   ("EditorLevelUtils", "new_empty_level"),
                   ("LevelEditorSubsystem", "new_level"),
                   ("LevelEditorSubsystem", "new_map")):
    h = getattr(unreal, holder, None)
    f = getattr(h, fn, None) if h else None
    out["docs"]["{}.{}".format(holder, fn)] = (f.__doc__ or "")[:300] if f else "ABSENT"

path = os.path.join(unreal.Paths.convert_relative_path_to_full(
    unreal.Paths.project_dir()), "Build", "probe_ravenshoe_map.json")
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, default=str)
