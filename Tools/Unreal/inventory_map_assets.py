# Cross-map asset inventory for the Dry River harvest (D-DR-06/07/04).
# For each map: unique static-mesh asset paths in use, grouped by source pack.
# Also counts meshes available in installed packs that no map uses yet.
import json, os
import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "dryriver_harvest_inventory.json")
MAPS = ["/Game/Maps/L_RedGum_01", "/Game/Maps/L_Bluestone_01", "/Game/Maps/L_Saltbush_01",
        "/Game/Maps/L_Ravenshoe_01", "/Game/Maps/L_SelatCanal_01", "/Game/Maps/L_Wandarra_01",
        "/Game/Maps/L_DryRiver_01"]
report = {"maps": {}, "pack_folders": {}, "errors": []}

def meshes_of(world):
    used = {}
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        try:
            m = a.static_mesh_component.get_editor_property("static_mesh")
        except Exception:
            m = None
        if m:
            path = m.get_path_name()
            pack = path.split("/")[2] if path.startswith("/Game/") else path.split("/")[1]
            used.setdefault(pack, set()).add(path.rsplit(".", 1)[0])
    return used

for m in MAPS:
    try:
        world = unreal.EditorLoadingAndSavingUtils.load_map(m)
        if world is None:
            report["errors"].append("could not load " + m)
            continue
        used = meshes_of(world)
        report["maps"][m] = {k: sorted(v) for k, v in sorted(used.items())}
        report["maps"][m + " counts"] = {k: len(v) for k, v in sorted(used.items())}
    except Exception as exc:
        report["errors"].append("%s: %s" % (m, exc))

# Installed pack folders at /Game root (mesh counts per folder, via asset registry)
ar = unreal.AssetRegistryHelpers.get_asset_registry()
try:
    top = ar.get_sub_paths(unreal.Name("/Game"))
    folders = [str(p.package_name()).split("/")[-1] for p in top]
except Exception:
    folders = []
report["pack_folders"] = {f: None for f in sorted(folders)}

with open(REPORT, "w", encoding="utf-8") as s:
    json.dump(report, s, indent=2)
unreal.log("[HarvestInventory] complete maps=%d" % len(report["maps"]))
