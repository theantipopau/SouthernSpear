"""Sky domes, cloud cards and other huge or unlit meshes must stay classic:
Nanite drew the Red Gum sky dome as a dark patterned shell (producer: "no sky
box"). Reverts Nanite on meshes used by the playable maps whose name marks a
sky/cloud/dome/atmosphere or whose bounds exceed 1 km, or whose base material
is unlit. Report: Build/sky_nanite_report.json."""
import json
import unreal

MAPS = ["/Game/Maps/L_RedGum_01", "/Game/Maps/L_DryRiver_01", "/Game/Maps/L_Saltbush_01", "/Game/Maps/L_SelatCanal_01"]
KEYS = ("sky", "cloud", "dome", "atmos", "fog", "horizon", "backdrop")
eal = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
out = []
seen = set()


def base(m):
    while isinstance(m, unreal.MaterialInstance):
        m = m.get_editor_property("parent")
    return m


for map_path in MAPS:
    if not les.load_level(map_path):
        continue
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh = comp.get_editor_property("static_mesh")
            if not mesh or mesh.get_path_name() in seen:
                continue
            seen.add(mesh.get_path_name())
            s = mesh.get_editor_property("nanite_settings")
            if not s.get_editor_property("enabled") or mesh.get_path_name().startswith("/Engine"):
                continue
            box = mesh.get_bounding_box()
            size = max(box.max.x - box.min.x, box.max.y - box.min.y, box.max.z - box.min.z)
            unlit = any(base(m.get_editor_property("material_interface")) and
                        base(m.get_editor_property("material_interface")).get_editor_property("shading_model") == unreal.MaterialShadingModel.MSM_UNLIT
                        for m in mesh.get_editor_property("static_materials"))
            name = mesh.get_name().lower()
            if any(k in name for k in KEYS) or size > 100000 or unlit:
                s.set_editor_property("enabled", False)
                mesh.set_editor_property("nanite_settings", s)
                eal.save_loaded_asset(mesh)
                out.append({"mesh": mesh.get_path_name(), "size_cm": round(size), "unlit": unlit})
json.dump(out, open("E:/SouthernSpear/Build/sky_nanite_report.json", "w"), indent=1)
unreal.log("SS_SKYNANITE " + json.dumps(out))
