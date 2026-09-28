#!/usr/bin/env python3
"""Finish ADF_Extracted: top-level Models\\ and Animations\\ folders plus
Source\\ (all non-texture files from the source pack: sounds, materials,
configs, icons). Texture stubs (.paa LFS pointers) are skipped - their
content lives in Textures\\ as PNG.
"""
import os
import shutil

ROOT = r"E:\SouthernSpear"
SRC = os.path.join(ROOT, r"Content\Sourced\ADF")
EX = os.path.join(ROOT, r"Content\Sourced\ADF_Extracted")
MODELS = os.path.join(EX, "Models")
ANIM = os.path.join(EX, "Animations")
SRCOUT = os.path.join(EX, "Source")
WORKSHOP = os.path.join(EX, "Workshop")


def copy_tree_files(src_root, dst_root, pred, counter):
    for r, _d, fs in os.walk(src_root):
        for f in fs:
            p = os.path.join(r, f)
            if not pred(p):
                continue
            rel = os.path.relpath(p, src_root)
            dst = os.path.join(dst_root, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if not os.path.exists(dst):
                shutil.copy2(p, dst)
            counter[0] += 1


def main():
    stats = {}

    # 1) Models: every .p3d from the workshop dump, grouped by pbo name
    c = [0]
    copy_tree_files(WORKSHOP, MODELS,
                    lambda p: p.lower().endswith(".p3d"), c)
    stats["models"] = c[0]

    # 2) Animations: .rtm from source pack + workshop dump
    c = [0]

    def is_rtm(p):
        return p.lower().endswith(".rtm")

    copy_tree_files(SRC, os.path.join(ANIM, "Source"), is_rtm, c)
    copy_tree_files(WORKSHOP, os.path.join(ANIM, "Workshop"), is_rtm, c)
    stats["animations"] = c[0]

    # 3) Source pack: everything except .paa stubs (textures already decoded)
    c = [0]
    copy_tree_files(SRC, SRCOUT,
                    lambda p: not p.lower().endswith(".paa"), c)
    stats["source_files"] = c[0]

    for k, v in stats.items():
        print(f"{k}: {v}")

    # summary sizes
    for name in ("Models", "Animations", "Source", "Textures", "Workshop"):
        d = os.path.join(EX, name)
        n = b = 0
        for r, _d, fs in os.walk(d):
            for f in fs:
                p = os.path.join(r, f)
                n += 1
                try:
                    b += os.path.getsize(p)
                except OSError:
                    pass
        print(f"{name:12s} {n:6d} files {b / 1e6:10.1f} MB")


if __name__ == "__main__":
    main()
