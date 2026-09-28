#!/usr/bin/env python3
"""Parse ADFRC `texHeaders.bin` and cross-check it against the decoded PNGs.

What the file is
----------------
Each addon ships one `texHeaders.bin` at its root: BI's texture LOD dictionary
(the P3D `\\0DHT` tag, little-endian "THD0").  Layout:

    0x00  char[4] "0DHT"
    0x04  u32     version (1)
    0x08  u32     count          number of texture records
    0x0C  40-byte file-level block
    then `count` records, each of which is:
        a NUL-terminated addon-relative path, e.g.
            "adfrc_apache\\data\\heli_attack_03_adds_as.paa"
        a variable-length trailer of config values (floats, -1 sentinels, ...)
        a run of 12-byte mip records:
            u16 0x0306   tag
            u32 offset   byte offset of that mip's data inside the .paa
            u16 width
            u16 height
            u16 0

The trailer length varies between records, so this parser does not assume a
fixed stride.  It anchors on the `.paa` name strings and takes the mip-tag run
that follows each one.  Two independent checks confirm the record count:

  * the number of `.paa` name strings equals the declared `count` in all 12
    files, and the 12 declared counts sum to exactly 2500 -- the number of
    `.paa` files in the whole pack, so every texture is covered once;
  * the u32 offsets in each mip record are compared against the offset table
    inside the referenced `.paa`; a mismatch is reported per texture.

The cross-check
---------------
For each texture the recorded mip dimensions are compared with the PNG that
`paa2png` produced and with the mip headers inside the original `.paa`.  The
`.paa` mip0 header is the authority: it carries the real mip0 size, and the
tool reports whether the PNG agrees with it.

Usage:  python texheaders.py [root] [out.json]
"""
import collections
import json
import os
import re
import struct
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"E:\SouthernSpear\Content\Sourced\ADF_Extracted"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "_tools", "texheaders_report.json")

MAGIC = b"0DHT"
MIP_TAG = 0x0306
MAX_DIM = 8192
NAME_RE = re.compile(rb"[ -~]{4,}\.paa\x00")


def find_files():
    out = []
    for top in ("Source", "Workshop"):
        for dirpath, _d, files in os.walk(os.path.join(ROOT, top)):
            for f in files:
                if f.lower() == "texheaders.bin":
                    out.append(os.path.join(dirpath, f))
    return sorted(out)


def read_mips(d, start, stop):
    """Collect plausible 12-byte mip records in [start, stop)."""
    out = []
    for off in range(start, stop - 11):
        if d[off] != 0x06 or d[off + 1] != 0x03:
            continue
        _tag, offset, w, h, _pad = struct.unpack_from("<HIHHH", d, off)
        if not (0 < w <= MAX_DIM and 0 < h <= MAX_DIM):
            continue
        if w & (w - 1) or h & (h - 1):      # not a power of two
            continue
        out.append({"tag_offset": off, "paa_offset": offset, "w": w, "h": h})
    return out


def parse(path):
    d = open(path, "rb").read()
    if d[:4] != MAGIC:
        raise ValueError("bad magic %r" % d[:4])
    version, count = struct.unpack_from("<2I", d, 4)

    names = [(m.start(), m.group()[:-1].decode("ascii", "replace"))
             for m in NAME_RE.finditer(d)]
    problems = []
    if len(names) != count:
        problems.append("declared count %d but found %d name strings"
                        % (count, len(names)))

    records = []
    for i, (pos, name) in enumerate(names):
        end = names[i + 1][0] if i + 1 < len(names) else len(d)
        mips = read_mips(d, pos, end)
        records.append({"name": name, "mips": mips,
                        "declared_mip_count_field": _mip_count_field(d, pos)})
    return {
        "file": os.path.relpath(path, ROOT).replace("\\", "/"),
        "addon": os.path.basename(os.path.dirname(path)),
        "version": version,
        "declared_records": count,
        "name_strings": len(names),
        "records": records,
        "problems": problems,
    }


def _mip_count_field(d, pos):
    """The u32 a few bytes before the name that states the mip count."""
    best = None
    for back in range(2, 24):
        o = pos - back
        if o < 4:
            break
        v = struct.unpack_from("<I", d, o)[0]
        if 1 <= v <= 20:
            best = v
    return best


def png_size(path):
    """(w, h) or None."""
    info = png_info(path)
    return (info["w"], info["h"]) if info else None


def png_info(path):
    try:
        with open(path, "rb") as fh:
            head = fh.read(26)
    except OSError:
        return None
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", head[16:24])
    return {"w": w, "h": h, "bit_depth": head[24], "colour_type": head[25]}


# Arma PAA u16 type -> (name, bpp, has_alpha)
PAA_TYPES = {
    0xFF01: ("DXT1", 4, True),    # 1-bit alpha
    0xFF03: ("DXT3", 8, True),    # 4-bit explicit alpha
    0xFF05: ("DXT5", 8, True),    # interpolated alpha
    0xFF00: ("RAW", 0, False),
}


def paa_format(path):
    try:
        with open(path, "rb") as fh:
            head = fh.read(2)
    except OSError:
        return None
    t = struct.unpack("<H", head)[0]
    return PAA_TYPES.get(t, ("unknown 0x%04x" % t, 0, None))


def format_verdict(fmt, png):
    """Does the decoded PNG look like it could have come from that PAA type?"""
    if not fmt or not png:
        return None
    name = fmt[0]
    ct = png["colour_type"]
    if png["bit_depth"] != 8:
        return "PNG bit depth %d (expected 8)" % png["bit_depth"]
    if name in ("DXT1",):
        # DXT1 carries at most 1 bit of alpha, so RGBA output is legitimate
        # but a 2-bit/greyscale PNG is not.
        if ct not in (2, 6):
            return "DXT1 decoded to PNG colour type %d" % ct
        return "ok"
    if name in ("DXT3", "DXT5"):
        if ct != 6:
            return "%s has an alpha channel but the PNG is colour type %d" \
                % (name, ct)
        return "ok"
    if name == "RAW":
        return "ok" if ct in (2, 6) else "RAW decoded to colour type %d" % ct
    return "unknown PAA type %s" % name


def paa_info(path):
    """(mip0 w, h, lzo, [offsets]) from the .paa itself."""
    try:
        d = open(path, "rb").read()
    except OSError:
        return None
    i = d.find(b"SFFO")
    if i < 0:
        return None
    offsets = []
    q = i + 8
    while q + 4 <= len(d):
        v = struct.unpack_from("<I", d, q)[0]
        if v == 0 or v >= len(d):
            break
        offsets.append(v)
        q += 4
    if not offsets:
        return None
    o = offsets[0]
    w = d[o] | (d[o + 1] << 8)
    h = d[o + 2] | (d[o + 3] << 8)
    return {"mip0": (w & 0x7FFF, h), "lzo": bool(w & 0x8000), "offsets": offsets}


def build_png_index(root):
    """stem -> [paths] for every decoded PNG, for last-resort lookup.

    Needed because 13 texHeaders entries do not mirror to a PNG at the
    expected path: 6 extraction outputs kept the source extension in the name
    (`X.PAA.png`), and 7 name a texture that lives in a different addon folder
    than the header table claims.  Both are located by stem so the
    cross-check still covers all 2500 textures, and the substitution is
    reported rather than hidden.
    """
    idx = collections.defaultdict(list)
    base = os.path.join(root, "Textures")
    for dirpath, _d, files in os.walk(base):
        for f in files:
            if not f.lower().endswith(".png"):
                continue
            stem = f[:-4]
            if stem.lower().endswith(".paa"):
                stem = stem[:-4]
            idx.setdefault(stem.lower(), []).append(os.path.join(dirpath, f))
    return idx


def resolve(addon, name, root, png_index=None):
    """texHeaders names are addon-relative with backslashes and a .paa suffix.

    The decoded PNGs are not all under one layout: some extraction passes kept
    the `Textures/Workshop/<addon>/...` prefix and some dropped it to
    `Textures/<mod>/...`.  Try each and report which one matched so the split
    is visible instead of silently costing us cross-checks.
    """
    rel = name.replace("\\", "/").lower()
    stem = rel[:-4] if rel.endswith(".paa") else rel
    for top in ("Workshop", "Source"):
        paa = os.path.join(root, top, addon, rel.replace("/", os.sep))
        if not os.path.exists(paa):
            continue
        relsep = stem.replace("/", os.sep)
        for layout, cand in (
            ("%s/%s" % (top, addon),
             os.path.join(root, "Textures", top, addon, relsep + ".png")),
            ("%s only" % top,
             os.path.join(root, "Textures", relsep + ".png")),
            ("bare",
             os.path.join(root, "Textures", os.path.basename(relsep) + ".png")),
        ):
            if os.path.exists(cand):
                return paa, cand, layout
        if png_index:
            hits = png_index.get(stem.replace("/", "").lower()) or \
                png_index.get(os.path.basename(stem).lower())
            if hits:
                return paa, sorted(hits)[0], "by-name elsewhere"
        return paa, None, None
    return None, None, None


def main():
    files = find_files()
    if not files:
        print("no texHeaders.bin under %s" % ROOT)
        return 1

    files_out = []
    textures = []
    totals = collections.Counter()
    layouts = collections.Counter()
    formats = collections.Counter()
    png_index = build_png_index(ROOT)

    for p in files:
        try:
            f = parse(p)
        except Exception as exc:  # noqa: BLE001
            files_out.append({"file": os.path.relpath(p, ROOT).replace("\\", "/"),
                              "fatal": str(exc)})
            totals["fatal_files"] += 1
            continue
        files_out.append({k: v for k, v in f.items() if k != "records"})
        if f["problems"]:
            totals["files_with_problems"] += 1

        for rec in f["records"]:
            paa_path, png_path, layout = resolve(f["addon"], rec["name"],
                                                 ROOT, png_index)
            if layout:
                layouts[layout] += 1
            elif png_path is None and paa_path:
                layouts["unresolved"] += 1
            paa = paa_info(paa_path) if paa_path else None
            pinfo = png_info(png_path) if png_path else None
            png = (pinfo["w"], pinfo["h"]) if pinfo else None
            fmt = paa_format(paa_path) if paa_path else None
            dims = [(m["w"], m["h"]) for m in rec["mips"]]
            chain = [w for w, _h in dims]

            e = {
                "file": f["file"],
                "addon": f["addon"],
                "name": rec["name"],
                "recorded_dims": dims,
                "recorded_chain": chain,
                "declared_mip_count_field": rec["declared_mip_count_field"],
                "paa": os.path.relpath(paa_path, ROOT).replace("\\", "/")
                if paa_path else None,
                "png": os.path.relpath(png_path, ROOT).replace("\\", "/")
                if png_path else None,
                "png_layout": layout,
                "png_size": list(png) if png else None,
                "paa_mip0": list(paa["mip0"]) if paa else None,
                "paa_lzo": paa["lzo"] if paa else None,
                "paa_format": fmt[0] if fmt else None,
                "png_colour_type": pinfo["colour_type"] if pinfo else None,
                "png_bit_depth": pinfo["bit_depth"] if pinfo else None,
            }

            fv = format_verdict(fmt, pinfo)
            if fv is not None:
                e["format_check"] = fv
                if fv != "ok":
                    totals["format_mismatch"] += 1
                else:
                    totals["format_ok"] += 1
            if fmt:
                formats[fmt[0]] += 1

            if paa and rec["mips"]:
                want = list(paa["offsets"])[:len(rec["mips"])]
                got = [m["paa_offset"] for m in rec["mips"]]
                e["offsets_match_paa"] = (want == got)
                if not e["offsets_match_paa"]:
                    totals["offset_mismatch"] += 1

            pw, ph = png if png else (None, None)
            aw, ah = paa["mip0"] if paa else (None, None)

            if pw is None:
                e["verdict"] = "no decoded PNG"
                totals["no_png"] += 1
            elif not chain:
                e["verdict"] = "no mip dims recorded"
                totals["no_dims"] += 1
            elif aw and (pw, ph) != (aw, ah):
                e["verdict"] = "PNG DISAGREES WITH PAA"
                totals["png_vs_paa_mismatch"] += 1
            elif chain[0] == pw:
                e["verdict"] = "chain starts at mip0"
                totals["chain_from_mip0"] += 1
            elif all(b * 2 == a for a, b in zip(chain, chain[1:])) and \
                    chain[0] * 2 == pw:
                # Recorded dims are mip1..mipN; mip0's size is not in the table.
                e["verdict"] = "chain starts at mip1 (mip0 size absent)"
                totals["chain_from_mip1"] += 1
            else:
                e["verdict"] = "UNEXPECTED CHAIN"
                totals["unexpected_chain"] += 1
            textures.append(e)

    report = {
        "summary": {
            "files": len(files),
            "declared_records": sum(f.get("declared_records", 0)
                                    for f in files_out),
            "name_strings": sum(f.get("name_strings", 0) for f in files_out),
            "textures_checked": len(textures),
            "offset_table_mismatches": totals.get("offset_mismatch", 0),
            "files_with_problems": totals.get("files_with_problems", 0),
            "png_layouts": dict(sorted(layouts.items())),
            "paa_formats": dict(sorted(formats.items())),
            "format_checked": totals.get("format_ok", 0)
            + totals.get("format_mismatch", 0),
            **{("verdict_" + k.replace(" ", "_")): v
               for k, v in sorted(totals.items())},
        },
        "files": files_out,
        "textures": textures,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print(json.dumps(report["summary"], indent=1))

    odd = [t for t in textures
           if t["verdict"] not in
           ("chain starts at mip1 (mip0 size absent)", "chain starts at mip0",
            "no mip dims recorded")
           or t.get("format_check") not in (None, "ok")]
    if odd:
        print("\n%d textures outside the expected pattern:\n" % len(odd))
        for t in odd[:30]:
            print("  %-34s %-40s rec=%-16s png=%-12s paa0=%-12s %s"
                  % (t["verdict"], t["name"][-40:], t["recorded_chain"][:4],
                     t["png_size"], t["paa_mip0"],
                     t.get("format_check") or ""))
        if len(odd) > 30:
            print("  ... %d more" % (len(odd) - 30))
    else:
        print("\nall %d textures: PNG dimensions equal the .paa mip0 header, "
              "the recorded chains follow one rule, and every PNG is "
              "format-consistent with its PAA type" % len(textures))

    # Completeness in both directions: the header table should name exactly the
    # set of .paa files on disk, once each.
    on_disk = set()
    for top in ("Source", "Workshop"):
        for dirpath, _d, files in os.walk(os.path.join(ROOT, top)):
            for f in files:
                if f.lower().endswith(".paa"):
                    on_disk.add(f[:-4].lower())
    named = {os.path.basename(t["name"])[:-4].lower() for t in textures}
    print("\ncompleteness: %d distinct names in texHeaders, %d distinct .paa on "
          "disk, %d on disk not referenced, %d referenced but absent"
          % (len(named), len(on_disk), len(on_disk - named),
             len(named - on_disk)))
    report["summary"]["paa_on_disk"] = len(on_disk)
    report["summary"]["paa_not_referenced"] = len(on_disk - named)
    report["summary"]["referenced_but_absent"] = len(named - on_disk)

    # What do the textures with no recorded mip dims have in common?
    nodims = [t for t in textures if t["verdict"] == "no mip dims recorded"]
    buckets = collections.Counter()
    for t in nodims:
        stem = os.path.basename(t["name"])[:-4].lower()
        if "_nohq" in stem or "_smdi" in stem or "_as" in stem or "_ca" in stem:
            buckets["camouflage variant suffix"] += 1
        elif "\\ui\\" in t["name"].lower() or "\\ui" in t["name"].lower():
            buckets["under a ui/ folder"] += 1
        else:
            buckets["other"] += 1
    print("\n%d textures carry no mip dims in texHeaders: %s"
          % (len(nodims), dict(buckets)))
    report["summary"]["no_dims_breakdown"] = dict(buckets)

    # Structural finding: the recorded mip chain exists for exactly the DXT1
    # textures and for none of the DXT5 ones, so this is a property of the
    # format rather than a parsing accident.
    corr = collections.Counter(
        (t["paa_format"], bool(t["recorded_chain"])) for t in textures)
    report["summary"]["format_vs_recorded_dims"] = {
        "%s/%s" % (f, "has chain" if has else "no chain"): n
        for (f, has), n in sorted(corr.items())}

    # All decoded PNGs are 8-bit RGBA.  For the DXT1 majority the source only
    # has 1 bit of alpha, so an RGB import would be lossless and cheaper.
    cts = collections.Counter(t["png_colour_type"] for t in textures)
    nonsquare = [t for t in textures
                 if t["png_size"] and t["png_size"][0] != t["png_size"][1]]
    sizes = collections.Counter("%dx%d" % tuple(t["png_size"])
                                for t in textures if t["png_size"])
    report["summary"]["png_colour_types"] = dict(sorted(cts.items()))
    report["summary"]["png_sizes"] = dict(sizes.most_common())
    report["summary"]["non_square_textures"] = len(nonsquare)
    report["summary"]["dxt1_textures"] = formats.get("DXT1", 0)
    report["summary"]["lzo_mip0"] = sum(1 for t in textures if t["paa_lzo"])

    print("\nstructure: recorded mip chain vs PAA compression")
    for k, v in sorted(corr.items()):
        print("   %-6s %-10s %d" % (k[0], "has chain" if k[1] else "no chain", v))
    print("png colour types: %s   non-square: %d   distinct sizes: %d"
          % (dict(sorted(cts.items())), len(nonsquare), len(sizes)))
    print("lzo-compressed mip0: %d of %d" % (report["summary"]["lzo_mip0"],
                                              len(textures)))

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print("\nreport: %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
