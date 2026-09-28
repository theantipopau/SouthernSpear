#!/usr/bin/env python3
"""Extract Arma 3 PBO archives (Workshop mod) into ADF_Extracted\\Workshop.

Format (verified against KoffeinFlummi/armake src/unpack.c and real ADFRC PBOs):
  byte 0        : unknown/marker
  [1..5]        : "sreV" optional header-extension marker
  offset 21     : null-terminated key/value pairs until empty key   (if sreV)
  then entries  : name\0 + u32 method + u32 originalSize + u32 skip
                  + u32 timestamp + u32 dataSize   (20 bytes after name)
  empty name\0  : + 20 bytes  -> end of table
  then data     : blobs in entry order, dataSize bytes each
Blobs starting with 1f 8b are gzipped (Arma binarized configs) -> decompressed.
"""
import gzip
import io
import os
import sys

ROOT = r"E:\SouthernSpear"
PBO_DIR = r"D:\SteamLibrary\steamapps\common\Arma 3\!Workshop\@ADF Re-Cut [Beta]\addons"
OUT_ROOT = os.path.join(ROOT, r"Content\Sourced\ADF_Extracted\Workshop")

BAD = set('<>:"|?*') | {chr(i) for i in range(32)}


def read_cstr(buf, pos):
    end = buf.index(b"\x00", pos)
    return buf[pos:end].decode("latin-1"), end + 1


def parse_pbo(path):
    with open(path, "rb") as fh:
        buf = fh.read()
    pos = 0
    props = {}
    if len(buf) > 5 and buf[1:5] == b"sreV":
        pos = 21
        while True:
            key, pos = read_cstr(buf, pos)
            if key == "":
                break
            val, pos = read_cstr(buf, pos)
            props[key] = val
    entries = []
    while True:
        name, pos = read_cstr(buf, pos)
        if name == "":
            pos += 20
            break
        method = int.from_bytes(buf[pos:pos + 4], "little")
        orig = int.from_bytes(buf[pos + 4:pos + 8], "little")
        data_size = int.from_bytes(buf[pos + 16:pos + 20], "little")
        pos += 20
        entries.append({"name": name, "method": method, "orig": orig,
                        "size": data_size, "offset": pos})
        pos += data_size  # data is interleaved right after each header?
    return buf, props, entries


def parse_pbo_sequential(path):
    """Headers are contiguous; data blobs follow in entry order (armake style)."""
    with open(path, "rb") as fh:
        buf = fh.read()
    pos = 0
    props = {}
    if len(buf) > 5 and buf[1:5] == b"sreV":
        pos = 21
        while True:
            key, pos = read_cstr(buf, pos)
            if key == "":
                break
            val, pos = read_cstr(buf, pos)
            props[key] = val
    entries = []
    while True:
        name, pos = read_cstr(buf, pos)
        if name == "":
            pos += 20
            break
        method = int.from_bytes(buf[pos:pos + 4], "little")
        orig = int.from_bytes(buf[pos + 4:pos + 8], "little")
        data_size = int.from_bytes(buf[pos + 16:pos + 20], "little")
        pos += 20
        entries.append({"name": name, "method": method, "orig": orig, "size": data_size})
    data_start = pos
    off = data_start
    for e in entries:
        e["offset"] = off
        off += e["size"]
    return buf, props, entries, off


def safe_path(base, rel):
    rel = rel.replace("\\", "/").strip("/")
    parts = [p for p in rel.split("/") if p not in ("", ".", "..")]
    return os.path.join(base, *parts)


def extract(pbo_path, out_base, limit_report=10):
    buf, props, entries, end = parse_pbo_sequential(pbo_path)
    stats = {"files": 0, "bytes": 0, "gz": 0, "skipped_garbage": 0, "errors": []}
    os.makedirs(out_base, exist_ok=True)
    if props:
        with open(os.path.join(out_base, "$PBOPREFIX$.txt"), "w", encoding="utf-8") as fh:
            for k, v in props.items():
                fh.write(f"{k}={v}\n")
    for e in entries:
        name = e["name"]
        blob = buf[e["offset"]:e["offset"] + e["size"]]
        if any(c in BAD for c in name):
            stats["skipped_garbage"] += 1
            continue
        if blob[:2] == b"\x1f\x8b":
            try:
                blob = gzip.decompress(blob)
                stats["gz"] += 1
            except Exception as ex:  # noqa: BLE001
                stats["errors"].append(f"gzip {name}: {ex}")
                continue
        dst = safe_path(out_base, name)
        os.makedirs(os.path.dirname(dst) or out_base, exist_ok=True)
        try:
            with open(dst, "wb") as fh:
                fh.write(blob)
            stats["files"] += 1
            stats["bytes"] += len(blob)
        except OSError as ex:
            stats["errors"].append(f"write {name}: {ex}")
    return props, entries, end, len(buf), stats


def main():
    pbos = sorted(f for f in os.listdir(PBO_DIR) if f.lower().endswith(".pbo"))
    only = sys.argv[1:] or None
    grand = {"files": 0, "bytes": 0, "gz": 0, "skipped_garbage": 0, "errors": []}
    for pbo in pbos:
        stem = os.path.splitext(pbo)[0]
        if only and stem not in only:
            continue
        src = os.path.join(PBO_DIR, pbo)
        out = os.path.join(OUT_ROOT, stem)
        props, entries, end, size, stats = extract(src, out)
        print(f"{pbo:24s} entries={len(entries):5d} files={stats['files']:5d} "
              f"gz={stats['gz']:3d} garbage={stats['skipped_garbage']:3d} "
              f"out={stats['bytes'] / 1e6:9.1f}MB  span_ok={end <= size}"
              f"{' prefix=' + props.get('prefix', '?') if props else ''}")
        for err in stats["errors"][:10]:
            print("   ERR:", err)
        for k in grand:
            if k != "errors":
                grand[k] += stats[k]
        grand["errors"].extend(stats["errors"])
    print(f"TOTAL files={grand['files']} bytes={grand['bytes'] / 1e6:.1f}MB "
          f"gz={grand['gz']} garbage={grand['skipped_garbage']} errors={len(grand['errors'])}")


if __name__ == "__main__":
    main()
