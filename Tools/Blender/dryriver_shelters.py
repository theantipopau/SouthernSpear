# Southern Spear - Dry River shelters and hard cover: original, script-built station structures (ADR-020).
#
#   blender -b --factory-startup -P Tools/Blender/dryriver_shelters.py
#   -> Content/Art/Environment/DryRiver/SS_DR_<Name>.fbx (+ print SS_SHELTERS <json>)
#
# The Rural Australia pack has no buildings, so these are modelled here: a corrugated-iron lean-to, an open bush
# machinery shed with half walls and a rainwater tank on a timber stand. Sandbag positions, crates, barrels and
# tubs come from the Singapore Canal pack instead (Tools/Unreal/expand_dryriver.py).
# Each mesh has its origin at the base centre (metres, Z up) and named material slots that expand_dryriver.py
# maps to the pack's textured materials: Timber (weathered raw wood), Iron (rusted metal).

import json
import math
import os

import bmesh
import bpy

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT_DIR = os.path.join(ROOT, "Content", "Art", "Environment", "DryRiver")


class Builder:
    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []

    def slot(self, name):
        if name not in self.mats:
            self.mats.append(name)
        return self.mats.index(name)

    def box(self, mat, cx, cy, cz, sx, sy, sz, rot_x=0.0, rot_z=0.0):
        """Box of size (sx, sy, sz) centred at (cx, cy, cz), rotated about X then Z (radians)."""
        idx = self.slot(mat)
        verts = []
        for dx in (-0.5, 0.5):
            for dy in (-0.5, 0.5):
                for dz in (-0.5, 0.5):
                    x, y, z = dx * sx, dy * sy, dz * sz
                    y, z = y * math.cos(rot_x) - z * math.sin(rot_x), y * math.sin(rot_x) + z * math.cos(rot_x)
                    x, y = x * math.cos(rot_z) - y * math.sin(rot_z), x * math.sin(rot_z) + y * math.cos(rot_z)
                    verts.append(self.bm.verts.new((cx + x, cy + y, cz + z)))
        v = verts
        for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            face = self.bm.faces.new([v[i] for i in f])
            face.material_index = idx

    def cylinder(self, mat, cx, cy, z0, r, h, seg=24, cap=True):
        idx = self.slot(mat)
        bottom = [self.bm.verts.new((cx + r * math.cos(2 * math.pi * i / seg), cy + r * math.sin(2 * math.pi * i / seg), z0))
                  for i in range(seg)]
        top = [self.bm.verts.new((v.co.x, v.co.y, z0 + h)) for v in bottom]
        for i in range(seg):
            j = (i + 1) % seg
            self.bm.faces.new((bottom[i], bottom[j], top[j], top[i])).material_index = idx
        if cap:
            self.bm.faces.new(list(reversed(bottom))).material_index = idx
            apex = self.bm.verts.new((cx, cy, z0 + h + r * 0.18))  # shallow conical lid
            for i in range(seg):
                self.bm.faces.new((top[i], top[(i + 1) % seg], apex)).material_index = idx

    def corrugated(self, mat, cx, cy, cz, sx, sy, rot_x=0.0, rot_z=0.0, pitch=0.076, depth=0.018, vertical=False):
        """Corrugated sheet (sx along X, sy along its own Y), ridges run along Y; tilted by rot_x, turned by rot_z.
        vertical=True stands the sheet up (a wall): its Y axis becomes Z."""
        idx = self.slot(mat)
        n = max(2, int(sx / pitch) * 2)
        rows = []
        for yy in (-0.5 * sy, 0.5 * sy):
            row = []
            for i in range(n + 1):
                x = -0.5 * sx + sx * i / n
                z = depth * (1 if i % 2 else -1) * 0.5
                if vertical:
                    lx, ly, lz = x, z, yy
                else:
                    lx, ly, lz = x, yy, z
                ly, lz = ly * math.cos(rot_x) - lz * math.sin(rot_x), ly * math.sin(rot_x) + lz * math.cos(rot_x)
                lx, ly = lx * math.cos(rot_z) - ly * math.sin(rot_z), lx * math.sin(rot_z) + ly * math.cos(rot_z)
                row.append(self.bm.verts.new((cx + lx, cy + ly, cz + lz)))
            rows.append(row)
        for i in range(n):
            f = self.bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
            f.material_index = idx
            f.smooth = True

    def export(self, name):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        mesh = bpy.data.meshes.new(name)
        self.bm.normal_update()
        self.bm.to_mesh(mesh)
        for m in self.mats:
            mesh.materials.append(bpy.data.materials.new(m))
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        # Double-sided sheets: thin iron would be invisible from behind with one-sided faces.
        mod = obj.modifiers.new("thick", "SOLIDIFY")
        mod.thickness = 0.012
        mod.offset = 0.0
        bpy.ops.object.modifier_apply(modifier="thick")
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.cube_project(cube_size=2.0)  # 2 m per UV unit: timber / iron textures tile at a plausible scale
        bpy.ops.object.mode_set(mode="OBJECT")
        path = os.path.join(OUT_DIR, name + ".fbx")
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True, global_scale=1.0,
                                 apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y",
                                 object_types={"MESH"}, mesh_smooth_type="FACE")
        dims = obj.dimensions
        return {"tris": sum(len(p.vertices) - 2 for p in mesh.polygons), "size_m": [round(dims.x, 2), round(dims.y, 2), round(dims.z, 2)],
                "slots": self.mats}


def brace(b, x0, y0, z0, x1, y1, z1, t=0.08):
    """Timber member between two points (square section t)."""
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    yaw = math.atan2(dy, dx)
    pitch = math.atan2(dz, math.hypot(dx, dy))
    # Box along X, tilted up by pitch (rotation about Y), then turned by yaw.
    idx = b.slot("Timber")
    verts = []
    for ex in (-0.5, 0.5):
        for ey in (-0.5, 0.5):
            for ez in (-0.5, 0.5):
                x, y, z = ex * length, ey * t, ez * t
                x, z = x * math.cos(pitch) - z * math.sin(pitch), x * math.sin(pitch) + z * math.cos(pitch)
                x, y = x * math.cos(yaw) - y * math.sin(yaw), x * math.sin(yaw) + y * math.cos(yaw)
                verts.append(b.bm.verts.new(((x0 + x1) / 2 + x, (y0 + y1) / 2 + y, (z0 + z1) / 2 + z)))
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        b.bm.faces.new([verts[i] for i in f]).material_index = idx


def lean_to():
    """Bush lean-to: bush-pole frame, skillion roof of rusted iron, back wall to the ground, half side wall."""
    b = Builder()
    w, d, hf, hb = 4.2, 3.0, 2.5, 1.9
    xs = (-w / 2 + 0.1, 0.0, w / 2 - 0.1)
    for x in xs:
        b.box("Timber", x, -d / 2 + 0.1, hf / 2, 0.13, 0.13, hf)
        b.box("Timber", x, d / 2 - 0.1, hb / 2, 0.13, 0.13, hb)
        brace(b, x, -d / 2 + 0.1, hf - 0.1, x, d / 2 - 0.1, hb - 0.1, 0.1)       # rafter
    b.box("Timber", 0, -d / 2 + 0.1, hf - 0.06, w + 0.2, 0.12, 0.12)            # front beam
    b.box("Timber", 0, d / 2 - 0.1, hb - 0.06, w + 0.2, 0.12, 0.12)             # back beam
    for x in (-w / 2 + 0.1, w / 2 - 0.1):                                       # knee braces
        brace(b, x, -d / 2 + 0.1, hf - 0.7, x + (0.6 if x < 0 else -0.6), -d / 2 + 0.1, hf - 0.1, 0.07)
    slope = math.atan2(hf - hb, d)
    b.corrugated("Iron", 0, 0, (hf + hb) / 2 + 0.07, w + 0.5, d / math.cos(slope) + 0.5, rot_x=-slope)
    b.corrugated("Iron", 0, d / 2 - 0.02, hb / 2 - 0.05, w, hb - 0.1, vertical=True)
    b.corrugated("Iron", -w / 2 + 0.02, 0, 0.6, d - 0.2, 1.2, rot_z=math.pi / 2, vertical=True)
    b.box("Timber", 0.6, -0.2, 0.42, 1.8, 0.4, 0.06)                            # bench seat
    for x in (-0.2, 1.4):
        b.box("Timber", x, -0.2, 0.2, 0.08, 0.35, 0.4)
    return b


def shed():
    """Open machinery shed: 3 bays, gable roof, braced posts, half walls on the back and one end."""
    b = Builder()
    w, d, h, ridge = 6.0, 4.4, 2.7, 0.7
    xs = (-w / 2 + 0.1, -w / 6, w / 6, w / 2 - 0.1)
    for x in xs:
        for y in (-d / 2 + 0.1, d / 2 - 0.1):
            b.box("Timber", x, y, h / 2, 0.15, 0.15, h)
        brace(b, x, -d / 2 + 0.1, h, x, 0.0, h + ridge, 0.11)                    # rafters
        brace(b, x, d / 2 - 0.1, h, x, 0.0, h + ridge, 0.11)
        b.box("Timber", x, 0, h - 0.05, 0.1, d, 0.12)                            # tie beam
    for y in (-d / 2 + 0.1, d / 2 - 0.1):
        b.box("Timber", 0, y, h - 0.06, w + 0.2, 0.13, 0.13)
        for x in xs[:-1]:
            brace(b, x, y, h - 0.8, x + 0.7, y, h - 0.1, 0.08)
    b.box("Timber", 0, 0, h + ridge, w + 0.4, 0.12, 0.12)                        # ridge beam
    half = math.atan2(ridge, d / 2)
    run = (d / 2 + 0.35) / math.cos(half)
    for sgn in (-1, 1):
        b.corrugated("Iron", 0, sgn * (d / 4 + 0.08), h + ridge / 2 + 0.08, w + 0.6, run,
                     rot_x=sgn * -half if sgn > 0 else half)
    b.corrugated("Iron", 0, d / 2 - 0.03, 0.62, w, 1.24, vertical=True)
    b.corrugated("Iron", w / 2 - 0.03, 0, 0.62, d, 1.24, rot_z=math.pi / 2, vertical=True)
    b.box("Timber", 0, d / 2 - 0.1, 1.27, w, 0.09, 0.1)
    return b


def tank():
    """Corrugated rainwater tank on a timber stand, with a ladder and outlet."""
    b = Builder()
    r, h, stand, seg = 1.45, 2.3, 0.7, 96
    for x in (-1.0, 0.0, 1.0):
        for y in (-1.0, 1.0):
            b.box("Timber", x, y, stand / 2, 0.16, 0.16, stand)
    for y in (-1.0, 1.0):
        brace(b, -1.0, y, 0.1, 0.0, y, stand - 0.05, 0.07)
        brace(b, 1.0, y, 0.1, 0.0, y, stand - 0.05, 0.07)
    b.box("Timber", 0, 0, stand + 0.06, 3.1, 3.1, 0.12)
    idx = b.slot("Iron")
    z0 = stand + 0.12
    rings = [z0 + h * k / 12 for k in range(13)]
    loops = []
    for z in rings:
        loop = []
        for i in range(seg):
            t = 2 * math.pi * i / seg
            rr = r + 0.022 * math.sin(t * seg / 2)  # vertical corrugations
            loop.append(b.bm.verts.new((rr * math.cos(t), rr * math.sin(t), z)))
        loops.append(loop)
    for a, c in zip(loops, loops[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            f = b.bm.faces.new((a[i], a[j], c[j], c[i]))
            f.material_index = idx
            f.smooth = True
    top = loops[-1]
    apex = b.bm.verts.new((0, 0, rings[-1] + 0.3))
    for i in range(seg):
        b.bm.faces.new((top[i], top[(i + 1) % seg], apex)).material_index = idx
    b.bm.faces.new(list(reversed(loops[0]))).material_index = idx
    b.cylinder("Iron", r + 0.05, 0.5, 0.0, 0.04, z0 + 0.3, seg=8, cap=False)       # outlet
    b.cylinder("Iron", 0.0, 0.0, rings[-1] + 0.28, 0.25, 0.06, seg=16)            # inspection hatch
    for sgn in (-1, 1):                                                            # ladder rails
        b.box("Iron", -r - 0.12, sgn * 0.22, (z0 + rings[-1]) / 2 + 0.2, 0.04, 0.04, rings[-1] - z0 + 0.5)
    for k in range(8):
        b.box("Iron", -r - 0.12, 0, z0 + 0.3 * (k + 1), 0.03, 0.44, 0.03)
    return b


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    out = {}
    for name, fn in (("LeanTo", lean_to), ("Shed", shed), ("Tank", tank)):
        out["SS_DR_" + name] = fn().export("SS_DR_" + name)
    print("SS_SHELTERS " + json.dumps(out))


main()
