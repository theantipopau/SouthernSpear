# Southern Spear - Ravenshoe Crossing outer ground ("skirt"): the world beyond the 200 x 300 m playable terrain.
#
#   blender -b --factory-startup -P Tools/Blender/ravenshoe_skirt.py
#   -> Content/Art/Blockout/SS_MAP_Ravenshoe_Skirt.fbx (+ print SS_SKIRT <json>)
#
# The first play test showed a black band on the horizon: the terrain stops at the playable edge and
# there is nothing beyond it. The skirt is a ring mesh around the playable rectangle, the same fix
# Dry River took (dryriver_skirt.py, Session 041):
#   - its grid lines up with the terrain's 2 m grid (ravenshoe_blockout.build_terrain) near the
#     boundary, so the shared edge vertices coincide and there is no seam; spacing then grows outward;
#   - heights continue the analytic ground_z() of Tools/Common/ravenshoe_spec.py (the gorge walls and
#     the road corridor carry on past the edge), blend into rolling hills within ~300 m, and rise into
#     a distant rim so the horizon is ground, not sky (ravenshoe_world.height);
#   - same FBX axes/units as ravenshoe_blockout.py; the Unreal actor sits at the origin like the terrain.
# Presentation only: the skirt is outside the playable area; the expand pass keeps players in.

import json
import os
import sys

import bpy

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "Tools", "Common"))
from ravenshoe_spec import MAP_HALF_X, MAP_N, MAP_S  # noqa: E402
from ravenshoe_world import EXTENT_X, EXTENT_Y, height  # noqa: E402

OUT = os.path.join(ROOT, "Content", "Art", "Blockout", "SS_MAP_Ravenshoe_Skirt.fbx")
CELL = 2.0        # terrain grid (ravenshoe_blockout: TERRAIN_STEP)
DENSE = 60.0      # m of 2 m cells beyond the edge
GROWTH, MAX_CELL = 1.18, 60.0

HY = max(abs(MAP_N), abs(MAP_S))   # 150


def axis(half_play, extent):
    """Grid coordinates: the terrain's own 2 m lines inside and DENSE m beyond, then growing cells."""
    inner = [-half_play + i * CELL for i in range(int(round(2 * half_play / CELL)) + 1)]
    outer, x, step = [], half_play, CELL
    while x < extent:
        x += step
        outer.append(min(x, extent))
        if x - half_play > DENSE:
            step = min(step * GROWTH, MAX_CELL)
    return [-v for v in reversed(outer)] + inner + outer


def main():
    hx, hy = MAP_HALF_X, HY
    xs, ys = axis(hx, EXTENT_X), axis(hy, EXTENT_Y)
    verts, index, faces = [], {}, []
    eps = 1e-6
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            x0, x1, y0, y1 = xs[i], xs[i + 1], ys[j], ys[j + 1]
            # Skip cells inside the playable rectangle: the terrain mesh covers them.
            if x0 >= -hx - eps and x1 <= hx + eps and y0 >= -hy - eps and y1 <= hy + eps:
                continue
            quad = []
            for (a, b) in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)):
                key = (a, b)
                if key not in index:
                    index[key] = len(verts)
                    verts.append((xs[a], ys[b], height(xs[a], ys[b])))
                quad.append(index[key])
            faces.append(tuple(quad))

    bpy.ops.wm.read_factory_settings(use_empty=True)
    mesh = bpy.data.meshes.new("SS_MAP_Ravenshoe_Skirt_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    # World-planar UVs (one unit per 10 m), the same convention as dryriver_skirt.py: the ground
    # material is world-aligned, and a mesh without any UV channel rendered with the default grey.
    uv = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        x, y, _ = verts[loop.vertex_index]
        uv.data[loop.index].uv = (x / 10.0, y / 10.0)
    for poly in mesh.polygons:
        poly.use_smooth = True
    obj = bpy.data.objects.new("SS_MAP_Ravenshoe_Skirt", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, apply_unit_scale=True, global_scale=1.0,
                             apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y",
                             object_types={"MESH"}, mesh_smooth_type="FACE")
    # The shared edge must continue the terrain exactly, or there is a visible crease at the old edge.
    edge_err = max(abs(height(x, y) - __import__("ravenshoe_spec").ground_z(x, y))
                   for x in (-hx, hx) for y in [-hy + k * CELL for k in range(int(2 * hy / CELL) + 1)])
    zs = [v[2] for v in verts]
    print("SS_SKIRT " + json.dumps({"out": OUT, "verts": len(verts), "faces": len(faces),
                                    "grid": [len(xs), len(ys)], "z_range_m": [round(min(zs), 1), round(max(zs), 1)],
                                    "edge_height_error_m": round(edge_err, 4)}))


main()
