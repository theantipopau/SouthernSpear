# Southern Spear - export Fab optics (FPS Weapon Bundle, Fab Standard L-0016) to FBX
# so Tools/Blender/adfrc_weapon.py can merge them onto the A-series rifles.
import os
import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
OUT = os.path.join(PROJECT_DIR, "Art", "Weapons", "_Optics")
for name in ["SM_T4_Sight"]:
    mesh = unreal.load_asset("/Game/FPS_Weapon_Bundle/Weapons/Meshes/Accessories/" + name)
    task = unreal.AssetExportTask()
    task.object = mesh
    task.filename = os.path.join(OUT, name + ".fbx")
    task.automated = True
    task.replace_identical = True
    task.prompt = False
    task.exporter = unreal.StaticMeshExporterFBX()
    ok = unreal.Exporter.run_asset_export_task(task)
    unreal.log("[Optics] {} -> {} ok={}".format(name, task.filename, ok))
