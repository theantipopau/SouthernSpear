# Copyright Southern Spear. All Rights Reserved.
#
# Southern Spear pack verifier.
#
# ADR-021 says vendor packs are referenced in place and never committed, and
# .gitignore enforces it for every pack in Content/. That is a sound rule and it
# has a cost: the repository alone cannot open any map. Dry River references 207
# Namaqualand packages, Bluestone 118 QuarrySlate ones, Wandarra 47 MOUT ones.
#
# A rule you cannot check is a rule you eventually forget, so this checks three
# things and fails loudly on the first two:
#
#   1. each pack in Docs/PACK_MANIFEST.json is present, with the file count and
#      byte size recorded when the manifest was written. A pack that is missing,
#      half-copied or half-deleted is reported as MISSING or ALTERED.
#   2. --deep additionally hashes every file, which catches a pack that has been
#      edited -- the one thing ADR-021 exists to prevent.
#   3. every pack that committed assets actually reference has a row in
#      Docs/ASSET_REGISTER.md, and that row does not say NOT_USED while the pack
#      is in use. Both of those were true before this existed: Singapore_Canal and
#      World_Flags are registered NOT_USED and referenced by hundreds of committed
#      assets, and StoneWell, Namaqualand and Modern_Insurgent_7 have no row at all.
#
# Pure stdlib, no editor, so CI can run it anywhere.
#
#   python Tools/verify_packs.py                        # verify, exit 1 on a problem
#   python Tools/verify_packs.py --json                 # machine-readable to stdout
#   python Tools/verify_packs.py --report Build/x.json  # also write a report
#   python Tools/verify_packs.py --deep                 # hash every file as well
#   python Tools/verify_packs.py --write-manifest       # re-measure the manifest
#
# Exit codes: 0 clean, 1 pack problem, 2 could not run.

import argparse
import hashlib
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "Docs", "PACK_MANIFEST.json")
REGISTER = os.path.join(ROOT, "Docs", "ASSET_REGISTER.md")
ASSET_SUFFIXES = (".uasset", ".umap")


def load_reference_module():
    """check_asset_references lives next door and is imported rather than copied."""
    path = os.path.join(ROOT, "Tools", "check_asset_references.py")
    spec = importlib.util.spec_from_file_location("check_asset_references", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def measure(folder):
    files = 0
    total = 0
    for dirpath, _dirs, names in os.walk(folder):
        for name in names:
            files += 1
            try:
                total += os.path.getsize(os.path.join(dirpath, name))
            except OSError:
                pass
    return files, total


def tree_digest(folder, suffixes=ASSET_SUFFIXES):
    """Hash of every asset path + content in the folder. Order-independent."""
    h = hashlib.sha256()
    entries = []
    for dirpath, _dirs, names in os.walk(folder):
        for name in names:
            if suffixes and not name.lower().endswith(suffixes):
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            entries.append(rel)
    for rel in sorted(entries):
        h.update(rel.encode("utf-8"))
        with open(os.path.join(ROOT, rel.replace("/", os.sep)), "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
    return h.hexdigest()


def register_rows():
    """Index every table row in both registers, by content path and by pack name.

    Later rows win. The registers correct their own earlier rows in place --
    ASSET_REGISTER 4.9j literally says a row was 'corrected 2026-09-29 to NOT_USED,
    corrected again 2026-09-30 on first map use' -- so a pack's status is its most
    recent mention, not the union of every mention ever written about it.
    """
    index = {}
    for label, path in (("asset", REGISTER), ("licence", os.path.join(ROOT, "Docs", "LICENCE_REGISTER.md"))):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                lines = fh.read().splitlines()
        except Exception:
            continue
        for n, line in enumerate(lines, 1):
            if not line.startswith("|"):
                continue
            for token in line.split("`"):
                norm = normalise_path(token)
                if norm:
                    index.setdefault(norm, []).append((n, line, label))
                    continue
                name = token.strip().strip("/")
                # A pack named in prose ('`RuralAustralia` trees, logs, fence') is
                # still a mention; it is just weaker evidence than a path row.
                if name and name.replace("_", "").replace("-", "").isalnum() and "/" not in name:
                    index.setdefault("name:" + name, []).append((n, line, label))
    return index


def normalise_path(token):
    """/Game/Foo/Bar, Content/Foo/Bar and Content/Foo/Bar/ all name one folder."""
    token = token.strip().strip("/").rstrip("/")
    if token.startswith("Game/"):
        token = "Content/" + token[len("Game/"):]
    if not token.startswith("Content/"):
        return None
    return token


def claims_not_used(row):
    """True when NOT_USED is this row's status, not a word inside a sentence.

    ASSET_REGISTER 4.9j reads 'Row corrected 2026-09-29 to `NOT_USED`, corrected
    again 2026-09-30 on first map use' on the same row that now says IN_USE. A
    substring search calls that pack unused; reading the status cell does not.
    """
    for cell in row.split("|"):
        if cell.strip().strip("`").strip().startswith("NOT_USED"):
            return True
    return False


def claims_unregistered(row):
    """A row that says UNREGISTERED is a placeholder, not a clearance.

    Stone Well's row reads 'UNREGISTERED - PROVENANCE UNKNOWN'. Accepting that as
    registered would turn the gate green the moment somebody typed the words, so
    the row has to record an actual licence before it stops failing.
    """
    for cell in row.split("|"):
        if cell.strip().strip("`").strip().startswith("UNREGISTERED"):
            return True
    return False


def register_state(path, rows):
    """(registered, not_used_rows, all_rows) for a pack folder.

    Deliberately conservative. A NOT_USED claim in ASSET_REGISTER that contradicts
    live references is exactly the defect this exists to surface, so ANY such row
    counts -- not just the most recent one. LICENCE_REGISTER rows count for
    registration but never cancel a status claim: that register owns licence
    classes, ASSET_REGISTER owns the status vocabulary, and letting one silently
    override the other is how a pack ends up 'registered' and 'not used' at once.
    Every row found is returned so the report can quote the contradiction.
    """
    name = path.replace("\\", "/").split("/")[-1]
    path_hits = rows.get(normalise_path(path)) or []
    name_hits = rows.get("name:" + name) or []
    if path_hits:
        basis = "ASSET_REGISTER path row" if path_hits[0][2] == "asset" else "LICENCE_REGISTER path row"
    elif name_hits:
        basis = "register name mention"
    else:
        return False, [], []
    all_rows = path_hits + name_hits
    not_used = [(n, lbl) for n, text, lbl in path_hits + name_hits
                if claims_not_used(text) and lbl == "asset"]
    unregistered = [(n, lbl) for n, text, lbl in path_hits + name_hits
                    if claims_unregistered(text)]
    return True, not_used + unregistered, [(n, lbl, basis) for n, _t, lbl in all_rows]


def scan_references():
    """Which pack folders do committed assets reference, and how much of each."""
    mod = load_reference_module()
    paths, tracked = mod.tracked_files()
    mounts = mod.mount_points()
    exists = mod.exists_predicate()
    refs = {}
    for rel in paths:
        if not rel.lower().endswith(ASSET_SUFFIXES):
            continue
        full = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.exists(full):
            continue
        for ref in mod.package_references(full):
            file = mod.resolve(ref, mounts, exists)
            if file is None or file.lower() in tracked:
                continue
            top = "/".join(file.split("/")[:2])
            rec = refs.setdefault(top, {"packages": set(), "referrers": set()})
            rec["packages"].add(file)
            rec["referrers"].add(rel)
    return refs


def write_manifest(refs, rows):
    old = {}
    if os.path.exists(MANIFEST):
        try:
            with open(MANIFEST, "r", encoding="utf-8") as fh:
                for entry in json.load(fh).get("packs", []):
                    old[entry["path"]] = entry
        except Exception:
            old = {}
    packs = []
    for path in sorted(refs):
        folder = os.path.join(ROOT, path.replace("/", os.sep))
        files, total = measure(folder)
        prior = old.get(path, {})
        registered, not_used_rows, all_rows = register_state(path, rows)
        packs.append({
            # hand-written provenance survives a regeneration
            "path": path,
            "licence": prior.get("licence"),
            "register_row": prior.get("register_row"),
            "restore": prior.get("restore"),
            "note": prior.get("note"),
            "registered_in_asset_register": registered,
            "register_rows": all_rows,
            "register_says_not_used": bool(not_used_rows),
            "register_not_used_lines": [n for n, _lbl in not_used_rows],
            "files": files,
            "bytes": total,
            "referenced_packages": len(refs[path]["packages"]),
            "referenced_by": sorted(refs[path]["referrers"])[:8],
            "referenced_by_count": len(refs[path]["referrers"]),
        })
    doc = {
        "_comment": "Generated by Tools/verify_packs.py --write-manifest. The licence, register_row, "
                    "restore and note fields are hand-maintained and survive regeneration; the rest is "
                    "measured. ADR-021 keeps these folders out of git, so this file is the only record "
                    "in the repository of what the maps need.",
        "generated_by": "Tools/verify_packs.py",
        "packs": packs,
    }
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    return packs


def verify(packs, refs, rows, deep):
    results = []
    for entry in packs:
        path = entry["path"]
        folder = os.path.join(ROOT, path.replace("/", os.sep))
        # Recomputed here, never read from the manifest: the manifest records what the
        # registers said when it was generated, and the whole point of the check is
        # that it notices when they change.
        registered, not_used_rows, all_rows = register_state(path, rows)
        rec = {"path": path, "state": "OK", "files": 0, "bytes": 0,
               "expected_files": entry.get("files"), "expected_bytes": entry.get("bytes"),
               "referenced_by_count": entry.get("referenced_by_count", 0),
               "licence": entry.get("licence"), "register_row": entry.get("register_row"),
               "registered_in_asset_register": registered,
               "register_rows": all_rows,
               "register_says_not_used": bool(not_used_rows),
               "register_not_used_lines": [n for n, _lbl in not_used_rows]}
        if not os.path.isdir(folder):
            rec["state"] = "MISSING"
            results.append(rec)
            continue
        files, total = measure(folder)
        rec["files"], rec["bytes"] = files, total
        if entry.get("files") is not None and files != entry["files"]:
            rec["state"] = "ALTERED"
            rec["detail"] = "file count %d, manifest says %s" % (files, entry["files"])
        elif entry.get("bytes") is not None and abs(total - entry["bytes"]) > 1024:
            rec["state"] = "ALTERED"
            rec["detail"] = "size %d, manifest says %d" % (total, entry["bytes"])
        if deep and rec["state"] == "OK":
            digest = tree_digest(folder)
            rec["tree_sha256"] = digest
            if entry.get("tree_sha256") and entry["tree_sha256"] != digest:
                rec["state"] = "ALTERED"
                rec["detail"] = "content hash differs -- vendor packs are referenced in place and never modified (ADR-021)"
        if rec["state"] == "OK" and not rec.get("registered_in_asset_register"):
            rec["state"] = "UNREGISTERED"
            rec["detail"] = ("referenced by %d committed assets but no register row names it, "
                             "by path or by name" % rec["referenced_by_count"])
        if rec["state"] == "OK" and rec.get("register_says_not_used"):
            rec["state"] = "REGISTER_MISMATCH"
            rec["detail"] = ("ASSET_REGISTER marks it NOT_USED or UNREGISTERED (line%s %s) while %d "
                             "committed assets reference it"
                             % ("s" if len(rec["register_not_used_lines"]) > 1 else "",
                                ", ".join(str(n) for n in rec["register_not_used_lines"]),
                                rec["referenced_by_count"]))
        results.append(rec)
    # a pack that the current scan finds but the manifest has never heard of
    for path, rec in refs.items():
        if path not in {p["path"] for p in packs}:
            results.append({"path": path, "state": "NOT_IN_MANIFEST",
                            "referenced_by_count": len(rec["referrers"]),
                            "referenced_packages": len(rec["packages"]),
                            "detail": "referenced but absent from PACK_MANIFEST.json -- run --write-manifest"})
    return results


def main():
    ap = argparse.ArgumentParser(description="Verify the vendor packs the maps depend on.")
    ap.add_argument("--json", action="store_true", help="write the report to stdout as JSON")
    ap.add_argument("--report", metavar="PATH", help="also write the report to PATH")
    ap.add_argument("--deep", action="store_true", help="hash every asset file as well as counting it")
    ap.add_argument("--write-manifest", action="store_true",
                    help="re-measure Docs/PACK_MANIFEST.json from what committed assets reference")
    ap.add_argument("--quiet", action="store_true", help="only print the summary line")
    args = ap.parse_args()

    try:
        refs = scan_references()
        rows = register_rows()
    except Exception as exc:
        print("FAIL: %s" % exc, file=sys.stderr)
        return 2

    if args.write_manifest:
        packs = write_manifest(refs, rows)
        if not args.json:
            print("wrote %s: %d packs, %d referenced packages"
                  % (os.path.relpath(MANIFEST, ROOT), len(packs),
                     sum(p["referenced_packages"] for p in packs)))
        else:
            json.dump({"packs": packs}, sys.stdout, indent=2)
        return 0

    if not os.path.exists(MANIFEST):
        print("FAIL: %s does not exist -- run with --write-manifest first"
              % os.path.relpath(MANIFEST, ROOT), file=sys.stderr)
        return 2
    try:
        with open(MANIFEST, "r", encoding="utf-8") as fh:
            packs = json.load(fh).get("packs", [])
    except Exception as exc:
        print("FAIL: could not read the manifest: %s" % exc, file=sys.stderr)
        return 2

    results = verify(packs, refs, rows, args.deep)
    problems = [r for r in results if r["state"] != "OK"]
    report = {
        "ok": not problems,
        "deep": bool(args.deep),
        "packs_checked": len(packs),
        "counts": {},
        "results": results,
    }
    for r in results:
        report["counts"][r["state"]] = report["counts"].get(r["state"], 0) + 1

    if args.json:
        json.dump(report, sys.stdout, indent=2)
        print()
    if args.report:
        target = args.report if os.path.isabs(args.report) else os.path.join(ROOT, args.report)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)

    if not args.json and not args.quiet:
        print("%d pack(s) in the manifest, %d referenced package(s) found in the committed assets"
              % (len(packs), sum(len(r["packages"]) for r in refs.values())))
        for r in results:
            mark = "    " if r["state"] == "OK" else "!!  "
            print("%s%-44s %-20s %7.1f MB  %4d files  referenced by %s"
                  % (mark, r["path"], r["state"], r["bytes"] / 1048576.0, r["files"],
                     r.get("referenced_by_count", "-")))
            if r.get("detail"):
                print("        %s" % r["detail"])
        print("\nOK: %d, problems: %d" % (report["counts"].get("OK", 0), len(problems)))

    print("PASS" if report["ok"] else "FAIL")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())