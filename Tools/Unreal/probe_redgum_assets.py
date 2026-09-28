"""Read-only inventory for Red Gum's Rural Australia foliage and selected assets.

Run with UE 5.8 UnrealEditor-Cmd and -ExecutePythonScript. It does not save the
level or modify assets; it reports counts and bounds to Build/redgum_asset_probe.json.
"""
import json
import os
import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
MAP = "/Game/Maps/L_RedGum_01"
OUT = os.path.join(PROJECT_DIR, "Build", "redgum_asset_probe.json")
ASSETS = [
    "/Game/RuralAustralia/StaticMeshes/Vegetation/Tree_L_01/SM_Tree_L_01",
    "/Game/RuralAustralia/StaticMeshes/Vegetation/Tree_M_01/SM_Tree_M_01",
    "/Game/RuralAustralia/StaticMeshes/Vegetation/Tree_M_02/SM_Tree_M_02",
    "/Game/RuralAustralia/StaticMeshes/Vegetation/Tree_S_01/SM_Tree_S_01",
    "/Game/RuralAustralia/StaticMeshes/Vegetation/GrassTree_01/SM_GrassTree_01",
    "/Game/RuralAustralia/StaticMeshes/Vegetation/Log_L_01/SM_Log_L_01",
    "/Game/RuralAustralia/StaticMeshes/Vegetation/Log_M_01/SM_Log_M_01",
    "/Game/RuralAustralia/StaticMeshes/Vegetation/Log_S_01/SM_Log_S_01",
    "/Game/RuralAustralia/StaticMeshes/Rocks/Rock_M_01/SM_Rock_M_01",
    "/Game/RuralAustralia/StaticMeshes/Rocks/Rock_M_02/SM_Rock_M_02",
    "/Game/RuralAustralia/StaticMeshes/Rocks/Ridge_Dirt_01/SM_Ridge_Dirt_01_A",
    "/Game/RuralAustralia/StaticMeshes/Rocks/Ridge_Dirt_01/SM_Ridge_Dirt_01_B",
    "/Game/RuralAustralia/StaticMeshes/Props/Fence_01/SM_Fence_02",
    "/Game/RuralAustralia/StaticMeshes/Props/Fence_01/SM_Fence_Wires_01",
]

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError("Could not load " + MAP)

result = {"map": MAP, "actor_count": 0, "actors": [], "assets": []}
all_actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
result["actor_count"] = len(all_actors)
for actor in all_actors:
    cls = actor.get_class().get_name()
    if cls in ("InstancedFoliageActor", "ProceduralFoliageVolume", "NavMeshBoundsVolume", "Landscape"):
        row = {"label": actor.get_actor_label(), "class": cls,
               "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y,
                               actor.get_actor_location().z]}
        if isinstance(actor, (unreal.NavMeshBoundsVolume, unreal.ProceduralFoliageVolume)):
            try:
                origin, extent = actor.get_actor_bounds(False)
                row["bounds_cm"] = [[origin.x-extent.x, origin.y-extent.y, origin.z-extent.z],
                                     [origin.x+extent.x, origin.y+extent.y, origin.z+extent.z]]
            except Exception as exc:
                row["bounds_error"] = str(exc)
        result["actors"].append(row)

# Count existing static mesh actors from the rural pack; this does not inspect
# instanced foliage internals, which vary by UE version.
for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
    mesh = actor.static_mesh_component.static_mesh
    if mesh and mesh.get_path_name().startswith("/Game/RuralAustralia/"):
        counts = result.setdefault("rural_static_mesh_actor_counts", {})
        counts[mesh.get_name()] = counts.get(mesh.get_name(), 0) + 1

for path in ASSETS:
    mesh = unreal.load_asset(path)
    row = {"path": path, "loaded": mesh is not None}
    if mesh:
        try:
            b = mesh.get_bounds()
            row["bounds_cm"] = {"origin": [b.origin.x, b.origin.y, b.origin.z],
                                "extent": [b.box_extent.x, b.box_extent.y, b.box_extent.z]}
        except Exception as exc:
            row["bounds_error"] = str(exc)
        try:
            body = mesh.get_editor_property("body_setup")
            row["trace_flag"] = str(body.get_editor_property("collision_trace_flag")) if body else None
        except Exception as exc:
            row["collision_error"] = str(exc)
    result["assets"].append(row)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(result, fh, indent=2)
unreal.log("[RedGumAssetProbe] wrote {}".format(OUT))
