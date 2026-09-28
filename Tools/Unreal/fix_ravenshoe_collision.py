# Southern Spear - Ravenshoe Crossing: collide with the surfaces you see.
#
#   UnrealEditor-Cmd ... -ExecutePythonScript=E:/SouthernSpear/Tools/Unreal/fix_ravenshoe_collision.py
#   then build_ravenshoe_nav.py with SS_RAVENSHOE_NAV_BUILD=1
#
# The terrain, bridge and gate house were imported with one auto-generated convex hull each and CTF_USE_DEFAULT,
# so the game collided with the hull: a lid over the gorge and a solid box for the bridge (first play test:
# players and bots ran 50 m above the ground). Sets complex-as-simple and drops the hulls. Also gives the terrain
# a textured ground material in place of the FBX importer's flat white Phong. Report: Build/ravenshoe_collision.json.

import json
import os

import unreal

ROOT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
MESHES = "/Game/Art/Environment/Ravenshoe/Meshes/"
GROUND = "/Game/Art/Environment/Ravenshoe/Materials/MI_SS_Raven_Road"
report = {"ok": False, "meshes": {}, "errors": []}

for name in ("SS_MAP_Ravenshoe_01", "SS_Raven_Bridge", "SS_Raven_Gatehouse"):
    mesh = unreal.load_asset(MESHES + name)
    body = mesh.get_editor_property("body_setup")
    agg = body.get_editor_property("agg_geom")
    agg.set_editor_property("convex_elems", [])
    body.set_editor_property("agg_geom", agg)
    body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    mesh.set_editor_property("body_setup", body)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    body = mesh.get_editor_property("body_setup")
    report["meshes"][name] = [str(body.get_editor_property("collision_trace_flag")),
                              len(body.get_editor_property("agg_geom").get_editor_property("convex_elems"))]
    if "COMPLEX_AS_SIMPLE" not in report["meshes"][name][0]:
        report["errors"].append(name + " flag did not take")

world = unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/L_Ravenshoe_01")
ground = unreal.load_asset(GROUND)
for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
    if a.get_actor_label() == "SS_Raven_Geo_Terrain":
        a.static_mesh_component.set_material(0, ground)
        report["terrain_material"] = a.static_mesh_component.get_material(0).get_path_name()
report["ok"] = not report["errors"] and report.get("terrain_material", "").startswith(GROUND)
if report["ok"]:
    unreal.EditorLoadingAndSavingUtils.save_current_level()
with open(os.path.join(ROOT, "Build", "ravenshoe_collision.json"), "w") as fh:
    json.dump(report, fh, indent=1)
