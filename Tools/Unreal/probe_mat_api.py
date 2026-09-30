# Probe: exact MaterialEditingLibrary API names available in this build (for authoring M_SS_CreekWater).
import json
import os
import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
keys = ("Constant3", "Constant2", "Scalar", "TextureSample", "Multiply", "Add",
        "LinearInterpolate", "Panner", "TextureCoordinate", "Fresnel", "DepthFade", "Vector")
out = {
    "MaterialEditingLibrary": sorted(m for m in dir(unreal.MaterialEditingLibrary) if not m.startswith("_")),
    "expressions": sorted(m for m in dir(unreal) if "MaterialExpression" in m and any(k in m for k in keys)),
}
with open(os.path.join(PROJECT_DIR, "Build", "probe_mat_api.json"), "w") as fh:
    json.dump(out, fh, indent=1)
print("MEL:", len(out["MaterialEditingLibrary"]), "expr:", len(out["expressions"]))
