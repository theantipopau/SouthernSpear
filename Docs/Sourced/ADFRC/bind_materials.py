"""Re-export FBX models with PNG textures bound into each material.

The ADFRC FBX files carry Arma material *names* that embed the texture, e.g.

    P3D: heli_attack_03_body_indp_co.paa :: heli_attack_03_adds.rvmat

but no image bindings, so meshes import into Unreal untextured.  This script
re-imports each FBX, resolves the texture name to a PNG under Textures\, builds
a Principled BSDF node tree with the right image on the right socket (inferred
from the Arma filename suffix), and re-exports.

Run:
  blender --background --python bind_materials.py -- <fbx_root> <dst_root> <tex_root> <listfile>
"""
import os
import re
import sys
import time
import traceback

import bpy

FBX_ROOT = None
DST_ROOT = None
TEX_ROOT = None

# Arma filename suffix -> UE Principled BSDF socket it should drive.
# Verified suffix -> channel census over Textures/:
#   _co 692  _nohq 409  _smdi 391  _as 327  _mc 2  _ca (camo/albedo variant)
SUFFIX_SOCKET = {
    "co": "Base Color",
    "ca": "Base Color",
    "nohq": "Normal Map",
    "n": "Normal Map",
    "smdi": "Roughness",        # packed spec+metal+dirt; UE ORM needs unpacking
    "sm": "Roughness",
    "di": "Metallic",
    "as": "Emissive",           # ambient-smooth approximation
    "mc": "Metallic",
    "ao": "Ambient Occlusion",
    "gi": "Roughness",
    "ret": "Emissive",           # Arma reticles are drawn with colour
    "ca2": "Base Color",
    "01": "Base Color",
    "02": "Base Color",
    "roo": "Base Color",
    "empty": "Base Color",
}

# Arma lets a material name carry an inline flat colour instead of a texture,
# e.g.  P3D: #(argb,8,8,3)color(1.000,0.310,0.310,1.000,co) :: foo.rvmat
INLINE_COLOR_RE = re.compile(
    r"color\(\s*(?P<r>[\d.]+)\s*,\s*(?P<g>[\d.]+)\s*,\s*(?P<b>[\d.]+)"
    r"\s*,\s*(?P<a>[\d.]+)\s*,\s*(?P<kind>\w+)\s*\)")

# Material name shapes seen in the FBX material stack.
MAT_RE = re.compile(r"P3D:\s*(?P<tex>[^:]*?)\s*::\s*(?P<mat>.+?)\s*$")

# Textures that ship with the Arma engine, not with ADFRC.  Absent from
# Textures/ by design; a neutral stand-in keeps the material non-black.
ENGINE_TEX = ("a3\\", "z\\", "ace\\", "bis_", "config\\", "ui\\")

# Arma procedural materials (no texture at all in the .p3d).  Give each a
# plausible UE look so the surface is not pure black.
PROCEDURAL_LOOK = {
    "glass": dict(rough=0.05, metal=0.0, alpha=0.25),
    "plexiglass": dict(rough=0.12, metal=0.0, alpha=0.3),
    "iron": dict(rough=0.55, metal=1.0),
    "steel": dict(rough=0.45, metal=1.0),
    "armour": dict(rough=0.6, metal=0.85),
    "armor": dict(rough=0.6, metal=0.85),
    "tyre": dict(rough=0.9, metal=0.0),
    "rubber": dict(rough=0.9, metal=0.0),
    "plastic": dict(rough=0.35, metal=0.0),
}


def clear_scene():
    """Empty the scene without read_factory_settings (unloads extensions)."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    for blocks in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials,
                   bpy.data.actions, bpy.data.images, bpy.data.node_groups):
        for d in list(blocks):
            if d.users == 0:
                blocks.remove(d)


# ---------------------------------------------------------------- textures

def build_index():
    """Map lowercase texture basename -> png path, and basename -> [paths].

    ADFRC repeats a texture name in many packs (the same mag58 texture lives
    under ADF_Weapons and ADF_Wheeled); any one of them is byte-identical, so a
    first-wins index is correct and cheap.
    """
    idx = {}
    for r, _d, fs in os.walk(TEX_ROOT):
        for f in fs:
            if not f.lower().endswith(".png"):
                continue
            key = os.path.splitext(f)[0].lower()
            idx.setdefault(key, os.path.join(r, f))
    return idx


def suffix_of(tex_name):
    stem = os.path.splitext(os.path.basename(tex_name))[0].lower()
    parts = stem.split("_")
    return parts[-1] if len(parts) > 1 else ""


def socket_for(tex_name):
    return SUFFIX_SOCKET.get(suffix_of(tex_name))


# Blender renamed several Principled sockets across versions (4.x "Emission" ->
# 5.x "Emission Color", etc.), so resolve by trying each known alias.
SOCKET_ALIASES = {
    "Emissive": ("Emission Color", "Emission"),
    "Base Color": ("Base Color",),
    "Normal Map": ("Normal",),
    "Roughness": ("Roughness",),
    "Metallic": ("Metallic",),
    "Ambient Occlusion": ("Ambient Occlusion",),
}


def resolve_socket(bsdf, name):
    for cand in SOCKET_ALIASES.get(name, (name,)):
        if cand in bsdf.inputs:
            return bsdf.inputs[cand]
    return None


def bind(mat, tex_png, socket, tex_root):
    """Point a Principled socket at a PNG, using a relative path UE can find."""
    if not socket:
        return False
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
        if out is None:
            out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    img = bpy.data.images.load(tex_png, check_existing=True)
    tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE"), None)
    if tex is None:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.location = (bsdf.location.x - 300, bsdf.location.y)
    tex.image = img

    if socket == "Normal Map":
        # _nohq is a two-channel DXT5 normal; UE expects tangent-space RGB.
        nrm = next((n for n in nt.nodes if n.type == "NORMAL_MAP"), None)
        if nrm is None:
            nrm = nt.nodes.new("ShaderNodeNormalMap")
            nrm.location = (bsdf.location.x - 300, bsdf.location.y - 300)
        nrm.space = "TANGENT"
        nrm.uv_map = "UVMap"
        nt.links.new(tex.outputs["Color"], nrm.inputs["Color"])
        nt.links.new(nrm.outputs["Normal"], resolve_socket(bsdf, "Normal Map"))
    else:
        sock = resolve_socket(bsdf, socket)
        if sock is None:
            raise KeyError("Principled has no socket for %r" % socket)
        nt.links.new(tex.outputs["Color"], sock)

    # Store the source texture path so the manifest/agents can trace it back.
    mat["adfrc_source_texture"] = os.path.relpath(tex_png, tex_root).replace("\\", "/")
    mat["adfrc_socket"] = socket
    return True


def _bsdf(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
        if out is None:
            out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return nt, bsdf


def procedural_look(mat, mat_name):
    """Synthesise a stand-in for an Arma procedural (.rvmat) material."""
    low = (mat_name or "").lower()
    for key, look in PROCEDURAL_LOOK.items():
        if key in low:
            _nt, bsdf = _bsdf(mat)
            bsdf.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1.0)
            bsdf.inputs["Roughness"].default_value = look["rough"]
            bsdf.inputs["Metallic"].default_value = look["metal"]
            if "Alpha" in bsdf.inputs and "alpha" in look:
                bsdf.inputs["Alpha"].default_value = look["alpha"]
            mat["adfrc_procedural"] = mat_name
            return True
    return False


def flat_look(mat, rough, metal):
    _nt, bsdf = _bsdf(mat)
    bsdf.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return bsdf


# ---------------------------------------------------------------- per model

def dst_for(src):
    rel = os.path.relpath(src, FBX_ROOT)
    return rel, os.path.join(DST_ROOT, rel)


def process(src, index):
    rel, dst = dst_for(src)
    tmp = os.path.splitext(dst)[0] + ".part.fbx"
    os.makedirs(os.path.dirname(dst), exist_ok=True)

    clear_scene()
    bpy.ops.import_scene.fbx(filepath=src)

    bound, procedural, engine, inline, unresolved = 0, 0, 0, 0, []
    for mat in list(bpy.data.materials):
        m = MAT_RE.search(mat.name or "")
        tex_name = (m.group("tex").strip() if m else "").lower()
        mat_name = (m.group("mat").strip() if m else (mat.name or ""))

        # 0. Inline flat colour carried in the material name.
        cm = INLINE_COLOR_RE.search(mat.name or "") or INLINE_COLOR_RE.search(tex_name)
        if cm:
            r, g, b, a = (float(cm.group(k)) for k in "rgba")
            bsdf = flat_look(mat, 0.5, 0.0)
            bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
            if "Alpha" in bsdf.inputs:
                bsdf.inputs["Alpha"].default_value = a
            mat["adfrc_inline_color"] = (r, g, b, a)
            inline += 1
            continue

        # 1. Procedural Arma material - no texture, synthesise a look.
        if not tex_name:
            if procedural_look(mat, mat_name):
                procedural += 1
            else:
                flat_look(mat, 0.6, 0.0)   # neutral, never black
                unresolved.append("%s (procedural, neutral fallback)" % mat_name)
            continue

        # 2. Engine-shipped texture - neutral stand-in, record it.
        if tex_name.startswith(ENGINE_TEX):
            flat_look(mat, 0.5, 0.0)
            engine += 1
            continue

        # 3. Real ADFRC texture.
        key = os.path.splitext(os.path.basename(tex_name))[0].lower()
        png = index.get(key)
        if not png:
            flat_look(mat, 0.6, 0.0)   # texture genuinely absent from the pack
            unresolved.append(tex_name)
            continue
        sock = socket_for(tex_name)
        if not sock:
            unresolved.append("%s (no socket for _%s)" % (tex_name, suffix_of(tex_name)))
            continue
        if bind(mat, png, sock, TEX_ROOT):
            bound += 1

    bpy.ops.export_scene.fbx(
        filepath=tmp,
        use_selection=False,
        object_types={"MESH", "ARMATURE"},
        bake_anim=False,
        add_leaf_bones=False,
        use_mesh_modifiers=True,
        path_mode="RELATIVE",
        embed_textures=False,
    )
    if not os.path.exists(tmp):
        raise RuntimeError("no FBX produced")
    os.replace(tmp, dst)
    return rel, bound, procedural, engine, inline, unresolved


def main():
    global FBX_ROOT, DST_ROOT, TEX_ROOT
    args = sys.argv[sys.argv.index("--") + 1:]
    FBX_ROOT, DST_ROOT, TEX_ROOT, listfile = args[0], args[1], args[2], args[3]

    index = build_index()
    print("texture index: %d png basenames" % len(index), flush=True)

    paths = [l.strip() for l in open(listfile, encoding="utf-8") if l.strip()]
    log_path = os.path.join(DST_ROOT, "_bind_log.txt")
    os.makedirs(DST_ROOT, exist_ok=True)

    ok = fail = skip = 0
    t0 = time.time()
    with open(log_path, "a", encoding="utf-8") as log:
        for src in paths:
            rel, dst = dst_for(src)
            if os.path.exists(dst) and os.path.getsize(dst) > 0:
                skip += 1
                continue
            try:
                rel2, bound, proc, eng, inl, unres = process(src, index)
                ok += 1
                log.write("OK   %s bound=%d procedural=%d engine=%d inline=%d "
                          "unresolved=%d\n"
                          % (rel2, bound, proc, eng, inl, len(unres)))
                for u in unres[:40]:
                    log.write("       unresolved: %s\n" % u)
            except Exception:  # noqa: BLE001
                fail += 1
                log.write("FAIL %s\n%s\n" % (rel, traceback.format_exc()))
            log.flush()
            if ok + fail == 1 or (ok + fail) % 20 == 0:
                print("  %d/%d ok=%d fail=%d skip=%d %.0fs"
                      % (ok + fail, len(paths), ok, fail, skip, time.time() - t0),
                      flush=True)
    print("DONE ok=%d fail=%d skip=%d %.0fs" % (ok, fail, skip, time.time() - t0),
          flush=True)


main()
