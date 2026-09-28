"""Probe the ADFRC-derived game weapon FBXes: slots, textures on import."""
import bpy
import os

ROOT = r"E:\SouthernSpear"
FILES = [
    r"Art\Weapons\A4\ADFRC\SM_A4.fbx",
    r"Art\Weapons\A416\ADFRC\SM_A416.fbx",
    r"Art\Weapons\A25\ADFRC\SM_A25.fbx",
    r"Art\Weapons\A89\ADFRC\SM_A89.fbx",
    r"Art\Weapons\A9\ADFRC\SM_A9.fbx",
    r"Art\Weapons\A88\New\SM_A88_Sourced.fbx",
]

for rel in FILES:
    path = os.path.join(ROOT, rel)
    print("=" * 60)
    print(rel)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        print(" mesh", repr(ob.name), "tris", sum(len(p.vertices) - 2 for p in ob.data.polygons),
              "uvs", [l.name for l in ob.data.uv_layers])
        for m in ob.data.materials:
            if not m:
                continue
            texs = []
            if m.use_nodes:
                for n in m.node_tree.nodes:
                    if n.type == "TEX_IMAGE" and n.image:
                        texs.append((n.image.name, tuple(n.image.size)))
            print("   slot", repr(m.name), "tex", texs if texs else "-")
    print(" images:", [(i.name, tuple(i.size)) for i in bpy.data.images])
