"""Performance pass: Nanite (and the Nanite usage flag on base materials) for
opaque/masked static meshes used by the playable maps; non-Nanite props
overflowed virtual shadow maps. Vegetation with authored LODs, translucent
meshes and the weapons stay classic (see fix_visual_regressions.py). Report: Build/nanite_report.json."""
import json
import unreal

MAPS = ["/Game/Maps/L_RedGum_01", "/Game/Maps/L_DryRiver_01", "/Game/Maps/L_Saltbush_01", "/Game/Maps/L_SelatCanal_01"]
WEAPONS = ["/SSExp_ObjectiveAssault/Weapons/{0}/SM_{0}".format(n) for n in ["A88", "A88G", "A89", "A4", "A416", "A25", "A9"]]
eal = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
report = {"meshes_enabled": 0, "meshes_skipped_translucent": [], "materials_flagged": 0, "per_map": {}}


def base_material(mi):
    while isinstance(mi, unreal.MaterialInstance):
        mi = mi.get_editor_property("parent")
    return mi


def materials_of(mesh):
    out = []
    for sm in mesh.get_editor_property("static_materials"):
        m = sm.get_editor_property("material_interface")
        if m:
            out.append(m)
    return out


paths = set()  # weapons stay non-Nanite: translucent lenses (fix_visual_regressions.py)
for map_path in MAPS:
    if not les.load_level(map_path):
        continue
    found = set()
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh = comp.get_editor_property("static_mesh")
            if mesh:
                found.add(mesh.get_path_name().split(".")[0])
    report["per_map"][map_path] = len(found)
    paths |= found

flagged = set()
for path in sorted(paths):
    mesh = unreal.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh) or path.startswith("/Engine"):
        continue
    # Vegetation with authored LODs stays classic: Nanite recoloured the Rural Australia leaves.
    if mesh.get_num_lods() > 1 and any(k in path.lower() for k in ("vegetation", "tree", "plant", "grass", "bush", "foliage", "shrub", "scrub", "leaf", "fern")):
        continue
    mats = materials_of(mesh)
    bases = [base_material(m) for m in mats]
    if any(b and b.get_editor_property("blend_mode") in (unreal.BlendMode.BLEND_TRANSLUCENT, unreal.BlendMode.BLEND_ADDITIVE, unreal.BlendMode.BLEND_MODULATE) for b in bases):
        report["meshes_skipped_translucent"].append(path)
        continue
    for b in bases:
        if b and b.get_path_name() not in flagged and not b.get_path_name().startswith("/Engine"):
            flagged.add(b.get_path_name())
            if not b.get_editor_property("used_with_nanite"):
                b.set_editor_property("used_with_nanite", True)
                unreal.MaterialEditingLibrary.recompile_material(b)
                eal.save_loaded_asset(b)
                report["materials_flagged"] += 1
    nanite = mesh.get_editor_property("nanite_settings")
    if not nanite.get_editor_property("enabled"):
        nanite.set_editor_property("enabled", True)
        mesh.set_editor_property("nanite_settings", nanite)
        if eal.save_loaded_asset(mesh):
            report["meshes_enabled"] += 1
report["meshes_considered"] = len(paths)
json.dump(report, open("E:/SouthernSpear/Build/nanite_report.json", "w"), indent=1)
unreal.log("SS_NANITE_OPT meshes={} materials={} translucent_skipped={}".format(
    report["meshes_enabled"], report["materials_flagged"], len(report["meshes_skipped_translucent"])))
