"""Read-only validation of Red Gum's stored Recast data after expansion."""
import json
import os
import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
OUT = os.path.join(PROJECT_DIR, "Build", "redgum_nav_probe.json")
MAP = "/Game/Maps/L_RedGum_01"
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError("Could not load " + MAP)

result = {"map": MAP, "nav_data": [], "bounds": [], "queries": []}
for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
    if isinstance(actor, unreal.NavMeshBoundsVolume):
        origin, extent = actor.get_actor_bounds(False)
        result["bounds"].append({
            "label": actor.get_actor_label(),
            "size_m": [round(2*extent.x/100), round(2*extent.y/100), round(2*extent.z/100)],
            "centre_m": [round(origin.x/100), round(origin.y/100), round(origin.z/100)],
        })
    if isinstance(actor, unreal.RecastNavMesh):
        row = {"label": actor.get_actor_label(), "class": actor.get_class().get_name()}
        for prop in ("runtime_generation", "tile_pool_size", "max_tile_number"):
            try:
                row[prop] = str(actor.get_editor_property(prop))
            except Exception:
                pass
        result["nav_data"].append(row)

# Project 21 ground-sampled points across the current 720 x 600 m bounds.
for x in (-34000, 0, 34000):
    for y in (-28000, -18000, 0, 18000, 28000):
        ground = unreal.SystemLibrary.line_trace_single(
            world, unreal.Vector(x, y, 50000), unreal.Vector(x, y, -50000),
            unreal.TraceTypeQuery.ECC_VISIBILITY, True, [], unreal.DrawDebugTrace.NONE, True)
        if isinstance(ground, (list, tuple)):
            ground = ground[1] if len(ground) > 1 and ground[0] else None
        point = unreal.Vector(x, y, 300)
        if ground:
            try:
                hit = ground.to_dict()
                point = hit.get("impact_point") or hit.get("location") or point
            except Exception:
                pass
        projected = unreal.NavigationSystemV1.project_point_to_navigation(
            world, point, None, None, unreal.Vector(400, 400, 3000))
        result["queries"].append({"point_m": [x/100, y/100],
                                 "projected": [projected.x, projected.y, projected.z] if projected else None})

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)
unreal.log("[RedGumNavProbe] wrote {}".format(OUT))
