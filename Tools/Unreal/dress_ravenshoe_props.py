"""Dress Ravenshoe Crossing with the new Fab props, and set the deck on fire.

This is a SEPARATE pass from import_ravenshoe.py on purpose. That script builds
the map from scratch - terrain, truss, gatehouse, cover, dressing - and re-runs
it and you lose an afternoon of iterating on this layer. This one opens the
saved L_Ravenshoe_01, swaps its own actors, and leaves everything else alone.

What it does:
  0. Run order: import_ravenshoe -> dress_ravenshoe_props ->
     setup_ravenshoe_surfaces. The surfaces pass comes last because the import
     re-spawns the bridge actor and strips its material overrides.
  1. Imports the prepped prop FBX from Build/ravenshoe/props (Blender output -
     vendor scale, ground planes and triangle budgets already fixed there).
  2. Imports the downscaled texture set.
  3. Authors MI_SS_Raven_* instances parented to M_SS_ScanPBR. That material is
     parameterised (Tint, Tiling, BaseColor/Normal/Roughness/AO/Metalness), so
     new materials re-use the project's own PBR shading instead of being flat
     constants - and every pack texture already in the project can be pointed
     at through it rather than duplicating shader work.
  4. Places the props, and the burning wreck on the bridge deck at OBJ A with
     the Realistic Starter VFX pack's fire, smoke and ember systems.

ENGINE NOTES (5.8; each of these cost a run to learn):
  * EditorLevelLibrary.get_editor_world() is the working world getter in a
    -nullrhi commandlet. EditorActorSubsystem.get_world() returns None.
  * line_trace_single cannot hit StaticMeshActor here, so every z comes from
    ravenshoe_spec.ground_z() or from the deck constant - never from a trace.
  * print() and unreal.log() do not reach the commandlet log. The JSON report
    is the only channel; every step is recorded there.

Run:
    UnrealEditor-Cmd.exe <uproject> -run=pythonscript \
        -script="<project>/Tools/Unreal/dress_ravenshoe_props.py" \
        -nullrhi -unattended -nosplash -nop4
"""
import json
import math
import os
import random
import sys
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
MAP = "/Game/Maps/L_Ravenshoe_01"
PROP_DIR = os.path.join(PROJECT_DIR, "Build", "ravenshoe", "props")
TEX_DIR = os.path.join(PROP_DIR, "tex")
REPORT = os.path.join(PROJECT_DIR, "Build", "ravenshoe_dress_report.json")

sys.path.insert(0, os.path.join(PROJECT_DIR, "Tools", "Common"))
import ravenshoe_spec as SPEC  # noqa: E402

PROP_DEST = "/Game/Art/Environment/Ravenshoe/Props"
TEX_DEST = PROP_DEST + "/Textures"
MAT_DEST = "/Game/Art/Environment/Ravenshoe/Materials"
SCAN_PBR = "/Game/Art/Environment/Fab/M_SS_ScanPBR"
CORRUGATED = "/Game/Art/Environment/Fab/CorrugatedIron/MI_SS_CorrugatedIron"

FOLDER = unreal.Name("Ravenshoe/Props")
LABEL = "Dress_Prop_"

# The only Blueprint in the project that already carries a ParticleSystemComponent.
PARTICLE_BP = "/Game/Realistic_Starter_VFX_Pack_Vol2/Blueprints/Spawn_Particle"
PARTICLE_BP_CLASS = None

report = {"steps": [], "errors": [], "warnings": [],
          "imported": {}, "materials": {}, "placed": {}}

# ---------------------------------------------------------------------------
# Placement table. Blender metres, matching ravenshoe_spec's coordinate frame.
# `z` of None means "ask the spec", which is the only correct answer for
# anything standing on terrain.
# ---------------------------------------------------------------------------
WRECK_X, WRECK_Y = -0.8, 0.6        # skewed across mid-span, not square-on
WRECK_YAW = 22.0
WRECK_Z = SPEC.DECK_Z               # the deck is level; the spec road is not


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return bool(ok)


def warn(msg):
    report["warnings"].append(str(msg))


def to_ue(bl_x, bl_y, bl_z, bl_yaw=0.0):
    """Blender metres to Unreal centimetres. See the module docstring."""
    return unreal.Vector(bl_x * 100.0, -bl_y * 100.0, bl_z * 100.0), -bl_yaw


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

def import_prop(label, filename, collision=True):
    """Import one prepped FBX and force it to block (or explicitly not)."""
    fbx = os.path.join(PROP_DIR, filename)
    if not os.path.isfile(fbx):
        report["errors"].append("missing FBX " + fbx)
        return None

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", fbx)
    task.set_editor_property("destination_path", PROP_DEST)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)

    opts = unreal.FbxImportUI()
    for prop, value in (("import_mesh", True),
                        ("import_as_skeletal", False),
                        ("import_animations", False),
                        # Off deliberately. Every one of these props gets one of
                        # our own ScanPBR instances below, and letting the FBX
                        # importer create its own materials drops a dozen
                        # nameless Material__NNNNN and T_Override assets into
                        # the content folder that nothing references.
                        ("import_materials", False),
                        ("import_textures", False)):
        try:
            opts.set_editor_property(prop, value)
        except Exception as exc:  # noqa: BLE001
            warn("FbxImportUI.{}: {}".format(prop, exc))
    try:
        smi = opts.get_editor_property("static_mesh_import_data")
        smi.set_editor_property("combine_meshes", True)
        smi.set_editor_property("auto_generate_collision", bool(collision))
        smi.set_editor_property("generate_lightmap_u_vs", False)
    except Exception as exc:  # noqa: BLE001
        warn("{}: static_mesh_import_data: {}".format(label, exc))
    task.set_editor_property("options", opts)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = list(task.get_editor_property("imported_object_paths") or [])
    if not imported:
        report["errors"].append("import produced nothing for " + label)
        return None

    # The FBX importer names the asset after the FILE, not after the object
    # inside it, so the lookup key is the filename stem. Asking for a name we
    # invented here is how five of seven props came back "no StaticMesh" on the
    # first pass.
    stem = os.path.splitext(filename)[0]
    path = "{}/{}".format(PROP_DEST, stem)
    mesh = unreal.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        found = [p for p in imported if "/Meshes/" not in p]
        report["errors"].append("no StaticMesh at {} (imported: {})".format(
            path, found or imported))
        return None

    # Read collision back rather than assuming the import honoured it. A prop
    # that silently does not block is a gameplay bug nothing else reports.
    try:
        body = mesh.get_editor_property("body_setup")
        flag = body.get_editor_property("collision_trace_flag")
        applied = str(flag)
    except Exception as exc:  # noqa: BLE001
        applied = "<err {}>".format(exc)[:80]
    want = "CTF_USE_DEFAULT" if collision else "CTF_USE_ASYNC_ONLY"
    if collision and "CTF_USE_DEFAULT" not in applied:
        report["errors"].append("{}: trace flag is {!r}, wanted {}".format(
            stem, applied, want))
    if not collision and "NoCollision" not in applied and "ASYNC" not in applied:
        report["errors"].append("{}: collision is {!r}, wanted off".format(
            stem, applied))

    tris = None
    try:
        tris = mesh.get_num_triangles(0)
    except Exception:  # noqa: BLE001
        pass
    report["imported"][stem] = {"tris": tris, "collision": applied}
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    return mesh


def import_texture(filename):
    path = os.path.join(TEX_DIR, filename)
    if not os.path.isfile(path):
        report["warnings"].append("missing texture " + path)
        return None
    name = os.path.splitext(filename)[0]
    dest = "{}/{}".format(TEX_DEST, name)
    if unreal.EditorAssetLibrary.does_asset_exist(dest):
        return unreal.load_asset(dest)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", path)
    task.set_editor_property("destination_path", TEX_DEST)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = unreal.load_asset(dest)
    if isinstance(tex, unreal.Texture2D):
        for prop, value in (("srgb", True), ("compression_settings",
                                              unreal.TextureCompressionSettings.TC_DEFAULT)):
            try:
                tex.set_editor_property(prop, value)
            except Exception as exc:  # noqa: BLE001
                warn("texture {} .{}: {}".format(name, prop, exc))
        unreal.EditorAssetLibrary.save_loaded_asset(tex)
    return tex


# ---------------------------------------------------------------------------
# Materials - all instances of the project's own parameterised ScanPBR
# ---------------------------------------------------------------------------

def scan_pbr_template():
    """Read MI_SS_CorrugatedIron's parameter values as a working example.

    ScanPBR exposes Roughness, AO and Metalness as slots. The wreck pack ships
    an albedo and a grunge map and NO normal, roughness, AO or metalness at all,
    so anything we do not override has to come from an instance that is known
    to work - the parent material's defaults are tuned for a scan, not for a
    car panel.

    get_material_instance_texture_parameter_value returns a PATH STRING, not
    an object. Passing that string straight back into the setter is a nativise
    error, so every texture is resolved to a real asset here.
    """
    src = unreal.load_asset(CORRUGATED)
    if src is None:
        report["errors"].append("missing template instance " + CORRUGATED)
        return {}
    lib = unreal.MaterialEditingLibrary
    out = {"_textures": {}, "_scalars": {}}
    for name in ("Roughness", "Tiling", "Metalness"):
        try:
            out["_scalars"][name] = float(lib.get_material_instance_scalar_parameter_value(
                src, name))
        except Exception as exc:  # noqa: BLE001
            out["_scalars"][name] = None
            warn("template scalar {}: {}".format(name, exc))
    for name in ("Normal", "AO", "BaseColor", "Roughness", "Metalness"):
        try:
            p = lib.get_material_instance_texture_parameter_value(src, name)
        except Exception:  # noqa: BLE001
            continue
        path = str(p)
        if not path.startswith("/Game"):
            continue
        out["_textures"][name] = unreal.load_asset(path.split(".")[0])
    out["_raw_textures"] = {k: str(v.get_path_name()) if v else None
                            for k, v in out["_textures"].items()}
    return out


def make_instance(name, base_colour=None, normal=None, tint=(1, 1, 1),
                  tiling=1.0, roughness=None, ao=None, metalness=None,
                  roughness_scalar=None):
    path = "{}/MI_SS_Raven_{}".format(MAT_DEST, name)
    mic = unreal.load_asset(path)
    if mic is None:
        factory = unreal.MaterialInstanceConstantFactoryNew()
        mic = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "MI_SS_Raven_{}".format(name), MAT_DEST,
            unreal.MaterialInstanceConstant, factory)
    if mic is None:
        report["errors"].append("could not create " + path)
        return None
    parent = unreal.load_asset(SCAN_PBR)
    if parent is None:
        report["errors"].append("missing parent " + SCAN_PBR)
        return None
    mic.set_editor_property("parent", parent)

    lib = unreal.MaterialEditingLibrary
    applied = {}
    if base_colour is not None:
        lib.set_material_instance_texture_parameter_value(
            mic, "BaseColor", base_colour)
        applied["BaseColor"] = str(base_colour.get_name())
    if normal is not None:
        lib.set_material_instance_texture_parameter_value(mic, "Normal", normal)
        applied["Normal"] = str(normal.get_name())
    for key, tex in (("AO", ao), ("Roughness", roughness),
                     ("Metalness", metalness)):
        if tex is not None:
            lib.set_material_instance_texture_parameter_value(mic, key, tex)
            applied[key] = str(tex.get_name())
    try:
        lib.set_material_instance_vector_parameter_value(
            mic, "Tint", unreal.LinearColor(tint[0], tint[1], tint[2], 1.0))
        applied["Tint"] = str(tint)
    except Exception as exc:  # noqa: BLE001
        warn("{} Tint: {}".format(name, exc))
    try:
        lib.set_material_instance_scalar_parameter_value(mic, "Tiling", float(tiling))
        applied["Tiling"] = float(tiling)
    except Exception as exc:  # noqa: BLE001
        warn("{} Tiling: {}".format(name, exc))
    if roughness_scalar is not None:
        try:
            lib.set_material_instance_scalar_parameter_value(
                mic, "Roughness", float(roughness_scalar))
            applied["Roughness_scalar"] = float(roughness_scalar)
        except Exception as exc:  # noqa: BLE001
            warn("{} Roughness: {}".format(name, exc))

    unreal.EditorAssetLibrary.save_loaded_asset(mic)
    report["materials"][name] = applied
    return mic


def apply_material(actor, mat):
    """Put one material on every slot of a PLACED actor.

    Every route to the mesh ASSET's slots was tried and all of them silently
    did nothing on 5.8: writing into the array returned by
    get_editor_property("static_materials") changes local copies, and assigning
    it back with set_editor_property does not persist either - the audit read
    the slots back as [None, None].

    The per-instance override on the component - StaticMeshComponent
    .set_material - is a real component property, and it survives a save and
    reload. It is also the property that decides what renders, so it is the
    right place for it regardless.
    """
    comp = actor.static_mesh_component if hasattr(actor, "static_mesh_component") else None
    if comp is None:
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if comp is None:
        warn("apply_material: no StaticMeshComponent")
        return -1
    try:
        n = comp.get_num_materials()
        for i in range(n):
            comp.set_material(i, mat)
        readback = [comp.get_material(i).get_name() if comp.get_material(i) else None
                    for i in range(n)]
        bad = [m for m in readback if m != mat.get_name()]
        if bad:
            report["errors"].append("{}: material override read back as {}".format(
                actor.get_actor_label(), readback))
            return -1
        return n
    except Exception as exc:  # noqa: BLE001
        warn("apply_material: {}".format(exc))
        return -1


# ---------------------------------------------------------------------------
# Placement
# ---------------------------------------------------------------------------

def open_map():
    """Open the saved Ravenshoe map and hand back a world we can edit.

    get_editor_world() on its own returns whatever the commandlet happens to
    be holding, which in this build is a BLANK UNTITLED LEVEL. Placing into
    that succeeds, reports fine, and is then thrown away - the .umap on disk
    never changes. So the map is loaded explicitly, and the world is verified
    before a single actor is spawned.
    """
    world = None
    try:
        world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    except Exception as exc:  # noqa: BLE001
        report["errors"].append("load_map raised: {}".format(exc)[:200])
    if world is None:
        world = unreal.EditorLevelLibrary.get_editor_world()
    return world


def verify_world(world):
    """Refuse to dress anything that is not the Ravenshoe map.

    The check is on CONTENT, not on the world name: a blank level has no
    SS_Raven_Geo_* actors and no deployment markers, and a map that lost its
    geometry is just as wrong as a level that never had any.
    """
    actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    geo = [a for a in actors if a.get_actor_label().startswith("SS_Raven_Geo_")]
    terrain = [a for a in geo if "Terrain" in a.get_actor_label()]
    report["world_check"] = {
        "name": world.get_name(), "actors": len(actors),
        "geo": len(geo), "terrain": len(terrain),
    }
    if len(actors) < 300 or len(geo) < 3 or not terrain:
        report["errors"].append(
            "world is not Ravenshoe Crossing: {} actors, {} geo, {} terrain".format(
                len(actors), len(geo), len(terrain)))
        return False
    return True


def purge_own(world):
    """Remove only the actors this pass owns, so a re-run is idempotent."""
    removed = 0
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_actor_label().startswith(LABEL):
            unreal.EditorActorSubsystem().destroy_actor(actor)
            removed += 1
    return removed


def spawn_prop(world, mesh, tag, bl_x, bl_y, bl_z, yaw=0.0, scale=1.0,
               collision=True, tilt=0.0):
    loc, ue_yaw = to_ue(bl_x, bl_y, bl_z, yaw)
    actor = unreal.get_editor_subsystem(
        unreal.EditorActorSubsystem).spawn_actor_from_class(
            unreal.StaticMeshActor, loc,
            unreal.Rotator(roll=0.0, pitch=tilt, yaw=ue_yaw))
    if not actor:
        warn("spawn returned nothing for " + tag)
        return None
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_label(LABEL + tag)
    try:
        actor.set_folder_path(FOLDER)
    except Exception:  # noqa: BLE001
        pass
    if scale != 1.0:
        actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    actor.set_actor_enable_collision(collision)
    report["placed"][tag] = report["placed"].get(tag, 0) + 1
    return actor


def spawn_particles(world, system_path, tag, loc_cm, scale=1.0):
    """Place a Cascade particle system from the VFX pack.

    A runtime-added ParticleSystemComponent CANNOT be persisted from a Python
    commandlet in 5.8. Every route was tested against a real save and reload:
    Actor.add_instance_component does not exist, ActorComponent
    .register_component does not exist, EditorActorSubsystem
    .add_actor_component does not exist, and call_method into either raises
    "Failed to find function". Components created that way are not owned by
    the actor, so the serialised level has none of them - the actor sits in
    the outliner and emits nothing.

    What does persist is a component property on a placed actor. The VFX pack
    ships exactly one Blueprint that already has a ParticleSystemComponent
    (Spawn_Particle), so its GENERATED CLASS is spawned and the template is
    then set on the instance's component. Verified across a save and reload.

    Returns the actor if the template stuck, else None.
    """
    ps = unreal.load_asset(system_path)
    if ps is None:
        report["warnings"].append("missing particle system " + system_path)
        return None
    gen = PARTICLE_BP_CLASS
    if gen is None:
        report["errors"].append("no particle Blueprint class available")
        return None

    actor = unreal.get_editor_subsystem(
        unreal.EditorActorSubsystem).spawn_actor_from_class(
            gen, loc_cm, unreal.Rotator())
    if not actor:
        report["errors"].append("{}: spawn returned None".format(tag))
        return None

    comps = actor.get_components_by_class(unreal.ParticleSystemComponent)
    if not comps:
        report["errors"].append("{}: spawned instance has no particle component".format(tag))
        return None
    comp = comps[0]
    comp.set_editor_property("template", ps)
    for prop, value in (("auto_activate", True), ("auto_destroy", True),
                        ("bAutoDestroy", True)):
        try:
            comp.set_editor_property(prop, value)
        except Exception:  # noqa: BLE001
            pass

    actor.set_actor_label(LABEL + tag)
    try:
        actor.set_folder_path(unreal.Name("Ravenshoe/VFX"))
    except Exception:  # noqa: BLE001
        pass
    if scale != 1.0:
        actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))

    # Read it back. A particle actor that is in the outliner but has a null
    # template is worse than no actor at all.
    try:
        check = comp.get_editor_property("template")
    except Exception:  # noqa: BLE001
        check = None
    if check is None:
        report["errors"].append("{}: template did not stick".format(tag))
        return None

    report["placed"][tag] = report["placed"].get(tag, 0) + 1
    return actor


def particle_bp_class():
    """The spawnable generated class for the pack's particle Blueprint."""
    global PARTICLE_BP_CLASS
    if PARTICLE_BP_CLASS is not None:
        return PARTICLE_BP_CLASS
    bp = unreal.load_asset(PARTICLE_BP)
    if bp is None:
        report["errors"].append("missing particle Blueprint " + PARTICLE_BP)
        return None
    try:
        PARTICLE_BP_CLASS = bp.generated_class()
    except Exception as exc:  # noqa: BLE001
        report["errors"].append("generated_class: {}".format(exc)[:160])
    return PARTICLE_BP_CLASS


# ---------------------------------------------------------------------------

def main():
    report["deck_z_m"] = SPEC.DECK_Z
    report["deck_half_width_m"] = SPEC.DECK_W * 0.5

    # -- 1. textures and props -------------------------------------------
    tex = {name: import_texture("T_Raven_{}.{}".format(name, ext))
           for name, ext in (("wreck_albedo", "jpg"),
                             ("wreck_grunge", "jpg"),
                             ("junk_albedo", "jpg"),
                             ("junk_normal", "png"),
                             ("junk_ao", "jpg"))}
    step("import_textures", True,
         " ".join("{}={}".format(k, "ok" if v else "MISSING") for k, v in tex.items()))

    # An earlier pass ran with import_materials on and left the FBX importer's
    # own nameless materials in the folder. The windmill also drags in nine
    # vendor textures, which nothing references once its materials are replaced
    # by ours. Both are unreferenced assets that would otherwise ship.
    swept = []
    for a in unreal.EditorAssetLibrary.list_assets(PROP_DEST, recursive=True):
        leaf = a.split("/")[-1].split(".")[0]
        is_vendor_mat = (leaf.startswith("Material__") or leaf.startswith("MatID_")
                         or leaf.startswith("T_Override")
                         or leaf in ("material0", "material1")
                         or leaf in ("barn", "roof", "barrel_mtl"))
        is_vendor_tex = (leaf.startswith("T_WM_") or leaf.startswith("T_Wind")
                         or leaf == "Water_tower" or leaf in ("PWE", "PB", "wood"))
        if is_vendor_mat or is_vendor_tex:
            if unreal.EditorAssetLibrary.delete_asset(a):
                swept.append(leaf)
    step("sweep_vendor_assets", True,
         "deleted {} unused importer materials and textures".format(len(swept)))

    props = {}
    for label, fname, coll in (
            ("SS_Raven_WreckCar", "SS_Raven_wreck_car.fbx", True),
            ("SS_Raven_WreckJunk", "SS_Raven_wreck_junk.fbx", True),
            ("SS_Raven_FuelDrum", "SS_Raven_fuel_drum.fbx", True),
            ("SS_Raven_Windmill", "SS_Raven_windmill.fbx", True),
            ("SS_Raven_Barn", "SS_Raven_barn.fbx", True),
            ("SS_Raven_SandbagStack", "SS_Raven_sandbag_stack.fbx", True),
            ("SS_Raven_TrenchWall", "SS_Raven_trench_wall.fbx", True),
            ("SS_Raven_WaterTower", "SS_Raven_water_tower.fbx", True),
            ("SS_Raven_HandPump", "SS_Raven_hand_pump.fbx", True),
            ("SS_Raven_OldBarn", "SS_Raven_old_barn.fbx", True)):
        props[label] = import_prop(label, fname, coll)
    step("import_props", all(props.values()),
         "{} of {} meshes".format(sum(1 for v in props.values() if v), len(props)))

    # -- 2. materials ----------------------------------------------------
    tmpl = scan_pbr_template()
    report["scanpbr_template"] = tmpl.get("_raw_textures", {})
    corr_normal = tmpl.get("_textures", {}).get("Normal")
    ao_tex = tmpl.get("_textures", {}).get("AO")
    rough_tex = tmpl.get("_textures", {}).get("Roughness")
    metal_tex = tmpl.get("_textures", {}).get("Metalness")
    rough_scalar = tmpl.get("_scalars", {}).get("Roughness")

    mats = {}
    # The wreck pack ships an albedo and a grunge map but NO normal, roughness,
    # AO or metalness. The project's own ScanPBR maps are generic surface
    # detail, so re-using them at tiling gives the burnt shell its surface
    # breakup without shipping a new shader or a new texture.
    mats["wreck"] = make_instance("Wreck", base_colour=tex["wreck_albedo"],
                                  normal=corr_normal, tint=(0.62, 0.60, 0.58),
                                  tiling=2.0, ao=ao_tex, roughness=rough_tex,
                                  metalness=metal_tex)
    mats["wreck_junk"] = make_instance("WreckJunk", base_colour=tex["junk_albedo"],
                                       normal=tex["junk_normal"], tint=(0.78, 0.70, 0.62),
                                       tiling=1.5, ao=tex["junk_ao"],
                                       roughness_scalar=rough_scalar)
    mats["drum"] = make_instance("FuelDrum", tint=(0.55, 0.30, 0.16), tiling=1.0,
                                 normal=corr_normal, roughness_scalar=rough_scalar)
    mats["metal"] = make_instance("Metal", tint=(0.52, 0.50, 0.47), tiling=1.5,
                                  normal=corr_normal, ao=ao_tex,
                                  roughness_scalar=rough_scalar)
    mats["timber"] = make_instance("Timber", tint=(0.42, 0.35, 0.28), tiling=1.0,
                                   ao=ao_tex, roughness_scalar=rough_scalar)
    mats["canvas"] = make_instance("Canvas", tint=(0.56, 0.51, 0.40), tiling=1.0,
                                   ao=ao_tex, roughness_scalar=rough_scalar)
    step("materials", all(mats.values()),
         "{} of {} instances".format(sum(1 for v in mats.values() if v), len(mats)))

    slot_for = {"SS_Raven_WreckCar": "wreck", "SS_Raven_WreckJunk": "wreck_junk",
                "SS_Raven_FuelDrum": "drum", "SS_Raven_Windmill": "timber",
                "SS_Raven_Barn": "timber", "SS_Raven_SandbagStack": "canvas",
                "SS_Raven_TrenchWall": "metal", "SS_Raven_WaterTower": "metal",
                "SS_Raven_HandPump": "metal", "SS_Raven_OldBarn": "timber"}
    report["prop_material"] = slot_for
    particle_bp_class()

    # -- 3. place --------------------------------------------------------
    # Every prop is spawned first and then given its material as a per-instance
    # component override, which is the only material route in 5.8 that
    # survives a save. spawn_prop() records the tag so the material pass can
    # find each actor again.
    world = open_map()
    if world is None:
        report["errors"].append("could not open " + MAP)
        return
    step("open_map", True, "{} ({})".format(MAP, world.get_name()))
    if not verify_world(world):
        step("verify_world", False, json.dumps(report["world_check"]))
        return
    step("verify_world", True, json.dumps(report["world_check"]))

    removed = purge_own(world)
    step("purge_previous", True, "removed {} existing prop actors".format(removed))

    rng = random.Random(20260928)

    # The wreck. On the deck at OBJ A, skewed so it reads as a casualty that
    # came to rest against the parapet rather than a barricade someone placed.
    # With the doors open the car is 3.5 m across on a 7.5 m deck, so there is
    # still fighting room down both flanks.
    wreck = None
    if props.get("SS_Raven_WreckCar"):
        wreck = spawn_prop(world, props["SS_Raven_WreckCar"], "WreckCar",
                           WRECK_X, WRECK_Y, WRECK_Z, WRECK_YAW, collision=True)
    step("place_wreck", wreck is not None,
         "({:.1f}, {:.1f}, {:.1f}) yaw {:.0f}".format(WRECK_X, WRECK_Y, WRECK_Z, WRECK_YAW))

    # A roadblock of dead vehicles at the SOUTH lip, on the road between the
    # south deployment and the abutment.
    #
    # It is here and not out on the span because the deck's cover is the
    # structure itself. Scattering cars down the 68 m would add cover, but it
    # would also narrow a 6.8 m lane and blunt the exposure that the 20 m rule
    # and the 3.4 m bay rhythm depend on. At the lip the same vehicles do three
    # jobs instead: they say why the road is shut, they give the south approach
    # a fight before anyone commits to the span, and they leave the deck itself
    # untouched.
    #
    # Placed with deliberate gaps. A continuous wall of cars would read as a
    # level-designer's barricade and would also just seal the route; these leave
    # a walkable line down the west side and a vehicle-width gap at the abutment.
    blocked = 0
    for tag, px, py, yaw in (("Roadblock_0", 2.20, -39.5, 28.0),
                             ("Roadblock_1", -2.40, -42.0, -14.0),
                             ("Roadblock_2", 0.40, -45.5, 62.0)):
        mesh = props.get("SS_Raven_WreckJunk") or props.get("SS_Raven_WreckCar")
        if mesh is None:
            break
        if spawn_prop(world, mesh, tag, px, py, SPEC.ground_z(px, py), yaw,
                      collision=True, tilt=rng.uniform(-3, 3)):
            blocked += 1
    step("place_roadblock", blocked == 3, "{} of 3 vehicle(s)".format(blocked))

    # Fire and smoke, offset along the wreck's own axis. Placed at the engine
    # end and the cabin rather than only at the centre, so the effect still
    # reads as a burning vehicle from the north approach. The VFX pack sorts
    # its systems into subfolders - they are NOT all directly under Particles.
    VFX = "/Game/Realistic_Starter_VFX_Pack_Vol2/Particles"
    yaw_rad = math.radians(WRECK_YAW)
    fired = 0
    for dx, sub, sys_name, tag, scl in ((1.15, "Fire", "P_Fire_Big", "Fire_Engine", 1.0),
                                        (-1.25, "Fire", "P_Fire_Small", "Fire_Cabin", 0.8),
                                        (0.0, "Smoke", "P_Smoke_A", "Smoke_Column", 2.2),
                                        (0.0, "Sparks", "P_Embers_A", "Embers", 1.0)):
        ox = dx * math.cos(yaw_rad)
        oy = dx * math.sin(yaw_rad)
        loc = unreal.Vector((WRECK_X + ox) * 100.0,
                            -(WRECK_Y + oy) * 100.0,
                            (WRECK_Z + 0.9) * 100.0)
        if spawn_particles(world, "{}/{}/{}.{}".format(VFX, sub, sys_name, sys_name),
                           tag, loc, scl):
            fired += 1
    step("place_fire", fired == 4, "{}/4 VFX systems placed".format(fired))

    # Fuel drums: a spill trail across the deck towards the wreck, plus a
    # cluster at the gatehouse. This is the reason it is burning.
    drum = props.get("SS_Raven_FuelDrum")
    if drum:
        for i in range(7):
            a = rng.uniform(0, math.tau)
            r = rng.uniform(1.6, 4.4)
            spawn_prop(world, drum, "Drum_Deck_%d" % i,
                       WRECK_X + r * math.cos(a), WRECK_Y + r * math.sin(a),
                       WRECK_Z, rng.uniform(0, 360), collision=(i < 4),
                       tilt=rng.uniform(-9, 9) if i >= 4 else 0.0)
        for i, (dx, dy) in enumerate(((6.4, 64.5), (7.0, 60.0), (5.9, 59.4))):
            spawn_prop(world, drum, "Drum_Gate_%d" % i, dx, dy,
                       SPEC.ground_z(dx, dy), rng.uniform(0, 360), collision=True)
    step("place_drums", drum is not None, "7 on the deck, 3 at the gatehouse")

    # Sandbags: hard cover stacked against the parapet on the approaches.
    bag = props.get("SS_Raven_SandbagStack")
    if bag:
        for side, ay in (("N", 1), ("S", -1)):
            for i, x in enumerate((-2.6, -0.9, 0.9, 2.6)):
                y = ay * (26.0 + i * 1.6)
                spawn_prop(world, bag, "Sandbag_%s%d" % (side, i), x, y,
                           SPEC.ground_z(x, y), rng.uniform(-14, 14), collision=True)
    step("place_sandbags", bag is not None, "8 stacks on the approaches")

    # Corrugated wall panels leaned against the parapet as improvised cover.
    wall = props.get("SS_Raven_TrenchWall")
    if wall:
        for i, (x, ay) in enumerate(((-2.4, 1), (2.5, 1), (-2.4, -1), (2.5, -1))):
            y = ay * 30.5
            spawn_prop(world, wall, "TrenchWall_%d" % i, x, y,
                       SPEC.ground_z(x, y), 90 + rng.uniform(-8, 8),
                       collision=True, tilt=rng.uniform(-6, 6))
    step("place_trench_walls", wall is not None, "4 panels at the abutments")

    # Ridge furniture. A windmill and a barn give the north ridge a silhouette
    # and a landmark, and both sit well clear of the road corridor.
    wm = props.get("SS_Raven_Windmill")
    if wm:
        spawn_prop(world, wm, "Windmill", 58, 96, SPEC.ground_z(58, 96),
                   rng.uniform(0, 360), collision=True)
    barn = props.get("SS_Raven_Barn")
    if barn:
        spawn_prop(world, barn, "Barn", -64, 112, SPEC.ground_z(-64, 112),
                   rng.uniform(0, 360), collision=True)

    # The old barn goes on the SOUTH ridge, mirrored across the road. Until now
    # every landmark on the map sat north: windmill, barn, water tower, two of
    # the three hand pumps. The south deployment therefore opened onto an empty
    # plateau, and the player spawning there had nothing to navigate by. The
    # two deployments are meant to be interchangeable, so each gets a
    # silhouette and a landmark.
    old_barn = props.get("SS_Raven_OldBarn")
    if old_barn:
        spawn_prop(world, old_barn, "OldBarn", 66, -104,
                   SPEC.ground_z(66, -104), rng.uniform(0, 360), collision=True)

    # A water tower beside the road is the one piece of built infrastructure
    # that explains why there is a road across this gorge at all. Set back
    # from the corridor so it frames the approach rather than blocking it.
    tower = props.get("SS_Raven_WaterTower")
    if tower:
        spawn_prop(world, tower, "WaterTower", 14, 78, SPEC.ground_z(14, 78),
                   rng.uniform(0, 360), collision=True)

    # Hand pumps at the road edge: the detail that says "closed rural road"
    # rather than "abandoned", and they are the smallest thing on the map, so
    # they are placed where the player walks past them on both approaches.
    pump = props.get("SS_Raven_HandPump")
    if pump:
        for i, (px, py) in enumerate(((7.6, 84.0), (-7.4, -88.0), (6.6, 70.0))):
            spawn_prop(world, pump, "HandPump_%d" % i, px, py,
                       SPEC.ground_z(px, py), rng.uniform(0, 360),
                       collision=True, tilt=rng.uniform(-4, 4))
    step("place_ridge", bool(wm or barn or tower or pump or old_barn),
         "windmill, barn, old barn, water tower, 3 hand pumps")

    # The second wreck goes in the creek bed: the second lane needs the same
    # read, and the bed is where a vehicle that went off the road would end up.
    if props.get("SS_Raven_WreckJunk"):
        spawn_prop(world, props["SS_Raven_WreckJunk"], "WreckJunk_Bed",
                   14, 4, SPEC.ground_z(14, 4), 38, collision=True, tilt=6)
    step("place_wreck_bed", props.get("SS_Raven_WreckJunk") is not None,
         "second wreck in the creek bed")

    # -- 4. materials on the placed actors -------------------------------
    # Matched on the actor label prefix, which is what spawn_prop() set. The
    # four VFX actors are not meshes and are deliberately skipped.
    VFX_TAGS = ("Fire_Engine", "Fire_Cabin", "Smoke_Column", "Embers")
    KEY_BY_PREFIX = (("WreckCar", "wreck"), ("WreckJunk", "wreck_junk"),
                     ("Roadblock", "wreck_junk"),
                     ("Drum", "drum"), ("Sandbag", "canvas"),
                     ("TrenchWall", "metal"), ("WaterTower", "metal"),
                     ("HandPump", "metal"), ("Windmill", "timber"),
                     ("Barn", "timber"), ("OldBarn", "timber"),
                     ("Roadblock", "wreck_junk"))
    applied, failed = 0, []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        lbl = actor.get_actor_label()
        if not lbl.startswith(LABEL):
            continue
        tag = lbl[len(LABEL):]
        if tag in VFX_TAGS:
            continue
        key = next((k for p, k in KEY_BY_PREFIX if tag.startswith(p)), None)
        if key is None or not mats.get(key):
            failed.append(tag + " (no material)")
            continue
        if apply_material(actor, mats[key]) >= 0:
            applied += 1
        else:
            failed.append(tag)
    step("apply_materials", not failed,
         "{} actors materialed{}".format(
             applied, "" if not failed else ", FAILED: " + str(failed[:5])))

    # -- 5. save ---------------------------------------------------------
    sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    saved = bool(sub.save_current_level()) if sub else False
    if not saved:
        saved = bool(unreal.EditorLoadingAndSavingUtils.save_current_level())
    step("save_map", saved, MAP)

    total = sum(v for v in report["placed"].values())
    report["ok"] = (not report["errors"]) and saved and total > 0
    report["placed_total"] = total


try:
    main()
except Exception:  # noqa: BLE001
    report["errors"].append(traceback.format_exc()[-2000:])
    report["ok"] = False

os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2, default=str)
