# Southern Spear - ambient-occlusion bake for the first-person arms (Session 094).
# The glove region of T_FP_Arms_*_BC was a flat colour fill: no finger separation, no knuckles, so the hands
# read as mitts. This bakes AO from the arms mesh itself into its own UV layout; make_fp_arms_texture.py then
# multiplies it into the sleeve and glove.
#
#   blender -b --factory-startup -P Tools/Blender/bake_fp_arms_ao.py -- Build/fp_arms/SK_FP_Arms_Rifle.fbx Build/fp_arms/AO_Rifle.png
import sys

import bpy

SRC, OUT = sys.argv[sys.argv.index("--") + 1:][:2]
SIZE = 2048

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, automatic_bone_orientation=False)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
assert meshes, "no mesh in " + SRC
for o in bpy.data.objects:
    o.select_set(False)

img = bpy.data.images.new("ao", SIZE, SIZE, alpha=False)
img.colorspace_settings.name = "Non-Color"
for o in meshes:
    o.data.materials.clear()
    mat = bpy.data.materials.new("bake")
    mat.use_nodes = True
    node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = img
    mat.node_tree.nodes.active = node
    o.data.materials.append(mat)
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]

sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 64
sc.cycles.bake_type = "AO"
sc.render.bake.margin = 16
bpy.ops.object.bake(type="AO")
img.filepath_raw = OUT
img.file_format = "PNG"
img.save()
print("[bake_fp_arms_ao] wrote", OUT)
