"""Objective flags (presentation): MI_SS_Flag_Friendly (the Australian flag
tile of the Fab World Flags atlas, L-0016) and MI_SS_Flag_MAF (our fictional
flag, Tools/Textures/maf_flag.py) under /SSExp_ObjectiveAssault/Flags, on the
pack's cloth-flag material. USSObjectiveFlagSubsystem shows them per viewer.
Report: Build/flags_setup.json."""
import json
import unreal

DEST = "/SSExp_ObjectiveAssault/Flags"
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
report = {}

au = unreal.load_asset("/Game/World_Flags/Material_Instances/MI_au")
base = au.get_editor_property("parent")


def mi(name):
    path = DEST + "/" + name
    if eal.does_asset_exist(path):
        return unreal.load_asset(path)
    return tools.create_asset(name, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())


friendly = mi("MI_SS_Flag_Friendly")
friendly.set_editor_property("parent", base)
for p in au.get_editor_property("texture_parameter_values"):
    mel.set_material_instance_texture_parameter_value(friendly, p.get_editor_property("parameter_info").get_editor_property("name"), p.get_editor_property("parameter_value"))
for p in au.get_editor_property("scalar_parameter_values"):
    mel.set_material_instance_scalar_parameter_value(friendly, p.get_editor_property("parameter_info").get_editor_property("name"), p.get_editor_property("parameter_value"))
eal.save_loaded_asset(friendly)

task = unreal.AssetImportTask()
task.filename = "E:/SouthernSpear/Art/Flags/T_SS_Flag_MAF.png"
task.destination_path = DEST
task.destination_name = "T_SS_Flag_MAF"
task.replace_existing = True
task.automated = True
task.save = True
tools.import_asset_tasks([task])
tex = unreal.load_asset(DEST + "/T_SS_Flag_MAF")
maf = mi("MI_SS_Flag_MAF")
maf.set_editor_property("parent", base)
mel.set_material_instance_texture_parameter_value(maf, "BC", tex)
mel.set_material_instance_scalar_parameter_value(maf, "UV_Size", 1.0)
mel.set_material_instance_scalar_parameter_value(maf, "Xoffset", 0.0)
mel.set_material_instance_scalar_parameter_value(maf, "Yoffset", 0.0)
eal.save_loaded_asset(maf)
report = {"friendly": friendly is not None, "maf": maf is not None and tex is not None, "base": base.get_path_name()}
json.dump(report, open("E:/SouthernSpear/Build/flags_setup.json", "w"), indent=1)
unreal.log("SS_FLAGS " + json.dumps(report))
