# Southern Spear - Dry River look pass with the Fab Rural Australia assets (ADR-021, L-0016).
#
# Dry River's layout stays original (ADR-013/015); this dresses it:
# - terrain material slots get the pack's non-landscape ground materials by slot
#   name (dirt / gravel for creek and track / stones for rock);
# - blockout fences take the pack's timber fence material;
# - each blockout scrub is swapped for a pack grass tree or small tree at the
#   same spot (same cover layout);
# - extra trees and rocks are scattered by ground trace, kept clear of
#   objectives and deployments. Run build_dryriver_nav.py afterwards.
# Idempotent (removes its own SS_RA_* actors first). Writes Build/dryriver_texture.json.

import json
import os
import random
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "dryriver_texture.json")
MAP = "/Game/Maps/L_DryRiver_01"
RA = "/Game/RuralAustralia"
GROUND = RA + "/Landscape/Non-LandscapeMaterials/"
SLOT_RULES = [  # (keywords, material)
    (("creek", "bed", "river", "sand", "track", "road", "path"), GROUND + "MI_Ground_Gravel_01"),
    (("rock", "stone", "boulder"), GROUND + "MI_Ground_Stones_01"),
    (("ground", "terrain", "bank", "dirt", "earth", "land", "grass"), GROUND + "MI_Ground_Dirt_01"),
]
CLEARANCE_CM = 1800.0
EXTRA_TREES = 40
EXTRA_ROCKS = 25

eal = unreal.EditorAssetLibrary
report = {"ok": False, "slots": {}, "swapped": 0, "scattered": 0, "errors": []}
random.seed(20260927)


def find_meshes(folder, prefix="SM_"):
    out = []
    for p in eal.list_assets(folder, recursive=True):
        name = p.split("/")[-1].split(".")[0]
        if name.startswith(prefix) and "LOD" not in name and "Billboard" not in name:
            a = unreal.load_asset(p)
            if isinstance(a, unreal.StaticMesh):
                out.append(a)
    return out


def ground(world, x, y, ignore):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, 50000), unreal.Vector(x, y, -50000),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore, unreal.DrawDebugTrace.NONE, True)
    return None if hit is None else hit.to_dict()["impact_point"]


def main():
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        if a.get_actor_label().startswith("SS_RA_"):
            actors.destroy_actor(a)
    unreal.SystemLibrary.execute_console_command(world, "BUILDPATHS")  # traces need it

    veg = RA + "/StaticMeshes/Vegetation"
    small = [m for m in find_meshes(veg) if any(k in m.get_name() for k in ("GrassTree", "Tree_S"))]
    trees = [m for m in find_meshes(veg) if "Tree_M" in m.get_name() or "Tree_L" in m.get_name()]
    rocks = [m for m in find_meshes(RA + "/StaticMeshes/Rocks") if "Rock_" in m.get_name()]
    fence_mat = None
    fence = unreal.load_asset(RA + "/StaticMeshes/Props/Fence_01/SM_Fence_02")
    if fence:
        mats = [fence.get_material(i) for i in range(len(fence.get_editor_property("static_materials")))]
        fence_mat = next((m for m in mats if m and "Wire" not in m.get_name()), None)
    report["pools"] = {"small": len(small), "trees": len(trees), "rocks": len(rocks), "fence_material": str(fence_mat)}

    keep_clear, scrub, terrain = [], [], None
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if isinstance(a, (unreal.PlayerStart, unreal.SSObjectiveActor)):
            keep_clear.append(a.get_actor_location())
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        comp = a.static_mesh_component
        mesh = comp.static_mesh
        name = mesh.get_name() if mesh else ""
        if name == "SS_MAP_DryRiver_01":
            terrain = a
            for i, sm in enumerate(mesh.get_editor_property("static_materials")):
                slot = str(sm.material_slot_name).lower()
                # Unnamed slots (the blockout exports one "material_0") default to dirt.
                chosen = next((m for keys, m in SLOT_RULES if any(k in slot for k in keys)), GROUND + "MI_Ground_Dirt_01")
                report["slots"][slot] = chosen
                if chosen:
                    comp.set_material(i, unreal.load_asset(chosen))
        elif name.startswith("SS_Dressing_Fence") and fence_mat:
            for i in range(comp.get_num_materials()):
                comp.set_material(i, fence_mat)
        elif name == "SS_Dressing_Scrub" and small:
            scrub.append(a)

    for a in scrub:
        t = a.get_actor_transform()
        new = actors.spawn_actor_from_object(random.choice(small), t.translation,
                                             unreal.Rotator(roll=0, pitch=0, yaw=random.uniform(0, 360)))
        new.set_actor_label("SS_RA_Scrub")
        s = random.uniform(0.8, 1.2)
        new.set_actor_scale3d(unreal.Vector(s, s, s))
        a.set_is_temporarily_hidden_in_editor(True)
        a.static_mesh_component.set_visibility(False)
        a.set_actor_enable_collision(False)
        report["swapped"] += 1

    if terrain:
        origin, extent = terrain.get_actor_bounds(False)
        for count, pool, label in ((EXTRA_TREES, trees, "SS_RA_Tree"), (EXTRA_ROCKS, rocks, "SS_RA_Rock")):
            placed, tries = 0, 0
            while placed < count and tries < count * 20 and pool:
                tries += 1
                x = origin.x + random.uniform(-extent.x, extent.x) * 0.9
                y = origin.y + random.uniform(-extent.y, extent.y) * 0.9
                if any(((x - p.x) ** 2 + (y - p.y) ** 2) ** 0.5 < CLEARANCE_CM for p in keep_clear):
                    continue
                g = ground(world, x, y, [])
                if g is None:
                    continue
                new = actors.spawn_actor_from_object(random.choice(pool), g,
                                                     unreal.Rotator(roll=0, pitch=0, yaw=random.uniform(0, 360)))
                new.set_actor_label(label)
                placed += 1
            report["scattered"] += placed

    report["saved"] = unreal.EditorLoadingAndSavingUtils.save_current_level()
    report["ok"] = bool(terrain) and report["saved"] and any(report["slots"].values())


try:
    main()
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[DryRiverTexture] ok={}".format(report["ok"]))
