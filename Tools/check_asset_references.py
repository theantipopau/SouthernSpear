# Copyright Southern Spear. All Rights Reserved.
#
# Southern Spear asset reference guard.
#
# Why this exists: an Unreal asset is a binary that names its dependencies as
# text. The reference survives even when the file it names does not, so a map can
# be committed that renders correctly on the machine it was built on and wrong on
# every other one. That is not hypothetical -- M_SS_CreekWater referenced
# /Game/WaterPlane/Lake/Textures/T_MediumWaves_N, and that texture was never
# committed. The map looked right here and had no normal map anywhere else.
#
# So this reads every committed .uasset/.umap, pulls out the package paths it
# names, and sorts each one into exactly one bucket:
#
#   ok         referenced, present on disk, tracked by git
#   untracked  present on disk, NOT tracked  -> a fresh clone silently loses it
#   missing    referenced, not on disk at all -> renders wrong, or fails to load
#   external   /Engine or /Script, supplied by the engine, never in this repo
#
# The distinction between "untracked" and "missing" is the useful one: untracked is
# a decision someone has not made yet, missing is a broken reference.
#
# Pure stdlib, no editor and no third-party packages, so CI can run it anywhere.
#
#   python Tools/check_asset_references.py                  # exit 1 on missing/untracked
#   python Tools/check_asset_references.py --json           # machine-readable to stdout
#   python Tools/check_asset_references.py --report f.json  # also write a report file
#   python Tools/check_asset_references.py --allow-untracked # missing only
#
# Exit codes: 0 clean, 1 dangling references, 2 could not run.

import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_SUFFIXES = (".uasset", ".umap")

# A package reference as Unreal writes it: /Game/A/B/C.C, or -- for the mesh of a
# HISM component, an instanced component, and many soft paths -- the bare package
# path with no object name at all, /Game/A/B/C. The trailing .Name is therefore
# optional; requiring it hides every reference of the second kind, which is most
# of what a map references. Asset names in this project are alphanumeric with
# underscores; the character class stays tight on purpose, because a loose one
# matches binary noise and then reports garbage as a broken reference.
REF = re.compile(rb"/(?:[A-Za-z][A-Za-z0-9_]*)/[A-Za-z0-9_./+-]+")
# UTF-16 name tables exist when an asset name is not representable in ASCII.
REF16 = re.compile("/(?:[A-Za-z][A-Za-z0-9_]*)/[A-Za-z0-9_./+-]+".encode("utf-16-le"))


def git(*args):
    return subprocess.run(("git",) + args, cwd=ROOT, capture_output=True, check=False)


def tracked_files():
    """Tracked paths, and a lower-cased set for lookups (Windows and git are case-insensitive)."""
    r = git("ls-files", "-z")
    if r.returncode != 0:
        raise RuntimeError("git ls-files failed: " + r.stderr.decode("utf-8", "replace").strip())
    paths = [p for p in r.stdout.decode("utf-8", "replace").split("\0") if p]
    return paths, {p.replace("\\", "/").lower() for p in paths}


def mount_points():
    """/Game plus every plugin that can hold content, mapped to its Content directory.

    A .uplugin with no explicit MountPoint mounts at /<plugin file stem>, which is
    what the editor does; reading the descriptor rather than guessing the folder
    name is what keeps this right for Plugins/GameFeatures/*.
    """
    mounts = {"/Game": "Content"}
    plugins_dir = os.path.join(ROOT, "Plugins")
    for dirpath, _dirs, files in os.walk(plugins_dir):
        for name in files:
            if not name.endswith(".uplugin"):
                continue
            path = os.path.join(dirpath, name)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    desc = json.load(fh)
            except Exception:
                continue
            if not desc.get("CanContainContent"):
                continue
            content = os.path.join(dirpath, "Content")
            if not os.path.isdir(content):
                continue
            mount = desc.get("MountPoint") or ("/" + os.path.splitext(name)[0])
            mounts[mount] = os.path.relpath(content, ROOT).replace("\\", "/")
    return mounts


def package_references(path):
    """Every package path this asset names. Hard and soft: a Blueprint's soft
    reference breaks a clone exactly as hard as a texture reference does."""
    with open(path, "rb") as fh:
        data = fh.read()
    found = set()
    for m in REF.findall(data):
        found.add(m.decode("utf-8", "replace"))
    if not found:
        # UTF-16 leaves a null between every character, so the ASCII pass finds
        # nothing. Only pay for the second pass when the first came back empty.
        for m in REF16.findall(data):
            found.add(m.decode("utf-16-le", "replace"))
    del data
    return found


def resolve(ref, mounts, exists):
    """Object path -> repo-relative file, or None when the mount is not ours.

    Asset names may contain dots -- Content/Effects/NiagaraModules/NM_BPSystemEvent
    is really named 'NM_BPSystemEvent.NM_BPSystemEvent' -- so the package is found by
    trying every dot boundary after the mount, longest name first, against what is
    actually on disk. Stripping a single trailing '.Name' reports those as missing
    references to themselves, which is noise, not a finding.
    """
    parts = ref.split("/")
    mount = "/" + parts[1]
    rest = "/".join(parts[2:])
    content = mounts.get(mount)
    if not content or not rest:
        return None
    tail = rest
    cuts = [len(rest) - len(rest[i:]) for i, ch in enumerate(rest) if ch == "."]
    # Longest name first, then shorter, then the whole path: the last candidate is
    # the reference that named no object at all, which is how a HISM component
    # stores its mesh.
    stems = [content + "/" + rest[:cut] for cut in sorted(cuts, reverse=True)]
    stems.append(content + "/" + rest)
    for stem in stems:
        for suffix in ASSET_SUFFIXES:
            candidate = stem + suffix
            if exists(candidate):
                return candidate
    return None


def prefix_artifact(ref, mounts):
    """True when the reference is a truncated prefix of a file that does exist.

    UE does not always store a package path whole: an export can carry
    '/Game/Scene_QuarrySlate/.../SM_Qua_Sla_Rock_S' where the real asset is
    'SM_Qua_Sla_Rock_S_10', alongside the whole name elsewhere in the same file.
    Those render correctly, so calling them broken references is a false positive
    that would bury the real ones. A genuine miss -- MF_Pistol_TurnLeft for a file
    named MF_Pistol_Turn_Left -- is not a prefix of anything and still reports.
    """
    parts = ref.split("/")
    content = mounts.get("/" + parts[1])
    if not content or len(parts) < 4:
        return None
    folder = os.path.join(ROOT, content.replace("/", os.sep), *parts[2:-1])
    leaf = parts[-1]
    if not os.path.isdir(folder) or len(leaf) < 4:
        return None
    for name in os.listdir(folder):
        if name.startswith(leaf) and name.lower().endswith(ASSET_SUFFIXES):
            return content + "/" + "/".join(parts[2:-1]) + "/" + os.path.splitext(name)[0]
    return None


def exists_predicate():
    def exists(repo_path):
        return os.path.exists(os.path.join(ROOT, repo_path.replace("/", os.sep)))
    return exists


def main():
    ap = argparse.ArgumentParser(description="Find committed assets that reference untracked or missing files.")
    ap.add_argument("--json", action="store_true", help="write the report to stdout as JSON")
    ap.add_argument("--report", metavar="PATH", help="also write the report to PATH")
    ap.add_argument("--allow-untracked", action="store_true",
                    help="do not fail on references to files that exist but are not committed")
    ap.add_argument("--baseline", metavar="PATH",
                    help="JSON file of already-broken package references to ignore (see "
                         "Tools/asset_reference_baseline.json). Without it every missing reference fails.")
    ap.add_argument("--quiet", action="store_true", help="only print the summary line")
    args = ap.parse_args()

    try:
        paths, tracked = tracked_files()
        mounts = mount_points()
    except Exception as exc:
        print("FAIL: %s" % exc, file=sys.stderr)
        return 2

    assets = [p for p in paths if p.lower().endswith(ASSET_SUFFIXES)]
    exists = exists_predicate()
    refs = {}          # package path -> set of referrer paths
    for path in assets:
        full = os.path.join(ROOT, path.replace("/", os.sep))
        if not os.path.exists(full):
            continue                    # LFS pointer not smudged; nothing to learn here
        try:
            for pkg in package_references(full):
                refs.setdefault(pkg, set()).add(path)
        except Exception as exc:
            print("WARN: %s: %s" % (path, exc), file=sys.stderr)

    buckets = {"ok": [], "untracked": [], "missing": [], "folder": [], "artifact": [], "external": []}
    for pkg, referrers in refs.items():
        mount = "/" + pkg.split("/")[1]
        if mount in ("/Engine", "/Script"):
            buckets["external"].append({"package": pkg, "referrers": sorted(referrers)})
            continue
        resolved = resolve(pkg, mounts, exists)
        if resolved is None:
            # A reference can name a folder, not an asset: project settings store
            # content paths as FFilePath, and Lyra's frontend points at /Game/Athena.
            # Those are not broken references and must not be counted as any.
            rest = "/".join(pkg.split("/")[2:])
            as_dir = mounts.get(mount, "") + "/" + rest if mounts.get(mount) else None
            if as_dir and os.path.isdir(os.path.join(ROOT, as_dir.replace("/", os.sep))):
                buckets["folder"].append({"package": pkg, "referrers": sorted(referrers)})
                continue
            artifact = prefix_artifact(pkg, mounts)
            if artifact:
                buckets["artifact"].append({"package": pkg, "file": artifact,
                                            "referrers": sorted(referrers)})
                continue
            # Not ours, or genuinely gone. Only report it as broken when the mount
            # is one we own -- an unknown plugin mount is somebody else's content.
            if mount in mounts:
                buckets["missing"].append({"package": pkg, "file": None, "referrers": sorted(referrers)})
            else:
                buckets["external"].append({"package": pkg, "referrers": sorted(referrers)})
            continue
        rec = {"package": pkg, "file": resolved, "referrers": sorted(referrers)}
        if resolved.lower() in tracked:
            buckets["ok"].append(rec)
        elif exists(resolved):
            rec["bytes"] = os.path.getsize(os.path.join(ROOT, resolved.replace("/", os.sep)))
            buckets["untracked"].append(rec)
        else:
            buckets["missing"].append(rec)

    def by_folder(items, depth=2):
        out = {}
        for it in items:
            if not it.get("file"):
                continue
            key = "/".join(it["file"].split("/")[:depth])
            agg = out.setdefault(key, {"count": 0, "referrers": 0, "bytes": 0})
            agg["count"] += 1
            agg["referrers"] += len(it["referrers"])
            agg["bytes"] += it.get("bytes", 0)
        return dict(sorted(out.items(), key=lambda kv: -kv[1]["count"]))

    def mb(n):
        return "%.1f MB" % (n / 1048576.0)

    baseline = set()
    if args.baseline:
        base_path = args.baseline if os.path.isabs(args.baseline) else os.path.join(ROOT, args.baseline)
        try:
            with open(base_path, "r", encoding="utf-8") as fh:
                baseline = set(json.load(fh).get("packages", []))
        except Exception as exc:
            print("FAIL: could not read baseline %s: %s" % (args.baseline, exc), file=sys.stderr)
            return 2
    baselined = [m for m in buckets["missing"] if m["package"] in baseline]
    stale = [p for p in sorted(baseline) if p not in {m["package"] for m in buckets["missing"]}]
    buckets["missing"] = [m for m in buckets["missing"] if m["package"] not in baseline]

    report = {
        "assets_scanned": len(assets),
        "references_found": len(refs),
        "counts": {k: len(v) for k, v in buckets.items()},
        "mounts": dict(sorted(mounts.items())),
        "missing": sorted(buckets["missing"], key=lambda r: r["package"]),
        "baselined_missing": sorted(baselined, key=lambda r: r["package"]),
        "stale_baseline": stale,
        "untracked": sorted(buckets["untracked"], key=lambda r: r["package"]),
        "untracked_by_folder": by_folder(buckets["untracked"]),
        "missing_by_folder": by_folder(buckets["missing"]),
    }
    failed = bool(buckets["missing"]) or (bool(buckets["untracked"]) and not args.allow_untracked)

    if args.json:
        json.dump(report, sys.stdout, indent=2)
        print()
    if args.report:
        target = args.report if os.path.isabs(args.report) else os.path.join(ROOT, args.report)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)

    if not args.json and not args.quiet:
        print("scanned %d committed assets, %d distinct package references"
              % (report["assets_scanned"], report["references_found"]))
        for label in ("missing", "untracked"):
            items = buckets[label]
            if not items:
                print("PASS: no %s references" % label)
                continue
            print("\n%s: %d referenced packages" % (label.upper(), len(items)))
            for folder, agg in report[label + "_by_folder"].items():
                print("  %-46s %4d assets  %10s  referenced by %d"
                      % (folder, agg["count"], mb(agg["bytes"]), agg["referrers"]))
            print("  (per-package detail: --json)")
        print("\nfolder references (settings paths, not broken): %d" % len(buckets["folder"]))
        print("truncated-prefix artifacts resolved against real files: %d" % len(buckets["artifact"]))
        if args.baseline:
            print("baselined (known inherited breakage, not failing): %d" % len(baselined))
            for p in stale:
                print("  STALE baseline entry, the reference is no longer broken: %s" % p)
        print("external (engine/Lyra supplied): %d" % len(buckets["external"]))

    print("FAIL" if failed else "PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())