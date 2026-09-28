#!/usr/bin/env python3
"""Build a UE import manifest for the ADFRC texture set.

Arma encodes what a texture *is* in its filename suffix, not in any sidecar
file.  Unreal needs the opposite: an explicit sRGB flag and a compression
scheme per asset.  This script writes `Textures/_ue_manifest.json` describing
every PNG, plus a ready-to-run Unreal Editor Python script that applies those
settings to already-imported assets.

Usage:  python texture_manifest.py [root] [manifest_out] [ue_script_out]
"""
import glob
import json
import os
import re
import struct
import sys
import zlib
from collections import Counter

ROOT = sys.argv[1] if len(sys.argv) > 1 else r'E:\SouthernSpear\Content\Sourced\ADF_Extracted'
TEX = os.path.join(ROOT, "Textures")
MANIFEST = (sys.argv[2] if len(sys.argv) > 2
            else os.path.join(TEX, "_ue_manifest.json"))
UE_SCRIPT = (sys.argv[3] if len(sys.argv) > 3
             else os.path.join(ROOT, "_tools", "ue_apply_texture_settings.py"))

# Arma filename suffix -> what the channels actually contain.
#   co  colour / diffuse            -> sRGB on,  BC7 / Default
#   ca  camo / albedo variant       -> sRGB on,  BC7 / Default
#   nohq  normal, 2-channel DXT5    -> sRGB OFF, TC_Normalmap
#   smdi specular+metal+dirt packed -> sRGB OFF, TC_Masks (needs channel split)
#   as  ambient smooth              -> sRGB OFF, BC4 / Grayscale
#   mc  metal                       -> sRGB OFF, BC4 / Grayscale
#   ao  ambient occlusion           -> sRGB OFF, BC4 / Grayscale
#   di  dirtiness                   -> sRGB OFF, BC4 / Grayscale
ROLES = {
    "co":    dict(channel="basecolour", srgb=True,  compression="TC_Default",
                  note="albedo / diffuse"),
    "ca":    dict(channel="basecolour", srgb=True,  compression="TC_Default",
                  note="camo albedo variant"),
    "nohq":  dict(channel="normal",     srgb=False, compression="TC_Normalmap",
                  note="2-channel DXT5 normal; UE wants tangent-space RGB"),
    "n":     dict(channel="normal",     srgb=False, compression="TC_Normalmap",
                  note="normal map"),
    "smdi":  dict(channel="orm_packed", srgb=False, compression="TC_Masks",
                  note="specular+metal+dirtiness packed; split to ORM"),
    "sm":    dict(channel="specmask",   srgb=False, compression="TC_Masks",
                  note="specular mask"),
    "di":    dict(channel="dirt",       srgb=False, compression="TC_Grayscale",
                  note="dirtiness / grime mask"),
    "as":    dict(channel="ambientsmooth", srgb=False, compression="TC_Grayscale",
                  note="ambient smooth term, used as a faint emissive"),
    "mc":    dict(channel="metallic",   srgb=False, compression="TC_Grayscale",
                  note="metallic mask"),
    "ao":    dict(channel="ao",         srgb=False, compression="TC_Grayscale",
                  note="ambient occlusion"),
    "gi":    dict(channel="gloss",      srgb=False, compression="TC_Grayscale",
                  note="glossiness"),
    "ret":   dict(channel="reticle",    srgb=False, compression="TC_Emissive",
                  note="weapon reticle, drawn as emissive"),
}

DEFAULT_ROLE = dict(channel="unknown", srgb=True, compression="TC_Default",
                    note="no recognised Arma suffix; treated as colour")

# ~250 ADFRC textures carry no standard suffix. Fall back to filename hints,
# then to the PNG colour type, so nothing ships with default sRGB by accident.
NAME_HINTS = (
    ("mask",    dict(channel="mask", srgb=False, compression="TC_Grayscale",
                     note="greyscale mask by filename")),
    ("_ao",     dict(channel="ao", srgb=False, compression="TC_Grayscale",
                     note="ambient occlusion by filename")),
    ("insig",   dict(channel="basecolour", srgb=True, compression="TC_Default",
                     note="insignia decal")),
    ("icon",    dict(channel="basecolour", srgb=True, compression="TC_Default",
                     note="UI icon")),
    ("logo",    dict(channel="basecolour", srgb=True, compression="TC_Default",
                     note="logo decal")),
    ("decal",   dict(channel="basecolour", srgb=True, compression="TC_Default",
                     note="decal")),
    ("stripe",  dict(channel="basecolour", srgb=True, compression="TC_Default",
                     note="livery stripe")),
    ("glass",   dict(channel="basecolour", srgb=True, compression="TC_Default",
                     note="glass tint")),
    ("camo",    dict(channel="basecolour", srgb=True, compression="TC_Default",
                     note="camouflage")),
    ("flag",    dict(channel="basecolour", srgb=True, compression="TC_Default",
                     note="flag")),
)

# PNG colour types: 0 greyscale, 2 rgb, 3 palette, 4 grey+alpha, 6 rgba
GREYSCALE_TYPES = (0, 4)


def png_info(path):
    """Width/height/alpha straight from the IHDR chunk."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(26)
        if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
            return None
        w, h = struct.unpack(">II", head[16:24])
        depth, ctype = head[24], head[25]
        return dict(width=w, height=h, bit_depth=depth, color_type=ctype)
    except Exception:  # noqa: BLE001
        return None


def role_for(name, info=None):
    stem = os.path.splitext(os.path.basename(name))[0].lower()
    parts = stem.split("_")
    # Walk the suffix chain from the right: foo_veh_nohq -> nohq
    for part in reversed(parts[1:]):
        if part in ROLES:
            return part
    if len(parts) > 1 and parts[-1] in ROLES:
        return parts[-1]
    for hint, role in NAME_HINTS:
        if hint in stem:
            return role
    # Last resort: an opaque greyscale PNG is a mask, not colour.
    if info and info.get("color_type") in GREYSCALE_TYPES:
        return dict(channel="mask", srgb=False, compression="TC_Grayscale",
                    note="greyscale PNG content")
    # RGBA with no standard suffix is overwhelmingly UI/insignia/decal art in
    # this pack (call signs, labels, helmet art) - colour with alpha.
    if info and info.get("color_type") in (4, 6):
        return dict(channel="decal", srgb=True, compression="TC_Default",
                    note="RGBA decal/UI art, no Arma suffix")
    return None


def main():
    files = sorted(glob.glob(os.path.join(TEX, "**", "*.png"), recursive=True))
    entries, by_channel, by_suffix = [], Counter(), Counter()
    for p in files:
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        key = os.path.basename(p)
        info = png_info(p) or {}
        suf = role_for(key, info)
        if isinstance(suf, dict):
            role, suf = suf, ""
        else:
            role = ROLES.get(suf, DEFAULT_ROLE)
        e = {
            "path": rel,
            "name": key,
            "suffix": suf or "",
            "channel": role["channel"],
            "srgb": role["srgb"],
            "compression": role["compression"],
            "note": role["note"],
        }
        e.update(info)
        entries.append(e)
        by_channel[role["channel"]] += 1
        if suf:
            by_suffix[suf] += 1

    manifest = {
        "schema": "adfrc-ue-texture-manifest/1",
        "note": ("Arma stores channel semantics in the filename suffix. "
                 "Unreal needs sRGB + compression set explicitly. Run "
                 "_tools/ue_apply_texture_settings.py inside the editor."),
        "root": ROOT,
        "counts": {
            "total": len(entries),
            "by_channel": dict(by_channel.most_common()),
            "by_suffix": dict(by_suffix.most_common()),
        },
        "textures": entries,
    }
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)

    print("textures: %d" % len(entries))
    print("by channel role:")
    seen = set()
    for e in entries:
        key = (e["channel"], e["srgb"], e["compression"])
        if key in seen:
            continue
        seen.add(key)
        print("   %-14s srgb=%-5s %-14s %5d"
              % (key[0], key[1], key[2], by_channel[key[0]]))
    print("by suffix:")
    for k, v in by_suffix.most_common():
        print("   _%-6s %5d" % (k, v))
    print("manifest -> %s" % MANIFEST)
    write_ue_script()


def write_ue_script():
    """Emit the Unreal-side half: a script that applies the manifest in-editor."""
    body = '''"""Apply ADFRC texture import settings inside the Unreal editor.

Run from the UE Python console or via -ExecutePythonScript:

    import ue_apply_texture_settings
    ue_apply_texture_settings.run()

It finds every Texture2D whose asset name matches a manifest entry and forces
sRGB + compression.  Safe to re-run; it only touches ADFRC textures.
"""
import json
import os

import unreal

MANIFEST = os.path.join(unreal.Paths.project_dir(), "Sourced", "ADF_Extracted",
                        "Textures", "_ue_manifest.json")

# Unreal's ETextureCompression equivalent enum names.
COMPRESSION = {
    "TC_Default": unreal.TextureCompressionSettings.TC_DEFAULT,
    "TC_Normalmap": unreal.TextureCompressionSettings.TC_NORMALMAP,
    "TC_Masks": unreal.TextureCompressionSettings.TC_MASKS,
    "TC_Grayscale": unreal.TextureCompressionSettings.TC_GREYSCALE,
    "TC_Emissive": unreal.TextureCompressionSettings.TC_EMISSIVE,
}


def load_manifest(path=MANIFEST):
    if not os.path.exists(path):
        unreal.log_warning("ADFRC manifest not found: %s" % path)
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def run(manifest_path=MANIFEST):
    data = load_manifest(manifest_path)
    wanted = {e["name"]: e for e in data.get("textures", [])}
    if not wanted:
        return 0

    changed = 0
    for tex in unreal.EditorAssetLibrary.list_assets("T_", recursive=True, include_folder=True):
        name = os.path.basename(tex.split(".")[0])
        entry = wanted.get(name + ".png") or wanted.get(name)
        if not entry:
            continue
        obj = unreal.EditorAssetLibrary.load_asset(tex)
        if not isinstance(obj, unreal.Texture2D):
            continue
        obj.set_editor_property("srgb", entry["srgb"])
        obj.set_editor_property(
            "compression_settings", COMPRESSION[entry["compression"]])
        obj.set_editor_property("filter", unreal.TextureFilter.TFILTER_ANISOTROPIC
                                if entry["srgb"] else unreal.TextureFilter.TFILTER_DEFAULT)
        changed += 1
        if changed % 200 == 0:
            unreal.log("ADFRC: %d textures configured" % changed)

    unreal.EditorAssetLibrary.save_directory("/Game/T_", only_if_is_dirty=False,
                                            recursive=True)
    unreal.log("ADFRC: configured %d / %d manifest textures" % (changed, len(wanted)))
    return changed
'''
    os.makedirs(os.path.dirname(UE_SCRIPT), exist_ok=True)
    with open(UE_SCRIPT, "w", encoding="utf-8") as fh:
        fh.write(body)
    print("ue script -> %s" % UE_SCRIPT)


if __name__ == "__main__":
    main()
