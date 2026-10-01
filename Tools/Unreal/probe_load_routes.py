# Southern Spear - which load route reaches the Game Feature content in a commandlet.
#
# SSExp_ObjectiveAssault is a Game Feature plugin: in a -run=pythonscript commandlet its content is
# not always resolvable, and the failure is a quiet None. setup_soldiers.py hard-fails if its meshes
# do not load, so this probe measures the routes first (and what the registry thinks exists).
#
# Report: Build/load_route_probe.json.

import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "load_route_probe.json")
PACKAGES = [
    "/SSExp_ObjectiveAssault/Characters/B_SS_Soldier",
    "/SSExp_ObjectiveAssault/Characters/ADF/SK_ADF_Uniform_G3",
    "/SSExp_ObjectiveAssault/Characters/ADF/MI_ADF_crye_g3_shirt_amc",
    "/SSExp_ObjectiveAssault/Characters/QuantumProto/SKM_Head",
    "/SSExp_ObjectiveAssault/Characters/QuantumProto/SKM_Jeans",
]
report = {"ok": False, "routes": {}, "registry": {}, "errors": []}

try:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.scan_paths_synchronous(["/SSExp_ObjectiveAssault"], force_rescan=True)
    for root in ("/SSExp_ObjectiveAssault/Characters", "/SSExp_ObjectiveAssault/Characters/ADF",
                 "/SSExp_ObjectiveAssault/Characters/QuantumProto"):
        assets = registry.get_assets_by_path(root, recursive=False, include_only_on_disk_assets=True)
        report["registry"][root] = sorted(a.asset_name.to_string() if hasattr(a.asset_name, "to_string")
                                          else str(a.asset_name) for a in assets)[:60]

    for package in PACKAGES:
        short = package.rsplit("/", 1)[-1]
        entry = {}
        for label, fn in (
            ("load_asset_package", lambda p=package: unreal.load_asset(p)),
            ("load_asset_object", lambda p=package: unreal.load_asset(p + "." + p.rsplit("/", 1)[-1])),
            ("editor_load_asset", lambda p=package: unreal.EditorAssetLibrary.load_asset(p)),
            ("registry_data", lambda p=package: registry.get_asset_by_object_path(p + "." + p.rsplit("/", 1)[-1])
             .get_asset() if registry.get_asset_by_object_path(p + "." + p.rsplit("/", 1)[-1]).is_valid() else None),
        ):
            try:
                asset = fn()
                entry[label] = asset.get_path_name() if asset else None
            except Exception as exc:
                entry[label] = "raise: {}".format(exc)
        entry["does_asset_exist"] = unreal.EditorAssetLibrary.does_asset_exist(package)
        report["routes"][package] = entry
    report["ok"] = True
except Exception:
    report["errors"].append(traceback.format_exc())

with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[LoadRoutes] ok={}".format(report["ok"]))
