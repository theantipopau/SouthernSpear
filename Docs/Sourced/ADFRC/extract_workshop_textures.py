#!/usr/bin/env python3
"""Convert Workshop-extracted .paa textures to PNG, skipping any whose
content (sha256 == Git LFS oid) was already converted from the source pack.
Output: ADF_Extracted\\Textures\\Workshop\\<pbo stem>\\<path>.png
"""
import concurrent.futures as cf
import hashlib
import os
import re
import subprocess
import sys

ROOT = r"E:\SouthernSpear"
SRC = os.path.join(ROOT, r"Content\Sourced\ADF")
WORKSHOP = os.path.join(ROOT, r"Content\Sourced\ADF_Extracted\Workshop")
OUT = os.path.join(ROOT, r"Content\Sourced\ADF_Extracted\Textures\Workshop")
PAA2PNG = os.path.join(ROOT, r"Saved\AdfrcLfsTemp\build\paa2png.exe")
WORKERS = 8
OID_RE = re.compile(rb"oid sha256:([0-9a-f]{64})")


def already_converted():
    done = set()
    for r, _d, fs in os.walk(SRC):
        for f in fs:
            if f.lower().endswith(".paa"):
                with open(os.path.join(r, f), "rb") as fh:
                    head = fh.read(200)
                if head.startswith(b"version https://git-lfs"):
                    done.add(OID_RE.search(head).group(1).decode())
                else:
                    done.add(hashlib.sha256(head).hexdigest())  # rare non-pointer
    return done


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def convert(job):
    src, rel = job
    dst = os.path.join(OUT, rel + ".png")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        return ("skip", rel)
    r = subprocess.run([PAA2PNG, src, dst], capture_output=True, text=True)
    if r.returncode != 0:
        if os.path.exists(dst):
            os.remove(dst)
        return ("FAIL", rel + " :: " + (r.stderr.strip() or f"exit {r.returncode}"))
    return ("ok", rel)


def main():
    done = already_converted()
    print(f"already converted (unique oids): {len(done)}")
    jobs, dup = [], 0
    for r, _d, fs in os.walk(WORKSHOP):
        for f in fs:
            if not f.lower().endswith(".paa"):
                continue
            p = os.path.join(r, f)
            if os.path.getsize(p) < 100:
                continue
            if sha256(p) in done:
                dup += 1
                continue
            rel = os.path.relpath(p, WORKSHOP)
            jobs.append((p, rel))
    print(f"workshop paa: dup={dup} new={len(jobs)} -> converting")

    fails, n = [], 0
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for status, rel in ex.map(convert, jobs):
            n += 1
            if status == "FAIL":
                fails.append(rel)
            if n % 100 == 0:
                print(f"  {n}/{len(jobs)}")
    print(f"converted {n - len(fails)}/{len(jobs)}, failures {len(fails)}")
    for f in fails[:30]:
        print("  FAIL:", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
