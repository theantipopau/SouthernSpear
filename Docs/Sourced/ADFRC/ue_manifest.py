#!/usr/bin/env python3
"""Build the single UE-ready asset registry for the extracted ADFRC set.

Everything else in ADF_Extracted is per-format.  Another agent that wants to
know "what can I use for the M4A5, and what do I need to import first?" has to
stitch together FBX paths, texture names buried in material strings, decoded
.rvmat stage tables, rig definitions and clip lists.  This produces one
`ASSET_MANIFEST.json` that answers that directly.

Usage:  python ue_manifest.py [root] [out.json]
"""
import collections
import glob
import json
import os
import re
import struct
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"E:\SouthernSpear\Content\Sourced\ADF_Extracted"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "ASSET_MANIFEST.json")

MAT_RE = re.compile(r"P3D:\s*(?P<tex>[^:]*?)\s*::\s*(?P<mat>.+?)\s*$")
PROP_RE = re.compile(r'texture\s*=\s*"([^"]*)"')
CLASS_RE = re.compile(r"class\s+(\w+)\s*\{(.*?)\n\s*\};", re.S)


def png_size(path):
    try:
        with open(path, "rb") as fh:
            head = fh.read(26)
        if head[:8] != b"\x89PNG\r\n\x1a\n":
            return None
        w, h = struct.unpack(">II", head[16:24])
        return w, h
    except Exception:  # noqa: BLE001
        return None


def fbx_objects(path):
    """Count Geometry/Model records so LOD count can be reported."""
    try:
        data = open(path, "rb").read()
    except Exception:  # noqa: BLE001
        return 0, 0
    geom = data.count(b"\x00\x00\x00\x1eKaydara")
    return data.count(b"Geometry\x00\x01"), geom


def build_models():
    """Parse the UE FBX set: geometry + material -> texture bindings."""
    out = []
    by_name = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "Models_UE", "**", "*.fbx"), recursive=True)):
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        try:
            data = open(p, "rb").read()
        except Exception:  # noqa: BLE001
            continue
        # Material names survive as `P3D: <texture> :: <material>`.
        mats = []
        for m in re.finditer(rb"P3D:[^\x00]{0,200}?\.rvmat", data):
            s = m.group(0).decode("latin1", "replace")
            mm = MAT_RE.search(s)
            if mm:
                mats.append({"texture": mm.group("tex").strip(),
                             "material": mm.group("mat").strip()})
        # Deduplicate, keep order stable.
        seen, uniq = set(), []
        for m in mats:
            k = (m["texture"], m["material"])
            if k not in seen:
                seen.add(k)
                uniq.append(m)
        size = os.path.getsize(p)
        e = {
            "fbx": rel,
            "size_bytes": size,
            "pack": rel.split("/")[1] if "/" in rel else "",
            "name": os.path.splitext(os.path.basename(p))[0],
            "materials": uniq,
            "material_count": len(uniq),
            "textures": sorted({m["texture"] for m in uniq if m["texture"]}),
        }
        out.append(e)
        by_name[e["name"].lower()] = e
    return out, by_name


def build_textures():
    path = os.path.join(ROOT, "Textures", "_ue_manifest.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["textures"]


def build_materials():
    """Stage -> texture from the decoded material text (readable + binarised)."""
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "Materials_Text", "**", "*.txt"),
                              recursive=True)):
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        if not rel.lower().endswith(".rvmat.txt"):
            continue
        try:
            text = open(p, encoding="utf-8", errors="ignore").read()
        except Exception:  # noqa: BLE001
            continue
        stages = []
        for name, body in CLASS_RE.findall(text):
            tm = PROP_RE.search(body)
            if not tm:
                continue
            tex = tm.group(1)
            stages.append({
                "stage": name,
                "texture": tex,
                "kind": "proc" if tex.startswith("#") else "texture",
            })
        out.append({
            "material": "/" + rel.replace("Materials_Text/", "").replace(".txt", ""),
            "source_rvmat": rel.replace("Materials_Text/", "").replace(".txt", ".rvmat"),
            "stages": stages,
        })
    return out


def build_rigs():
    rig_dir = os.path.join(ROOT, "Animations", "Rig")
    idx = os.path.join(rig_dir, "_rig_index.json")
    if not os.path.exists(idx):
        return [], {}
    with open(idx, encoding="utf-8") as fh:
        clips = json.load(fh)["clips"]
    rigs = []
    for p in sorted(glob.glob(os.path.join(rig_dir, "*.json"))):
        if os.path.basename(p).startswith("_"):
            continue
        with open(p, encoding="utf-8") as fh:
            r = json.load(fh)
        key = r["rig"]
        mine = sorted(os.path.basename(os.path.join(os.path.dirname(p), d))
                      for d in os.listdir(os.path.join(rig_dir, key))
                      if d.endswith(".json"))
        mine = [m[:-5] for m in mine]
        rigs.append({
            "rig": key,
            "root": r["root"],
            "bone_count": r["bone_count"],
            "max_depth": r["max_depth"],
            "bones": r["bones"],
            "definition": "Animations/Rig/%s.json" % key,
            "skeleton_fbx": "Animations_UE/%s/%s_skeleton.fbx" % (key, key),
            "clip_fbx": ["Animations_UE/%s/%s.fbx" % (key, c) for c in mine],
            "clip_names": mine,
        })
    return rigs, clips


def build_sounds():
    """Every WAV in the tree, plus provenance for the ones decoded from OGG."""
    ogg_prov = {}
    ogg_report = os.path.join(ROOT, "_tools", "ogg_sounds.json")
    if os.path.exists(ogg_report):
        try:
            with open(ogg_report, encoding="utf-8") as fh:
                data = json.load(fh)
            for e in data.get("files", []):
                if e.get("wav"):
                    # Case-insensitive: the tree mixes MAG-58.wss / mag-58.ogg
                    # and Windows will not tell us which casing won.
                    ogg_prov[e["wav"].replace("\\", "/").lower()] = e
        except Exception:  # noqa: BLE001
            ogg_prov = {}

    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "**", "*.wav"), recursive=True)):
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        if "/Textures/" in "/" + rel or rel.startswith("Textures/"):
            continue
        try:
            import wave
            with wave.open(p, "rb") as w:
                dur = w.getnframes() / float(w.getframerate() or 1)
                meta = {"channels": w.getnchannels(), "rate": w.getframerate(),
                        "bits": w.getsampwidth() * 8}
        except Exception:  # noqa: BLE001
            dur, meta = 0.0, {}
        entry = {"wav": rel, "seconds": round(dur, 3), **meta}
        prov = ogg_prov.get(rel.lower())
        if prov:
            src = prov.get("ogg_audio") or {}
            if prov.get("existing_wav_differs"):
                # Same name, different audio: this WAV is the .wss decode.
                entry["source"] = "wss"
                entry["name_conflicts_with_ogg"] = {
                    "ogg": prov["ogg"],
                    "ogg_seconds": src.get("seconds"),
                    "ogg_rate": src.get("rate"),
                    "ogg_channels": src.get("channels"),
                    "wss_seconds": (prov.get("existing_wav") or {}).get("seconds"),
                    "note": ("the .ogg and the .wss of this name are different "
                             "recordings; this file is the .wss, which is what "
                             "Arma plays"),
                }
            else:
                entry["source"] = "ogg"
                entry["ogg"] = prov["ogg"]
                entry["ogg_md5"] = prov["ogg_md5"]
                if src.get("peak_dbfs") is not None:
                    # Vorbis decodes above 0 dBFS; 16-bit PCM clips there.
                    entry["source_peak_dbfs"] = src["peak_dbfs"]
                    entry["source_over_0dbfs_pct"] = src.get("clipped_pct")
        out.append(entry)
    return out


def main():
    models, by_name = build_models()
    textures = build_textures()
    materials = build_materials()
    rigs, clips = build_rigs()
    sounds = build_sounds()

    chan = collections.Counter(t["channel"] for t in textures)
    bound_tex = set()
    for m in models:
        for t in m["textures"]:
            bound_tex.add(os.path.splitext(os.path.basename(t))[0].lower())
    in_manifest = {os.path.splitext(t["name"])[0].lower() for t in textures}
    missing = sorted(bound_tex - in_manifest)

    manifest = {
        "schema": "adfrc-ue-asset-manifest/1",
        "generated_for": "Unreal Engine 5 import + downstream AI tooling",
        "root": ROOT,
        "summary": {
            "models_ue_fbx": len(models),
            "materials_bound": sum(m["material_count"] for m in models),
            "distinct_bound_textures": len(bound_tex),
            "textures_total": len(textures),
            "textures_by_channel": dict(chan.most_common()),
            "materials_decoded": len(materials),
            "rigs": len(rigs),
            "animation_clips": len(clips),
            "sounds_wav": len(sounds),
            "sounds_from_ogg": sum(1 for s in sounds if s.get("source") == "ogg"),
        },
        "notes": {
            "binding": ("Models_UE FBX carry image bindings; Models_FBX do not. "
                        "Always prefer Models_UE."),
            "scale": "Arma is metres, UE is centimetres. Import FBX with scale 0.01 "
                     "or convert on import.",
            "textures": ("Textures/_ue_manifest.json carries per-texture sRGB + "
                         "compression. Run _tools/ue_apply_texture_settings.py in-editor."),
            "rigs": ("Animations_UE holds a skeleton FBX per rig plus one FBX per "
                     "clip. Clips are parent-relative and need retargeting to a UE "
                     "skeleton."),
            "sounds": ("sounds[] covers both sources: .wss and .ogg. WAVs with "
                       "source=ogg were decoded by _tools/ogg_to_wav.py and are "
                       "16-bit PCM at the OGG's native rate. A few OGGs decode "
                       "above 0 dBFS (lossy Vorbis) and are clipped by 16-bit "
                       "PCM; source_peak_dbfs records the pre-clip level so the "
                       "gain can be dialled back on import. Two files carry "
                       "name_conflicts_with_ogg: mag-58 exists as both a .wss "
                       "(1.0s mono 11kHz, what Arma plays) and an .ogg (2.4s "
                       "stereo 44.1kHz), which are different recordings. Both "
                       "were kept; _tools/ogg_sounds.json has the details."),
            "unbound_textures": missing,
        },
        "models": models,
        "materials": materials,
        "rigs": rigs,
        "clips": clips,
        "sounds": sounds,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)

    print(json.dumps(manifest["summary"], indent=1))
    print("unbound texture refs: %d" % len(missing))
    for m in missing[:12]:
        print("   %s" % m)
    print("-> %s (%.1f MB)" % (OUT, os.path.getsize(OUT) / 1e6))


if __name__ == "__main__":
    main()
