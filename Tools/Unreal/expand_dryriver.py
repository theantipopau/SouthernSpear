# Southern Spear - Dry River expansion: the world beyond the playable edge, and ground cover inside it.
#
#   UnrealEditor-Cmd ... -ExecutePythonScript=E:/SouthernSpear/Tools/Unreal/expand_dryriver.py
#   (after Tools/Blender/dryriver_skirt.py and dryriver_shelters.py; then build_dryriver_nav.py)
#
# Places, all labelled SS_Expand_* and replaced on every run (idempotent):
#   1. Skirt: Content/Art/Blockout/SS_MAP_DryRiver_Skirt.fbx (outer ground, ~1.6 km each way, seamless with the
#      terrain), the pack's MI_Ground_Dirt_01 like the terrain, collision on (it is ground).
#   2. Playable area 340 x 240 m (the 260 x 180 m terrain plus a band of the skirt, dryriver_world.PLAY_HALF_*):
#      four blocking volumes on its edge, and the level's nav volume resized to cover it.
#   3. Horizon: Rural Australia SM_Horizon_01 as a ring well beyond the skirt rim, and a VolumetricCloud.
#   4. Scatter, instanced (HISM), no collision, so sightlines, cover and navigation are unchanged:
#      inside - grass tufts, low shrubs (<= 1 m), stones (denser in the creek bed), bark debris;
#      outside - tufts near the edge, shrubs, trees, boulders.
#   5. Cover, with collision (changes sightlines and navigation: run build_dryriver_nav.py afterwards):
#      Rural Australia trees (their meshes have no simple collision, so each gets a hidden trunk collider),
#      Rural Australia rocks (also in the creek bed) and logs, the station structures of
#      Tools/Blender/dryriver_shelters.py (lean-to, shed, water tank) with yard clutter, and Singapore Canal pack
#      props: packed-sack sangars, crate/barrel supply dumps, a wheelcart, tubs. Pack meshes that ship without
#      simple collision are switched to complex-as-simple. Kept clear of deployments (45 m), objectives (8 m),
#      the creek centre line (except creek boulders), the existing dressing and each other.
#   7. African Slate Quarry (Megascans) pieces, tinted to ironstone: ledge rocks in the cut banks and rock
#      clusters (cover, collision), small stones along the creek bed (no collision).
#      Heights from Tools/Common/dryriver_world.height() (the same function that built the ground).
# Assets: Rural Australia (L-0016, ADR-022) and Namaqualand (registered Session 041). Report:
# Build/expand_dryriver_report.json.

import json
import math
import os
import random
import sys
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
sys.path.insert(0, os.path.join(PROJECT_DIR, "Tools", "Common"))
from dryriver_spec import DEPLOY_OFFSET  # noqa: E402
from dryriver_world import PLAY_HALF_X, PLAY_HALF_Y, height, outside_playable  # noqa: E402

REPORT = os.path.join(PROJECT_DIR, "Build", "expand_dryriver_report.json")
MAP = "/Game/Maps/L_DryRiver_01"
SKIRT_FBX = os.path.join(PROJECT_DIR, "Content", "Art", "Blockout", "SS_MAP_DryRiver_Skirt.fbx")
# The pack's world-space red dirt on the terrain and the skirt alike: one material, no seam at the old edge
# (Session 041: a blended material read "slightly off" next to it). Variety comes from quarry ground patches.
GROUND_MAT = "/Game/RuralAustralia/Landscape/Non-LandscapeMaterials/MI_Ground_Dirt_01"
RA = "/Game/RuralAustralia"
NQ = "/Game/Namaqualand/Meshes"
PREFIX = "SS_Expand_"
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
sdl = unreal.SubobjectDataBlueprintFunctionLibrary
report = {"ok": False, "steps": [], "scatter": {}, "errors": []}
rng = random.Random(20260928)


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def ue(x, y, z_offset=0.0):
    """Spec metres -> Unreal cm on the ground."""
    return unreal.Vector(x * 100.0, -y * 100.0, height(x, y) * 100.0 + z_offset)


def creek_distance(x, y):
    return abs(y - 2.5 * math.sin(x / 45.0))


# --------------------------------------------------------------------------- 1. skirt

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
    mesh = unreal.load_asset("/Game/Art/Blockout/SS_MAP_DryRiver_Skirt")
    if mesh:
        # The FBX carries no material, so the mesh may import without a usable slot and a component
        # override on slot 0 silently does nothing (the skirt rendered plain grey: Session 041 aerial capture).
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
    step("skirt_material", applied == [GROUND_MAT.rsplit("/", 1)[1]], applied)
    return a


# --------------------------------------------------------------------------- 2. boundary

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
    return made


def nav_volume():
    """Grow the level's nav volume over the expanded area. Its brush scale needs read-back correction (see
    build_dryriver_level.set_and_confirm_scale). Bounds half-width in cm == scale * 100."""
    vols = [a for a in actors.get_all_level_actors() if isinstance(a, unreal.NavMeshBoundsVolume)]
    if len(vols) != 1:
        return step("nav_volume", False, "{} nav volumes".format(len(vols)))
    v = vols[0]
    tx, ty, tz = PLAY_HALF_X + 10.0, PLAY_HALF_Y + 10.0, v.get_actor_scale3d().z
    ask = unreal.Vector(tx, ty, tz)
    for _ in range(8):
        v.set_actor_scale3d(ask)
        got = v.get_actor_scale3d()
        if abs(got.x - tx) < 0.5 and abs(got.y - ty) < 0.5:
            return step("nav_volume", True, "scale ({:.0f},{:.0f},{:.0f})".format(got.x, got.y, got.z))
        ask = unreal.Vector(ask.x * tx / max(got.x, 1e-3), ask.y * ty / max(got.y, 1e-3), tz)
    got = v.get_actor_scale3d()
    return step("nav_volume", False, "scale stuck at ({:.0f},{:.0f},{:.0f})".format(got.x, got.y, got.z))


# --------------------------------------------------------------------------- 5. cover (called last from main)

PROP_DIR = "/Game/Art/Environment/DryRiver"
SHELTER_FBX = os.path.join(PROJECT_DIR, "Content", "Art", "Environment", "DryRiver")
SG = "/Game/Singapore_Canal"
SHELTER_MATS = {  # first candidate that loads as a material wins (some pack "MI_" assets are layer functions)
    "Timber": [SG + "/Materials/MI_WoodOldRaw_01", SG + "/Materials/MI_WoodRaw_02"],
    # Megascans corrugated iron (setup_fab_materials.py); the Singapore "metal" carried carved Asian ornament.
    "Iron": ["/Game/Art/Environment/Fab/CorrugatedIron/MI_SS_CorrugatedIron", SG + "/Materials/MI_Barrel_01"],
}
# First-pass assets (flat-colour blocks, Session 041 draft) that the pack props replaced.
OBSOLETE = [PROP_DIR + "/" + n for n in ("SS_DR_Sangar", "SS_DR_Trough", "MI_SS_Prop_Iron", "MI_SS_Prop_Concrete",
                                         "MI_SS_Prop_Sandbag", "M_SS_PropFlat", "SS_DR_Puddle_01", "SS_DR_Puddle_02", "SS_DR_Puddle_03")] + ["/Game/Art/Environment/M_SS_DryRiverGround"]
DEPLOY_CLEAR_M = 45.0   # collidable cover keeps this far from a deployment centre (spec PROTECTED uses 70 m for
                        # scatter; 45 m still leaves every spawn unobstructed on the way out - MAPS_DRYRIVER.md)
OBJECTIVE_CLEAR_M = 8.0


def solid(mesh):
    """Pack meshes mostly ship with no simple collision (players and bullets pass through). Collide against the
    render mesh instead; idempotent, and re-applied on every run so a fresh pack install gets it too."""
    body = mesh.get_editor_property("body_setup")
    if body and body.get_editor_property("collision_trace_flag") != unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE:
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
        report.setdefault("collision_set", []).append(mesh.get_name())
    return mesh


def import_shelters():
    mats = {}
    for k, paths in SHELTER_MATS.items():
        mats[k] = next((m for m in (unreal.load_asset(p) for p in paths) if isinstance(m, unreal.MaterialInterface)), None)
    out = {}
    for name in ("LeanTo", "Shed", "Tank"):
        asset = "SS_DR_" + name
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", os.path.join(SHELTER_FBX, asset + ".fbx"))
        task.set_editor_property("destination_path", PROP_DIR)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", True)
        opts = unreal.FbxImportUI()
        opts.set_editor_property("import_mesh", True)
        opts.set_editor_property("import_as_skeletal", False)
        opts.set_editor_property("import_materials", False)
        opts.set_editor_property("import_textures", False)
        opts.get_editor_property("static_mesh_import_data").set_editor_property("auto_generate_collision", False)
        task.set_editor_property("options", opts)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        mesh = unreal.load_asset(PROP_DIR + "/" + asset)
        if not mesh:
            step("shelter_" + name, False, "import failed")
            continue
        fixed = []
        for sm in mesh.get_editor_property("static_materials"):
            slot = str(sm.get_editor_property("material_slot_name"))
            key = next((k for k in mats if slot.startswith(k)), None)
            fixed.append(unreal.StaticMaterial(material_interface=mats.get(key), material_slot_name=slot))
        mesh.set_editor_property("static_materials", fixed)
        mesh.get_editor_property("body_setup").set_editor_property(
            "collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
        out[name] = mesh
        step("shelter_" + name, bool(fixed) and all(f.material_interface for f in fixed),
             [str(f.material_slot_name) + "=" + (f.material_interface.get_name() if f.material_interface else "None")
              for f in fixed])
    return out


def place_actor(label, mesh, x, y, yaw, scale, z_cm, collide=True):
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x * 100.0, -y * 100.0, z_cm),
                                      unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    a.set_actor_label(label)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    if collide:
        c.set_collision_profile_name("BlockAll")
    else:
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return a


def footprint_heights(x, y, half):
    return [height(x + dx, y + dy) for dx in (-half, 0.0, half) for dy in (-half, 0.0, half)]


def local(x, y, yaw_deg, lx, ly):
    """Spec-metre point offset (lx forward, ly left in Unreal terms) from (x, y) facing Unreal yaw."""
    t = math.radians(yaw_deg)
    ux, uy = lx * math.cos(t) - ly * math.sin(t), lx * math.sin(t) + ly * math.cos(t)  # Unreal axes
    return x + ux, y - uy                                                                 # back to spec (y mirrored)


def cover(starts, objectives, dressing):
    """Collidable cover over the expanded playable area. Positions in spec metres."""
    for path in OBSOLETE:
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            unreal.EditorAssetLibrary.delete_asset(path)
    placed = []  # (x, y, radius_m)
    counts = {}
    hx, hy = PLAY_HALF_X - 4.0, PLAY_HALF_Y - 4.0
    deploy = [(0.0, -DEPLOY_OFFSET), (0.0, DEPLOY_OFFSET)]

    def free(x, y, r, gap, creek_ok=False):
        if not creek_ok and creek_distance(x, y) < 3.0:
            return False
        if any(math.hypot(x - dx, y - dy) < DEPLOY_CLEAR_M + r for dx, dy in deploy):
            return False
        for p in starts:
            if (p.x / 100.0 - x) ** 2 + (-p.y / 100.0 - y) ** 2 < 14.0 ** 2:
                return False
        for p in objectives:
            if (p.x / 100.0 - x) ** 2 + (-p.y / 100.0 - y) ** 2 < (OBJECTIVE_CLEAR_M + r) ** 2:
                return False
        for (dx, dy) in dressing:
            if (dx - x) ** 2 + (dy - y) ** 2 < (r + 3.0) ** 2:
                return False
        return all((px - x) ** 2 + (py - y) ** 2 >= (pr + r + gap) ** 2 for px, py, pr in placed)

    def candidates(n, r, gap, flat=None, where=None, creek_ok=False):
        for _ in range(n * 80):
            x, y = rng.uniform(-hx, hx), rng.uniform(-hy, hy)
            if where is not None and not where(x, y):
                continue
            if flat is not None:
                hs = footprint_heights(x, y, r)
                if max(hs) - min(hs) > flat:
                    continue
            if free(x, y, r, gap, creek_ok):
                yield x, y

    def bearing_to_nearest_objective(x, y):
        if not objectives:
            return rng.uniform(0, 360)
        p = min(objectives, key=lambda o: (o.x / 100.0 - x) ** 2 + (-o.y / 100.0 - y) ** 2)
        return math.degrees(math.atan2(p.y + y * 100.0, p.x - x * 100.0))

    def ground_cm(x, y, r=0.0):
        return (min(footprint_heights(x, y, r)) if r else height(x, y)) * 100.0

    sg = lambda n: solid(unreal.load_asset(SG + "/Meshes/" + n))
    sacks = [sg("SM_SacksPacked_01"), sg("SM_SacksPacked_02")]
    crates, barrel, cart, tub = [sg("SM_Crate_01"), sg("SM_CrateSmall_01")], sg("SM_Barrel_01"), sg("SM_Wheelcart_01"), sg("SM_Tub_01")
    planks = [sg("SM_PlanksBig_01"), sg("SM_PlanksBig_02"), sg("SM_PlanksBig_03")]
    frames = [sg("SM_WoodStructure_01"), sg("SM_WoodStructure_02"), sg("SM_WoodStructure_05")]

    def clutter(tag, x, y, yaw, items):
        """items: (mesh, lx, ly, dz_m, dyaw) in metres around the anchor."""
        for i, (m, lx, ly, dz, dyaw) in enumerate(items):
            px, py = local(x, y, yaw, lx, ly)
            place_actor("{}Cover_{}_{:02d}".format(PREFIX, tag, i), m, px, py, yaw + dyaw, 1.0, ground_cm(px, py) - 4.0 + dz * 100.0)

    # Station structures, each with yard clutter beside it (tanks get a tub: the stock trough).
    shelters = import_shelters()
    for name, n, r in (("LeanTo", 3, 3.2), ("Shed", 3, 4.0), ("Tank", 3, 2.2)):
        mesh = shelters.get(name)
        k = 0
        for x, y in (candidates(n, r + 2.0, 20.0, flat=0.6) if mesh else []):
            yaw = rng.choice(range(0, 360, 15))
            place_actor("{}Cover_{}_{:02d}".format(PREFIX, name, k), mesh, x, y, yaw, 1.0, ground_cm(x, y, r * 0.7) - 5.0)
            tag = "{}Yard_{:02d}".format(name, k)
            if name == "Tank":
                clutter(tag, x, y, yaw, [(tub, 0.0, r + 1.3, 0.0, 0), (barrel, 1.4, r + 0.9, 0.0, 30)])
            elif name == "Shed":
                clutter(tag, x, y, yaw, [(cart, 0.0, 0.2, 0.0, 10), (crates[0], -2.0, -0.6, 0.0, 0),
                                          (crates[0], -2.0, -0.6, 0.66, 12), (barrel, 2.3, -0.9, 0.0, 0),
                                          (barrel, 2.3, 0.1, 0.0, 40)])
            else:
                clutter(tag, x, y, yaw, [(barrel, 1.2, 0.4, 0.0, 0), (crates[1], -1.0, 0.0, 0.0, 20),
                                          (rng.choice(planks), 0.0, -3.0, 0.0, 5)])
            placed.append((x, y, r + 2.0))
            k += 1
            if k == n:
                break
        counts[name] = k

    # Sangars: packed-sack walls in an arc, two courses, the open side away from the nearest objective.
    k = 0
    for x, y in candidates(8, 2.8, 16.0, flat=0.5):
        face = bearing_to_nearest_objective(x, y)
        items = []
        for course in (0, 1):
            for j in range(5):
                a = face + (-56 + 28 * j) + (14 if course else 0) * (1 if j < 4 else 0)
                if course and j == 4:
                    continue
                px, py = local(x, y, a, 2.3, 0.0)
                items.append((px, py, a + 90.0, course))
        for i, (px, py, yaw, course) in enumerate(items):
            place_actor("{}Cover_Sangar_{:02d}_{:02d}".format(PREFIX, k, i), sacks[i % 2], px, py, yaw, 1.0,
                        ground_cm(px, py) - 6.0 + course * 52.0)
        clutter("SangarKit_{:02d}".format(k), x, y, face, [(crates[1], -0.6, 0.6, 0.0, 15)])
        placed.append((x, y, 2.8))
        k += 1
        if k == 8:
            break
    counts["Sangar"] = k

    # Supply dumps: stacked crates, barrels, timber - waist to chest high cover.
    k = 0
    for x, y in candidates(10, 2.5, 14.0, flat=0.5):
        yaw = rng.uniform(0, 360)
        items = [(crates[0], 0.0, 0.0, 0.0, 0), (crates[0], 0.0, 0.85, 0.0, 3), (crates[0], 0.0, 0.4, 0.66, 8),
                 (barrel, 1.3, -0.5, 0.0, 0), (barrel, 1.4, 0.4, 0.0, 70)]
        if rng.random() < 0.6:
            items.append((rng.choice(frames), -1.6, 0.2, 0.0, 90))
        if rng.random() < 0.5:
            items.append((rng.choice(planks), 0.5, -2.2, 0.0, 0))
        clutter("Supply_{:02d}".format(k), x, y, yaw, items)
        placed.append((x, y, 2.5))
        k += 1
        if k == 10:
            break
    counts["Supply"] = k

    def natural(name, pool, n, r, gap, scale_range, sink_frac, where=None, creek_ok=False):
        k = 0
        for x, y in candidates(n, r, gap, where=where, creek_ok=creek_ok):
            m = rng.choice(pool)
            s = rng.uniform(*scale_range)
            sink = m.get_bounds().box_extent.z * 2.0 * s * sink_frac
            place_actor("{}Cover_{}_{:03d}".format(PREFIX, name, k), m, x, y, rng.uniform(0, 360), s,
                        height(x, y) * 100.0 - sink)
            placed.append((x, y, r))
            k += 1
            if k == n:
                break
        counts[name] = k
        return k

    veg = RA + "/StaticMeshes/Vegetation/"
    rocks = [solid(m) for m in meshes([RA + "/StaticMeshes/Rocks/{0}/SM_{0}".format(n)
                                       for n in ("Rock_M_01", "Rock_M_02", "Rock_M_03", "Rock_S_01", "Rock_S_02")])]
    small_rocks = [solid(m) for m in meshes([RA + "/StaticMeshes/Rocks/{0}/SM_{0}".format(n) for n in ("Rock_S_01", "Rock_S_02")])]
    logs = meshes([veg + "{0}/SM_{0}".format(n) for n in ("Log_L_01", "Log_M_01", "Log_S_01", "Log_S_02")])
    natural("Rock", rocks, 50, 1.6, 5.0, (0.7, 1.2), 0.3)
    natural("Log", logs, 30, 2.0, 5.0, (0.9, 1.2), 0.1)
    # The creek bed: boulders the floods left, cover for anyone moving along the channel.
    natural("CreekRock", small_rocks, 30, 1.0, 4.0, (0.45, 0.85), 0.35,
            where=lambda x, y: creek_distance(x, y) < 3.5, creek_ok=True)

    # Trees render instanced (the pack's tree meshes carry no simple collision); each gets a hidden trunk
    # cylinder in one collision-only HISM so it stops players and bullets.
    trees = meshes([veg + "{0}/SM_{0}".format(t)
                    for t in ("Tree_M_01", "Tree_M_02", "Tree_M_03", "Tree_M_04", "Tree_S_01", "Tree_L_01")])
    by_mesh, trunks = {}, []
    for x, y in candidates(80, 2.5, 6.0):
        m = rng.choice(trees)
        s = rng.uniform(0.85, 1.25)
        base = ue(x, y, -10.0)
        by_mesh.setdefault(m, []).append(unreal.Transform(base, unreal.Rotator(roll=0, pitch=0, yaw=rng.uniform(0, 360)),
                                                          unreal.Vector(s, s, s)))
        d = (0.55 if "Tree_L" in m.get_name() else 0.4) * s  # trunk diameter, m (the cylinder is 1 m wide, 1 m tall)
        trunks.append(unreal.Transform(unreal.Vector(base.x, base.y, base.z + 300.0), unreal.Rotator(roll=0, pitch=0, yaw=0),
                                       unreal.Vector(d, d, 6.0)))
        placed.append((x, y, 2.5))
        if len(trunks) == 80:
            break
    for i, (m, ts) in enumerate(by_mesh.items()):
        hism_actor("{}Cover_Tree_{:02d}".format(PREFIX, i), m, ts, 0, True)
    counts["Tree"] = len(trunks)
    if trunks:
        a = actors.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        a.set_actor_label(PREFIX + "Cover_TreeTrunks")
        handles = sub.k2_gather_subobject_data_for_instance(a)
        handle, _ = sub.add_new_subobject(unreal.AddNewSubobjectParams(
            parent_handle=handles[0], new_class=unreal.HierarchicalInstancedStaticMeshComponent))
        comp = sdl.get_object(sdl.get_data(handle))
        comp.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cylinder"))
        comp.set_collision_profile_name("BlockAll")
        comp.set_editor_property("visible", False)
        comp.set_editor_property("hidden_in_game", True)
        comp.set_editor_property("cast_shadow", False)
        comp.add_instances(trunks, False, True)
        counts["TreeTrunkColliders"] = comp.get_instance_count()
    report["cover"] = counts
    return counts


# --------------------------------------------------------------------------- 6. blockout dressing upgrade

def upgrade_dressing():
    """The blockout dressing (dress_dryriver.py) still used grey-grid blocks for crates, barrels, wrecks and scrub.
    Swap each in place for a textured pack mesh of about the same footprint, keeping its position, yaw, label and
    collision (so cover and navigation stay as designed); wrecks keep their shape and get rusted metal."""
    swaps = {
        "SS_Dressing_Crate": [SG + "/Meshes/SM_Crate_01"],
        "SS_Dressing_Barrel": [SG + "/Meshes/SM_Barrel_01"],
        "SS_Dressing_Scrub": [NQ + "/Foliage/NN/SM_didelta_spinosa_large_NN", NQ + "/Foliage/NN/SM_didelta_spinosa_medium_NN"],
    }
    rust = next((m for m in (unreal.load_asset(p) for p in SHELTER_MATS["Iron"]) if isinstance(m, unreal.MaterialInterface)), None)
    done = {}
    for a in actors.get_all_level_actors():
        if not isinstance(a, unreal.StaticMeshActor) or a.get_actor_label().startswith(PREFIX):
            continue
        c = a.static_mesh_component
        m = c.static_mesh
        if not m:
            continue
        name = m.get_name()
        if name == "SS_Dressing_Wreck" and rust:
            for i in range(c.get_num_materials()):
                c.set_material(i, rust)
            done[name] = done.get(name, 0) + 1
            continue
        if name not in swaps:
            continue
        old_origin, old_ext = a.get_actor_bounds(False)
        new = solid(unreal.load_asset(rng.choice(swaps[name])))
        ne = new.get_bounds().box_extent
        scale = max(0.6, min(max(old_ext.x, old_ext.y) / max(ne.x, ne.y, 1.0), 2.5))
        a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
        c.set_static_mesh(new)
        c.set_editor_property("override_materials", [])
        # Keep the base on the ground: match the old bottom.
        new_origin, new_ext = a.get_actor_bounds(False)
        loc = a.get_actor_location()
        a.set_actor_location(unreal.Vector(loc.x, loc.y, loc.z + (old_origin.z - old_ext.z) - (new_origin.z - new_ext.z)), False, False)
        done[name] = done.get(name, 0) + 1
    report["dressing_upgraded"] = done
    return step("upgrade_dressing", True, done)


# --------------------------------------------------------------------------- 7. quarry pieces (African Slate Quarry)

QUARRY = "/Game/Scene_QuarrySlate"
TINT_DIR = PROP_DIR + "/QuarryTint"
IRONSTONE = unreal.LinearColor(0.95, 0.60, 0.42, 1.0)  # slate grey -> weathered ironstone red-brown


def quarry_mesh(name):
    for p in unreal.EditorAssetLibrary.list_assets(QUARRY + "/Assets", recursive=True):
        if p.split("/")[-1].split(".")[0] == name:
            m = unreal.load_asset(p)
            if isinstance(m, unreal.StaticMesh):
                return m
    return None


def tinted(mesh):
    """Child instances of the mesh's own Megascans materials with 'Albedo Tint' pushed to ironstone. The pack
    stays untouched; the instances live in the project (Content/Art/Environment/DryRiver/QuarryTint)."""
    out = []
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    for sm in mesh.get_editor_property("static_materials"):
        base = sm.material_interface
        if base is None:
            out.append(None)
            continue
        name = "MI_SS_Ironstone_" + base.get_name()
        path = TINT_DIR + "/" + name
        mi = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else tools.create_asset(
            name, TINT_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property("parent", base)
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, "Albedo Tint", IRONSTONE)
        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        out.append(mi)
    return out


def quarry_dressing(objectives, dressing):
    """Ledge rocks along the creek's cut banks and rock clusters on the flats (hard cover, collision), and small
    stones strewn along the creek bed."""
    if not unreal.EditorAssetLibrary.does_directory_exist(QUARRY):
        return step("quarry", False, "Scene_QuarrySlate not installed")
    deploy = [(0.0, -DEPLOY_OFFSET), (0.0, DEPLOY_OFFSET)]

    def clear(x, y, r):
        if any(math.hypot(x - dx, y - dy) < DEPLOY_CLEAR_M + r for dx, dy in deploy):
            return False
        if any(math.hypot(o.x / 100.0 - x, -o.y / 100.0 - y) < OBJECTIVE_CLEAR_M + r for o in objectives):
            return False
        return all(math.hypot(dx - x, dy - y) > r + 2.0 for dx, dy in dressing)

    counts = {}
    # Ledges: set into the bank, long axis along the channel, the face toward the bed.
    ledges = [m for m in (quarry_mesh(n) for n in ("SM_Qua_Sla_Ledge_Rock_L_01", "SM_Qua_Sla_Ledge_Rock_M_01",
                                                   "SM_Qua_Sla_Ledge_Rock_M_03", "SM_Qua_Sla_Ledge_Rock_S_01",
                                                   "SM_Qua_Sla_Cluster_Ledge_Rock_M_01")) if m]
    mats = {m.get_name(): tinted(solid(m)) for m in ledges}
    k, last = 0, []
    for _ in range(400):
        x = rng.uniform(-PLAY_HALF_X + 6, PLAY_HALF_X - 6)
        side = rng.choice((-1.0, 1.0))
        y = 2.5 * math.sin(x / 45.0) + side * rng.uniform(4.6, 6.0)
        if not clear(x, y, 3.0) or any(math.hypot(px - x, py - y) < 9.0 for px, py in last):
            continue
        m = rng.choice(ledges)
        heading = -math.degrees(math.atan(2.5 / 45.0 * math.cos(x / 45.0)))
        s = rng.uniform(0.8, 1.3)
        a = place_actor("{}Creek_Ledge_{:02d}".format(PREFIX, k), m, x, y, heading + (0 if side > 0 else 180) + rng.uniform(-12, 12),
                        s, height(x, y) * 100.0 - m.get_bounds().box_extent.z * s * 0.9)
        for i, mi in enumerate(mats[m.get_name()]):
            if mi:
                a.static_mesh_component.set_material(i, mi)
        last.append((x, y))
        k += 1
        if k == 26:
            break
    counts["Ledge"] = k

    # Rock clusters: extra hard cover across the flats, tinted.
    clusters = [m for m in (quarry_mesh(n) for n in ("SM_Qua_Sla_Cluster_Rock_M_06", "SM_Qua_Sla_Cluster_Rock_M_07",
                                                     "SM_Qua_Sla_Cluster_Rock_S_02", "SM_Qua_Sla_Cluster_Rock_S_05",
                                                     "SM_Qua_Sla_Rock_S_16", "SM_Qua_Sla_Pile_Rock_S_01")) if m]
    cmats = {m.get_name(): tinted(solid(m)) for m in clusters}
    k = 0
    for _ in range(600):
        x, y = rng.uniform(-PLAY_HALF_X + 5, PLAY_HALF_X - 5), rng.uniform(-PLAY_HALF_Y + 5, PLAY_HALF_Y - 5)
        if not clear(x, y, 2.0) or any(math.hypot(px - x, py - y) < 7.0 for px, py in last):
            continue
        m = rng.choice(clusters)
        s = rng.uniform(0.9, 1.5)
        a = place_actor("{}Quarry_Rocks_{:02d}".format(PREFIX, k), m, x, y, rng.uniform(0, 360), s,
                        height(x, y) * 100.0 - m.get_bounds().box_extent.z * s * 0.5)
        for i, mi in enumerate(cmats[m.get_name()]):
            if mi:
                a.static_mesh_component.set_material(i, mi)
        last.append((x, y))
        k += 1
        if k == 30:
            break
    counts["RockCluster"] = k

    # The pack's flat ground patches (gravel, dirt tracks, dried mud) were tried and removed: on this red they
    # read as pale slabs, "stepping stones" in the creek (producer screenshots, Session 041). The creek bed gets
    # the pack's small rocks instead, tinted, instanced, no collision (too small to be cover).
    small = [m for m in (quarry_mesh("SM_Qua_Sla_Rock_S_{:02d}".format(i)) for i in (2, 4, 8, 9, 10, 11, 14, 15)) if m]
    for i, m in enumerate(small):
        pm = tinted(m)
        ts = []
        for _ in range(4000):
            x = rng.uniform(-PLAY_HALF_X - 30, PLAY_HALF_X + 30)
            y = 2.5 * math.sin(x / 45.0) + rng.gauss(0.0, 1.6)
            s = rng.uniform(1.0, 3.2)
            ts.append(unreal.Transform(ue(x, y, 4.0), unreal.Rotator(roll=rng.uniform(-20, 20), pitch=rng.uniform(-20, 20),
                                                                     yaw=rng.uniform(0, 360)), unreal.Vector(s, s, s)))
            if len(ts) == 70:
                break
        a = actors.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        a.set_actor_label("{}Creek_Stones_{:02d}".format(PREFIX, i))
        handles = sub.k2_gather_subobject_data_for_instance(a)
        handle, _ = sub.add_new_subobject(unreal.AddNewSubobjectParams(
            parent_handle=handles[0], new_class=unreal.HierarchicalInstancedStaticMeshComponent))
        comp = sdl.get_object(sdl.get_data(handle))
        comp.set_static_mesh(m)
        if pm and pm[0]:
            comp.set_material(0, pm[0])
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        comp.set_cull_distances(10000, 15000)
        comp.add_instances(ts, False, True)
        counts["CreekStones"] = counts.get("CreekStones", 0) + comp.get_instance_count()
    report["quarry"] = counts
    return step("quarry", counts.get("Ledge", 0) > 0, counts)


# --------------------------------------------------------------------------- 3. horizon, clouds

def horizon():
    mesh = unreal.load_asset(RA + "/Landscape/Horizon_01/SM_Horizon_01")
    if not mesh:
        return step("horizon", False, "SM_Horizon_01 missing")
    b = mesh.get_bounds()
    ext = b.box_extent
    radius = max(ext.x, ext.y)
    scale = 260000.0 / max(radius, 1.0)   # ring at ~2.6 km, past the skirt rim (1.4-1.6 km)
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 2000.0), unreal.Rotator(0, 0, 0))
    a.set_actor_label(PREFIX + "Horizon")
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale * 0.6))
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    c.set_cast_shadow(False)
    step("horizon", True, "extent={:.0f},{:.0f},{:.0f} scale={:.2f}".format(ext.x, ext.y, ext.z, scale))
    have_cloud = any(isinstance(x, unreal.VolumetricCloud) for x in actors.get_all_level_actors())
    if not have_cloud:
        cl = actors.spawn_actor_from_class(unreal.VolumetricCloud, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        cl.set_actor_label(PREFIX + "Clouds")
    return True


# --------------------------------------------------------------------------- 4. scatter

def meshes(paths):
    out = []
    for p in paths:
        m = unreal.load_asset(p)
        if m:
            out.append(m)
    return out


def mesh_height(m):
    return m.get_bounds().box_extent.z * 2.0


def hism_actor(label, mesh, transforms, cull_end, shadow):
    a = actors.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    a.set_actor_label(label)
    handles = sub.k2_gather_subobject_data_for_instance(a)
    handle, reason = sub.add_new_subobject(unreal.AddNewSubobjectParams(
        parent_handle=handles[0], new_class=unreal.HierarchicalInstancedStaticMeshComponent))
    comp = sdl.get_object(sdl.get_data(handle))
    comp.set_static_mesh(mesh)
    comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    comp.set_editor_property("cast_shadow", shadow)
    comp.set_cull_distances(0 if cull_end == 0 else int(cull_end * 0.7), int(cull_end))
    comp.add_instances(transforms, False, True)
    return comp.get_instance_count()


def scatter(name, pool, count_for, place, cull_end, shadow, scale_range, max_height_m=None, align_up=True):
    """count_for: number of samples; place(x, y) -> accept probability (0..1) for a candidate point."""
    if not pool:
        return step("scatter_" + name, False, "no meshes loaded")
    by_mesh = {}
    xs_range, ys_range, n = count_for
    for _ in range(n):
        x = rng.uniform(*xs_range)
        y = rng.uniform(*ys_range)
        p = place(x, y)
        if p <= 0 or rng.random() > p:
            continue
        m = rng.choice(pool)
        s = rng.uniform(*scale_range)
        if max_height_m:
            s = min(s, max_height_m * 100.0 / max(mesh_height(m), 1.0))
        t = unreal.Transform(ue(x, y, -3.0), unreal.Rotator(roll=rng.uniform(-3, 3), pitch=rng.uniform(-3, 3), yaw=rng.uniform(0, 360)),
                             unreal.Vector(s, s, s))
        by_mesh.setdefault(m, []).append(t)
    total = 0
    for i, (m, ts) in enumerate(by_mesh.items()):
        total += hism_actor("{}Scatter_{}_{:02d}".format(PREFIX, name, i), m, ts, cull_end, shadow)
    report["scatter"][name] = {"instances": total, "meshes": len(by_mesh)}
    return total


def main():
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    removed = 0
    for a in actors.get_all_level_actors():
        if a.get_actor_label().startswith(PREFIX):
            actors.destroy_actor(a)
            removed += 1
    step("cleared_previous", True, removed)
    # The terrain takes the same ground material as the skirt, and loses Nanite: with Nanite the world-aligned
    # ground textures streamed at their lowest mips (flat orange, Session 041) and the render could differ from
    # the collision surface. ~7.5k vertices, so nothing is lost.
    terrain = [a for a in actors.get_all_level_actors() if isinstance(a, unreal.StaticMeshActor)
               and a.static_mesh_component.static_mesh
               and a.static_mesh_component.static_mesh.get_name() == "SS_MAP_DryRiver_01"]
    for a in terrain:
        mesh = a.static_mesh_component.static_mesh
        ns = mesh.get_editor_property("nanite_settings")
        if ns.enabled:
            ns.enabled = False
            mesh.set_editor_property("nanite_settings", ns)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
        a.static_mesh_component.set_material(0, unreal.load_asset(GROUND_MAT))
    step("terrain_material", len(terrain) == 1 and terrain[0].static_mesh_component.get_material(0).get_name() ==
         GROUND_MAT.rsplit("/", 1)[1], [a.static_mesh_component.get_material(0).get_name() for a in terrain])

    mesh = import_skirt()
    step("skirt_import", mesh is not None, mesh.get_path_name() if mesh else "import failed")
    if mesh:
        place_skirt(mesh)
    step("boundary", boundary() == 4)
    nav_volume()
    horizon()

    hx, hy = PLAY_HALF_X, PLAY_HALF_Y
    starts = [a.get_actor_location() for a in actors.get_all_level_actors() if a.get_class().get_name().endswith("PlayerStart")]
    objectives = [a.get_actor_location() for a in actors.get_all_level_actors() if a.get_class().get_name() == "SSObjectiveActor"]

    def clear_of(x, y, points, r_m):
        px, py = x * 100.0, -y * 100.0
        return all((p.x - px) ** 2 + (p.y - py) ** 2 > (r_m * 100.0) ** 2 for p in points)

    inside = ((-hx, hx), (-hy, hy))
    ring = lambda d: ((-hx - d, hx + d), (-hy - d, hy + d))
    area_in = (2 * hx) * (2 * hy)
    # Existing dressing (dress_dryriver / texture_dryriver pieces) that new cover must keep clear of.
    dressing = [(a.get_actor_location().x / 100.0, -a.get_actor_location().y / 100.0)
                for a in actors.get_all_level_actors()
                if isinstance(a, unreal.StaticMeshActor) and not a.get_actor_label().startswith(PREFIX)
                and a.static_mesh_component.static_mesh
                and not a.static_mesh_component.static_mesh.get_name().startswith("SS_MAP_DryRiver")]
    report["existing_dressing"] = len(dressing)

    def slope_ok(x, y):  # avoid steep banks for tufts and shrubs
        g = math.hypot(height(x + 0.5, y) - height(x - 0.5, y), height(x, y + 0.5) - height(x, y - 0.5))
        return g < 0.6

    tufts = meshes([RA + "/Scatter/SM_Scatter_01_" + c for c in "ABCDEFGHIJKLMNOP"])
    tufts = [m for m in tufts if mesh_height(m) < 90.0] or tufts
    shrubs = meshes([RA + "/Scatter/SM_Scatter_0{}".format(s) for s in ("2_A", "2_B", "2_C", "2_D", "2_E", "4_A", "4_B", "4_C", "4_D", "5")]
                    + [NQ + "/Foliage/NN/SM_didelta_spinosa_{}_NN".format(s) for s in ("small", "medium", "large")])
    stones = meshes([NQ + "/General/NN/SM_namaqualand_stones_01_{}_NN".format(c) for c in "abcde"]
                    + [NQ + "/General/NN/SM_namaqualand_rocks_01_{}_NN".format(c) for c in "abcd"])
    debris = meshes([NQ + "/General/NN/SM_bark_debris_01_{}_NN".format(c) for c in "abcd"]
                    + [NQ + "/General/NN/SM_dead_quiver_branch_0{}_NN".format(i) for i in (1, 2)])
    veg = RA + "/StaticMeshes/Vegetation/"
    trees = meshes([veg + "{0}/SM_{0}".format(t) for t in ("Tree_L_01", "Tree_M_01", "Tree_M_02", "Tree_M_03", "Tree_M_04", "Tree_S_01")]
                   + [veg + "GrassTree_01/SM_GrassTree_0{}".format(i) for i in (1, 2, 3, 4)])
    logs = meshes([veg + "{0}/SM_{0}".format(t) for t in ("Log_L_01", "Log_M_01", "Log_S_01", "Log_S_02")])
    boulders = meshes([NQ + "/General/NN/SM_namaqualand_boulder_0{}_NN".format(i) for i in (2, 3, 4, 5, 6)]
                      + [NQ + "/General/NN/SM_namaqualand_boulders_01_{}_NN".format(c) for c in "ab"])
    report["pools"] = {k: len(v) for k, v in dict(tufts=tufts, shrubs=shrubs, stones=stones, debris=debris,
                                                     trees=trees, boulders=boulders, logs=logs).items()}

    # Inside the playable area (no collision: sightlines, cover and navigation unchanged).
    scatter("Tuft", tufts, (inside[0], inside[1], int(area_in * 0.22)),
            lambda x, y: 0.0 if creek_distance(x, y) < 6.0 or not slope_ok(x, y) or not clear_of(x, y, starts, 2.5) else 0.8,
            6000, False, (0.8, 1.3))
    scatter("Shrub", shrubs, (inside[0], inside[1], int(area_in * 0.012)),
            lambda x, y: 0.0 if creek_distance(x, y) < 7.0 or not slope_ok(x, y) or not clear_of(x, y, starts + objectives, 6.0) else 1.0,
            25000, True, (0.7, 1.1), max_height_m=1.0)
    scatter("Stone", stones, (inside[0], inside[1], int(area_in * 0.05)),
            lambda x, y: 1.0 if creek_distance(x, y) < 6.0 else 0.25,
            12000, True, (0.6, 1.2), max_height_m=0.35)
    scatter("Debris", debris, (inside[0], inside[1], int(area_in * 0.006)),
            lambda x, y: 1.0 if clear_of(x, y, starts, 3.0) else 0.0, 8000, True, (0.8, 1.2), max_height_m=0.4)

    # Outside: the world past the edge (never reachable; cheaper, larger pieces).
    out = lambda lo, hi: (lambda x, y: 1.0 if lo <= outside_playable(x, y) <= hi else 0.0)
    r = ring(60.0)
    scatter("EdgeTuft", tufts, (r[0], r[1], int(((2 * hx + 120) * (2 * hy + 120) - area_in) * 0.12)),
            out(0.5, 60.0), 6000, False, (0.9, 1.4))
    r = ring(450.0)
    ring_area = (2 * hx + 900) * (2 * hy + 900) - area_in
    scatter("FarShrub", shrubs, (r[0], r[1], int(ring_area * 0.004)), out(1.0, 450.0), 30000, True, (0.8, 1.5))
    scatter("FarTree", trees, (r[0], r[1], int(ring_area * 0.0009)), out(8.0, 450.0), 0, True, (0.8, 1.3))
    scatter("FarBoulder", boulders, (r[0], r[1], int(ring_area * 0.00025)), out(12.0, 450.0), 0, True, (0.7, 1.6))
    scatter("FarLog", logs, (r[0], r[1], int(ring_area * 0.0002)), out(4.0, 450.0), 30000, True, (0.8, 1.2))

    upgrade_dressing()
    cover(starts, objectives, dressing)
    # Creek pools removed: the pack water read as a glossy orange strip on the banks (producer screenshots).
    quarry_dressing(objectives, dressing)

    saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
    step("saved", saved)


try:
    main()
    report["ok"] = all(s["ok"] for s in report["steps"])
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[ExpandDryRiver] ok={}".format(report["ok"]))
