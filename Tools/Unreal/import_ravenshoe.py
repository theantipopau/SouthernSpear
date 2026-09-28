"""
Ravenshoe Crossing - Unreal import, place and dress pass (ADR-027).

Creates /Game/Maps/L_Ravenshoe_01, imports the three original meshes generated
by Tools/Blender/ravenshoe_blockout.py, and replaces every greybox cover marker
with a real mesh from an already-installed Fab pack.

RUN ORDER
    import_ravenshoe -> dress_ravenshoe_props -> setup_ravenshoe_surfaces

    This pass must come FIRST. It re-imports the bridge FBX with
    replace_existing and re-spawns the SS_Raven_Geo_* actors, which resets the
    mesh's material slots AND the per-instance surface overrides. Run
    setup_ravenshoe_surfaces before this one and the next run silently strips
    every surface back to flat colours, with the Road slot falling to
    WorldGridMaterial and nothing reporting an error.
    audit_ravenshoe.py asserts the overrides on the saved map, which is how
    that failure is caught rather than shipped.

WHAT IS OURS AND WHAT IS LICENSED
    Class F, authored here, imported by this pass:
        SS_MAP_Ravenshoe_01   terrain heightfield, road corridor, both ramps
        SS_Raven_Bridge       the wrought-iron lattice girder
        SS_Raven_Gatehouse    the stone road-gate house and its arch
    Class A, installed already, referenced in place and NEVER modified (L-0016):
        Scene_QuarrySlate   gorge rock, ledges, scree  (the best rock we have)
        RuralAustralia      gums, grass trees, logs, fences on the approaches
        Namaqualand         dry scrub and stones on the bed
    The pack meshes bring their own PBR materials, so this pass is where most
    of the map's visual quality actually arrives - the originals are greybox
    geometry and stay that way until the art pass.

WHY THE GROUND HEIGHT COMES FROM THE SPEC AND NOT FROM A TRACE
    line_trace_single in a -nullrhi commandlet cannot hit StaticMeshActor, so a
    trace cannot find this map's terrain - which is itself a StaticMeshActor.
    Every cover object would be placed at z=0 and buried or floating. So this
    pass reads z from the layout CSV, which the Blender generator filled in from
    Tools/Common/ravenshoe_spec.py: the same function the terrain was built
    from. The placement is exact by construction rather than sampled at runtime,
    and the shared-spec pattern means there is only one definition of the
    ground. Do not "fix" this by adding a trace.

COORDINATES
    The FBX carries its own transform, so each mesh is authored in Blender space
    and lands mirrored in Y on import (Blender is +Y forward right-handed, the
    engine is left-handed). Every layout CSV row is converted the same way, so
    the map reads exactly as Docs/MAPS_RAVENSHOE.md describes it, with Blender
    +Y becoming engine -Y:
        ue_x =  bl_x * 100
        ue_y = -bl_y * 100
        ue_z =  bl_z * 100
        ue_yaw = -bl_yaw
    "North" in this document therefore points along engine -Y. The relative
    layout - which deployment is 130 m from the span, where the gatehouse sits -
    is unaffected, and is what the design actually specifies.

IDEMPOTENCE AND OWNERSHIP
    Everything this pass creates is labelled with SS_Raven_ and a stage prefix,
    and a rerun destroys only what it owns before rebuilding. That is the rule
    from expand_redgum.py, and the sanity gate at the end is that one too: this
    pass deletes and rebuilds, so a spawn route that silently does nothing would
    otherwise save a map with its dressing simply missing.

NAVIIGATION
    This pass CANNOT bake static Recast data. BUILDPATHS through a console
    command crashes the commandlet (see Tools/Unreal/redgum_crash_probe.py), so
    the navmesh must be baked in the interactive editor with Build > Build Paths.
    Do not describe any part of this map as AI-playable until that is done and
    verified.

Run:
    UnrealEditor-Cmd.exe <uproject> -run=pythonscript \
        -script="<project>/Tools/Unreal/import_ravenshoe.py" \
        -nullrhi -unattended -nosplash -nop4
"""

import csv
import json
import math
import os
import random
import sys
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
MAP = "/Game/Maps/L_Ravenshoe_01"
BLOCKOUT_DIR = os.path.join(PROJECT_DIR, "Content", "Art", "Blockout")
CSV_PATH = os.path.join(BLOCKOUT_DIR, "SS_MAP_Ravenshoe_01_Layout.csv")
REPORT = os.path.join(PROJECT_DIR, "Build", "ravenshoe_import_report.json")

MESH_DEST = "/Game/Art/Environment/Ravenshoe/Meshes"
MAT_DEST = "/Game/Art/Environment/Ravenshoe/Materials"
FOLDER_OWN = unreal.Name("Ravenshoe")
FOLDER_DRESS = unreal.Name("Ravenshoe/Dressing")

PREFIX = "SS_Raven_"
PREFIX_GEO = PREFIX + "Geo_"
PREFIX_COVER = PREFIX + "Cover_"
PREFIX_DRESS = PREFIX + "Dress_"
# The objective and deployment markers carry the map name, not PREFIX.
MARKER_PREFIX = "SS_MAP_Ravenshoe_"

# 68 cover markers is not enough scenery to read as a gorge. These extra
# passes are the difference between "a bridge on a heightfield" and a place.
DRESS_SEED = 20260928

# ---------------------------------------------------------------------------
# Class A pack meshes, by role. L-0016 / L-0016b - referenced in place only.
# ---------------------------------------------------------------------------

QS = "/Game/Scene_QuarrySlate/Assets/MS/3D"
RA = "/Game/RuralAustralia/StaticMeshes"

COVER_ROCK = [
    QS + "/Qua_Sla_Cluster_Ledge_Rock_M_01/SM_Qua_Sla_Cluster_Ledge_Rock_M_01",
    QS + "/Qua_Sla_Cluster_Rock_M_06/SM_Qua_Sla_Cluster_Rock_M_06",
    QS + "/Qua_Sla_Cluster_Rock_M_07/SM_Qua_Sla_Cluster_Rock_M_07",
    QS + "/Qua_Sla_Pile_Rock_S_01/SM_Qua_Sla_Pile_Rock_S_01",
]
COVER_BUSH = [
    RA + "/Vegetation/GrassTree_01/SM_GrassTree_01",
    RA + "/Rocks/Rock_M_01/SM_Rock_M_01",
    RA + "/Rocks/Rock_M_02/SM_Rock_M_02",
]
# Gorge wall and scree. Ledges go on the walls because that is what a ledge is.
WALL_ROCK = [
    QS + "/Qua_Sla_Ledge_Rock_L_01/SM_Qua_Sla_Ledge_Rock_L_01",
    QS + "/Qua_Sla_Ledge_Rock_M_01/SM_Qua_Sla_Ledge_Rock_M_01",
    QS + "/Qua_Sla_Ledge_Rock_M_03/SM_Qua_Sla_Ledge_Rock_M_03",
    QS + "/Qua_Sla_Ledge_Rock_S_01/SM_Qua_Sla_Ledge_Rock_S_01",
]
BED_ROCK = [
    QS + "/Qua_Sla_Cluster_Rock_M_06/SM_Qua_Sla_Cluster_Rock_M_06",
    QS + "/Qua_Sla_Cluster_Rock_M_07/SM_Qua_Sla_Cluster_Rock_M_07",
    QS + "/Qua_Sla_Pile_Rock_S_01/SM_Qua_Sla_Pile_Rock_S_01",
]
TREES = [
    RA + "/Vegetation/Tree_L_01/SM_Tree_L_01",
    RA + "/Vegetation/Tree_M_01/SM_Tree_M_01",
    RA + "/Vegetation/Tree_M_02/SM_Tree_M_02",
    RA + "/Vegetation/Tree_S_01/SM_Tree_S_01",
]
LOGS = [
    RA + "/Vegetation/Log_L_01/SM_Log_L_01",
    RA + "/Vegetation/Log_M_01/SM_Log_M_01",
    RA + "/Vegetation/Log_S_01/SM_Log_S_01",
]
FENCE_POST = RA + "/Props/Fence_01/SM_Fence_02"
FENCE_WIRE = RA + "/Props/Fence_01/SM_Fence_Wires_01"

# ---------------------------------------------------------------------------
# Authored materials for our own geometry. Constant colours: the originals are
# greybox and a greybox that looks finished stops being treated as one. The
# real look arrives with the dress meshes, which bring their own materials.
# ---------------------------------------------------------------------------

MATERIALS = {
    "Iron": (0.055, 0.058, 0.065, 0.55),   # wrought iron, near-black, metallic
    "Stone": (0.36, 0.345, 0.325, 0.10),   # local granite, warm grey
    "Deck": (0.145, 0.135, 0.120, 0.20),   # weathered timber deck
    "Road": (0.105, 0.101, 0.094, 0.20),   # the running surface on the deck
    "Terrain": (0.30, 0.255, 0.195, 0.05),  # dry high-country ground
}
MAT_KEY_BY_SLOT = {
    "Iron": "Iron", "Stone": "Stone", "Deck": "Deck", "Road": "Road",
    "Terrain": "Terrain",
}


# ---------------------------------------------------------------------------
# The shared spec. Imported as a module rather than reimplemented, so the
# ground this pass seats objects on is the ground the terrain was built from.
# ---------------------------------------------------------------------------

def load_spec():
    here = os.path.dirname(os.path.abspath(__file__))
    common = os.path.normpath(os.path.join(here, "..", "Common"))
    if common not in sys.path:
        sys.path.insert(0, common)
    try:
        import ravenshoe_spec
        return ravenshoe_spec
    except Exception as exc:  # noqa: BLE001
        unreal.log_warning("[Ravenshoe] could not import ravenshoe_spec: {}".format(exc))
        return None


SPEC = None
report = {
    "ok": False,
    "map": MAP,
    "steps": [],
    "errors": [],
    "warnings": [],
    "missing_assets": [],
    "placed": {},
    "removed_previous_pass": 0,
}


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    unreal.log("[Ravenshoe] {} {} {}".format("OK" if ok else "FAIL", name, detail))
    return bool(ok)


def warn(msg):
    report["warnings"].append(str(msg))
    unreal.log_warning("[Ravenshoe] {}".format(msg))


def to_ue(bl_x, bl_y, bl_z, bl_yaw=0.0):
    """Blender metres to Unreal centimetres. See the module docstring."""
    return unreal.Vector(bl_x * 100.0, -bl_y * 100.0, bl_z * 100.0), -bl_yaw


# ---------------------------------------------------------------------------

def build_materials():
    """Authored constant materials for our own geometry.

    A safety net, not the look. These give every surface a sane flat colour so
    nothing renders pure default-grey; setup_ravenshoe_surfaces.py then
    overrides the bridge, deck and masonry with the real generated surfaces.

    The colours go on as a MaterialInstanceConstant of the project's own
    M_SS_ScanPBR via its Tint scalar. The previous version called
    MaterialEditingLibrary.get_material_property, which does not exist in 5.8 -
    the call raised, was caught, and the materials were created with default
    values, so for a whole session the "authored constant materials" were
    whatever a fresh Material defaults to.
    """
    out = {}
    parent = unreal.load_asset("/Game/Art/Environment/Fab/M_SS_ScanPBR")
    if parent is None:
        report["errors"].append("parent M_SS_ScanPBR missing")
        return out
    for key, (r, g, b, rough) in MATERIALS.items():
        name = "MI_SS_RavenFlat_{}".format(key)
        path = "{}/{}".format(MAT_DEST, name)
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            unreal.EditorAssetLibrary.delete_asset(path)
        factory = unreal.MaterialInstanceConstantFactoryNew()
        mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, MAT_DEST, unreal.MaterialInstanceConstant, factory)
        if mi is not None:
            # The factory has no initial_parent property in 5.8; the parent is
            # assigned on the instance afterwards, which is what
            # dress_ravenshoe_props.py does and the only route that works.
            mi.set_editor_property("parent", parent)
        if mi is None:
            report["errors"].append("could not create " + path)
            continue
        try:
            unreal.MaterialEditingLibrary \
                .set_material_instance_vector_parameter_value(
                    mi, "Tint", unreal.LinearColor(r, g, b, 1.0))
            unreal.MaterialEditingLibrary \
                .set_material_instance_scalar_parameter_value(
                    mi, "Tiling", 1.0)
        except Exception as exc:  # noqa: BLE001
            warn("material {}: {}".format(key, exc))
        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        out[key] = mi
    return out


def import_mesh(label, filename, materials, slot_map):
    """Import one FBX with collision, then override its material slots by name."""
    fbx = os.path.join(BLOCKOUT_DIR, filename)
    if not os.path.isfile(fbx):
        report["errors"].append("missing FBX " + fbx)
        return None

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", fbx)
    task.set_editor_property("destination_path", MESH_DEST)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)

    opts = unreal.FbxImportUI()
    for prop, value in (("import_mesh", True),
                        ("import_as_skeletal", False),
                        ("import_animations", False),
                        ("import_materials", True),
                        ("import_textures", False)):
        try:
            opts.set_editor_property(prop, value)
        except Exception as exc:  # noqa: BLE001
            warn("FbxImportUI.{}: {}".format(prop, exc))
    try:
        smi = opts.get_editor_property("static_mesh_import_data")
        smi.set_editor_property("combine_meshes", True)
        # The terrain is the map's floor and must block; the bridge and the
        # gatehouse are cover and must block. Everything here is solid, so
        # collision is generated for all three.
        smi.set_editor_property("auto_generate_collision", True)
        smi.set_editor_property("generate_lightmap_u_vs", False)
    except Exception as exc:  # noqa: BLE001
        warn("static_mesh_import_data: {}".format(exc))
    task.set_editor_property("options", opts)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = list(task.get_editor_property("imported_object_paths") or [])
    if not imported:
        report["errors"].append("import produced nothing for " + label)
        return None

    path = "{}/{}".format(MESH_DEST, label)
    mesh = unreal.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        report["errors"].append("no StaticMesh at " + path)
        return None

    # CTF_USE_DEFAULT, written and read back. If this does not take, the mesh
    # will not block, and the map is unplayable in a way nothing else reports.
    flag, applied = unreal.CollisionTraceFlag.CTF_USE_DEFAULT, ""
    try:
        body = mesh.get_editor_property("body_setup")
        body.set_editor_property("collision_trace_flag", flag)
        applied = str(body.get_editor_property("collision_trace_flag"))
    except Exception as exc:  # noqa: BLE001
        report["errors"].append("{}: collision_trace_flag: {}".format(label, exc))
    if "CTF_USE_DEFAULT" not in applied:
        report["errors"].append("{}: trace flag is {!r}".format(label, applied))

    # Slot override BY NAME. StaticMesh.Materials is protected on 5.8 and
    # raises on read, so this goes through static_materials.
    try:
        slots = mesh.get_editor_property("static_materials")
        hit = 0
        for i, slot in enumerate(slots):
            # material_slot_name is a unreal.Name, not a str. Calling .strip()
            # on it raised, aborted the whole loop, and left every mesh slot
            # pointing at nothing - the slot override silently never ran.
            name = str(slot.get_editor_property("material_slot_name") or "").strip()
            key = slot_map.get(name)
            if key is None:
                for suffix, k in MAT_KEY_BY_SLOT.items():
                    if name.endswith(suffix):
                        key = k
                        break
            if key is not None and key in materials:
                slot.set_editor_property("material_interface", materials[key])
                hit += 1
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        report.setdefault("slots_mapped", {})[label] = "{}/{}".format(hit, len(slots))
    except Exception as exc:  # noqa: BLE001
        warn("{}: slot override: {}".format(label, exc))
    return mesh


def load_pack_meshes():
    """Load every pack mesh this pass wants, tolerating gaps."""
    wanted = {}
    for group, paths in (("cover_rock", COVER_ROCK), ("cover_bush", COVER_BUSH),
                         ("wall_rock", WALL_ROCK), ("bed_rock", BED_ROCK),
                         ("trees", TREES), ("logs", LOGS),
                         ("fence_post", [FENCE_POST]),
                         ("fence_wire", [FENCE_WIRE])):
        got = []
        for p in paths:
            asset = unreal.load_asset(p)
            if isinstance(asset, unreal.StaticMesh):
                got.append(asset)
            else:
                report["missing_assets"].append(p)
        if got:
            wanted[group] = got
        else:
            step("load_" + group, False, "none of {} paths resolved".format(len(paths)))
    return wanted


def remove_owned_actors(world):
    """Purge everything this pass owns, so a re-run is idempotent.

    The objective and deployment markers are labelled SS_MAP_Ravenshoe_*, not
    SS_Raven_*, so a purge matching only PREFIX never removed them. Every
    re-run of the import then added another objective and another deployment:
    the audit read 2, then 4, then 6 of each, and the map quietly grew a set of
    duplicate objective volumes. Both prefixes are ours - the second is the map
    name - so both are purged.
    """
    removed = 0
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in actor_sub.get_all_level_actors():
        label = actor.get_actor_label()
        if label.startswith(PREFIX) or label.startswith(MARKER_PREFIX):
            actor_sub.destroy_actor(actor)
            removed += 1
    report["removed_previous_pass"] = removed
    return removed


def spawn(world, meshes, group, label, bl_x, bl_y, bl_z, yaw, scale, collision=True,
          folder=FOLDER_DRESS, prefix=PREFIX_COVER):
    """Spawn one StaticMeshActor and give it a pack mesh.

    spawn_actor_from_object logs only "SpawnActorFromObject. No actor was
    spawned." and does nothing for any mesh in this commandlet. The class +
    set_static_mesh route below is the one dress_dryriver.py uses; the other one
    is what made a previous pass delete 864 actors, place nothing, and save the
    map without them.
    """
    pool = meshes.get(group) or []
    if not pool:
        return False
    mesh = pool[random.randrange(len(pool))]
    loc, ue_yaw = to_ue(bl_x, bl_y, bl_z, yaw)
    actor = unreal.get_editor_subsystem(
        unreal.EditorActorSubsystem).spawn_actor_from_class(
            unreal.StaticMeshActor, loc,
            unreal.Rotator(roll=0.0, pitch=0.0, yaw=ue_yaw))
    if not actor:
        warn("spawn returned nothing for " + label)
        return False
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_label(prefix + label)
    try:
        actor.set_folder_path(folder)
    except Exception:  # noqa: BLE001
        pass
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    actor.set_actor_enable_collision(collision)
    report["placed"][group] = report["placed"].get(group, 0) + 1
    return True


# ---------------------------------------------------------------------------
# Extra dressing passes - the quality layer
# ---------------------------------------------------------------------------

def dress_gorge_walls(world, meshes, rng):
    """Ledges along the gorge walls.

    The heightfield gives the gorge its shape but a smooth grey slope is not a
    gorge. Ledge clusters along both walls break the silhouette, give the
    ramps something to cut into, and put real cover on the flanks.
    """
    n = 0
    for side in (1.0, -1.0):
        for i in range(46):
            y = side * (12.0 + (i % 23) * 0.95)
            x = rng.uniform(-88.0, 88.0)
            if abs(x) < 7.0:
                continue
            if SPEC is not None:
                z = SPEC.ground_z(x, y)
            else:
                z = 0.0
            if n < 300 and spawn(world, meshes, "wall_rock",
                                 "Wall_{:+.0f}_{:02d}".format(y, i),
                                 x, y, z - rng.uniform(0.2, 1.4),
                                 rng.uniform(0.0, 360.0),
                                 rng.uniform(0.7, 1.9)):
                n += 1
    return n


def dress_bed(world, meshes, rng):
    """Boulders and drift wood on the creek bed."""
    n = 0
    for i in range(54):
        x = rng.uniform(-92.0, 92.0)
        y = rng.uniform(-26.0, 26.0)
        z = SPEC.ground_z(x, y) if SPEC is not None else 0.0
        if spawn(world, meshes, "bed_rock", "Bed_{:02d}".format(i),
                 x, y, z - rng.uniform(0.1, 0.9),
                 rng.uniform(0.0, 360.0), rng.uniform(0.6, 2.1)):
            n += 1
    for i in range(12):
        x = rng.uniform(-80.0, 80.0)
        y = rng.uniform(-24.0, 24.0)
        z = SPEC.ground_z(x, y) if SPEC is not None else 0.0
        if spawn(world, meshes, "logs", "BedLog_{:02d}".format(i),
                 x, y, z, rng.uniform(0.0, 360.0), rng.uniform(0.8, 1.4)):
            n += 1
    return n


def dress_treeline(world, meshes, rng):
    """Gums on the ridge above the gorge, and along both approaches.

    This is the sightline work. The map's axis is 300 m long and its flanks
    have to be closed, or the axial lane is a lane nobody has to use. Trees sit
    outside the road corridor and clear of the ramps.
    """
    n = 0
    lines = [(-95.0, 95.0, 74.0), (-95.0, 95.0, -74.0),
             (-88.0, -88.0, 40.0), (88.0, 88.0, 40.0),
             (-88.0, -88.0, -40.0), (88.0, 88.0, -40.0)]
    for li, (x0, x1, y) in enumerate(lines):
        count = 13
        for i in range(count):
            t = i / float(count - 1)
            x = x0 + (x1 - x0) * t + rng.uniform(-3.5, 3.5)
            yy = y + rng.uniform(-4.0, 4.0)
            if abs(x) < 11.0:
                continue
            # Keep the ramps' corridors clear: a gum on the traverse would
            # make the flank route impassable, and the flank is the map's
            # second lane, not decoration.
            if SPEC is not None:
                d = min(
                    min(SPEC.dist_xy(x, yy, px, py) for px, py, _pz in SPEC.RAMP_EAST),
                    min(SPEC.dist_xy(x, yy, px, py) for px, py, _pz in SPEC.RAMP_WEST))
                if d < 7.0:
                    continue
            z = SPEC.ground_z(x, yy) if SPEC is not None else 0.0
            if spawn(world, meshes, "trees", "Tree_{:02d}_{:02d}".format(li, i),
                     x, yy, z - 0.3, rng.uniform(0.0, 360.0),
                     rng.uniform(0.8, 1.5), collision=False, prefix=PREFIX_DRESS):
                n += 1
    return n


def dress_approach_fences(world, meshes, rng):
    """Post-and-wire along both road approaches, as on Red Gum.

    Visual only, collision off: Lyra has no vault, and a colliding wire fence
    splits the navmesh and stops pawns dead. Red Gum made the same call
    (ADR-022) for the same reason.
    """
    n = 0
    for side in (1.0, -1.0):
        for sign in (1.0, -1.0):
            for i in range(16):
                y = sign * (44.0 + i * 6.6)
                x = side * 11.5
                z = SPEC.ground_z(x, y) if SPEC is not None else 0.0
                if spawn(world, meshes, "fence_post",
                         "Fence_{:+.0f}_{:+.0f}_{:02d}".format(x, y, i),
                         x, y, z, 0.0, 1.0, collision=False,
                         prefix=PREFIX_DRESS):
                    n += 1
                if spawn(world, meshes, "fence_wire",
                         "Wire_{:+.0f}_{:+.0f}_{:02d}".format(x, y, i),
                         x, y, z, 0.0, 1.0, collision=False,
                         prefix=PREFIX_DRESS):
                    n += 1
    return n


def place_gameplay(world, rows):
    """Objectives, deployments and the nav volume, from the layout CSV."""
    placed = {"objective": 0, "deployment": 0}
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    for row in rows:
        kind = row.get("kind")
        x, y, z = float(row["x_m"]), float(row["y_m"]), float(row["z_m"])
        name = row["name"]
        if kind == "Objective":
            loc, _ = to_ue(x, y, z)
            obj = actor_sub.spawn_actor_from_class(
                unreal.SSObjectiveActor, loc, unreal.Rotator())
            if obj:
                obj.set_actor_label(name)
                placed["objective"] += 1
        elif kind == "Deployment":
            # Drop the player start onto the ground, not onto the marker slab.
            gz = SPEC.ground_z(x, y) if SPEC is not None else z
            loc, _ = to_ue(x, y, gz)
            ps = actor_sub.spawn_actor_from_class(
                unreal.PlayerStart, loc, unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
            if ps:
                ps.set_actor_label(name)
                placed["deployment"] += 1

    # Nav bounds volume. NavMeshBoundsVolume is a real class in 5.8 and
    # spawns directly; the Brush/BrushType route does not exist here at all -
    # unreal.BrushType has no BRUSH_NAV member, so a brush-based volume can
    # never be built from Python on this engine version.
    try:
        vol = actor_sub.spawn_actor_from_class(
            unreal.NavMeshBoundsVolume, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator())
        if vol:
            vol.set_actor_label(PREFIX + "NavBounds")
            # The map is 200 x 300 m; the volume covers it with margin, in cm.
            vol.set_actor_scale3d(unreal.Vector(115.0, 165.0, 45.0))
            # 5.8 requires the sweep argument positionally; omitting it raised
            # and the volume was left at the spawn point with no size, so the
            # map had a NavMeshBoundsVolume that bounded nothing.
            vol.set_actor_location(unreal.Vector(0.0, 0.0, 0.0), False, False)
            placed["nav_volume"] = 1
        else:
            warn("nav volume: spawn returned nothing")
    except Exception as exc:  # noqa: BLE001
        warn("nav volume: {}".format(exc))
    return placed


# ---------------------------------------------------------------------------

def current_world(map_path):
    """Get an editable world, trying every route that exists on 5.8.

    LevelEditorSubsystem.new_level() returns True and the level is created,
    but LevelEditorSubsystem.get_world() returns None straight afterwards in
    the python script commandlet - there is no editor world to hand back yet.
    So this walks the alternatives, and because new_level saves the level, the
    final fallback is simply to load the map back off disk.
    """
    tries = []

    def attempt(label, fn):
        try:
            w = fn()
        except Exception as exc:  # noqa: BLE001
            tries.append((label, "raised: {}".format(exc)))
            return None
        if w is None:
            tries.append((label, "None"))
            return None
        tries.append((label, "ok"))
        return w

    subs = unreal.get_editor_subsystem
    w = attempt("EditorActorSubsystem.get_world",
                lambda: subs(unreal.EditorActorSubsystem).get_world())
    if w is None:
        w = attempt("EditorLevelLibrary.get_editor_world",
                    lambda: unreal.EditorLevelLibrary.get_editor_world())
    if w is None:
        w = attempt("LevelEditorSubsystem.get_world",
                    lambda: subs(unreal.LevelEditorSubsystem).get_world())
    if w is None:
        w = attempt("EditorLoadingAndSavingUtils.load_map",
                    lambda: unreal.EditorLoadingAndSavingUtils.load_map(map_path))
    report["world_lookups"] = tries
    return w


def main():
    global SPEC
    random.seed(DRESS_SEED)
    SPEC = load_spec()
    step("load_spec", SPEC is not None,
         "ravenshoe_spec" if SPEC is not None else "unavailable; falling back to CSV z")

    if not os.path.isfile(CSV_PATH):
        report["errors"].append("missing layout CSV " + CSV_PATH)
        return
    with open(CSV_PATH, "r", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    step("read_layout_csv", bool(rows), "{} rows".format(len(rows)))

    # Create the map if it is not there yet.
    #
    # The API is LevelEditorSubsystem.new_level(asset_path, is_partitioned_world)
    # and it returns a BOOL, not a world. The first version of this pass called
    # EditorLevelUtils.new_empty_level and EditorLevelUtils.new_level, neither of
    # which exists in 5.8; getattr returned None, the loop fell through, and the
    # run stopped with "could not create" and no warning recorded - because
    # neither print() nor unreal.log() reaches this commandlet's log file. The
    # report JSON is the only reliable channel here, so every step goes in it.
    created = False
    level_sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP):
        ok = bool(level_sub.load_level(MAP))
    else:
        ok = bool(level_sub.new_level(MAP))
        created = ok
    if not ok:
        report["errors"].append("new_level/load_level returned False for " + MAP)
        step("create_map", False, "LevelEditorSubsystem returned False")
        return
    step("create_map", True, "{} ({})".format(MAP, "created" if created else "existing"))

    world = current_world(MAP)
    if world is None:
        report["errors"].append("no editable world after opening " + MAP)
        step("load_map", False,
             "all lookups failed: {}".format(report.get("world_lookups")))
        return
    step("load_map", True, MAP)

    materials = build_materials()
    if len(materials) != len(MATERIALS):
        return
    step("build_materials", True, "{} authored".format(len(materials)))

    meshes = {}
    for label, fname, slot_map in (
            ("SS_MAP_Ravenshoe_01", "SS_MAP_Ravenshoe_01.fbx", {"Terrain": "Terrain"}),
            ("SS_Raven_Bridge", "SS_Raven_Bridge.fbx",
             {"Iron": "Iron", "Deck": "Deck", "Road": "Road"}),
            ("SS_Raven_Gatehouse", "SS_Raven_Gatehouse.fbx", {"Stone": "Stone"})):
        m = import_mesh(label, fname, materials, slot_map)
        if m is not None:
            meshes[label] = m
    step("import_meshes", len(meshes) == 3, "{} of 3".format(len(meshes)))
    if len(meshes) != 3:
        return

    packs = load_pack_meshes()
    step("load_pack_meshes", bool(packs),
         "groups={} missing={}".format(sorted(packs.keys()), len(report["missing_assets"])))
    if not packs:
        return

    remove_owned_actors(world)
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # --- our geometry -----------------------------------------------------
    geo = [
        ("SS_MAP_Ravenshoe_01", "Terrain", 0.0, 0.0, 0.0, 0.0, 1.0),
        ("SS_Raven_Bridge", "Bridge", 0.0, 0.0, 14.0, 0.0, 1.0),
        ("SS_Raven_Gatehouse", "Gatehouse", 0.0, 62.0,
         SPEC.ground_z(0.0, 62.0) if SPEC is not None else 15.236, 0.0, 1.0),
    ]
    placed_geo = 0
    for mesh_label, name, bx, by, bz, byaw, scale in geo:
        loc, ue_yaw = to_ue(bx, by, bz, byaw)
        actor = actor_sub.spawn_actor_from_class(
            unreal.StaticMeshActor, loc, unreal.Rotator(roll=0.0, pitch=0.0, yaw=ue_yaw))
        if not actor:
            warn("geometry spawn returned nothing for " + name)
            continue
        actor.static_mesh_component.set_static_mesh(meshes[mesh_label])
        actor.set_actor_label(PREFIX_GEO + name)
        try:
            actor.set_folder_path(FOLDER_OWN)
        except Exception:  # noqa: BLE001
            pass
        actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
        placed_geo += 1
    step("place_geometry", placed_geo == 3, "{} of 3".format(placed_geo))
    if placed_geo != 3:
        return

    # --- the 68 layout cover markers become real pack meshes ---------------
    placed_cover = 0
    for row in rows:
        if not row.get("kind", "").startswith("Cover"):
            continue
        group = "cover_bush" if "Bush" in row["kind"] else "cover_rock"
        radius = float(row["half_x_m"])
        scale = max(0.5, min(2.2, radius / 0.9))
        if spawn(world, packs, group, row["name"],
                 float(row["x_m"]), float(row["y_m"]), float(row["z_m"]) - 0.25,
                 float(row["yaw_deg"]), scale):
            placed_cover += 1
    expected_cover = sum(1 for r in rows if r.get("kind", "").startswith("Cover"))
    step("place_cover", placed_cover == expected_cover,
         "{} of {} layout cover markers".format(placed_cover, expected_cover))

    # --- extra dressing ---------------------------------------------------
    rng = random.Random(DRESS_SEED)
    n_wall = dress_gorge_walls(world, packs, rng)
    n_bed = dress_bed(world, packs, rng)
    n_tree = dress_treeline(world, packs, rng)
    n_fence = dress_approach_fences(world, packs, rng)
    step("dress", (n_wall + n_bed + n_tree + n_fence) > 0,
         "wall={} bed={} trees={} fence={}".format(n_wall, n_bed, n_tree, n_fence))

    # --- gameplay ---------------------------------------------------------
    gp = place_gameplay(world, rows)
    step("place_gameplay", gp["objective"] == 2 and gp["deployment"] == 2,
         "objectives={} deployments={}".format(gp["objective"], gp["deployment"]))

    # --- sanity gate ------------------------------------------------------
    total = sum(report["placed"].values())
    removed = report.get("removed_previous_pass", 0)
    report["placed_total"] = total
    healthy = total > 0 and (removed == 0 or total >= removed * 0.5)
    step("dressing_sanity", healthy,
         "placed {} of {} removed".format(total, removed))
    if not healthy:
        report["ok"] = False
        step("save_map", False, "refused: the pass would have stripped the map")
        return

    saved = False
    try:
        saved = bool(unreal.get_editor_subsystem(
            unreal.LevelEditorSubsystem).save_current_level())
    except Exception:  # noqa: BLE001
        try:
            saved = bool(unreal.EditorLoadingAndSavingUtils.save_current_level())
        except Exception as exc:  # noqa: BLE001
            warn("save: {}".format(exc))
    step("save_map", saved, MAP)

    report["actor_total"] = len(
        unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    report["ok"] = all(s["ok"] for s in report["steps"])


try:
    main()
except Exception:  # noqa: BLE001
    report["errors"].append(traceback.format_exc())
    unreal.log_error("[Ravenshoe] " + traceback.format_exc())
finally:
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=str)
    unreal.log("[Ravenshoe] report -> " + REPORT)
