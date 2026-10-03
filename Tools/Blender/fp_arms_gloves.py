# Southern Spear - graft the Fab "Gloves for fps game" hands (CC BY 4.0, Bobeer; Content/Sourced/Gloves) onto the
# first-person arms of Tools/Blender/fp_arms.py (Session 095; producer: "could we not utilise the glove asset we have").
#
# The pack's own hand faces (bare skin the texture script painted as a flat glove) are removed; the glove asset's
# two hands replace them, rotated and scaled onto the pack's hand by the best of the 24 axis rotations (lowest
# nearest-vertex distance), skinned by copying the pack mesh's weights from the nearest surface, and pushed under
# the pack's sleeve cuff. The glove faces get their own material slot "FP_Gloves" (the glove asset's UVs/textures).
#
# Called from fp_arms.py when SS_FP_GLOVES=1.
import itertools
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ascii_fbx_mesh  # noqa: E402

GLOVE_FBX = "E:/SouthernSpear/Content/Sourced/Gloves/source/Hands.fbx"
HAND_Y_MAX = -22.0   # glove-asset local: hand and cuff are y < this (fingers point -y), the sleeve is beyond
CUFF_OVERLAP_CM = 3.0


def _is_glove_poly(mesh, groups, poly):
    weight = {}
    for vi in poly.vertices:
        for g in mesh.vertices[vi].groups:
            weight[groups[g.group]] = weight.get(groups[g.group], 0.0) + g.weight
    if not weight:
        return False
    top = max(weight, key=weight.get)
    total = sum(weight.values()) or 1.0
    forearm = sum(v for k, v in weight.items() if "ForeArm" in k) / total
    return "Hand" in top and forearm < 0.08


def _rotations():
    out = []
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            m = Matrix.Identity(3)
            for row, (col, s) in enumerate(zip(perm, signs)):
                m[row] = (0, 0, 0)
                m[row][col] = s
            if abs(m.determinant() - 1.0) < 1e-6:
                out.append(m)
    return out


def _chamfer(a_pts, b_pts):
    kd = KDTree(len(b_pts))
    for i, p in enumerate(b_pts):
        kd.insert(p, i)
    kd.balance()
    return sum(kd.find(p)[2] for p in a_pts) / len(a_pts)


def graft(arm, hand, report):
    me = hand.data
    groups = {g.index: g.name for g in hand.vertex_groups}
    glove_polys = [p.index for p in me.polygons if _is_glove_poly(me, groups, p)]
    report["glove_polys_removed"] = len(glove_polys)

    # Weight source: an untouched copy of the pack mesh.
    src = hand.copy()
    src.data = me.copy()
    src.name = "weights_src"
    bpy.context.scene.collection.objects.link(src)

    side_ref = {}
    sleeve_end = {}
    gp = set(glove_polys)
    for side, sign in (("L", 1.0), ("R", -1.0)):
        pts = {tuple(me.vertices[v].co) for pi in glove_polys for v in me.polygons[pi].vertices if me.vertices[v].co.x * sign > 0}
        side_ref[side] = [Vector(p) for p in pts]
        xs = [me.vertices[v].co.x * sign for p in me.polygons if p.index not in gp for v in p.vertices if me.vertices[v].co.x * sign > 20.0]
        sleeve_end[side] = max(xs)
    report["sleeve_end"] = sleeve_end

    geos = {n: (v, p, uv) for n, v, p, uv in ascii_fbx_mesh.read(GLOVE_FBX)}
    rots = _rotations()
    made = []
    for side, gname in (("L", "Lplam_low"), ("R", "Rplam_low")):
        verts, polys, loopuv = geos[gname]
        keep = [i for i, v in enumerate(verts) if v[1] < HAND_Y_MAX]
        hand_pts = [Vector(verts[i]) for i in keep]
        ref = side_ref[side]
        ref_c = sum(ref, Vector()) / len(ref)
        g_c = sum(hand_pts, Vector()) / len(hand_pts)
        ref_rms = (sum((p - ref_c).length_squared for p in ref) / len(ref)) ** 0.5
        best = None
        for m in rots:
            rp = [m @ (p - g_c) for p in hand_pts]
            rms = (sum(p.length_squared for p in rp) / len(rp)) ** 0.5
            s = ref_rms / rms
            placed = [p * s + ref_c for p in rp]
            c = _chamfer(placed, ref)
            if best is None or c < best[0]:
                best = (c, m, s)
        c, m, s = best
        report["glove_fit_" + side] = {"chamfer_cm": round(c, 3), "scale": round(s, 3)}

        def xf(p):
            return m @ (Vector(p) - g_c) * s + ref_c

        sign = 1.0 if side == "L" else -1.0
        glove_wrist = min(xf(verts[i]).x * sign for i in keep)   # the end nearest the elbow
        shift = (sleeve_end[side] - CUFF_OVERLAP_CM) - glove_wrist
        report["glove_cuff_shift_" + side] = round(shift, 3)
        new_verts = [xf(v) + Vector((shift * sign, 0, 0)) for v in verts]
        keepset = set(keep)
        new_polys, new_uv = [], []
        li = 0
        for poly in polys:
            uvs = loopuv[li:li + len(poly)]
            li += len(poly)
            if all(v in keepset for v in poly):
                new_polys.append(poly)
                new_uv.append(uvs)
        mesh = bpy.data.meshes.new("gloves_" + side)
        mesh.from_pydata([tuple(v) for v in new_verts], [], new_polys)
        mesh.update()
        uvl = mesh.uv_layers.new(name=me.uv_layers.active.name)
        for poly, uvs in zip(mesh.polygons, new_uv):
            for j, uv in enumerate(uvs):
                uvl.data[poly.loop_start + j].uv = uv
        obj = bpy.data.objects.new("gloves_" + side, mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.matrix_world = hand.matrix_world.copy()   # same frame as the pack mesh (cm local, armature-scaled world)
        for g in hand.vertex_groups:
            obj.vertex_groups.new(name=g.name)
        # Weights from the pack's own mesh: inverse-distance mix of the K nearest source vertices. (Blender's
        # Data Transfer modifier gave every vertex ForeArm = 1.0 here, so the fingers never curled in game.)
        gname_of = {g.index: g.name for g in hand.vertex_groups}
        kd = KDTree(len(me.vertices))
        for vi, v in enumerate(me.vertices):
            kd.insert(v.co, vi)
        kd.balance()
        for vi, v in enumerate(mesh.vertices):
            acc = {}
            near = kd.find_n(v.co, 4)
            norm = 0.0
            for _co, si, dist in near:
                w = 1.0 / (dist + 0.05)
                norm += w
                for g in me.vertices[si].groups:
                    acc[gname_of[g.group]] = acc.get(gname_of[g.group], 0.0) + g.weight * w
            for name, w in acc.items():
                obj.vertex_groups[name].add([vi], w / norm, "REPLACE")
        names = {g.index: g.name for g in obj.vertex_groups}
        cnt = {}
        for v in mesh.vertices:
            for g in v.groups:
                if g.weight > 0.3:
                    cnt[names[g.group]] = cnt.get(names[g.group], 0) + 1
        report["xfer_" + side] = cnt
        mat = bpy.data.materials.get("FP_Gloves") or bpy.data.materials.new("FP_Gloves")
        mesh.materials.append(mat)
        made.append(obj)

    # Remove the pack's hand faces, then join the gloves in.
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in glove_polys], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(me)
    bm.free()
    bpy.data.objects.remove(src, do_unlink=True)

    for o in bpy.data.objects:
        o.select_set(False)
    for o in made:
        o.select_set(True)
    hand.select_set(True)
    bpy.context.view_layer.objects.active = hand
    bpy.ops.object.join()
    bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)
    report["glove_materials"] = [mt.name if mt else None for mt in hand.data.materials]
    return hand
