"""Fix the two structural faults the first play test exposed.

1. The NavMeshBoundsVolume sat at the origin with its brush min-corner on the
   actor origin, so it covered only X 0..115 m, Y 0..165 m, Z 0..45 m. That is
   the positive quadrant. Objective B ("Gravel Gate") is at Y = -62 m and the
   Bravo deployments are at Y = -130 m, so the entire southern half of the map
   was never baked - which is why 16 deployments and 2 objectives produced
   0 of 32 routes. Measured by Tools/Unreal/diagnose_ravenshoe.py.

2. SS_Raven_Geo_Terrain had override_materials == [] - no material was ever
   assigned, so it rendered the engine default, which is white. The surfaces
   pass reported "0/1" for it and the audit only checks the bridge and the
   gate house, so the terrain passed 35/35 while being visibly broken.

Both are verified by reading the value back, because a write that reports
success and renders nothing is this project's most persistent defect.
Writes Build/ravenshoe_playtest_fix.json. Saves the map.
"""
import json
import os
import traceback

import unreal

MAP = "/Game/Maps/L_Ravenshoe_01"
OUT = os.path.join(
    unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()),
    "Build", "ravenshoe_playtest_fix.json")

report = {"map": MAP, "bounds": None, "terrain": None, "errors": [],
          "warnings": []}

# The map is 200 x 300 m with relief -18..+28 m. Cover it with margin so the
# navmesh is not clipped at the edge of the play space, and drop the floor
# below the creek bed at -18 m.
NEED_X_M, NEED_Y_M = 120.0, 170.0
Z_BOTTOM_M, Z_TOP_M = -30.0, 40.0


def v3(v):
    return [round(v.x, 1), round(v.y, 1), round(v.z, 1)]


def step(name, ok, detail=""):
    report.setdefault("steps", []).append(
        {"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def reset_recast(world, sub):
    """Replace the RecastNavMesh so its tile budget matches the new bounds.

    The existing navmesh was serialised against the old, small bounds volume
    and carries a pool of 2448 tiles (12 bits). Covering the whole map needs
    10143 (14 bits). UE logs "Recreating dtNavMesh instance due mismatch" and
    then access-violates inside UnrealEd, so the old actor has to go before
    the build rather than be resized during it.
    """
    old = [a for a in sub.get_all_level_actors()
           if isinstance(a, unreal.RecastNavMesh)]
    report["recast"] = {"before": len(old)}
    for a in old:
        report["recast"]["label"] = a.get_actor_label()
        sub.destroy_actor(a)
    report["recast"]["destroyed"] = len(old)
    step("destroy_old_recast", True, "{} destroyed".format(len(old)))

    fresh = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.RecastNavMesh, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    if fresh is None:
        step("spawn_new_recast", False, "spawn returned None")
        report["errors"].append("could not re-spawn RecastNavMesh")
        return
    fresh.set_actor_label("RecastNavMesh-Default")
    report["recast"]["after"] = fresh.get_actor_label()
    step("spawn_new_recast", True, fresh.get_actor_label())


def fix_bounds(sub):
    vols = [a for a in sub.get_all_level_actors()
            if isinstance(a, unreal.NavMeshBoundsVolume)]
    if not step("find_volume", bool(vols), "{} volume(s)".format(len(vols))):
        return
    v = vols[0]
    before = v.get_actor_bounds(False)
    report["bounds"] = {
        "before_loc": v3(v.get_actor_location()),
        "before_min": v3(before[0]),
        "before_max": v3(before[1]),
    }

    # Empirically world extent (cm) == scale * 100, with the brush min-corner
    # on the actor origin. So the location is the min corner, not the centre.
    sx = NEED_X_M * 2.0 * 100.0 / 100.0
    sy = NEED_Y_M * 2.0 * 100.0 / 100.0
    sz = (Z_TOP_M - Z_BOTTOM_M) * 100.0 / 100.0
    v.set_actor_scale3d(unreal.Vector(sx, sy, sz))
    v.set_actor_location(
        unreal.Vector(-NEED_X_M * 100.0, -NEED_Y_M * 100.0, Z_BOTTOM_M * 100.0),
        False, False)

    after = v.get_actor_bounds(False)
    report["bounds"]["after_loc"] = v3(v.get_actor_location())
    report["bounds"]["after_min"] = v3(after[0])
    report["bounds"]["after_max"] = v3(after[1])

    # Read it back and prove it covers what the layout actually needs.
    lo, hi = after[0], after[1]
    need = [("ObjB y=-6200", lo.y <= -6200), ("DeployBravo y=-13000", lo.y <= -13000),
            ("DeployAlpha y=+13000", hi.y >= 13000),
            ("creek bed z=-1800", lo.z <= -1800),
            ("ridge z=+3400", hi.z >= 3400)]
    ok = all(c for _, c in need)
    report["bounds"]["coverage"] = {n: c for n, c in need}
    step("bounds_cover_map", ok, "{}".format(
        "X %.0f..%.0f  Y %.0f..%.0f  Z %.0f..%.0f" % (
            lo.x, hi.x, lo.y, hi.y, lo.z, hi.z)))
    for n, c in need:
        if not c:
            report["errors"].append("bounds volume does not cover " + n)


def fix_terrain(sub):
    mats = {}
    for a in sub.get_all_level_actors():
        if a.get_actor_label() == "SS_Raven_Geo_Terrain":
            comp = a.get_component_by_class(unreal.StaticMeshComponent)
            if comp is None:
                step("terrain_component", False, "no StaticMeshComponent")
                return
            mesh = comp.get_editor_property("static_mesh")
            slots = mesh.get_num_sections(0) if mesh else 0
            before = list(comp.get_editor_property("override_materials"))
            report["terrain"] = {
                "mesh": mesh.get_name() if mesh else None,
                "sections": slots,
                "before": [m.get_name() if m else None for m in before],
            }

            road = unreal.load_asset(
                "/Game/Art/Environment/Ravenshoe/Materials/MI_SS_Raven_Road")
            if road is None:
                step("load_road_material", False, "MI_SS_Raven_Road missing")
                return
            for i in range(max(1, slots)):
                comp.set_material(i, road)
            comp.set_editor_property("override_materials", [road] * max(1, slots))

            after = list(comp.get_editor_property("override_materials"))
            report["terrain"]["after"] = [m.get_name() if m else None for m in after]
            got = [m.get_name() for m in after if m]
            step("terrain_has_material", len(got) == max(1, slots),
                 "{} override(s): {}".format(len(got), got))
            if not got:
                report["errors"].append(
                    "terrain override still empty after set_material")
            return
    step("find_terrain", False, "SS_Raven_Geo_Terrain not found")


try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    world = unreal.EditorLevelLibrary.get_editor_world()
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    step("load_map", True, MAP)

    fix_bounds(sub)
    reset_recast(world, sub)
    fix_terrain(sub)

    saved = unreal.EditorLoadingAndSavingUtils.save_map(world, MAP)
    step("save_map", saved, MAP)
    report["ok"] = not report["errors"]
except Exception:                                       # noqa: BLE001
    report["exception"] = traceback.format_exc()
    report["ok"] = False

with open(OUT, "w") as fh:
    json.dump(report, fh, indent=2, default=str)
print("FIX_WRITTEN", OUT, "ok=", report.get("ok"))
