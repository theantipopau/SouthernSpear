# Southern Spear - convert Arma MLOD .p3d files to .blend (Arma 3 Object Builder addon).
# Run without --factory-startup so the user extension is enabled:
#   blender --background --python Tools/Blender/p3d_to_blend.py -- <out_dir> <a.p3d> [b.p3d ...]
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
out_dir, files = argv[0], argv[1:]
os.makedirs(out_dir, exist_ok=True)
for f in files:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.ops.preferences.addon_enable(module="bl_ext.user_default.Arma3ObjectBuilder")
    except Exception:
        pass
    res = bpy.ops.a3ob.import_p3d(filepath=os.path.abspath(f))
    out = os.path.join(out_dir, os.path.splitext(os.path.basename(f))[0] + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print("[p3d_to_blend]", f, res, "->", out, len(bpy.data.objects), "objects")
