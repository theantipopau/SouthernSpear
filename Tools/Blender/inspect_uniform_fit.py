# Southern Spear - measure a fitted ADFRC garment before blaming the render.
#
#   blender -b --factory-startup -P Tools/Blender/inspect_uniform_fit.py -- <fbx> [texture.png]
#
# A pale band on the soldier's waist has two very different causes - a hole in the garment where
# Arma's separate body mesh used to be, or a texture whose UV island is a plain panel - and a
# screenshot cannot tell them apart. This prints, per material: face count, Z range and the radius
# of the geometry from the vertical axis, so a hollow waist reads as "no faces within 15 cm of the
# spine between 100 and 115 cm". With a texture it also reports what the colour sheet actually looks
# like at each material's UV centroid, which separates "wrong texture" from "no texture at all".

import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
fbx = argv[0]
texture = argv[1] if len(argv) > 1 else None

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not meshes:
    raise SystemExit("no mesh imported from " + fbx)

def url_name(mesh, polygon):
    material = mesh.materials[polygon.material_index] if polygon.material_index < len(mesh.materials) else None
    return material.name if material else "?"


raw = bpy.data.images.load(texture) if texture else None
pixels = list(raw.pixels) if raw else None
size = (raw.size[0], raw.size[1]) if raw else None


def sheet_colour(u, v):
    """Colour at a UV in the sheet (UV origin bottom-left, image rows bottom-up)."""
    if not pixels:
        return None
    x = min(size[0] - 1, max(0, int(u % 1.0 * size[0])))
    y = min(size[1] - 1, max(0, int(v % 1.0 * size[1])))
    i = (y * size[0] + x) * 4
    return tuple(round(c * 255) for c in pixels[i:i + 3])


for obj in meshes:
    mesh = obj.data
    print("== {} : {} verts, {} faces, {} material slots".format(
        obj.name, len(mesh.vertices), len(mesh.polygons), len(mesh.materials)))
    print("   dimensions m:", tuple(round(d, 3) for d in obj.dimensions))
    for index, material in enumerate(mesh.materials):
        polys = [p for p in mesh.polygons if p.material_index == index]
        if not polys:
            print("   [{}] {}: no faces".format(index, material.name if material else "?"))
            continue
        zs = [(obj.matrix_world @ mesh.vertices[v].co).z for p in polys for v in p.vertices]
        us = [mesh.uv_layers.active.data[li].uv for p in polys for li in p.loop_indices]
        cu = sum(u.x for u in us) / len(us)
        cv = sum(u.y for u in us) / len(us)
        # Radius from the vertical axis (x right, y forward in Blender's FBX import): the torso and
        # limbs are within ~25 cm, so a slab with nothing inside 15 cm is hollow.
        radii = [(obj.matrix_world @ mesh.vertices[v].co).xy.length for p in polys for v in p.vertices]
        print("   [{}] {}: {} faces, z {:.3f}..{:.3f} m, radius {:.3f}..{:.3f} m, "
              "uv centroid ({:.3f},{:.3f}) sheet {}".format(
                  index, material.name if material else "?", len(polys), min(zs), max(zs),
                  min(radii), max(radii), cu, cv, sheet_colour(cu, cv)))

    # What the colour sheet holds at the trunk's UVs: five samples per 5 cm slab. Camo there means a
    # patchy multi-colour spread; a tight cluster of one pale colour means the sheet's island for that
    # part of the garment is a plain panel, which no amount of lighting work will fix.
    if pixels:
        print("   --- trunk UV samples (radius < 25 cm, 5 cm slabs) ---")
        for low in [0.90, 0.95, 1.00, 1.05, 1.10, 1.15, 1.20, 1.30, 1.40]:
            points = []
            for p in mesh.polygons:
                co = [obj.matrix_world @ mesh.vertices[v].co for v in p.vertices]
                z = sum(c.z for c in co) / len(co)
                if low <= z < low + 0.05 and max(c.xy.length for c in co) <= 0.25:
                    uv = mesh.uv_layers.active.data[p.loop_start].uv
                    points.append((url_name(mesh, p), uv.x, uv.y, sheet_colour(uv.x, uv.y)))
            if not points:
                print("      z {:.2f}: no trunk faces".format(low))
                continue
            step = max(1, len(points) // 5)
            for name, u, v, colour in points[::step][:5]:
                print("      z {:.2f}: {:<34} uv ({:.3f},{:.3f}) sheet {}".format(low, name, u, v, colour))

    # Z coverage of the trunk: 2.5 cm slabs, counting faces whose vertices sit within 18 cm of the
    # spine. A hollow waist shows as slabs with zero (or only far) faces.
    print("   --- trunk coverage (faces within 18 cm of the axis, 2.5 cm slabs) ---")
    slabs = {}
    for p in mesh.polygons:
        co = [obj.matrix_world @ mesh.vertices[v].co for v in p.vertices]
        z = sum(c.z for c in co) / len(co)
        if min(c.xy.length for c in co) <= 0.18:
            key = round(z / 0.025) * 0.025
            slabs[key] = slabs.get(key, 0) + 1
    for key in sorted(slabs):
        if 0.75 <= key <= 1.55:
            print("      z {:.3f} m: {} faces".format(key, slabs[key]))
