# Southern Spear - Ravenshoe expansion: the world beyond the playable edge, and the ground under it.
#
#   UnrealEditor-Cmd ... -ExecutePythonScript=E:/SouthernSpear/Tools/Unreal/expand_ravenshoe.py
#   (after Tools/Blender/ravenshoe_skirt.py; then build_ravenshoe_nav.py)
#
# The first play test found the map ending in a black horizon band, the ground rendering white, and
# nothing keeping players inside the gorge country. This is the Dry River Session 041 treatment
# (Tools/Unreal/expand_dryriver.py), ported to the Ravenshoe spec. Places, all labelled SS_Expand_*
# and replaced on every run (idempotent):
#   1. Terrain: the pack's MI_Ground_Dirt_01 like the skirt (fixes the white ground - the terrain's
#      override had fallen back to the flat MI_SS_Raven_Road), Nanite off (world-aligned ground
#      textures stream at their lowest mips under Nanite, and the render can drift from the collision
#      surface; the terrain is ~15k faces, so nothing is lost).
#   2. Skirt: Content/Art/Blockout/SS_MAP_Ravenshoe_Skirt.fbx - outer ground to ~1.6-1.7 km each way,
#      grid-seamed to the terrain at the shared edge (ravenshoe_skirt.py measured 0.0 m edge error),
#      the same ground material, collision on (it is ground).
#   3. Playable area 260 x 360 m (the 200 x 300 m terrain plus a band of the skirt): four blocking
#      volumes on its edge, and the level's nav bounds volume resized to cover the play space.
#   4. Horizon: Rural Australia SM_Horizon_01 as a ring well beyond the skirt rim, and a
#      VolumetricCloud if the level has none.
# Assets: Rural Australia (L-0016, ADR-022). The nav bounds volume is sized here and only ASSERTED by
# build_ravenshoe_nav.py - one owner, or the two passes fight (which is how the positive-quadrant
# bounds came back after the play-test fix). Report: Build/expand_ravenshoe_report.json.

import json
import os
import sys
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
sys.path.insert(0, os.path.join(PROJECT_DIR, "Tools", "Common"))
from ravenshoe_spec import MAP_HALF_X, MAP_N, MAP_S  # noqa: E402

REPORT = os.path.join(PROJECT_DIR, "Build", "expand_ravenshoe_report.json")
MAP = "/Game/Maps/L_Ravenshoe_01"
SKIRT_FBX = os.path.join(PROJECT_DIR, "Content", "Art", "Blockout", "SS_MAP_Ravenshoe_Skirt.fbx")
GROUND_MAT = "/Game/RuralAustralia/Landscape/Non-LandscapeMaterials/MI_Ground_Dirt_01"
RA = "/Game/RuralAustralia"
PREFIX = "SS_Expand_"

# The playable area: the terrain plus a 30 m band of the skirt's dense 2 m grid, so the blocking
# volumes stand on real ground and the walls are never visible from a deployment.
PAD_M = 30.0
PLAY_HALF_X = MAP_HALF_X + PAD_M          # 130 m
PLAY_HALF_Y = max(abs(MAP_N), abs(MAP_S)) + PAD_M   # 180 m

# The nav bounds cover the play space, not the mesh: with TileSizeUU = 1000 a 260 x 360 m box needs
# ~1244 tiles at the layering factor fix_ravenshoe_playtest measured. The RecastNavMesh tile pool
# defaults to 1024 - which that tile count EXCEEDS, and an over-pool bake is what access-violated
# UnrealEd on save (the earlier 2448 figure was the required tile count of the old oversized volume,
# not the pool). The pool is raised to cover the play space with margin. Dry River fits its 1024
# pool with ~345 tiles, which is why only Ravenshoe crashed.
NAV_Z_BOTTOM_M, NAV_Z_TOP_M = -25.0, 40.0
NAV_MAX_TILES = 2400.0
RECAST_POOL = 4096

report = {"ok": False, "steps": [], "errors": []}
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    unreal.log("[ExpandRavenshoe] {} {} {}".format("OK  " if ok else "FAIL", name, detail))
    return bool(ok)


def v3(v):
    return [round(v.x, 1), round(v.y, 1), round(v.z, 1)]


# --------------------------------------------------------------------------- 1. terrain material

def terrain_material():
    terrain = [a for a in actors.get_all_level_actors() if isinstance(a, unreal.StaticMeshActor)
               and a.static_mesh_component.static_mesh
               and a.static_mesh_component.static_mesh.get_name() == "SS_MAP_Ravenshoe_01"]
    if len(terrain) != 1:
        return step("terrain_found", False, "{} terrain actors".format(len(terrain)))
    a = terrain[0]
    mesh = a.static_mesh_component.static_mesh
    ns = mesh.get_editor_property("nanite_settings")
    if ns.enabled:
        ns.enabled = False
        mesh.set_editor_property("nanite_settings", ns)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    ground = unreal.load_asset(GROUND_MAT)
    a.static_mesh_component.set_material(0, ground)
    # Read it back: a write that reports success and renders nothing is this project's most
    # persistent defect (the terrain passed 35/35 while rendering engine-default white).
    got = a.static_mesh_component.get_material(0)
    ok = got is not None and got.get_name() == GROUND_MAT.rsplit("/", 1)[1]
    return step("terrain_material", ok, got.get_name() if got else "None")


# --------------------------------------------------------------------------- 2. skirt

def import_skirt():
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", SKIRT_FBX)
    task.set_editor_property("destination_path", "/Game/Art/Blockout")
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    opts = unreal.FbxImportUI()
    opts.set_editor_property("import_mesh", True)
    opts.set_editor_property("import_as_skeletal", False)
    opts.set_editor_property("import_materials", False)
    opts.set_editor_property("import_textures", False)
    smi = opts.get_editor_property("static_mesh_import_data")
    smi.set_editor_property("combine_meshes", True)
    smi.set_editor_property("auto_generate_collision", False)
    task.set_editor_property("options", opts)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset("/Game/Art/Blockout/SS_MAP_Ravenshoe_Skirt")
    if not mesh:
        return None
    # The FBX carries no material, so the mesh may import without a usable slot and a component
    # override on slot 0 silently does nothing (the Dry River skirt rendered plain grey: Session 041).
    mesh.set_editor_property("static_materials", [unreal.StaticMaterial(
        material_interface=unreal.load_asset(GROUND_MAT), material_slot_name="Ground")])
    body = mesh.get_editor_property("body_setup")
    if body:
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    return mesh


def place_skirt(mesh):
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    a.set_actor_label(PREFIX + "Skirt")
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    c.set_material(0, unreal.load_asset(GROUND_MAT))
    c.set_collision_profile_name("BlockAll")
    applied = [m.get_name() if m else None for m in c.get_materials()]
    return step("skirt_placed", applied == [GROUND_MAT.rsplit("/", 1)[1]], applied)


# --------------------------------------------------------------------------- 3. boundary + nav bounds

def boundary():
    hx, hy = PLAY_HALF_X * 100.0, PLAY_HALF_Y * 100.0   # half extents, cm
    walls = [("N", unreal.Vector(0, -hy - 100, 2500), (hx * 2 + 400, 200, 6000)),
             ("S", unreal.Vector(0, hy + 100, 2500), (hx * 2 + 400, 200, 6000)),
             ("E", unreal.Vector(hx + 100, 0, 2500), (200, hy * 2 + 400, 6000)),
             ("W", unreal.Vector(-hx - 100, 0, 2500), (200, hy * 2 + 400, 6000))]
    made = 0
    for name, loc, size in walls:
        v = actors.spawn_actor_from_class(unreal.BlockingVolume, loc, unreal.Rotator(0, 0, 0))
        v.set_actor_label(PREFIX + "Boundary_" + name)
        v.set_actor_scale3d(unreal.Vector(size[0] / 200.0, size[1] / 200.0, size[2] / 200.0))  # default brush: 200 cm cube
        made += 1
    return step("boundary", made == 4, made)


def recast_pool():
    """Raise the RecastNavMesh tile pool above the play-space tile count. The pool is a property of
    the actor, and a bake that produces more tiles than the pool holds is what crashed the save."""
    recasts = [a for a in actors.get_all_level_actors() if isinstance(a, unreal.RecastNavMesh)]
    if len(recasts) != 1:
        return step("recast_pool", False, "{} recast actors".format(len(recasts)))
    r = recasts[0]
    before = r.get_editor_property("TilePoolSize")
    if before < RECAST_POOL:
        r.set_editor_property("TilePoolSize", RECAST_POOL)
    after = r.get_editor_property("TilePoolSize")
    report["recast_pool"] = {"before": before, "after": after}
    return step("recast_pool", after >= RECAST_POOL, "{} -> {}".format(before, after))


def set_bounds_readback(vol, loc, want_extents_cm):
    """Set a brush volume's location and extents, reading the bounds back and correcting the scale.

    The volume's world extent is not scale * 200 on this build (fix_ravenshoe_playtest measured
    ~150 cm per scale unit), and the bounds read can lag the scale set, so compute-then-hope is
    exactly the failure mode that put the volume in the positive quadrant. Iterate with ratio
    correction; the pass/fail decision is the coverage assert in nav_volume(), not an extent
    tolerance, because coverage is what the bake actually consumes.
    """
    vol.set_actor_location(loc, False, False)
    ask = unreal.Vector(want_extents_cm.x / 150.0, want_extents_cm.y / 150.0, want_extents_cm.z / 150.0)
    got = unreal.Vector(0, 0, 0)
    for _ in range(12):
        vol.set_actor_scale3d(ask)
        vol.set_actor_location(loc, False, False)
        lo, hi = vol.get_actor_bounds(False)
        got = unreal.Vector(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
        if (abs(got.x - want_extents_cm.x) < want_extents_cm.x * 0.02
                and abs(got.y - want_extents_cm.y) < want_extents_cm.y * 0.02
                and abs(got.z - want_extents_cm.z) < want_extents_cm.z * 0.02):
            break
        ask = unreal.Vector(
            ask.x * want_extents_cm.x / max(got.x, 1.0),
            ask.y * want_extents_cm.y / max(got.y, 1.0),
            ask.z * want_extents_cm.z / max(got.z, 1.0))
    return got


def nav_volume():
    """Size the level's nav bounds volume to the play space. One owner: this pass. The nav pass asserts."""
    vols = [a for a in actors.get_all_level_actors() if isinstance(a, unreal.NavMeshBoundsVolume)]
    if len(vols) != 1:
        return step("nav_volume", False, "{} nav volumes".format(len(vols)))
    v = vols[0]
    ext = unreal.Vector(PLAY_HALF_X * 200.0, PLAY_HALF_Y * 200.0,
                        (NAV_Z_TOP_M - NAV_Z_BOTTOM_M) * 100.0)
    loc = unreal.Vector(-PLAY_HALF_X * 100.0, -PLAY_HALF_Y * 100.0, NAV_Z_BOTTOM_M * 100.0)
    set_bounds_readback(v, loc, ext)
    lo, hi = v.get_actor_bounds(False)
    need = [("DeployAlpha y=+13000", hi.y >= 13000.0), ("DeployBravo y=-13000", lo.y <= -13000.0),
            ("ObjB y=-6200", lo.y <= -6200.0), ("DeployExtra x=+600", hi.x >= 600.0),
            ("ramp feet x=+/-9800", lo.x <= -9800.0 and hi.x >= 9800.0),
            ("creek bed z=-1800", lo.z <= -1800.0), ("ridge z=+3400", hi.z >= 3400.0)]
    covered = all(c for _, c in need)
    tiles = (hi.x - lo.x) / 1000.0 * (hi.y - lo.y) / 1000.0 * 1.33
    detail = "X {:.0f}..{:.0f} Y {:.0f}..{:.0f} Z {:.0f}..{:.0f} (~{:.0f} tiles)".format(
        lo.x, hi.x, lo.y, hi.y, lo.z, hi.z, tiles)
    report["nav_bounds"] = {"min": v3(lo), "max": v3(hi), "approx_tiles": round(tiles),
                            "coverage": {n: c for n, c in need}}
    if not covered:
        for n, c in need:
            if not c:
                report["errors"].append("nav bounds do not cover " + n)
    # Coverage and tile budget are the pass: exact extents are implementation detail the read-back
    # cannot be held to (the brush bounds lag the scale set on this build).
    return step("nav_volume", covered and tiles < NAV_MAX_TILES, detail)


# --------------------------------------------------------------------------- 4. horizon, clouds

def horizon():
    mesh = unreal.load_asset(RA + "/Landscape/Horizon_01/SM_Horizon_01")
    if not mesh:
        return step("horizon", False, "SM_Horizon_01 missing")
    b = mesh.get_bounds()
    ext = b.box_extent
    radius = max(ext.x, ext.y)
    scale = 260000.0 / max(radius, 1.0)   # ring at ~2.6 km, past the skirt rim (~1.7 km)
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 2000.0), unreal.Rotator(0, 0, 0))
    a.set_actor_label(PREFIX + "Horizon")
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale * 0.6))
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    c.set_cast_shadow(False)
    have_cloud = any(isinstance(x, unreal.VolumetricCloud) for x in actors.get_all_level_actors())
    if not have_cloud:
        cl = actors.spawn_actor_from_class(unreal.VolumetricCloud, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        cl.set_actor_label(PREFIX + "Clouds")
    return step("horizon", True, "extent={:.0f},{:.0f},{:.0f} scale={:.2f}".format(ext.x, ext.y, ext.z, scale))


def main():
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    removed = 0
    for a in actors.get_all_level_actors():
        if a.get_actor_label().startswith(PREFIX):
            actors.destroy_actor(a)
            removed += 1
    step("cleared_previous", True, removed)

    # terrain_material, place_skirt, boundary, nav_volume and horizon log their own step.
    terrain_material()
    mesh = import_skirt()
    step("skirt_import", mesh is not None, mesh.get_path_name() if mesh else "import failed")
    if mesh:
        place_skirt(mesh)
    boundary()
    nav_volume()
    recast_pool()
    horizon()

    saved = unreal.EditorLoadingAndSavingUtils.save_map(unreal.EditorLevelLibrary.get_editor_world(), MAP)
    step("save_map", bool(saved), MAP)
    report["ok"] = all(s["ok"] for s in report["steps"]) and not report["errors"]


try:
    main()
except Exception:                                 # noqa: BLE001
    report["exception"] = traceback.format_exc()
    report["ok"] = False

with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=2, default=str)
print("EXPAND_WRITTEN", REPORT, "ok=", report.get("ok"))
