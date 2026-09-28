"""Render the Loadout weapon set for the public website.

The producer has directed (2026-09-28, LICENCE_REGISTER L-0017/L-0021 and
ASSET_REGISTER intake rule) that the site's Loadout section shows renders of
the CURRENT internal weapon models, including third-party-derived material:

    a88   ADFRC EF88-derived service rifle (L-0021) - the in-game A88 mesh
    a89   ADFRC F89 (F89_Minimi_Mod) - the stand-in shown for the A89. The
          game's A89 mesh came from F89_Minimi_MLOD, which is built from Minimi
          parts plus Maximi (M249) and Mag58 parts and reads as an M249, so the
          ADFRC F89 itself is shown instead (producer decision, 2026-09-28).
    a4    ADFRC M4A5-derived rifle (L-0021)
    a416  ADFRC HK416-derived rifle (L-0021)
    a25   ADFRC SR25-derived marksman rifle (L-0021)
    akm   sourced AKM reference model (R-23) - published as an explicitly
          labelled reference render only; NOT a game weapon

TEXTURES COME FROM THE MANIFEST, NOT FROM A NAME GUESS. Every ADFRC weapon
folder carries manifest.json, written when the game FBX was exported, mapping
each material slot to the exact colour and normal maps it was textured with:

    "textures": { "adfrc_ef88_co": { "colour": "...EF88_CO.png",
                                     "normal": "...EF88_NOHQ.png" }, ... }

The slots in the FBX and the keys in the manifest match one for one, and the
files they name all exist, so the manifest is the authority. (Looking textures
up by filename across the whole ADFRC tree was wrong: the same stem ships in
several weapon packs, so slots picked up another weapon's map.) The map set is
completed from the siblings beside each colour file:

    <name>_NOHQ.png  normal map              (Arma: NOHQ = uncompressed normal)
    <name>_SMDI.png  R specular mask, G glossiness, B grime/AO

Arma's _CA maps are an OVERLAY layer, not a diffuse map. Several optic slots
(adfrc_ta31_glass_ca, adrc_acog_ret_ca) are almost fully transparent: used as
an opaque base colour they render the scope black, or the reticle as a white
blob. Slots whose map is transparent are therefore treated as what they are -
tinted glass for the lens, a reticle mask for the reticle - and the zero-alpha
optic shells get studio glass.

Usage:
    blender --background --factory-startup -P Tools/Blender/render_weapons.py -- [a88 ...]
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = r"E:\SouthernSpear"
OUT = os.path.join(ROOT, "Docs", "images", "weapons")

RES_X, RES_Y = 2000, 1400
SAMPLES = 160
MARGIN = 1.06

KEY = (1.00, 0.88, 0.70)
FILL = (0.58, 0.70, 0.68)
RIM = (0.95, 0.58, 0.32)
TOP = (0.85, 0.88, 1.00)

# name -> source path. The ADFRC entries are the same FBX the game ships.
WEAPONS = {
    "a88":  r"Art\Weapons\A88\ADFRC\SM_A88.fbx",
    "a89":  r"Art\Weapons\A89\ADFRC\SM_A89.fbx",
    "a4":   r"Art\Weapons\A4\ADFRC\SM_A4.fbx",
    "a416": r"Art\Weapons\A416\ADFRC\SM_A416.fbx",
    "a25":  r"Art\Weapons\A25\ADFRC\SM_A25.fbx",
    "akm":  r"Art\Weapons\AKM\Weathered AKM rifle.blend",
}

# The game's A89 mesh was exported from ADFRC_F89_Minimi_MLOD, which is built
# from Minimi body parts plus Maximi (M249) and Mag58 parts - it reads as an
# M249, not as an F89. ADFRC ships the F89 itself as a separate variant
# (F89_Base_01/02, F89_MK3_01, MK3_Handguard), and that is what the site shows.
ADFRC_BLEND_SOURCES = {
    "a89": r"Art\ADFRC_BLEND\adfrc_minimi\ADFRC_F89_Minimi_Mod_MLOD.blend",
}

# How each weapon is presented. `view` is the unit vector from the weapon to
# the camera. The game FBX exports lie along X; the sourced AKM blend lies
# along Y, so it needs its own angle or the camera stares down the barrel.
VIEWS = {
    "a88":  (-0.46, -1.0, 0.26),
    "a89":  (-0.52, -1.0, 0.30),
    "a4":   (-0.42, -1.0, 0.24),
    "a416": (-0.44, -1.0, 0.24),
    "a25":  (-0.38, -1.0, 0.22),
    "akm":  (1.0, -0.42, 0.20),
}

# The AKM pack is a near-mirror metal (metallic map averages 0.66, roughness
# 0.37), so the same rig that suits the matte rifles clips it to white. The
# F89's polymer is a shade lighter than the rifles'.
EXPOSURE = {"akm": -1.4, "a89": -0.4}

GLASS_TINT = (0.055, 0.085, 0.090, 1.0)
POLYMER = (0.055, 0.058, 0.052, 1.0)
METAL = (0.085, 0.088, 0.092, 1.0)
RETICLE_BRIGHT = (0.72, 0.80, 0.74, 1.0)

REPORT = []


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def add_area(name, target, offset, size, energy, color):
    """An area light placed relative to the target and AIMED AT IT.

    A light emits along its local -Z, so the rotation is derived from the
    offset instead of being hand-guessed: with guessed Euler angles the lamps
    ended up aimed away from the weapon and every render came out black.
    """
    data = bpy.data.lights.new(name, type="AREA")
    data.shape = "RECTANGLE"
    data.size, data.size_y = size
    data.energy = energy
    data.color = color
    ob = bpy.data.objects.new(name, data)
    target = Vector(target)
    ob.location = target + Vector(offset)
    ob.rotation_euler = (target - ob.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(ob)
    return ob


# --------------------------------------------------------------------------
# manifest / texture resolution
# --------------------------------------------------------------------------

def load_manifest(fbx_path):
    mpath = os.path.join(os.path.dirname(fbx_path), "manifest.json")
    if not os.path.isfile(mpath):
        return {}
    with open(mpath, encoding="utf-8") as handle:
        return json.load(handle).get("textures", {})


TEX_ROOT = os.path.join(ROOT, "Art", "ADFRC", "Textures")
TEX_INDEX = {}


def texture_index():
    """Every ADFRC PNG keyed by its lower-case stem. Built once per run.

    Only needed for the models read straight from an ADFRC blend, where the
    slot name IS the texture stem and there is no export manifest to follow.
    """
    if not TEX_INDEX:
        for dirpath, _dirnames, filenames in os.walk(TEX_ROOT):
            for fn in filenames:
                if fn.lower().endswith(".png"):
                    TEX_INDEX.setdefault(
                        os.path.splitext(fn)[0].lower().replace(" ", ""),
                        os.path.join(dirpath, fn))
    return TEX_INDEX


def stem_texture(stem):
    """The colour map for a texture stem, e.g. f89_base_01_co -> F89_Base_01_CO.png."""
    return texture_index().get(stem.lower().replace(" ", ""))


def collect_adfrc_blend(path):
    """Gather the visual LOD0 parts of an ADFRC blend, as adfrc_weapon.py does.

    The MLOD blends hold one object per part per LOD inside view_R0; the first
    occurrence of each (part, material) pair is the most detailed. Decals and
    anything without a texture are dropped. The result is a single joined mesh
    with material slots named after their texture stem, oriented muzzle to +X
    with the origin at the trigger - the same frame the game meshes use.
    """
    import re

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=path)

    memory = {}
    mem = bpy.data.objects.get("Memory")
    if mem:
        for group in mem.vertex_groups:
            pts = [v.co.copy() for v in mem.data.vertices
                   if any(e.group == group.index for e in v.groups)]
            if pts:
                memory[group.name] = sum(pts, Vector()) / len(pts)

    view = bpy.data.collections.get("view_R0") or bpy.data.collections.get("LODs")
    candidates = [o for o in (view.all_objects if view else bpy.data.objects)
                  if o.type == "MESH"]
    drop = re.compile(r"(tag|ruid|patch|flag|logo|insignia)", re.I)

    def stem_of(material):
        match = re.search(r"([\w\-]+)\.paa", material or "", re.I)
        return match.group(1).lower() if match else None

    seen, keep = set(), []
    for ob in sorted(candidates, key=lambda o: o.name):
        base = re.sub(r"\.\d+$", "", ob.name)
        mat = ob.data.materials[0].name if ob.data.materials and ob.data.materials[0] else ""
        key = (base, mat)
        if key in seen:
            continue
        seen.add(key)
        if drop.search(base) or drop.search(mat) or not stem_of(mat):
            continue
        if not stem_texture(stem_of(mat)):
            continue
        keep.append(ob)
    if not keep:
        raise SystemExit("no textured parts in " + path)

    bpy.ops.object.select_all(action="DESELECT")
    for ob in keep:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = keep[0]
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = obj.data.name = "adfrc_blend"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Everything not joined stays in the scene and would be rendered with it:
    # the blends carry six-triangle LOD proxy boxes several metres across, and
    # dropping them is exactly what the exporter does.
    for ob in list(bpy.data.objects):
        if ob is not obj:
            bpy.data.objects.remove(ob, do_unlink=True)

    for slot in obj.material_slots:
        stem = stem_of(slot.material.name if slot.material else "")
        if not stem:
            continue
        slot.material = bpy.data.materials.get(stem) or bpy.data.materials.new(stem)

    points = dict(memory)

    def apply(fn):
        for v in obj.data.vertices:
            v.co = fn(v.co)
        for key in points:
            points[key] = fn(points[key])

    dims = obj.dimensions
    if dims[1] > dims[0] and dims[1] >= dims[2]:
        apply(lambda c: Vector((c.y, -c.x, c.z)))
    if "muzzle_pos" in points and "trigger_axis" in points:
        if points["muzzle_pos"].x < points["trigger_axis"].x:
            apply(lambda c: Vector((-c.x, -c.y, c.z)))
    origin = points.get("trigger_axis", Vector((0, 0, 0)))
    apply(lambda c: c - origin)

    textures = {}
    for slot in obj.material_slots:
        stem = slot.material.name if slot.material else ""
        if stem:
            textures[stem] = {"colour": stem_texture(stem), "normal": None}
    return [obj], textures


def sibling(image_path, suffix):
    """Find <stem>_<suffix>.png beside image_path, case-insensitively.

    The packs are inconsistent about case and about the doubled stems used for
    the cavity variants (ADFRC_EF88_SMDI vs ADFRC_EF88_C_SMDI), and a slot's
    map is often named after the model rather than the part
    (ADFRC_TA31_ACOG_BLK_CO has its normal as ADFRC_TA31_ACOG_NOHQ). So try
    the exact spellings first, then fall back to the shortest file in the same
    folder that shares the model's prefix.
    """
    if not image_path:
        return None
    folder = os.path.dirname(image_path)
    stem = os.path.splitext(os.path.basename(image_path))[0]
    base = stem[:-3] if stem.lower().endswith("_co") else stem
    for candidate in (f"{stem}_{suffix}", f"{base}_{suffix}", f"{base}_c_{suffix}"):
        for name in os.listdir(folder):
            if name.lower() == (candidate + ".png").lower():
                return os.path.join(folder, name)

    # Drop trailing part qualifiers (_BLK, _FDE, ...) and match the prefix.
    tokens = base.split("_")
    for cut in range(len(tokens) - 1, 1, -1):
        prefix = "_".join(tokens[:cut]) + "_"
        matches = [n for n in os.listdir(folder)
                   if n.lower().startswith(prefix.lower()) and
                   n.lower().endswith("_" + suffix.lower() + ".png")]
        if matches:
            return os.path.join(folder, min(matches, key=len))
    return None


def image_stats(path):
    """Mean RGB and mean alpha of an image, sampled small.

    Decides whether a map is a real diffuse (alpha high) or an Arma overlay
    layer (alpha ~0), which must not be wired to Base Color.
    """
    img = bpy.data.images.load(path)
    try:
        img.scale(32, 32)
        px = list(img.pixels)
        n = len(px) // 4
        if not n:
            return None
        r = sum(px[0::4]) / n
        g = sum(px[1::4]) / n
        b = sum(px[2::4]) / n
        a = sum(px[3::4]) / n
        return (r, g, b, a)
    finally:
        bpy.data.images.remove(img)


def image_node(nt, path, label):
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path, check_existing=True)
    tex.label = label
    tex.location = (-1000, 0)
    return tex


def new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    return mat, mat.node_tree, mat.node_tree.nodes["Principled BSDF"]


def base_from_co(nt, bsdf, co_path, smdi_path=None, lift=1.0):
    """Diffuse + normal + gloss, the standard Arma decode."""
    co = image_node(nt, co_path, "CO")
    colour = co.outputs["Color"]
    if lift != 1.0:
        gain = nt.nodes.new("ShaderNodeMix")
        gain.data_type = "RGBA"
        gain.blend_type = "MULTIPLY"
        gain.location = (-1000, 0)
        gain.inputs["Factor"].default_value = 1.0
        nt.links.new(co.outputs["Color"], gain.inputs[6])
        gain.inputs[7].default_value = (lift, lift, lift, 1.0)
        colour = gain.outputs[2]
    nt.links.new(colour, bsdf.inputs["Base Color"])

    nrm = sibling(co_path, "nohq")
    if nrm:
        ntex = image_node(nt, nrm, "NOHQ")
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.location = (-1000, 0)
        nmap.inputs["Strength"].default_value = 0.6
        nt.links.new(ntex.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    smdi = smdi_path or sibling(co_path, "smdi")
    used_nrm, used_smdi = nrm, smdi
    if smdi:
        stex = image_node(nt, smdi, "SMDI")
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        sep.location = (-1000, 0)
        nt.links.new(stex.outputs["Color"], sep.inputs["Color"])
        # G is glossiness; invert into roughness.
        inv = nt.nodes.new("ShaderNodeInvert")
        inv.location = (-1000, 0)
        nt.links.new(sep.outputs["Green"], inv.inputs["Color"])
        nt.links.new(inv.outputs["Color"], bsdf.inputs["Roughness"])
        # B is grime/AO: darken the diffuse in the crevices. R is the specular
        # mask but ships at 255 across these packs, so it is left alone.
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.location = (-1000, 0)
        mix.inputs["Factor"].default_value = 0.35
        nt.links.new(colour, mix.inputs[6])
        nt.links.new(sep.outputs["Blue"], mix.inputs[7])
        nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    return used_nrm, used_smdi


def glass_material(name, co_path=None, ret_path=None):
    """A lens, not a white or black plastic shell.

    Arma's glass/reticle maps are transparent overlays; as an opaque diffuse
    they read as a black hole (or a white blob for the reticle). Tinted glass
    plus the reticle mask is what the source actually looks like.
    """
    mat, nt, bsdf = new_material(name)
    bsdf.inputs["Base Color"].default_value = GLASS_TINT
    bsdf.inputs["Roughness"].default_value = 0.06
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["IOR"].default_value = 1.5
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 0.85
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = 0.85

    if co_path:
        stats = image_stats(co_path)
        if stats and stats[3] > 0.35:
            # An opaque map here is a real tint; use it as the glass colour.
            co = image_node(nt, co_path, "glass tint")
            nt.links.new(co.outputs["Color"], bsdf.inputs["Base Color"])
        nrm = sibling(co_path, "nohq")
        if nrm:
            ntex = image_node(nt, nrm, "NOHQ")
            nmap = nt.nodes.new("ShaderNodeNormalMap")
            nmap.inputs["Strength"].default_value = 0.4
            nt.links.new(ntex.outputs["Color"], nmap.inputs["Color"])
            nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    if ret_path:
        # Reticle: a dark lens with the illuminated marks mixed in by alpha.
        rtex = image_node(nt, ret_path, "reticle")
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.location = (-1000, 0)
        mix.inputs[6].default_value = (0.02, 0.025, 0.022, 1.0)
        mix.inputs[7].default_value = RETICLE_BRIGHT
        nt.links.new(rtex.outputs["Alpha"], mix.inputs["Factor"])
        nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
        if "Emission Color" in bsdf.inputs:
            nt.links.new(rtex.outputs["Alpha"], bsdf.inputs["Emission Color"])
    return mat


def reticle_material(name, map_path):
    """Standalone reticle geometry: the map is a white-on-transparent mask."""
    mat, nt, bsdf = new_material(name)
    tex = image_node(nt, map_path, "reticle")
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.location = (-1000, 0)
    mix.inputs[6].default_value = (0.015, 0.02, 0.018, 1.0)
    mix.inputs[7].default_value = RETICLE_BRIGHT
    nt.links.new(tex.outputs["Alpha"], mix.inputs["Factor"])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.4
    return mat


def studio_material(name, color, rough, metal):
    mat, nt, bsdf = new_material(name)
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return mat


def akm_material():
    """The AKM pack carries five packed 4096 maps on one material."""
    mat, nt, bsdf = new_material("AKM_PBR")

    def packed(stem):
        # The AKM maps are packed into the .blend, so has_data is still False
        # until something reads them: matching on that flag alone silently
        # found nothing and rendered the rifle as default white plastic.
        for img in bpy.data.images:
            if img.name.lower() == stem.lower() and (img.packed_file or img.source == "FILE"):
                return img
        return None

    for stem, socket, label in (
            ("Material_BaseColor.png", "Base Color", "base"),
            ("Material_Roughness.png", "Roughness", "rough"),
            ("Material_Metallic.png", "Metallic", "metal")):
        img = packed(stem)
        if not img:
            continue
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        tex.label = label
        out = tex.outputs["Color"]
        if socket == "Roughness":
            # The pack's roughness averages 0.37, which on a 0.66-metallic
            # surface turns the whole rifle into a mirror of the studio
            # lights. Floor it so the weathering in the albedo stays visible.
            floor = nt.nodes.new("ShaderNodeMath")
            floor.operation = "MAXIMUM"
            floor.inputs[1].default_value = 0.45
            nt.links.new(out, floor.inputs[0])
            out = floor.outputs[0]
        elif socket == "Metallic":
            damp = nt.nodes.new("ShaderNodeMath")
            damp.operation = "MULTIPLY"
            damp.inputs[1].default_value = 0.45
            nt.links.new(out, damp.inputs[0])
            out = damp.outputs[0]
        nt.links.new(out, bsdf.inputs[socket])

    # The pack also ships an ambient-occlusion map; fold it into the diffuse.
    ao = packed("Material_AmbientOcclusion.png")
    if ao:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = ao
        tex.label = "AO"
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 0.6
        base = nt.nodes.new("ShaderNodeTexImage")
        base.image = packed("Material_BaseColor.png")
        nt.links.new(base.outputs["Color"], mix.inputs[6])
        nt.links.new(tex.outputs["Color"], mix.inputs[7])
        nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])

    normal = packed("Material_Normal.png")
    if normal:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = normal
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.inputs["Strength"].default_value = 0.7
        nt.links.new(tex.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    found = [n for n in ("Material_BaseColor.png", "Material_Normal.png",
                         "Material_Roughness.png", "Material_Metallic.png",
                         "Material_AmbientOcclusion.png") if packed(n)]
    missing = [n for n in ("Material_BaseColor.png", "Material_Normal.png",
                           "Material_Roughness.png", "Material_Metallic.png")
               if not packed(n)]
    if missing:
        print("  AKM WARNING: packed maps not found:", missing)
    REPORT.append(("akm", "packed PBR set", ", ".join(found), "ok" if found else "MISSING"))
    return mat


# --------------------------------------------------------------------------
# per-weapon material assignment
# --------------------------------------------------------------------------

def classify(slot):
    low = slot.lower()
    if "glass" in low or "lens" in low:
        return "glass"
    if "ret" in low:
        return "reticle"
    if "optic" in low or "scope" in low:
        return "optic"
    if any(k in low for k in ("grip", "stock", "m4_lower", "polymer", "a2_", "bt_",
                              "ctr_", "irons", "mbus", "kac_ch", "colt_buffer",
                              "flash", "urx2", "bs_")):
        return "polymer"
    if any(k in low for k in ("barrel", "receiver", "handguard", "bolt", "fh",
                              "gasblock", "charging", "kacris", "lower", "upper",
                              "buis", "mag", "minimi", "spectr", "m4_upper")):
        return "metal"
    return "polymer"


def apply_materials(meshes, kind, fbx_path, textures=None):
    """Texture every slot from the manifest, and say what it resolved to."""
    if kind == "akm":
        mat = akm_material()
        for ob in meshes:
            if not ob.data.materials:
                ob.data.materials.append(mat)
            for i in range(len(ob.data.materials)):
                ob.data.materials[i] = mat
        return

    textures = textures if textures is not None else load_manifest(fbx_path)

    # Reticle maps live on their own slots, white-on-transparent, and are
    # painted onto the lens of the scope they belong to.
    reticle_maps = []
    for other, entry in textures.items():
        path = entry.get("colour")
        if "ret" in other.lower() and path and os.path.isfile(path):
            stats = image_stats(path)
            if stats and stats[3] < 0.35:
                reticle_maps.append(path)

    for slot in sorted({m.name for ob in meshes for m in ob.data.materials if m}):
        entry = textures.get(slot) or {}
        co = entry.get("colour")
        nrm = entry.get("normal")
        kind_name = classify(slot)
        stats = image_stats(co) if co and os.path.isfile(co) else None
        overlay = bool(stats and stats[3] < 0.35)

        if co and not overlay and os.path.isfile(co):
            # Arma's _CA maps are the model's detail layer. Where one is
            # near-black it is a cavity/AO map, not a diffuse: render it as
            # detail over a dark polymer base so the part keeps its shape
            # instead of going to a black hole.
            lift = 1.0
            source = co
            mean = sum(stats[:3]) / 3.0 if stats else 1.0
            if slot.lower().endswith("_ca") and stats and max(stats[:3]) < 0.05:
                lift = 6.0
            elif kind_name in ("glass", "reticle", "optic") or "spectr" in slot.lower():
                # Optic bodies are black in game (the TA31 is literally the
                # "BLK" variant, the Spectr diffuse averages 30/255). Left at
                # face value the scope renders as a flat dark shape with no
                # visible surface, so lift the diffuse until the texture
                # reads. Body parts are left alone.
                if mean < 0.16:
                    lift = min(4.0, 0.22 / max(mean, 0.01))
            mat, nt, bsdf = new_material(slot)
            used_n, used_s = base_from_co(nt, bsdf, source, sibling(co, "smdi"), lift)
            state = "textured" if lift == 1.0 else "textured (cavity map lifted)"
            detail = os.path.basename(co)
            if used_n:
                detail += " + " + os.path.basename(used_n)
            if used_s:
                detail += " + " + os.path.basename(used_s)
        elif kind_name == "glass":
            ret = reticle_maps[0] if reticle_maps else None
            mat = glass_material(slot, co if (co and os.path.isfile(co)) else None, ret)
            state = "glass" + ("+reticle" if ret else "")
            detail = "lens"
            if ret:
                detail += " + " + os.path.basename(ret)
        elif kind_name == "reticle" and co and os.path.isfile(co):
            mat = reticle_material(slot, co)
            state = "reticle mask"
            detail = os.path.basename(co)
        elif kind_name in ("optic", "glass", "reticle"):
            mat = glass_material(slot)
            state = "studio glass (no map in source)"
            detail = "-"
        else:
            base = METAL if kind_name == "metal" else POLYMER
            mat = studio_material(slot, base, 0.45 if kind_name == "metal" else 0.6,
                                  0.55 if kind_name == "metal" else 0.0)
            state = "untextured in source"
            detail = "-"

        REPORT.append((os.path.splitext(os.path.basename(fbx_path))[0], slot, detail, state))

        for ob in meshes:
            if slot not in [m.name for m in ob.data.materials if m]:
                continue
            for i, m in enumerate(ob.data.materials):
                if m and m.name == slot:
                    ob.data.materials[i] = mat

    for ob in meshes:
        if not ob.data.materials:
            ob.data.materials.append(studio_material("Untextured", POLYMER, 0.6, 0.0))


# --------------------------------------------------------------------------
# camera, lighting, render
# --------------------------------------------------------------------------

def frame(camera, target, direction, points, margin=MARGIN):
    """Fit the projected silhouette into the frame, exactly.

    The projected extent of a long, thin object is not proportional to 1/d
    (the near end of a rifle subtends a much larger angle than the far end), so
    a single unit-distance measurement clipped the muzzle and the stock. Solve
    it directly instead: fix the rotation, then step the distance back until
    every corner is inside the frustum.
    """
    cam = camera.data
    view_dir = Vector(direction).normalized()
    quat = (-view_dir).to_track_quat("-Z", "Y")
    camera.rotation_euler = quat.to_euler()

    tan_x = (cam.sensor_width / 2.0) / cam.lens
    tan_y = tan_x / (RES_X / RES_Y)
    inv = quat.inverted()
    target = Vector(target)

    def required(dist):
        loc = target + view_dir * dist
        need = 0.0
        for c in points:
            local = inv @ (c - loc)
            depth = -local.z
            if depth <= 1e-4:
                return 1e9
            need = max(need, abs(local.x / depth) / tan_x, abs(local.y / depth) / tan_y)
        return need

    dist = 1.0
    for _ in range(40):
        need = required(dist)
        if need <= 1e8 and abs(need - 1.0) < 1e-4:
            break
        dist *= math.sqrt(max(need, 1e-6))
    dist *= margin
    camera.location = target + view_dir * dist


def render(stem, rel_path, out_path=None, transform="AgX", look="AgX - Base Contrast",
           exposure=-1.0):
    reset()
    scene = bpy.context.scene
    path = os.path.join(ROOT, rel_path)
    blend_textures = None
    if stem in ADFRC_BLEND_SOURCES:
        path = os.path.join(ROOT, ADFRC_BLEND_SOURCES[stem])
        meshes, blend_textures = collect_adfrc_blend(path)
        scene = bpy.context.scene
    elif path.lower().endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        bpy.ops.wm.open_mainfile(filepath=path)
        scene = bpy.context.scene

    if not ADFRC_BLEND_SOURCES.get(stem):
        meshes = [o for o in scene.objects if o.type == "MESH"]
    if not meshes:
        raise SystemExit("no mesh in " + path)

    apply_materials(meshes, stem, path, blend_textures)

    corners = [ob.matrix_world @ Vector(c) for ob in meshes for c in ob.bound_box]
    lo = Vector((min(c[i] for c in corners) for i in range(3)))
    hi = Vector((max(c[i] for c in corners) for i in range(3)))
    target = (lo + hi) / 2.0
    radius = max((hi - lo).length / 2.0, 0.05)

    # Framing fits the real silhouette, not the bounding box: the extreme
    # points of a projection are always vertices, and a rifle's eight box
    # corners sit in empty space at this angle, which would waste half the
    # frame.
    points = []
    for ob in meshes:
        count = len(ob.data.vertices)
        flat = [0.0] * (count * 3)
        ob.data.vertices.foreach_get("co", flat)
        matrix = ob.matrix_world
        points.extend(matrix @ Vector(flat[i:i + 3]) for i in range(0, len(flat), 3))

    scene.render.engine = "CYCLES"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.film_transparent = True
    scene.view_settings.view_transform = transform
    scene.view_settings.look = look
    scene.view_settings.exposure = exposure + EXPOSURE.get(stem, 0.0)

    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.035, 0.042, 0.050, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.35
    scene.world = world

    d = radius
    # The rig is placed relative to the model's own size, so the lamps sit
    # closer to a small weapon than to a large one. Illuminance falls off with
    # the square of the distance, so the power is scaled to match: without
    # this the AKM (a much smaller model) blew out to solid white.
    p = (d / 0.45) ** 2
    add_area("Key", target, (-d * 1.6, -d * 2.0, d * 1.9), (d * 1.5, d * 0.9), 420 * p, KEY)
    add_area("Fill", target, (d * 2.3, -d * 1.6, d * 0.3), (d * 2.0, d * 1.4), 120 * p, FILL)
    add_area("Rim", target, (d * 0.8, d * 1.9, d * 1.4), (d * 1.1, d * 0.7), 700 * p, RIM)
    add_area("Top", target, (0.0, -d * 0.3, d * 3.0), (d * 2.6, d * 1.6), 200 * p, TOP)

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 90
    cam_data.sensor_fit = "HORIZONTAL"
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    frame(cam, target, VIEWS.get(stem, (-0.45, -1.0, 0.25)), points)

    os.makedirs(OUT, exist_ok=True)
    scene.render.filepath = out_path or os.path.join(OUT, stem + ".png")
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scene.render.filepath)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    wanted = [a for a in argv if a in WEAPONS] or list(WEAPONS)
    for stem in wanted:
        render(stem, WEAPONS[stem])
    print("\n==== TEXTURE REPORT (model / slot / maps / state) ====")
    for row in REPORT:
        print("  %-10s %-26s %-58s %s" % row)
    print("done")
