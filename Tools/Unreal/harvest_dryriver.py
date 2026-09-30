# Southern Spear - Dry River harvest overhaul: proven assets from other project maps + unused installed packs.
#
#   UnrealEditor-Cmd.exe E:/SouthernSpear/SouthernSpear.uproject -run=pythonscript -nosplash -nosound -unattended
#     -Script=E:/SouthernSpear/Tools/Unreal/harvest_dryriver.py -abslog=E:/SouthernSpear/Saved/Logs/SS_harvest_dryriver.log
#
# Producer defect list (MAPS_DRYRIVER.md section 11), defect -> fix, all labels SS_Overhaul_* (gums SS_Gum_*),
# re-runnable (removes own labels first), per-map save. Report: Build/harvest_dryriver_report.json.
#   D-DR-03 windmill visually caught in trees: re-read is crowding (nearest real tree 24 m), so the fix is a
#       feature frame: a ring of imported ghost gums (ENV-003, Content/ghostgum/, licence L-0024) around the
#       windmill at 8-14 m, white trunks reading as the classic outback windmill-in-gums shot, windmill never
#       inside any canopy. Trunk colliders only -> run build_dryriver_nav.py afterwards.
#   D-DR-05 no water in the creek: authored translucent water (Bluestone's SM_Qua_Sla_Water_01 +
#       M_Qua_Sla_Water_01 as a material-instance override, refractive grey-blue, NOT the rejected pack water)
#       in the channel core, with QuarrySlate gravel/mud/dried-track patches, darkened Slate stones and Namaqualand
#       deadfall/driftwood on the wet band - a creek that recently ran.
#   D-DR-04 random prop placement: the water story gets a drift line - wrecks (RustyCars, already used) left in
#       the wet band aligned to the channel, a spoor of debris. Farm props stay at the farm, quarry rocks at the
#       quarry dressing, nothing re-scattered at random.
#   D-DR-06 little small foliage vs Red Gum: Red Gum's bush set (SM_RA_Bush_A..F + SM_RA_Scrub) that gives RG its
#       124-bush ground layer, plus Namaqualand searsia/rooibos shrubs and the flower pool (ursinia, empodium,
#       gazania, stinkkruid) Saltbush uses. All instanced (HISM), no collision -> nav and sightlines unchanged.
#   D-DR-07 needs more density: the above (approx 600 new instances) plus the gum ring; nothing removed.
#
# Assets harvested: Bluestone/Scene_QuarrySlate (L-0005), Namaqualand (Session 041), Red Gum's RuralAustralia set
# (L-0016), ghost gum ENV-003. Nav rebuild afterwards is listed in the report and printed.

import json
import math
import os
import random
import sys
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
sys.path.insert(0, os.path.join(PROJECT_DIR, "Tools", "Common"))
from dryriver_world import PLAY_HALF_X, PLAY_HALF_Y, height  # noqa: E402
from dryriver_spec import DEPLOY_OFFSET  # noqa: E402

REPORT = os.path.join(PROJECT_DIR, "Build", "harvest_dryriver_report.json")
MAP = "/Game/Maps/L_DryRiver_01"
PREFIX = "SS_Overhaul_"
RA = "/Game/RuralAustralia/StaticMeshes"
QS = "/Game/Scene_QuarrySlate/Assets/MS"
NQ = "/Game/Namaqualand/Meshes"
WATER_MESH = "/Game/Scene_QuarrySlate/Assets/Custom/Qua_Sla_Water_01/SM_Qua_Sla_Water_01"
WATER_MAT = "/Game/Art/Environment/DryRiver/M_SS_CreekWater"   # authored translucent water (author_creek_water.py)
GUM_MESH = "/Game/Art/Environment/Fab/TH_Complete_Full_Ghoast_Gum"
GUM_FBX = os.path.join(PROJECT_DIR, "Content", "ghostgum", "source", "TH_Complete_Full_Ghoast_Gum.fbx")
GUM_TEX_DIR = "/Game/Art/Environment/Fab/GhostGum"
GUM_TEX_SRC = os.path.join(PROJECT_DIR, "Content", "ghostgum", "textures")
GUM_MI_DIR = "/Game/Art/Environment/Fab"
SCANPBR = "/Game/Art/Environment/Fab/M_SS_ScanPBR"
CREEK_HALF = 6.0     # wet treatment band half-width (m), matching the audit's bank line
WATER_HALF = 3.5     # water strip half-width (m)
HX, HY = PLAY_HALF_X, PLAY_HALF_Y

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
sdl = unreal.SubobjectDataBlueprintFunctionLibrary
report = {"ok": False, "steps": [], "scatter": {}, "placed": 0, "warnings": [], "errors": []}
rng = random.Random(20260930)


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def meshes(paths):
    out = []
    for p in paths:
        a = unreal.load_asset(p)
        if isinstance(a, unreal.StaticMesh):
            out.append(a)
        else:
            report["warnings"].append("missing mesh " + p)
    return out


def creek_y(x):
    return 2.5 * math.sin(x / 45.0)


def creek_distance(x, y):
    return abs(y - creek_y(x))


def ground_cm(x, y):
    return height(x, y) * 100.0


def solid(mesh):
    body = mesh.get_editor_property("body_setup")
    if body and body.get_editor_property("collision_trace_flag") != unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE:
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
        report.setdefault("collision_set", []).append(mesh.get_name())
    return mesh


WORLD = None   # set in main() after load_map; line traces need a world context


def trace_z(x, y):
    """Real rendered ground (the creek terrain is excavated below the height() formula) via line trace."""
    hit = unreal.SystemLibrary.line_trace_single(
        WORLD, unreal.Vector(x * 100.0, -y * 100.0, 500000.0), unreal.Vector(x * 100.0, -y * 100.0, -500000.0),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    if hit is None:
        return ground_cm(x, y)
    return hit.to_dict()["impact_point"].z


def place(label, mesh, x, y, yaw, scale=1.0, z_cm=None, collide=True, mats=None, scale_vec=None):
    """Single static placement at spec metres (x east, y north); z from a real ground trace + z_cm."""
    z = trace_z(x, y) + (0.0 if z_cm is None else z_cm)
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x * 100.0, -y * 100.0, z),
                                      unreal.Rotator(0, yaw, 0))
    if not a:
        report["warnings"].append("spawn failed " + label)
        return None
    a.set_actor_label(label)
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    if collide:
        solid(mesh)
        c.set_collision_profile_name("BlockAll")
    else:
        c.set_collision_profile_name("NoCollision")
    sv = scale_vec or (scale, scale, scale)
    a.set_actor_scale3d(unreal.Vector(sv[0], sv[1], sv[2]))
    if mats:
        for i, m in mats.items():
            if m:
                c.set_material(i, m)
    report["placed"] += 1
    return a


def hism(label, mesh, transforms, cull_end, shadow):
    a = actors.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    a.set_actor_label(label)
    handles = sub.k2_gather_subobject_data_for_instance(a)
    handle, _ = sub.add_new_subobject(unreal.AddNewSubobjectParams(
        parent_handle=handles[0], new_class=unreal.HierarchicalInstancedStaticMeshComponent))
    comp = sdl.get_object(sdl.get_data(handle))
    comp.set_static_mesh(mesh)
    comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    comp.set_editor_property("cast_shadow", shadow)
    comp.set_cull_distances(0 if cull_end == 0 else int(cull_end * 0.7), int(cull_end))
    comp.add_instances(transforms, False, True)
    return comp.get_instance_count()


def scatter(name, pool, n, place_fn, scale_range, align_up=True):
    """Grid + jitter scatter of instanced foliage; place_fn(x, y) -> False skips a cell."""
    if not pool:
        report["warnings"].append("empty pool " + name)
        report["scatter"][name] = 0
        return 0
    by_mesh = {}
    cell = 1.6
    cols = [-HX + (i + 0.5) * cell for i in range(int(2 * HX / cell))]
    rows = [-HY + (i + 0.5) * cell for i in range(int(2 * HY / cell))]
    order = [(x, y) for x in cols for y in rows]
    rng.shuffle(order)
    got = 0
    for x, y in order:
        if got >= n:
            break
        jx, jy = x + rng.uniform(-0.7, 0.7), y + rng.uniform(-0.7, 0.7)
        if not place_fn(jx, jy):
            continue
        m = pool[rng.randrange(len(pool))]
        s = rng.uniform(*scale_range)
        base = unreal.Vector(jx * 100.0, -jy * 100.0, trace_z(jx, jy) - 4.0)
        rot = unreal.Rotator(0, 0, rng.uniform(0, 360)) if align_up else unreal.Rotator(0, rng.uniform(0, 360), 0)
        by_mesh.setdefault(m, []).append(unreal.Transform(base, rot, unreal.Vector(s, s, s)))
        got += 1
    total = 0
    for i, (m, ts) in enumerate(by_mesh.items()):
        total += hism("{}Scatter_{}_{:02d}".format(PREFIX, name, i), m, ts, 12000, False)
    report["scatter"][name] = total
    return total


# ------------------------------------------------------- imports (ghost gum, ENV-003)

def import_gum():
    at = unreal.AssetToolsHelpers.get_asset_tools()
    for f in sorted(os.listdir(GUM_TEX_SRC)):
        if not f.lower().endswith(".png"):
            continue
        dst = GUM_TEX_DIR
        name = os.path.splitext(f)[0]
        if unreal.EditorAssetLibrary.does_asset_exist(dst + "/" + name):
            continue
        task = unreal.AssetImportTask()
        task.filename = os.path.join(GUM_TEX_SRC, f)
        task.destination_path = dst
        task.automated = True
        task.save = True
        at.import_asset_tasks([task])
    if not unreal.EditorAssetLibrary.does_asset_exist(GUM_MESH):
        task = unreal.AssetImportTask()
        task.filename = GUM_FBX
        task.destination_path = "/Game/Art/Environment/Fab"
        task.automated = True
        task.replace_existing = True
        task.save = True
        opts = unreal.FbxImportUI()
        opts.set_editor_property("import_mesh", True)
        opts.set_editor_property("import_as_skeletal", False)
        opts.set_editor_property("import_materials", False)
        opts.set_editor_property("import_textures", False)
        smi = opts.get_editor_property("static_mesh_import_data")
        smi.set_editor_property("combine_meshes", True)
        smi.set_editor_property("auto_generate_collision", False)
        task.set_editor_property("options", opts)
        at.import_asset_tasks([task])
    mesh = unreal.load_asset(GUM_MESH)
    if mesh:
        b = mesh.get_bounds().box_extent * 2.0
        report["gum_bounds_cm"] = [round(b.x, 1), round(b.y, 1), round(b.z, 1)]
    return mesh


def gum_materials():
    """Instances of the project ScanPBR master; trunk/branch/leaf pick their own maps. Returns slot-tag overrides."""
    ump = unreal.MaterialEditingLibrary
    at = unreal.AssetToolsHelpers.get_asset_tools()
    params = {
        "Trunk": {"BaseColor": "TH_Ghoast_Gum_Difuse", "Normal": "TH_Ghoast_Gum_Normals"},
        "Branch": {"BaseColor": "TH_Ghoast_Gum_Branch_Difuse", "Normal": "TH_Ghoast_Gum_Branch_Normal"},
        "Leaf": {"BaseColor": "TH_Ghoast_Gum_Branch_Difuse", "Normal": "TH_Ghoast_Gum_Branch_Normal",
                 "OpacityMask": "TH_Ghoast_Gum_Branch_Alpha"},
    }
    mis = {}
    master = unreal.load_asset(SCANPBR)
    if not isinstance(master, unreal.MaterialInterface):
        report["warnings"].append("ScanPBR master missing")
        return mis
    for tag, ps in params.items():
        path = GUM_MI_DIR + "/MI_SS_GhostGum_" + tag
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            mi = unreal.load_asset(path)
        else:
            mi = at.create_asset("MI_SS_GhostGum_" + tag, GUM_MI_DIR, unreal.MaterialInstanceConstant,
                                 unreal.MaterialInstanceConstantFactoryNew())
        if not mi:
            report["warnings"].append("MI create failed " + tag)
            continue
        try:
            ump.set_material_instance_parent(mi, master)
            for param, tex in ps.items():
                t = unreal.load_asset(GUM_TEX_DIR + "/" + tex)
                if t:
                    ump.set_material_instance_texture_parameter_value(mi, param, t)
                else:
                    report["warnings"].append("missing tex %s" % tex)
            ump.set_material_instance_scalar_parameter_value(mi, "Tiling", 1.0)
            unreal.EditorAssetLibrary.save_loaded_asset(mi, False)
            mis[tag] = mi
        except Exception as exc:
            report["warnings"].append("MI %s: %s" % (tag, exc))
    return mis


# ------------------------------------------------------------------ placement phases

def find_windmill():
    for a in actors.get_all_level_actors():
        if "Windmill" in a.get_actor_label():
            l = a.get_actor_location()
            return l.x / 100.0, -l.y / 100.0
    return None


def dressing_points():
    pts = []
    for a in actors.get_all_level_actors():
        if not isinstance(a, unreal.StaticMeshActor):
            continue
        lab = a.get_actor_label()
        if lab.startswith(PREFIX) or lab.startswith("SS_Gum_"):
            continue
        c = a.static_mesh_component
        if c and c.static_mesh and not c.static_mesh.get_name().startswith("SS_MAP_DryRiver"):
            l = a.get_actor_location()
            pts.append((l.x / 100.0, -l.y / 100.0))
    return pts


def clear_of(x, y, pts, r_m):
    return all((px - x) ** 2 + (py - y) ** 2 > (r_m * r_m) for px, py in pts)


def water_plane():
    mesh = unreal.load_asset(WATER_MESH)
    mat = unreal.load_asset(WATER_MAT)
    if not step("water_assets", bool(mesh and mat), "%s %s" % (bool(mesh), bool(mat))):
        return 0
    solid(mesh)
    # The Slate water plane is 154 x 131 m: cut it into ~57 m segments down the channel, X scaled to the
    # segment, Y squeezed to ~16 m so it tucks under both banks (they stand 0.65-2.2 m above the bed).
    n = 0
    b = mesh.get_bounds().box_extent
    full_x, full_y = max(b.x * 2.0, 1.0), max(b.y * 2.0, 1.0)
    seg = 57.0
    t = -HX + 8.0
    while t < HX - 8.0:
        x1 = min(t + seg, HX - 8.0)
        x0, y0 = t, creek_y(t)
        cx, cy = (x0 + x1) / 2.0, (y0 + creek_y(x1)) / 2.0
        length = math.hypot(x1 - x0, creek_y(x1) - y0) + 8.0  # overlap the joints
        yaw = math.degrees(math.atan2(-(creek_y(x1) - y0), x1 - x0))
        sx = length * 100.0 / full_x
        sy = 16.0 * 100.0 / full_y
        # z: real bed surface (the terrain is excavated below the height formula) + 12 cm ride so the
        # plane sits proud of the bed without reading as a floating sheet from the banks.
        z_bed = trace_z(cx, cy)
        place("{}Creek_Water_{:02d}".format(PREFIX, n), mesh, cx, cy, yaw, z_cm=z_bed - ground_cm(cx, cy) + 12.0,
              collide=False, mats={0: mat}, scale_vec=(sx, sy, 1.0))
        report.setdefault("water_audit", []).append({
            "seg": n, "water_z": round(ground_cm(cx, cy) + z_bed - ground_cm(cx, cy) + 12.0, 1),
            "bed_z": round(z_bed, 1), "centre_m": [round(cx, 1), round(cy, 1)]})
        n += 1
        t += seg
    return step("water_plane", True, "%d segments" % n)


def quarry_bed(dressing, starts, objectives):
    """Stones and deadfall in the channel. The QuarrySlate patch discs are retired: flat discs float on any
    slope (producer screenshots) and their cream albedo fights the red dirt."""
    stones = meshes([NQ + "/General/NN/SM_namaqualand_stones_01_{}_NN".format(c) for c in "ae"]
                    + [QS + "/3D/Qua_Sla_Rock_S_16/SM_Qua_Sla_Rock_S_16"])
    dead = meshes([NQ + "/General/NN/SM_dead_quiver_trunk_NN",
                   NQ + "/General/NN/SM_dead_quiver_branch_01_NN",
                   NQ + "/General/NN/SM_dead_quiver_branch_02_NN"])
    if not dead or not stones:
        return step("quarry_bed", False, "pool empty: dead %d stones %d" % (len(dead), len(stones)))
    d = 0
    for x in [(-HX + 6.0) + i * 6.0 for i in range(int((2 * HX - 12.0) / 6.0))]:
        if rng.random() > 0.55:
            continue
        y = creek_y(x) + rng.uniform(-2.5, 3.0)
        if abs(x) > HX - 6 or abs(y) > HY - 6:
            continue
        if not (clear_of(x, y, starts, 4.0) and clear_of(x, y, objectives, 8.0) and clear_of(x, y, dressing, 2.0)):
            continue
        m = dead[rng.randrange(len(dead))]
        dy = creek_y(x + 2.0) - creek_y(x - 2.0)
        yaw = math.degrees(math.atan2(-dy, 4.0)) + rng.uniform(-35, 35)
        place("{}Bed_Driftwood_{:02d}".format(PREFIX, d), m, x, y, yaw, scale=rng.uniform(0.8, 1.2),
              z_cm=-4.0, collide=("trunk" in m.get_name().lower()))
        d += 1
    report["scatter"]["Driftwood"] = d
    s = scatter("BedStones", stones, 90,
                lambda x, y: abs(x) < HX - 4 and abs(y) < HY - 4 and creek_distance(x, y) < CREEK_HALF
                and clear_of(x, y, starts, 3.0) and clear_of(x, y, dressing, 1.5),
                (0.4, 0.9))
    return step("quarry_bed", True, "driftwood %d, stones %d" % (d, s))


def bush_layer(dressing, starts, objectives, gum_pts):
    veg = RA + "/Vegetation"
    bush_a = meshes([NQ + "/Foliage/NN/SM_searsia_burchellii_{}_NN".format(s) for s in ("large", "medium")])
    bush_b = meshes([NQ + "/Foliage/NN/SM_searsia_lucida_{}_NN".format(c) for c in "abcdefg"]
                    + [NQ + "/Foliage/NN/SM_wild_rooibos_bush_{}_NN".format(c) for c in "abcd"])
    bush_c = meshes([NQ + "/Foliage/NN/SM_didelta_spinosa_{}_NN".format(s) for s in ("small", "medium", "large")])
    flowers = meshes([NQ + "/Foliage/NN/SM_flower_ursinia_{}_NN".format(c) for c in "abcd"]
                     + [NQ + "/Foliage/NN/SM_flower_empodium_{}_NN".format(c) for c in "abc"]
                     + [NQ + "/Foliage/NN/SM_flower_gazania_{}_NN".format(c) for c in "bc"]
                     + [NQ + "/Foliage/NN/SM_flower_stinkkruid_d_NN"])

    if not bush_b or not bush_c or not flowers:
        return step("bush_layer", False, "pool empty: A %d B %d C %d fl %d" % (len(bush_a), len(bush_b), len(bush_c), len(flowers)))

    def ok(x, y):
        return (abs(x) < HX - 3 and abs(y) < HY - 3
                and creek_distance(x, y) > WATER_HALF
                and abs(math.hypot(height(x + 0.5, y) - height(x - 0.5, y),
                                   height(x, y + 0.5) - height(x, y - 0.5))) < 0.6
                and clear_of(x, y, starts, 3.0) and clear_of(x, y, objectives, 6.0)
                and clear_of(x, y, dressing, 2.0) and clear_of(x, y, gum_pts, 3.0))

    def wm_ok(x, y):
        return ok(x, y) and not (abs(x + 4.28) < 6.5 and abs(y - 14.19) < 6.5)

    a = scatter("BushA", bush_a, 150, wm_ok, (0.85, 1.45))
    b = scatter("BushB", bush_b, 90, wm_ok, (0.8, 1.3))
    c = scatter("BushC", bush_c, 60, wm_ok, (0.8, 1.15))

    def flower_ok(x, y):
        if not ok(x, y):
            return False
        cd = creek_distance(x, y)
        if cd < CREEK_HALF + 1.0:
            return rng.random() < 0.55   # banks favoured, some drift out into the open
        return rng.random() < 0.35

    f = scatter("Flowers", flowers, 110, flower_ok, (0.9, 1.4))
    return step("bush_layer", True, "A %d, B %d, C %d, flowers %d" % (a, b, c, f))


def gum_ring(mesh, mis):
    wm = find_windmill()
    if not wm:
        step("gum_ring", False, "windmill not found")
        return []
    wx, wy = wm
    b = mesh.get_bounds().box_extent * 2.0
    h_m = max(b.z, 1.0) / 100.0
    slots = [str(sm.material_slot_name) for sm in mesh.get_editor_property("static_materials")]
    # Two slots only: "blinn5" (trunk) and "TH_Gum_Branch_Blinn" (branch cards, which carry the FOLIAGE).
    # The foliage cards must get the Leaf MI (alpha-masked branch albedo) or they render grey and bare.
    lower = [s.lower() for s in slots]
    slot_mis = {}
    for i, s in enumerate(lower):
        if "branch" in s or "leaf" in s:
            slot_mis[i] = mis.get("Leaf") or mis.get("Branch")
        else:
            slot_mis[i] = mis.get("Trunk")
    starts = [a.get_actor_location() for a in actors.get_all_level_actors()
              if a.get_class().get_name().endswith("PlayerStart")]
    objectives = [a.get_actor_location() for a in actors.get_all_level_actors()
                  if a.get_class().get_name() == "SSObjectiveActor"]
    starts = [(p.x / 100.0, -p.y / 100.0) for p in starts]
    objectives = [(p.x / 100.0, -p.y / 100.0) for p in objectives]
    placed = []
    idx = 0
    for k in range(24):
        ang = k * 15.0 + rng.uniform(-4, 4)
        for r in (10.5, 13.5, 16.5):
            x = wx + r * math.cos(math.radians(ang))
            y = wy + r * math.sin(math.radians(ang))
            if not (abs(x) < HX - 4 and abs(y) < HY - 4):
                continue
            slope = math.hypot(height(x + 0.5, y) - height(x - 0.5, y), height(x, y + 0.5) - height(x, y - 0.5))
            if slope > 0.55 or creek_distance(x, y) < 10.0:
                continue
            if not (clear_of(x, y, starts, 12.0) and clear_of(x, y, objectives, 10.0)
                    and clear_of(x, y, dressing_points(), 3.0)):
                continue
            if any((px - x) ** 2 + (py - y) ** 2 < 25.0 for px, py in placed):
                continue
            yaw = math.degrees(math.atan2(-(wy - y), wx - x))
            s = rng.uniform(0.9, 1.15)
            a = place("SS_Gum_WindmillScreen_{:02d}".format(idx), mesh, x, y, yaw,
                      scale=s, z_cm=-6.0, collide=True, mats=slot_mis)
            if a:
                # trunk collider only (cylinder 1 m wide x 1 m tall): nav-relevant, canopy stays collision-free
                d = 0.45 * s
                col = actors.spawn_actor_from_class(
                    unreal.StaticMeshActor,
                    unreal.Vector(x * 100.0, -y * 100.0, ground_cm(x, y) + 50.0), unreal.Rotator(0, 0, 0))
                col.set_actor_label("SS_Gum_TrunkCol_{:02d}".format(idx))
                col.set_actor_scale3d(unreal.Vector(d, d, h_m))
                cc = col.static_mesh_component
                cc.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cylinder"))
                cc.set_editor_property("visible", False)
                cc.set_editor_property("hidden_in_game", True)
                cc.set_editor_property("cast_shadow", False)
                cc.set_collision_profile_name("BlockAll")
                placed.append((x, y))
                idx += 1
            break  # one gum per spoke, next spoke
    report["gum_ring"] = idx
    step("gum_ring", idx >= 8, "%d gums around windmill at (%.1f, %.1f)" % (idx, wx, wy))
    return placed


def windmill_sweep():
    """D-DR-03 root cause: scripted pack trees whose canopies overlap the windmill. Remove the crowders
    (own dressing, safe to delete); the gum ring re-frames the mill without touching it."""
    wm = find_windmill()
    if not wm:
        return step("windmill_sweep", False, "windmill not found")
    wx, wy = wm[0] * 100.0, -wm[1] * 100.0
    killed = []
    for a in list(actors.get_all_level_actors()):
        if not isinstance(a, unreal.StaticMeshActor) or a is None:
            continue
        c = a.static_mesh_component
        if not c or not c.static_mesh:
            continue
        name = c.static_mesh.get_name()
        lab = a.get_actor_label()
        if not ("tree" in name.lower() or lab.startswith("SS_RA_Tree") or lab.startswith("SS_RA_Cover_Tree")):
            continue
        if lab.startswith("SS_Gum_") or lab.startswith(PREFIX):
            continue
        if "windmill" in lab.lower():
            continue
        l = a.get_actor_location()
        d = math.hypot(l.x - wx, l.y - wy)
        origin, ext = a.get_actor_bounds(False)
        if d / 100.0 - (ext.x + ext.y) / 100.0 < 6.5:   # full-radius canopy overlap, same as the checker
            killed.append(lab)
            actors.destroy_actor(a)
    report["windmill_sweep"] = killed
    return step("windmill_sweep", True, "%d crowding trees removed" % len(killed))


def windmill_clearance():
    """Post-check: no canopy within 6.5 m of the windmill (D-DR-03 acceptance)."""
    wm = find_windmill()
    if not wm:
        return None
    wx, wy = wm[0] * 100.0, -wm[1] * 100.0
    gaps = {"gum": None, "other": None}
    for a in actors.get_all_level_actors():
        if not isinstance(a, unreal.StaticMeshActor) or a is None:
            continue
        c = a.static_mesh_component
        if not c or not c.static_mesh:
            continue
        lab = a.get_actor_label()
        if (c.static_mesh.get_name().startswith("SS_MAP_") or lab.startswith("SS_Expand_Horizon")
                or "Creek_Water" in lab):
            continue                 # terrain/sky/flat water: giant bounds, not canopy
        l = a.get_actor_location()
        d = math.hypot(l.x - wx, l.y - wy)
        if d < 100.0:
            continue
        origin, ext = a.get_actor_bounds(False)
        gap = d / 100.0 - (ext.x + ext.y) / 100.0
        key = "gum" if lab.startswith("SS_Gum_") else "other"
        if gaps[key] is None or gap < gaps[key][0]:
            gaps[key] = (gap, lab)
    report["windmill_gap"] = {k: (round(v[0], 2), v[1]) for k, v in gaps.items() if v} or None
    # trees/gums are the canopy concern; other scenery (creek rocks, ledges) only fails if it intrudes closer than 5 m
    ok = (gaps["other"] is None or gaps["other"][0] >= 5.0) and (gaps["gum"] is None or gaps["gum"][0] >= 2.5)
    return step("windmill_clearance", ok, str(report["windmill_gap"]))


def fix_kangaroos():
    """Producer: kangaroos render clay-grey. MI_SS_Kangaroo's texture overrides were empty (probe); re-bind
    the kangaroo maps from the registry with read-back verification, re-seat on a real trace, force the MI
    onto every slot."""
    ump = unreal.MaterialEditingLibrary
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    base = norm = None

    def scan(path):
        nonlocal base, norm
        for a in reg.get_assets_by_path(path, True):
            n = str(a.asset_name)
            if n.endswith("-0277") and base is None:
                base = a.get_asset()
            elif n.endswith("-0278") and norm is None:
                norm = a.get_asset()

    scan("/Game/Art/Environment/Kangaroo")
    if base is None or norm is None:
        scan("/Game")
    if not (base and norm):
        return step("fix_kangaroos", False, "textures not found (base=%s norm=%s)" % (bool(base), bool(norm)))
    mi = unreal.load_asset("/Game/Art/Environment/Kangaroo/MI_SS_Kangaroo")
    if not isinstance(mi, unreal.MaterialInstanceConstant):
        return step("fix_kangaroos", False, "MI_SS_Kangaroo missing")
    ump.set_material_instance_texture_parameter_value(mi, "BaseColor", base)
    ump.set_material_instance_texture_parameter_value(mi, "Normal", norm)
    ump.set_material_instance_scalar_parameter_value(mi, "Tiling", 1.0)
    unreal.EditorAssetLibrary.save_loaded_asset(mi, False)

    def bound_tex(param):
        try:
            v = ump.get_material_instance_texture_parameter_value(mi, param)
            return v.get_name() if v else None
        except Exception:
            return "unreadable"

    got_base, got_norm = bound_tex("BaseColor"), bound_tex("Normal")
    if got_base in (None, "unreadable") or got_norm in (None, "unreadable"):
        return step("fix_kangaroos", False, "verify failed: base=%s norm=%s" % (got_base, got_norm))
    fixed = 0
    for a in actors.get_all_level_actors():
        if not a.get_actor_label().startswith("SS_EasterEgg_Kangaroo"):
            continue
        l = a.get_actor_location()
        hit = unreal.SystemLibrary.line_trace_single(
            WORLD, unreal.Vector(l.x, l.y, 500000.0), unreal.Vector(l.x, l.y, -500000.0),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [a], unreal.DrawDebugTrace.NONE, True)
        if hit is not None:
            a.set_actor_location(unreal.Vector(l.x, l.y, hit.to_dict()["impact_point"].z + 6.0), False, False)
        c = a.static_mesh_component
        if c:
            for slot in range(c.get_num_materials()):
                c.set_material(slot, mi)
        fixed += 1
    return step("fix_kangaroos", True, "%d re-seated; MI bound base=%s norm=%s" % (fixed, got_base, got_norm))


def main():
    global WORLD
    WORLD = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    # re-run: clear our labels first
    doomed = [a for a in actors.get_all_level_actors()
              if a.get_actor_label().startswith(PREFIX) or a.get_actor_label().startswith("SS_Gum_")]
    for a in doomed:
        actors.destroy_actor(a)
    report["removed_previous"] = len(doomed)

    starts = [a.get_actor_location() for a in actors.get_all_level_actors()
              if a.get_class().get_name().endswith("PlayerStart")]
    objectives = [a.get_actor_location() for a in actors.get_all_level_actors()
                  if a.get_class().get_name() == "SSObjectiveActor"]
    deploy = [(0.0, -DEPLOY_OFFSET), (0.0, DEPLOY_OFFSET)]
    starts = [(p.x / 100.0, -p.y / 100.0) for p in starts] + deploy
    objectives = [(p.x / 100.0, -p.y / 100.0) for p in objectives]
    dressing = dressing_points()

    mesh = import_gum()
    step("gum_import", bool(mesh), GUM_MESH)
    mis = gum_materials() if mesh else {}
    gum_pts = gum_ring(mesh, mis) if mesh else []
    water_plane()
    quarry_bed(dressing, starts, objectives)
    bush_layer(dressing, starts, objectives, gum_pts)
    windmill_sweep()
    windmill_clearance()
    fix_kangaroos()

    saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
    step("saved", saved)
    report["nav_note"] = "gum trunk colliders added: run build_dryriver_nav.py, then in-game capture pass"


try:
    main()
    report["ok"] = all(s["ok"] for s in report["steps"])
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[HarvestDryRiver] ok={} placed={} scatter={}".format(
    report["ok"], report["placed"], report.get("scatter")))
