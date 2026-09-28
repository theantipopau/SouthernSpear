#!/usr/bin/env python3
"""Batch-convert the ADFRC pack's .paa textures to PNG.

The files under Content/Sourced/ADF are Git LFS *pointer* stubs; the real
data was fetched into Saved/AdfrcLfsTemp/repo by `git lfs pull`. Each local
pointer's LFS oid (sha256 of content) is used to locate the real file in
that clone, then paa2png.exe decodes it to PNG under the destination root,
mirroring the local tree.
"""
import concurrent.futures as cf
import hashlib
import os
import re
import shutil
import subprocess
import sys

ROOT = r"E:\SouthernSpear"
SRC = os.path.join(ROOT, r"Content\Sourced\ADF")
CLONE = os.path.join(ROOT, r"Saved\AdfrcLfsTemp\repo")
OUT = os.path.join(ROOT, r"Content\Sourced\ADF_Extracted")
PAA2PNG = os.path.join(ROOT, r"Saved\AdfrcLfsTemp\build\paa2png.exe")
WORKERS = 8

OID_RE = re.compile(rb"oid sha256:([0-9a-f]{64})")


def build_oid_map():
    """sha256 of every materialised .paa in the clone -> its path."""
    m = {}
    for r, _d, fs in os.walk(os.path.join(CLONE, "Addons")):
        for f in fs:
            if not f.lower().endswith(".paa"):
                continue
            p = os.path.join(r, f)
            if os.path.getsize(p) < 100:
                continue
            h = hashlib.sha256()
            with open(p, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            m[h.hexdigest()] = p
    return m


def local_pointers():
    out = []
    for r, _d, fs in os.walk(SRC):
        for f in fs:
            if not f.lower().endswith(".paa"):
                continue
            p = os.path.join(r, f)
            with open(p, "rb") as fh:
                head = fh.read(200)
            if head.startswith(b"version https://git-lfs"):
                oid = OID_RE.search(head).group(1).decode()
                out.append((p, oid))
            else:
                out.append((p, None))  # real paa already on disk
    return out


def convert(job):
    src_path, oid, real_path = job
    rel = os.path.relpath(src_path, SRC)
    dst = os.path.join(OUT, "Textures", os.path.splitext(rel)[0] + ".png")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        return ("skip", rel)
    r = subprocess.run([PAA2PNG, real_path, dst], capture_output=True, text=True)
    if r.returncode != 0:
        if os.path.exists(dst):
            os.remove(dst)
        return ("FAIL", rel + " :: " + (r.stderr.strip() or f"exit {r.returncode}"))
    return ("ok", rel)


def main():
    oid_map = build_oid_map()
    print(f"clone index: {len(oid_map)} real textures")
    jobs, missing = [], []
    for path, oid in local_pointers():
        real = path if oid is None else oid_map.get(oid)
        if real is None:
            missing.append(path)
            continue
        jobs.append((path, oid, real))
    print(f"to convert: {len(jobs)}, missing data: {len(missing)}")
    for p in missing:
        print("  MISSING:", os.path.relpath(p, SRC))

    fails, n = [], 0
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for status, rel in ex.map(convert, jobs):
            n += 1
            if status == "FAIL":
                fails.append(rel)
            if n % 100 == 0:
                print(f"  {n}/{len(jobs)} done")
    print(f"converted: {n - len(fails) - 0}/{len(jobs)}  failures: {len(fails)}")
    for f in fails:
        print("  FAIL:", f)
    return 1 if fails or missing else 0


if __name__ == "__main__":
    sys.exit(main())
