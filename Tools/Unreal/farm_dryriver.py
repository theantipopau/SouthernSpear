# Southern Spear - Dry River farm pass: real props in place of blockout shapes, and a working station.
#
#   UnrealEditor-Cmd ... -ExecutePythonScript=E:/SouthernSpear/Tools/Unreal/farm_dryriver.py
#   (after expand_dryriver.py; then build_dryriver_nav.py)
#
# Producer (Session 045): "replace the 'cars' that were just boxes with actual cars from the new assets, add
# barns, the windmill, wells etc - give it more life."
#   1. Every blockout wreck (SS_Dressing_Wreck, a box) becomes the Fab car wreck (SS_Raven_WreckCar), same
#      place and heading, sat on the ground, collision on (it was cover and stays cover).
#   2. Water Point objective: a windmill and a water tower beside it, a hand pump (the well) at its edge.
#   3. Farmstead objective: two barns and a hand pump.
#   4. Fuel drums in small clusters beside the sheds and barns.
# All new actors are labelled SS_Farm_* and replaced on every run. The props are the Ravenshoe agent's prepared
# meshes and materials (/Game/Art/Environment/Ravenshoe/Props, Materials: measured, rescaled, decimated by
# Tools/Blender/prep_fab_props.py). Fab, cleared under ADR-028; seller AI flags recorded in ADR-029.
# Report: Build/farm_dryriver_report.json.

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
from dryriver_world import PLAY_HALF_X, PLAY_HALF_Y, height  # noqa: E402

REPORT = os.path.join(PROJECT_DIR, "Build", "farm_dryriver_report.json")
MAP = "/Game/Maps/L_DryRiver_01"
PREFIX = "SS_Farm_"
PROPS = "/Game/Art/Environment/Ravenshoe/Props/"
MATS = "/Game/Art/Environment/Ravenshoe/Materials/"
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
report = {"ok": False, "steps": [], "placed": [], "errors": []}
rng = random.Random(20260929)


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def creek_distance(x, y):
    return abs(y - 2.5 * math.sin(x / 45.0))


def load(path):
    a = unreal.load_asset(path)
    if a is None:
        report["errors"].append("missing " + path)
    return a


def ground_cm(x, y, r):
    """Lowest ground under a footprint of radius r (m), so nothing floats on a slope."""
    hs = [height(x + dx, y + dy) for dx in (-r, 0.0, r) for dy in (-r, 0.0, r)]
    return min(hs) * 100.0


def flatness(x, y, r):
    hs = [height(x + dx, y + dy) for dx in (-r, 0.0, r) for dy in (-r, 0.0, r)]
    return max(hs) - min(hs)


def footprint_m(mesh, scale=1.0):
    e = mesh.get_bounds().box_extent
    return max(e.x, e.y) * scale / 100.0


# ----------------------------------------------------------------------------- textures (producer: "all of these have
# no textures on them and look strange"). The Ravenshoe prep gave every prop one flat tinted instance. Four of the
# Fab downloads (windmill, barn, old barn, fuel barrel) shipped their FBX without the texture files it references,
# so those take tileable textured materials from the Modular Rural Cabin pack slot by slot (timber, rusted and
# galvanised iron). The hand pump's textures are embedded in its FBX (Tools/Blender/extract_fab_textures.py ->
# Build/farm_tex/pump); the water tower ships its PNGs. Both get instances of M_SS_ScanPBR with their own maps.
FARM_DEST = "/Game/Art/Environment/DryRiver/Farm"
SCAN_PBR = "/Game/Art/Environment/Fab/M_SS_ScanPBR"
CABIN = "/Game/Modular_Rural_Cabin/Materials/Instances/"
FAB = os.path.join(PROJECT_DIR, "Content", "Downloaded", "VaultCache", "FabLibrary")
TOWER_TEX = os.path.join(FAB, "Water_Tower-86b17984", "fbx", "water-tower_extracted", "source", "Water_tower_extracted",
                         "Water_tower", "Textures")
PUMP_TEX = os.path.join(PROJECT_DIR, "Build", "farm_tex", "pump")
MAPS = {  # file suffix -> (M_SS_ScanPBR parameter, compression, sRGB)
    "BaseColor": ("BaseColor", unreal.TextureCompressionSettings.TC_DEFAULT, True),
    "Normal": ("Normal", unreal.TextureCompressionSettings.TC_NORMALMAP, False),
    "Roughness": ("Roughness", unreal.TextureCompressionSettings.TC_MASKS, False),
    "Metallic": ("Metalness", unreal.TextureCompressionSettings.TC_MASKS, False),
}


def import_texture(path, compression, srgb):
    name = "T_SS_Farm_" + os.path.splitext(os.path.basename(path))[0]
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", path)
    task.set_editor_property("destination_path", FARM_DEST + "/Textures")
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = unreal.load_asset(FARM_DEST + "/Textures/" + name)
    if tex:
        tex.set_editor_property("compression_settings", compression)
        tex.set_editor_property("srgb", srgb)
        unreal.EditorAssetLibrary.save_loaded_asset(tex, False)
    return tex


def own_material(name, folder, prefix):
    """MI_SS_Farm_<name>: M_SS_ScanPBR with the pack's own maps <folder>/<prefix><Suffix>.png."""
    master = load(SCAN_PBR)
    if not master or not os.path.isdir(folder):
        report["errors"].append("own_material {}: master or {} missing".format(name, folder))
        return None
    path = FARM_DEST + "/MI_SS_Farm_" + name
    mi = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else \
        unreal.AssetToolsHelpers.get_asset_tools().create_asset("MI_SS_Farm_" + name, FARM_DEST, unreal.MaterialInstanceConstant,
                                                                unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", master)
    got = []
    for suffix, (param, compression, srgb) in MAPS.items():
        f = os.path.join(folder, prefix + suffix + ".png")
        if os.path.exists(f):
            tex = import_texture(f, compression, srgb)
            if tex:
                unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, param, tex)
                got.append(suffix)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "Tiling", 1.0)
    unreal.EditorAssetLibrary.save_loaded_asset(mi, False)
    report.setdefault("own_materials", {})[name] = got
    return mi


def slot_materials():
    """Mesh name -> {slot: material}. Slots not listed keep the first entry's material ('*')."""
    c = lambda n: load(CABIN + n)
    rust, galv = c("Rust_Generic"), c("Metal_Generic")
    # Timber and roofing iron: the Dry River shelters' own (expand_dryriver SHELTER_MATS). The Modular Cabin's
    # Side_Shed_Wood / Rust_Roof came out green and blotchy on these barns (producer screenshot): they are tuned to
    # that pack's own meshes.
    timber = load("/Game/Singapore_Canal/Materials/MI_WoodOldRaw_01")
    roof = load("/Game/Art/Environment/Fab/CorrugatedIron/MI_SS_CorrugatedIron")
    planks = timber
    return {
        "SS_Raven_windmill": {"*": galv, "T_WindMill_Planks": planks, "T_WM_Planks_Base": planks,
                              "T_WM_Wings": rust, "T_WM_Wings_Structure": rust, "T_WM_Hub": rust, "T_WM_Nose_Cone": rust,
                              "T_Wind_Mill_Arrow": rust, "T_WM_Arrow_Base": rust},
        "SS_Raven_barn": {"*": timber, "roof": roof},
        "SS_Raven_old_barn": {"*": timber, "Metal": roof},
        "SS_Raven_hand_pump": {"*": own_material("PumpBody", PUMP_TEX, "kol_body_"),
                               "PWE": own_material("PumpSpout", PUMP_TEX, "koler_mukh_")},
        "SS_Raven_water_tower": {"*": own_material("WaterTower", TOWER_TEX, "Water_Tower_Water_tower_")},
    }


def apply_slots(actor, mats):
    c = actor.static_mesh_component
    names = [str(s.material_slot_name) for s in c.static_mesh.get_editor_property("static_materials")]
    for i, slot in enumerate(names):
        m = mats.get(slot, mats.get("*"))
        if m:
            c.set_material(i, m)


def place(label, mesh, mat, x, y, yaw, r, collide=True, tilt=0.0):
    """Spec metres; the mesh's base (bounds bottom) on the lowest ground under its footprint. mat: one material
    for every slot, a {slot: material} map, or None to keep the mesh's own."""
    b = mesh.get_bounds()
    base = (b.origin.z - b.box_extent.z)
    z = ground_cm(x, y, max(r * 0.6, 0.3)) - base - 4.0
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x * 100.0, -y * 100.0, z),
                                      unreal.Rotator(roll=tilt, pitch=0, yaw=yaw))
    a.set_actor_label(label)
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    if isinstance(mat, dict):
        apply_slots(a, mat)
    elif mat:
        for i in range(c.get_num_materials()):
            c.set_material(i, mat)
    if collide:
        c.set_collision_profile_name("BlockAll")
    else:
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    report["placed"].append({"label": label, "x": round(x, 1), "y": round(y, 1), "yaw": round(yaw), "r": round(r, 1)})
    return a


def main():
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    step("open_map", world is not None and "DryRiver" in world.get_name(), world.get_name() if world else None)

    removed = 0
    for a in actors.get_all_level_actors():
        if a.get_actor_label().startswith(PREFIX):
            actors.destroy_actor(a)
            removed += 1
    step("cleared_previous", True, removed)

    car = load(PROPS + "SS_Raven_wreck_car")
    barn, old_barn = load(PROPS + "SS_Raven_barn"), load(PROPS + "SS_Raven_old_barn")
    windmill, tower = load(PROPS + "SS_Raven_windmill"), load(PROPS + "SS_Raven_water_tower")
    pump = load(PROPS + "SS_Raven_hand_pump")
    # Fuel drums: the Modular Rural Cabin pack's textured drum (the Fab fuel barrel shipped without textures),
    # its three paint variants.
    drum = load("/Game/Modular_Rural_Cabin/Meshes/Props/Metal_Barrel")
    drum_mats = [load(CABIN + "Metal_Barrel_{}".format(i)) for i in (1, 2, 3)]
    well = load("/Game/StoneWell/Asset/StaticMeshes/SM_Well")                     # the stone well, own materials
    caravan = load("/Game/Modular_Rural_Cabin/Meshes/Props/Caravan")
    outhouse = load("/Game/Modular_Rural_Cabin/Meshes/Props/Outhouse_House")
    m_wreck = load(MATS + "MI_SS_Raven_Wreck")
    slots = slot_materials()
    m_metal = None  # unused: every prop now has its own or a slot map
    m_timber = None
    report["sizes_m"] = {m.get_name(): [round(v / 50.0, 2) for v in (m.get_bounds().box_extent.x, m.get_bounds().box_extent.y,
                                                                     m.get_bounds().box_extent.z)]
                         for m in (car, barn, old_barn, windmill, tower, pump, drum) if m}
    # Pack props collide against their render mesh (several ship without simple collision), as expand_dryriver.solid().
    for m in (drum, well, caravan, outhouse):
        body = m.get_editor_property("body_setup") if m else None
        if body and body.get_editor_property("collision_trace_flag") != unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE:
            body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            unreal.EditorAssetLibrary.save_loaded_asset(m, False)
    if not all((car, barn, old_barn, windmill, tower, pump, drum)):
        step("props", False, "missing props")
        return

    # Keep-clear set: deployments, player starts, and every existing collidable prop (x, y, radius m).
    deploy = [(0.0, -DEPLOY_OFFSET), (0.0, DEPLOY_OFFSET)]
    starts = [(a.get_actor_location().x / 100.0, -a.get_actor_location().y / 100.0)
              for a in actors.get_all_level_actors() if a.get_class().get_name().endswith("PlayerStart")]
    objectives = {}
    for a in actors.get_all_level_actors():
        if a.get_class().get_name() == "SSObjectiveActor":
            name = str(a.get_editor_property("objective_name"))
            objectives[name] = (a.get_actor_location().x / 100.0, -a.get_actor_location().y / 100.0)
    report["objectives"] = objectives
    occupied = []
    for a in actors.get_all_level_actors():
        if not isinstance(a, unreal.StaticMeshActor):
            continue
        m = a.static_mesh_component.static_mesh
        if not m or m.get_name().startswith("SS_MAP_") or a.get_actor_label().startswith("SS_Expand_Skirt") \
                or a.get_actor_label().startswith("SS_Expand_Horizon"):
            continue
        o, e = a.get_actor_bounds(False)
        r = max(e.x, e.y) / 100.0
        if any(k in m.get_name() for k in ("Tree", "Log_", "Scrub", "didelta")):
            # Vegetation bounds are the canopy (20-30 m); only the trunk or log body stands in the way.
            loc = a.get_actor_location()
            o, r = loc, min(r, 2.0)
        occupied.append((o.x / 100.0, -o.y / 100.0, r))

    # 1. Blockout wrecks (boxes) -> the car wreck, at the hand-placed wreck positions of the dressing CSV
    #    (dryriver_dressing.py WRECKS: x, y in spec metres, rot_y the Unreal yaw as dress_dryriver.py spawns it).
    #    Any box still in the level is removed.
    for a in actors.get_all_level_actors():
        if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh \
                and a.static_mesh_component.static_mesh.get_name() == "SS_Dressing_Wreck":
            loc = a.get_actor_location()
            occupied[:] = [p for p in occupied if math.hypot(p[0] - loc.x / 100.0, p[1] + loc.y / 100.0) > 0.5]
            actors.destroy_actor(a)
    swapped = 0
    with open(os.path.join(PROJECT_DIR, "Content", "Art", "Blockout", "SS_MAP_DryRiver_02_Dressing.csv")) as fh:
        rows = [r.strip().split(",") for r in fh.readlines()[1:]]
    for name, kind, x, y, _z, rot, _s in (r for r in rows if len(r) == 7):
        if kind != "wreck":
            continue
        x, y = float(x), float(y)
        place("{}Wreck_{:02d}".format(PREFIX, swapped), car, m_wreck, x, y, float(rot) + rng.uniform(-8, 8), footprint_m(car))
        occupied.append((x, y, footprint_m(car)))
        swapped += 1
    step("wrecks", swapped == 3, "{} car wrecks at the dressing plan's wreck positions".format(swapped))

    def free(x, y, r, gap=2.0):
        if abs(x) > PLAY_HALF_X - r - 4 or abs(y) > PLAY_HALF_Y - r - 4:
            return False
        if creek_distance(x, y) < r + 4.0:
            return False
        if any(math.hypot(x - dx, y - dy) < 45.0 + r for dx, dy in deploy):
            return False
        if any(math.hypot(x - sx, y - sy) < 12.0 + r for sx, sy in starts):
            return False
        if any(math.hypot(x - ox, y - oy) < 7.0 + r for ox, oy in objectives.values()):
            return False
        return all(math.hypot(x - px, y - py) >= pr + r + gap for px, py, pr in occupied)

    def near(centre, lo, hi, r, flat, tries=3000):
        cx, cy = centre
        for _ in range(tries):
            a = rng.uniform(0, math.tau)
            d = rng.uniform(lo, hi)
            x, y = cx + d * math.cos(a), cy + d * math.sin(a)
            if flatness(x, y, r) <= flat and free(x, y, r):
                return x, y
        return None

    def put(tag, mesh, mat, centre, lo, hi, flat, face=True, collide=True):
        r = footprint_m(mesh)
        at = near(centre, lo, hi, r, flat)
        if not at:
            step("place_" + tag, False, "no free spot {}-{} m from {}".format(lo, hi, centre))
            return None
        x, y = at
        # Face the objective (Unreal yaw of the direction back to it), roughly: buildings front the yard.
        yaw = math.degrees(math.atan2(-(centre[1] - y), centre[0] - x)) if face else rng.uniform(0, 360)
        place(PREFIX + tag, mesh, mat, x, y, yaw + rng.uniform(-10, 10), r, collide)
        occupied.append((x, y, r))
        step("place_" + tag, True, "({:.0f}, {:.0f}) r {:.1f} m".format(x, y, r))
        return at

    water = next((v for k, v in objectives.items() if "Water" in k), None)
    farm = next((v for k, v in objectives.items() if "Farm" in k), None)
    step("objectives_found", water is not None and farm is not None, list(objectives))

    # 2. Water Point: the windmill that pumps it, a tank stand, the well pump at its edge.
    if water:
        put("Windmill", windmill, slots["SS_Raven_windmill"], water, 14.0, 30.0, 1.2, face=False)
        put("WaterTower", tower, slots["SS_Raven_water_tower"], water, 12.0, 26.0, 0.8)
        put("Pump_Water", pump, slots["SS_Raven_hand_pump"], water, 7.5, 11.0, 0.8, face=False)
    # 3. Farmstead: two barns fronting the yard, the stone well, a pump, a caravan and a dunny.
    # The buildings stand where the blockout designed them (Docs/MAPS_DRYRIVER.md 4.4; the greybox boxes left the
    # terrain export in Session 045): the open machinery shed ON the objective -> the open pole barn, long axis
    # east-west like the 18 x 10 m shed; the enclosed residence at (+18, +61) -> the enclosed barn; the chest-high
    # stock-pen rails from x +66 to +94 at y +48 -> a timber rail fence (blocks movement, not fire).
    barns = []
    if farm:
        def designed(tag, mesh, mats, x, y, yaw):
            r = footprint_m(mesh)
            # Anything collidable of the expansion inside the footprint goes (a rock inside a barn).
            for a in actors.get_all_level_actors():
                if a.get_actor_label().startswith("SS_Expand_Cover_") or a.get_actor_label().startswith("SS_Expand_Quarry_"):
                    loc = a.get_actor_location()
                    if math.hypot(loc.x / 100.0 - x, -loc.y / 100.0 - y) < r + 1.0:
                        report.setdefault("cleared_for_buildings", []).append(a.get_actor_label())
                        actors.destroy_actor(a)
            place(PREFIX + tag, mesh, mats, x, y, yaw, r)
            occupied.append((x, y, r))
            step("place_" + tag, True, "designed ({:.0f}, {:.0f}) yaw {:.0f}".format(x, y, yaw))
            return (x, y)

        # 9 m south of the objective centre so the flag stands in the barn's yard instead of through its roof;
        # the barn is still the objective's cover, inside the capture area's edge.
        barns.append(designed("OldBarn", old_barn, slots["SS_Raven_old_barn"], farm[0], farm[1] - 9.0, 90.0))
        barns.append(designed("Barn", barn, slots["SS_Raven_barn"], farm[0] - 22.0, farm[1] + 9.0, 0.0))
        fence = load("/Game/Modular_Rural_Cabin/Meshes/Props/Fence_Old_1_2m")
        if fence:
            fe = fence.get_bounds().box_extent
            seg = max(fe.x, fe.y) * 2.0 / 100.0                  # segment length, m
            along_x_yaw = 0.0 if fe.x >= fe.y else 90.0
            n = int(28.0 / seg)
            for i in range(n):
                fx = farm[0] + 26.0 + seg * (i + 0.5)  # the pens line, x +66..+94
                place("{}PenFence_{:02d}".format(PREFIX, i), fence, None, fx, farm[1] - 4.0, along_x_yaw + rng.uniform(-2, 2),
                      0.3, tilt=rng.uniform(-3, 3))
                occupied.append((fx, farm[1] - 4.0, seg * 0.5))
            step("pen_fence", n > 0, "{} segments of {:.1f} m".format(n, seg))
        put("Pump_Farm", pump, slots["SS_Raven_hand_pump"], farm, 7.5, 12.0, 0.8, face=False)
        if well:
            put("Well", well, None, farm, 9.0, 24.0, 0.7, face=False)
        if caravan:
            put("Caravan", caravan, None, farm, 14.0, 36.0, 1.0)
        if outhouse:
            put("Outhouse", outhouse, None, farm, 18.0, 28.0, 0.5)
    if water and well:
        put("Well_Water", well, None, water, 16.0, 26.0, 0.5, face=False)

    # 4. Fuel drums: clusters of 2-4 beside the barns and the existing sheds (SS_Expand_Cover_Shed_*).
    anchors = [b for b in barns if b]
    for a in actors.get_all_level_actors():
        if a.get_actor_label().startswith("SS_Expand_Cover_Shed_") or a.get_actor_label().startswith("SS_Expand_Cover_LeanTo_"):
            loc = a.get_actor_location()
            anchors.append((loc.x / 100.0, -loc.y / 100.0))
    rd = footprint_m(drum)
    n = 0
    for k, anchor in enumerate(anchors):
        centre = near(anchor, 4.0, 9.0, 1.2, 0.3)
        if not centre:
            continue
        for i in range(rng.randint(2, 4)):
            x = centre[0] + rng.uniform(-1.1, 1.1)
            y = centre[1] + rng.uniform(-1.1, 1.1)
            if not all(math.hypot(x - px, y - py) >= pr + rd + 0.05 for px, py, pr in occupied):
                continue
            place("{}Drum_{:02d}_{}".format(PREFIX, k, i), drum, rng.choice(drum_mats), x, y, rng.uniform(0, 360), rd, collide=True)
            occupied.append((x, y, rd))
            n += 1
    step("drums", n > 0, "{} drums at {} sites".format(n, len(anchors)))

    saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
    step("saved", saved)


try:
    main()
    report["ok"] = all(s["ok"] for s in report["steps"]) and not report["errors"]
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[FarmDryRiver] ok={}".format(report["ok"]))
