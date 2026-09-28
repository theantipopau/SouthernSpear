# Southern Spear - real surfaces on the Ravenshoe Crossing bridge (ADR-021, ADR-029).
#
# The bridge, its abutments and the gatehouse were four constant materials, so
# the one structure the map is named for read as untextured blockout however
# good the geometry was. This imports the script-generated surface sets from
# Tools/Textures/make_ravenshoe_surfaces.py, builds one material instance per
# surface from the project's own parameterised M_SS_ScanPBR, and assigns them
# to the three authored meshes.
#
# The textures are Class F original (L-0011), generated from noise on the same
# ground as the character camo sets (CH-TEX-001). No pack texture is copied and
# no vendor material is touched; the pack meshes keep their own MI_SS_Raven_*
# instances from dress_ravenshoe_props.py.
#
# Assignment goes through the per-instance component override
# StaticMeshComponent.set_material(i, mat), not through StaticMesh.Materials.
# On 5.8 every route to a mesh's own material slots is a silent no-op:
# writing into get_editor_property("static_materials") mutates a copy,
# set_editor_property("static_materials", slots) does not persist, and the slots
# read back [None, None] afterwards. The component override persists and is
# what renders.
#
# Idempotent: the instances are rebuilt each run and the overrides re-applied.
# Writes Build/ravenshoe_surfaces_setup.json.
#
# RUN ORDER - this pass MUST be last:
#     import_ravenshoe -> dress_ravenshoe_props -> setup_ravenshoe_surfaces
# import_ravenshoe re-imports the bridge FBX with replace_existing and re-spawns
# the SS_Raven_Geo_* actors, which resets both the mesh's material slots and the
# per-instance overrides. Running this pass before it means the next import
# silently strips every surface again - the map goes back to flat colours and
# the Road slot goes to WorldGridMaterial, with nothing reporting an error.
# audit_ravenshoe.py checks for exactly that, which is how it was caught.

import json
import os
import traceback

import unreal

PROJECT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
TEX_DEST = "/Game/Art/Environment/Ravenshoe/Surfaces"
MAT_DEST = "/Game/Art/Environment/Ravenshoe/Materials"
SCAN_PBR = "/Game/Art/Environment/Fab/M_SS_ScanPBR"
MAP = "/Game/Maps/L_Ravenshoe_01"
REPORT = os.path.join(PROJECT, "Build", "ravenshoe_surfaces_setup.json")

GEO_PREFIX = "SS_Raven_Geo_"

# Surface -> set, tint and the TILING scalar.
#
# Tiling is the one place the apparent size of a texture is decided, so it is
# derived from the UVs the blockout actually writes, not chosen by eye.
#
# The blockout unwraps with bpy.ops.uv.cube_project(cube_size=2.0) for the
# bridge and the gatehouse, which makes ONE UV UNIT = 2 METRES, and with a
# world-space planar projection at v/4.0 for the terrain, which makes one UV
# unit = 4 m. Repeats across the mesh are therefore uv_range * Tiling, and for
# a target tile size S metres:
#
#     Tiling = uv_metres_per_unit / S
#
# The first pass of this table assumed UVs ran 0..1 per face and used values
# around 3.75. Against a 2 m UV scale that is a 0.53 m tile: a 1024 map
# repeating every half metre reads as fine noise, which is the same greybox
# problem wearing a texture. The values below are the arithmetic.
UV_M_PER_UNIT = {"bridge": 2.0, "terrain": 4.0}

SURFACES = {
    # The running surface: one tile per 2.0 m of road, so the aggregate stays
    # gravel-sized against a 7.5 m deck instead of becoming a flat wash.
    "Road": {"set": "Gravel", "tint": (0.94, 0.92, 0.88),
             "tile_m": 2.0, "uv": "bridge"},
    # The lattice and the parapets: 1.5 m per tile, so the rust runs read at
    # the scale of a weathered iron member rather than as a stain.
    "Iron": {"set": "RustIron", "tint": (1.0, 1.0, 1.0),
             "tile_m": 1.5, "uv": "bridge"},
    # Deck slab, kerbs and soffit. Same paint, 0.9 m per tile, because the
    # members are smaller and the plate seams need to sit closer together.
    "Deck": {"set": "PaintedSteel", "tint": (1.0, 1.0, 1.0),
             "tile_m": 0.9, "uv": "bridge"},
    # Abutments and the gatehouse. 1.2 m per tile puts 8 courses in 1.2 m,
    # about 150 mm each, which is the coursing rubble granite is built at.
    "Stone": {"set": "Granite", "tint": (1.0, 1.0, 1.0),
              "tile_m": 1.2, "uv": "bridge"},
}

# Which slots of which mesh each surface drives. The bridge carries four, not
# three: the abutments are a Stone slot in the same mesh, so mapping only
# Iron/Deck/Road left the masonry on the flat safety-net colour while the rest
# of the bridge was textured.
SLOT_MAP = {
    "SS_Raven_Bridge": {"Iron": "Iron", "Deck": "Deck", "Road": "Road",
                        "Stone": "Stone"},
    "SS_Raven_Gatehouse": {"Stone": "Stone"},
    "SS_MAP_Ravenshoe_01": {"Terrain": None},   # terrain keeps its constant
}

MAPS = ("BC", "N", "R", "AO", "M")

eal = unreal.EditorAssetLibrary
report = {"ok": False, "textures": {}, "materials": {}, "surface_params": {},
          "assigned": {}, "errors": [], "warnings": []}


def err(msg):
    report["errors"].append(str(msg))


def warn(msg):
    report["warnings"].append(str(msg))


def import_textures():
    """Import the 20 generated PNGs. Missing files are reported, not fatal."""
    src = os.path.join(PROJECT, "Art", "Environment", "Ravenshoe", "Surfaces")
    out = {}
    for set_name in sorted({v["set"] for v in SURFACES.values()}):
        for suffix in MAPS:
            fname = "T_SS_Raven_{}_{}.png".format(set_name, suffix)
            path = os.path.join(src, fname)
            if not os.path.isfile(path):
                err("missing source texture " + fname)
                continue
            dest = "{}/T_SS_Raven_{}_{}".format(TEX_DEST, set_name, suffix)
            task = unreal.AssetImportTask()
            task.set_editor_property("filename", path)
            task.set_editor_property("destination_path", TEX_DEST)
            task.set_editor_property("automated", True)
            task.set_editor_property("replace_existing", True)
            task.set_editor_property("save", True)
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            tex = eal.load_asset(dest)
            if tex is None:
                err("import produced nothing for " + fname)
                continue
            out["{}_{}".format(set_name, suffix)] = tex
    report["textures"] = {k: v.get_path_name() for k, v in out.items()}
    report["texture_uv_scale_note"] = "blockout: cube_project(2.0) => 1 uv = 2 m"
    return out


def build_instance(slot, cfg, textures):
    """One MI_SS_Raven_<Slot> off M_SS_ScanPBR, wired to the five maps."""
    set_name = cfg["set"]
    name = "MI_SS_Raven_{}".format(slot)
    path = "{}/{}".format(MAT_DEST, name)
    parent = unreal.load_asset(SCAN_PBR)
    if parent is None:
        err("parent material missing: " + SCAN_PBR)
        return None

    missing = [s for s in MAPS if "{}_{}".format(set_name, s) not in textures]
    if missing:
        err("{}: no texture for {}".format(slot, ", ".join(missing)))
        return None

    # Rebuild rather than fetch-or-edit: the instance is derived entirely from
    # the textures and the table above, so a stale one is never what we want.
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    fmi = unreal.MaterialInstanceConstantFactoryNew()
    mi = tools.create_asset(name, MAT_DEST, unreal.MaterialInstanceConstant, fmi)
    if mi is None:
        err("could not create " + path)
        return None
    # MaterialInstanceConstantFactoryNew has no initial_parent in 5.8; the
    # parent goes on the instance afterwards.
    mi.set_editor_property("parent", parent)

    # Parameter names are the ones dress_ravenshoe_props.py proves work on this
    # build. The AO slot is "AO", NOT "AmbientOcclusion" - the latter is the
    # material input name, and setting it silently does nothing.
    lib = unreal.MaterialEditingLibrary
    for param, suffix in (("BaseColor", "BC"), ("Normal", "N"),
                          ("Roughness", "R"), ("AO", "AO"),
                          ("Metalness", "M")):
        lib.set_material_instance_texture_parameter_value(
            mi, param, textures["{}_{}".format(set_name, suffix)])

    tint = cfg["tint"]
    tiling = UV_M_PER_UNIT[cfg["uv"]] / cfg["tile_m"]
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        mi, "Tint", unreal.LinearColor(tint[0], tint[1], tint[2], 1.0))
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        mi, "Tiling", float(tiling))
    report["surface_params"][name] = {"tile_m": cfg["tile_m"],
                                      "uv_m_per_unit": UV_M_PER_UNIT[cfg["uv"]],
                                      "tiling": round(tiling, 4),
                                      "set": cfg["set"]}

    eal.save_loaded_asset(mi)
    return mi


def apply_overrides(materials):
    """Assign the instances to the authored meshes via COMPONENT overrides.

    The map must already be open and loaded. A blank untitled level will accept
    a spawn and report clean and then be discarded on save, so the map is loaded
    explicitly and the presence of our own geometry is asserted before anything
    is written.
    """
    if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
        err("could not open " + MAP)
        return
    world = unreal.EditorLevelLibrary.get_editor_world()
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = sub.get_all_level_actors()

    geo = [a for a in actors if a.get_actor_label().startswith(GEO_PREFIX)]
    if not geo:
        err("no {} actors in {}: the level did not load".format(GEO_PREFIX, MAP))
        return
    report["actors_in_level"] = len(actors)
    report["geo_actors"] = len(geo)

    for actor in geo:
        label = actor.get_actor_label()
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp is None:
            warn("{}: no StaticMeshComponent".format(label))
            continue
        mesh = comp.get_editor_property("static_mesh")
        if mesh is None:
            warn("{}: no static mesh".format(label))
            continue
        mesh_name = mesh.get_name()
        slot_map = SLOT_MAP.get(mesh_name)
        if slot_map is None:
            continue

        # Slot NAMES are read off the mesh. Reading static_materials is fine;
        # it is only WRITING to it that is a silent no-op on 5.8, which is why
        # the override below goes through the component.
        try:
            slots = mesh.get_editor_property("static_materials")
            names = [str(s.get_editor_property("material_slot_name") or "").strip()
                     for s in slots]
        except Exception as exc:  # noqa: BLE001
            warn("{}: cannot read material slots: {}".format(mesh_name, exc))
            continue

        n = comp.get_num_materials()
        hit = 0
        for i, slot_name in enumerate(names[:n]):
            if not slot_name:
                continue
            key = next((k for k in slot_map if slot_name.endswith(k)), None)
            if key is None:
                warn("{}: slot {} {!r} is not in the surface table"
                     .format(mesh_name, i, slot_name))
                continue
            mat = materials.get(slot_map[key])
            if mat is None:
                continue
            comp.set_material(i, mat)
            hit += 1
        report["assigned"][mesh_name] = "{}/{}".format(hit, len(names))

    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP)


def main():
    textures = import_textures()
    report["textures_imported"] = len(textures)

    materials = {}
    for slot, cfg in SURFACES.items():
        mi = build_instance(slot, cfg, textures)
        if mi is not None:
            materials[slot] = mi
            report["materials"][mi.get_name()] = mi.get_path_name()

    if len(materials) != len(SURFACES):
        err("only %d of %d materials built" % (len(materials), len(SURFACES)))
    else:
        try:
            apply_overrides(materials)
        except Exception:  # noqa: BLE001
            err("apply_overrides:\n" + traceback.format_exc())

    report["ok"] = not report["errors"]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w") as fh:
        json.dump(report, fh, indent=1)


main()
