#!/usr/bin/env python3
"""Convert the Ogg Vorbis sounds in the ADFRC source tree to 16-bit PCM WAV.

Why this exists
---------------
The main audio pass decoded 257 `.wss` files to WAV.  Arma also ships some
sounds as plain `.ogg`, and none of them were picked up:

    Workshop/ADF_Weapons/core/animsounds/MPP_Fast_Reload.ogg
    Workshop/ADF_Weapons/core/animsounds/MPP_Slow_Reload.ogg
    Workshop/ADF_Wheeled/adfrc_boxer/sound/boxer-horn.ogg
    Workshop/ADF_Wheeled/adfrc_boxer/sound/skid_extend.ogg
    Source/adfrc_carlgustav/sound/carlgustav_shot.ogg
    Source/adfrc_carlgustav/sound/carlgustav_reload.ogg

Those six have no `.wss` anywhere, so before this pass they existed nowhere in
the UE sound set.  (A seventh unique OGG, `mag-58`, duplicates `MAG-58.wss`
and is deliberately left alone.)

Output lands beside the source `.ogg`, matching where the `.wss` conversions
already live, so `ue_manifest.py`'s `build_sounds()` picks them up with no
extra wiring.  Sample rate and channel count are preserved from the source,
which is what the `.wss` pass did too.

Resumable: an existing target WAV is skipped unless --force is given.

Usage:  venv_ogg/Scripts/python.exe ogg_to_wav.py [root] [--force]
Report: <root>/_tools/ogg_sounds.json
"""
import hashlib
import json
import os
import sys

import numpy as np
import soundfile as sf

ROOT = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else \
    r"E:\SouthernSpear\Content\Sourced\ADF_Extracted"
FORCE = "--force" in sys.argv
REPORT = os.path.join(ROOT, "_tools", "ogg_sounds.json")
SCAN_ROOTS = ("Source", "Workshop")


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def find_oggs():
    out = []
    for top in SCAN_ROOTS:
        base = os.path.join(ROOT, top)
        for dirpath, _dirs, files in os.walk(base):
            for f in files:
                if f.lower().endswith(".ogg"):
                    out.append(os.path.join(dirpath, f))
    return sorted(out)


def rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


def describe(data, rate):
    """Level and shape measurements for a block of float samples."""
    if not data.size:
        return {"frames": 0, "rate": int(rate), "channels": int(data.shape[1]),
                "seconds": 0.0, "peak_dbfs": None, "rms_dbfs": None,
                "clipped_samples": 0, "clipped_pct": 0.0}
    peak = float(np.max(np.abs(data)))
    rms = float(np.sqrt(np.mean(data ** 2)))
    over = int(np.count_nonzero(np.abs(data) > 1.0))
    return {
        "frames": int(data.shape[0]),
        "rate": int(rate),
        "channels": int(data.shape[1]),
        "seconds": round(data.shape[0] / float(rate), 3),
        "peak_dbfs": round(20 * np.log10(peak), 2) if peak > 0 else None,
        "rms_dbfs": round(20 * np.log10(rms), 2) if rms > 0 else None,
        "clipped_samples": over,
        "clipped_pct": round(100.0 * over / data.size, 4),
    }


def probe(path):
    """Header read of a WAV we did not write, for skip diagnostics."""
    try:
        import wave
        with wave.open(path, "rb") as w:
            return {
                "rate": w.getframerate(),
                "channels": w.getnchannels(),
                "seconds": round(w.getnframes() / float(w.getframerate() or 1), 3),
            }
    except Exception:  # noqa: BLE001
        return None


def load_prior():
    """Deprecated: kept out of the flow.  Reporting is stateless."""
    return {}


def main():
    oggs = find_oggs()
    if not oggs:
        print("no .ogg found under %s" % ROOT)
        return 1

    entries = []
    by_hash = {}
    for src in oggs:
        dst = os.path.splitext(src)[0] + ".wav"
        info = {
            "ogg": rel(src),
            "wav": rel(dst),
            "ogg_md5": md5(src),
        }
        try:
            data, rate = sf.read(src, dtype="float32", always_2d=True)
        except Exception as exc:  # noqa: BLE001
            info["status"] = "decode failed: %s" % exc
            entries.append(info)
            print("FAIL  %s  %s" % (rel(src), exc))
            continue

        # Measurements taken from the lossy source.  Vorbis can decode above
        # 0 dBFS, which 16-bit PCM cannot hold, so the source figures and the
        # written figures are recorded separately rather than conflated.
        info["ogg_audio"] = describe(data, rate)

        if os.path.exists(dst) and not FORCE:
            # A same-named WAV already exists.  It is usually the .wss
            # conversion, which is what Arma itself plays, so leave it alone.
            # But the two are NOT guaranteed to be the same audio, so verify
            # the existing file against the OGG and report the disagreement
            # rather than letting a same-named file pass unnoticed.
            src_a = info["ogg_audio"]
            existing = probe(dst)
            differs = bool(existing) and (
                existing["rate"] != src_a["rate"]
                or existing["channels"] != src_a["channels"]
                or abs(existing["seconds"] - src_a["seconds"]) > 0.05)
            info["status"] = ("wav predates this pass and DIFFERS from the ogg"
                              if differs else "wav already present")
            info["existing_wav"] = existing
            if differs:
                info["existing_wav_differs"] = True
            else:
                try:
                    wav, wrate = sf.read(dst, dtype="float32", always_2d=True)
                    info["wav_audio"] = describe(wav, wrate)
                    info["wav_audio"]["bytes"] = os.path.getsize(dst)
                    info["wav_audio"]["subtype"] = "PCM_16"
                except Exception as exc:  # noqa: BLE001
                    info["probe_failed"] = str(exc)
            entries.append(info)
            by_hash.setdefault(info["ogg_md5"], []).append(info)
            ex = existing or {}
            print("skip  %-58s existing %sch %dHz %.3fs  ogg %sch %dHz %.3fs%s" % (
                rel(dst), ex.get("channels"), ex.get("rate"), ex.get("seconds"),
                src_a["channels"], src_a["rate"], src_a["seconds"],
                "  <-- DIFFERS" if differs else "  (match)"))
            if not differs:
                print("      %-58s source peak %s dBFS, %s%% of samples "
                      "over 0 dBFS" % ("", src_a["peak_dbfs"],
                                       src_a["clipped_pct"]))
            continue

        os.makedirs(os.path.dirname(dst), exist_ok=True)
        sf.write(dst, data, rate, subtype="PCM_16", format="WAV")

        # Read back and confirm the file we just wrote is intact.
        back, back_rate = sf.read(dst, dtype="float32", always_2d=True)
        src_a = info["ogg_audio"]
        if back.shape[0] != src_a["frames"] or back_rate != rate:
            info["status"] = "verify failed (%d/%d frames, %d/%d Hz)" % (
                back.shape[0], src_a["frames"], back_rate, rate)
            entries.append(info)
            print("FAIL  %s  %s" % (rel(dst), info["status"]))
            continue

        info["status"] = "converted"
        info["wav_audio"] = describe(back, back_rate)
        info["wav_audio"]["bytes"] = os.path.getsize(dst)
        info["wav_audio"]["subtype"] = "PCM_16"
        entries.append(info)
        by_hash.setdefault(info["ogg_md5"], []).append(info)
        print("ok    %-58s %6.2fs %dch %dHz  source peak %s dBFS, "
              "%s%% over 0 dBFS" % (
                  rel(dst), src_a["seconds"], src_a["channels"], src_a["rate"],
                  src_a["peak_dbfs"], src_a["clipped_pct"]))

    # Collapse identical OGGs so duplicates are visible rather than silent.
    unique = []
    for h, group in sorted(by_hash.items()):
        first = group[0]
        src_a = first.get("ogg_audio") or {}
        produced = first["status"] == "converted"
        # The wav path is reported whenever a matching WAV is on disk, not
        # only when this particular run wrote it, so a no-op re-run still
        # tells you where the audio lives.
        on_disk = produced or first["status"] == "wav already present"
        unique.append({
            "name": os.path.splitext(os.path.basename(first["ogg"]))[0],
            "ogg_md5": h,
            "copies": len(group),
            "paths": [e["ogg"] for e in group],
            "wav": first.get("wav") if on_disk else None,
            "wav_produced_by_this_pass": produced,
            "rate": src_a.get("rate"),
            "channels": src_a.get("channels"),
            "seconds": src_a.get("seconds"),
            "source_peak_dbfs": src_a.get("peak_dbfs"),
            "source_over_0dbfs_pct": src_a.get("clipped_pct"),
            "status": first["status"],
            "note": ("a .wss-derived wav of the same name already exists and "
                     "differs from this ogg; both were kept"
                     if first.get("existing_wav_differs") else None),
        })

    report = {
        "summary": {
            "ogg_files": len(oggs),
            "unique_sounds": len(unique),
            "converted": sum(1 for e in entries if e["status"] == "converted"),
            "present": sum(1 for e in entries
                           if e["status"].startswith("wav already")),
            "skipped": sum(1 for e in entries if "DIFFERS" in e["status"]),
            "failed": sum(1 for e in entries if "failed" in e["status"]),
            "conflicts": sum(1 for e in entries
                             if e.get("existing_wav_differs")),
        },
        "unique": unique,
        "files": entries,
    }
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)

    print("\n%s" % json.dumps(report["summary"], indent=1))
    print("report: %s" % REPORT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
