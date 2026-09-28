import json
import os
import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
MAP = "/Game/Maps/L_RedGum_01"
REPORT = os.path.join(PROJECT_DIR, "Build", "redgum_scene_inventory.json")

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError("Could not load " + MAP)

actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
result = {"map": MAP, "actor_count": len(actors), "actors": [], "assets": []}

for actor in actors:
    cls = actor.get_class().get_name()
    loc = actor.get_actor_location()
    row = {"label": actor.get_actor_label(), "name": actor.get_name(), "class": cls,
           "location_cm": [round(loc.x), round(loc.y), round(loc.z)]}
    if isinstance(actor, (unreal.StaticMeshActor, unreal.LandscapeProxy,
                          unreal.NavMeshBoundsVolume, unreal.PlayerStart,
                          unreal.SSObjectiveActor)):
        try:
            origin, extent = actor.get_actor_bounds(False)
            row["bounds_cm"] = [[round(origin.x - extent.x), round(origin.y - extent.y), round(origin.z - extent.z)],
                                 [round(origin.x + extent.x), round(origin.y + extent.y), round(origin.z + extent.z)]]
        except Exception:
            pass
    if isinstance(actor, unreal.StaticMeshActor):
        mesh = actor.static_mesh_component.static_mesh
        row["mesh"] = mesh.get_path_name() if mesh else None
    if isinstance(actor, unreal.NavMeshBoundsVolume):
        scale = actor.get_actor_scale3d()
        row["scale"] = [round(scale.x, 2), round(scale.y, 2), round(scale.z, 2)]
    result["actors"].append(row)

registry = unreal.AssetRegistryHelpers.get_asset_registry()
for data in registry.get_assets_by_path("/Game/RuralAustralia", recursive=True):
    path = str(data.package_name)
    name = str(data.asset_name)
    cls = str(data.asset_class_path.asset_name)
    low = (path + "/" + name).lower()
    if cls in ("StaticMesh", "Blueprint", "World", "FoliageType_InstancedStaticMesh") or any(
            key in low for key in ("house", "farm", "homestead", "shed", "barn", "building", "station")):
        result["assets"].append({"path": path, "name": name, "class": cls})

os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w", encoding="utf-8") as stream:
    json.dump(result, stream, indent=2)
unreal.log("[RedGumInventory] wrote {} actors={} assets={}".format(
    REPORT, len(result["actors"]), len(result["assets"])))
