# Southern Spear - throwaway: dump the animated mannequin's bone names via the working UE 5.8 route.
# The ADF/MAF parts live in the SSExp_ObjectiveAssault game-feature plugin, which is not mounted in a
# commandlet, so their skeletons are read from the FBX instead (Tools/Blender/adfrc_gear_rig.py).
import json
import os

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "probe_manny_bones.json")
out = {}

for label, path in (("SK_Mannequin", "/Game/Characters/Heroes/Mannequin/Meshes/SK_Mannequin"),
                    ("SKM_Manny", "/Game/Characters/Heroes/Mannequin/Meshes/SKM_Manny")):
    mesh = unreal.load_asset(path)
    if mesh is None:
        out[label] = {"error": "load failed"}
        continue
    # The Mannequin path resolves to the Skeleton asset itself; a mesh needs one step of unwrapping.
    skeleton = mesh if isinstance(mesh, unreal.Skeleton) else mesh.get_editor_property("skeleton")
    pose = skeleton.get_reference_pose()
    names = [str(n) for n in pose.get_bone_names()]
    out[label] = {"skeleton": skeleton.get_path_name(), "count": len(names), "bones": names}

with open(REPORT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1)
unreal.log("SS_PROBE_DONE")
