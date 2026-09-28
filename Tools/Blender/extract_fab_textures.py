"""Extract the textures embedded in a Fab FBX (packed images) to a folder, as PNG.

    blender -b --factory-startup -P Tools/Blender/extract_fab_textures.py -- <pack.fbx> <out_dir>

Some Fab downloads carry their textures inside the FBX (the hand pump); the Unreal side (farm_dryriver.py)
imports them from <out_dir>. Prints one line per image: name, size, packed.
"""
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src)
for img in bpy.data.images:
    if not img.packed_file or img.size[0] == 0:
        print("skip", img.name, list(img.size), bool(img.packed_file))
        continue
    name = os.path.splitext(os.path.basename(img.filepath.replace("\\", "/")))[0] or img.name
    dest = os.path.join(out, name.replace(" ", "_") + ".png")
    img.filepath_raw = dest
    img.file_format = "PNG"
    img.save()
    print("saved", dest, list(img.size))
