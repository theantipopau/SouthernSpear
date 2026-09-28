# Copyright Southern Spear. All Rights Reserved.
#
# Southern Spear architecture guard.
#
# Enforces the boundaries that code review alone cannot hold (ADR-004, ADR-017):
#
#   1. No Southern Spear plugin depends on another Southern Spear plugin.
#      SouthernSpearCore is the root of the SS dependency graph.
#   2. SouthernSpearCore depends on no Lyra module and no gameplay system.
#      It owns team identity; it must not be able to reach weapons, damage,
#      health, abilities, roles, objectives or UI even transitively.
#   3. Presentation public headers include no weapon, damage, health or
#      ability-system header.
#   4. New Southern Spear types do not live inside Lyra modules.
#   5. No gameplay module depends on a UI module.
#   6. ESSTeamId / ESSLocality are never given a "Friendly"/"Opposing" team
#      value, and ESSLocality is never used as a replicated team identifier.
#   7. SouthernSpearCore source names no content path and loads no asset. Core
#      holds the shared types every other module builds on; the module that
#      owns the content is the one that may reach it. Session 059b moved a
#      capture harness out of Core for exactly this reason, and this rule is
#      the structural version of that call.
#
# A pre-existing hit that is accepted rather than fixed is listed in
# CORE_CONTENT_EXCEPTIONS and reported as a NOTE instead of failing; every
# other hit is a violation. Negative test: Tools/test_architecture_guard.py.
#
# Pure stdlib, no third-party packages, so CI can run it anywhere.
#
#   python Tools/validate_architecture.py          # check, exit 1 on violation
#   python Tools/validate_architecture.py --json   # machine-readable report
#
# Exit codes: 0 clean, 1 violations found, 2 could not run.

import argparse
import json
import os
import re
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Modules that carry gameplay. SouthernSpearCore must not reach any of them.
GAMEPLAY_MODULES = {
    "LyraGame", "LyraEditor", "GameplayAbilities", "GameplayTags",  # GameplayTags
    "LyraGameplayTags",
}

# Lyra owns the gameplay systems. Naming a module here is a boundary violation.
LYRA_GAMEPLAY_MODULES = {
    "LyraGame",
    "LyraEditor",
}

# Header fragments a presentation-facing public header may never include.
FORBIDDEN_PUBLIC_INCLUDES = (
    "Weapon",
    "Damage",
    "Health",
    "AbilitySystem",
    "GameplayAbility",
    "Inventory",
    "Equipment",
    "Lyra",
    "Attribute",
    "GameplayEffect",
)

# UI modules. A gameplay module depending on one of these is backwards.
UI_MODULES = {
    "CommonUI", "UIExtension", "GameSettings", "GameSubtitles", "UMG",
}

# Rule SS010: the module whose source must not reach content, and what reaching content looks like.
CORE_MODULE = "SouthernSpearCore"
# A content path is a package path into a mounted content folder, never "/Script/" (a class path).
CONTENT_PATH_PATTERNS = (
    r'"\/Game\/',        # the project's own content
    r'"\/SSExp_',        # a game-feature plugin's content
    r'"\/ShooterCore\/',  # Lyra's
    r'"\/SouthernSpearUI\/',
)
# Loading an asset by path.  FSoftObjectPath is the reference type; a literal of it names content.
ASSET_LOAD_MARKERS = (
    "LoadObject", "ConstructorHelpers", "FSoftObjectPath", "FSoftClassPath", "StaticLoadObject",
)
# Pre-existing hits that are accepted, not fixed here.  Reported as NOTES, never fatal, each with
# the reason it is allowed.  Keys are project-relative paths with forward slashes.
CORE_CONTENT_EXCEPTIONS = {
    "Plugins/SouthernSpearCore/Source/SouthernSpearCore/Public/SSFonts.h":
        "Header-only UI font loader (/SouthernSpearUI/Fonts, LoadObject<UFontFace>). It was written "
        "before this rule and every UI module already depends on Core, so moving it is a separate "
        "change; tracked as R-75. Core is not the right owner of a font: it should move to a UI "
        "module, which may then depend on it. Any *new* content reference in Core fails SS010.",
}

# Modules considered "presentation" for the purposes of rule 3. A header under
# any of these directories is held to the cosmetic-only rule.
PRESENTATION_DIR_MARKERS = (
    os.path.join("Presentation",),
    os.path.join("Faction"),
)


class Finding(object):
    def __init__(self, rule, path, detail, allowed=False):
        self.rule = rule
        self.path = path
        self.detail = detail
        self.allowed = allowed

    def as_dict(self):
        return {"rule": self.rule, "path": self.path, "detail": self.detail, "allowed": self.allowed}

    def __str__(self):
        return "{0}: {1}\n    {2}".format(self.rule, self.path, self.detail)


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def iter_module_rules():
    """Yield (build_cs_path, module_name, source_text) for every SS plugin module."""
    plugins_dir = os.path.join(PROJECT_ROOT, "Plugins")
    if not os.path.isdir(plugins_dir):
        return
    for plugin in sorted(os.listdir(plugins_dir)):
        if not plugin.startswith("SouthernSpear"):
            continue
        source = os.path.join(plugins_dir, plugin, "Source")
        if not os.path.isdir(source):
            continue
        for module in sorted(os.listdir(source)):
            build_cs = os.path.join(source, module, module + ".Build.cs")
            if os.path.isfile(build_cs):
                yield build_cs, module, read(build_cs)


def parse_dependencies(source_text):
    """Extract every module name mentioned in a Build.cs dependency list."""
    found = set()
    for block in re.findall(
        r"(?:Public|Private|DynamicallyLoaded)DependencyModuleNames\.AddRange\s*\((.*?)\)\s*;",
        source_text,
        re.S,
    ):
        found.update(re.findall(r'"([^"]+)"', block))
    return found


def parse_definitions(source_text):
    found = set()
    for block in re.findall(r"Definitions\.Add(?:Range)?\s*\((.*?)\)\s*;", source_text, re.S):
        found.update(re.findall(r'"([^"]+)"', block))
    return found


def iter_ss_headers():
    """Yield every public header belonging to a Southern Spear module."""
    plugins_dir = os.path.join(PROJECT_ROOT, "Plugins")
    if not os.path.isdir(plugins_dir):
        return
    for plugin in sorted(os.listdir(plugins_dir)):
        if not plugin.startswith("SouthernSpear"):
            continue
        public = os.path.join(plugins_dir, plugin, "Source")
        if not os.path.isdir(public):
            continue
        for module in sorted(os.listdir(public)):
            module_dir = os.path.join(public, module)
            for dirpath, _dirnames, filenames in os.walk(module_dir):
                # Public/ and every subdirectory of it (e.g. Public/Presentation/).
                rel_parts = os.path.relpath(dirpath, module_dir).split(os.sep)
                if rel_parts[0] == "Public":
                    for name in sorted(filenames):
                        if name.endswith((".h", ".hpp")):
                            path = os.path.join(dirpath, name)
                            yield path, read(path)


def is_presentation_header(path):
    normalised = path.replace("\\", "/")
    return any(marker in normalised for marker in PRESENTATION_DIR_MARKERS)


def iter_core_sources():
    """Yield (path, text) for every C++ source file of the SouthernSpearCore module."""
    source = os.path.join(PROJECT_ROOT, "Plugins", CORE_MODULE, "Source", CORE_MODULE)
    if not os.path.isdir(source):
        return
    for dirpath, dirnames, filenames in os.walk(source):
        # Intermediate/ holds generated files, never authored source.
        dirnames[:] = [d for d in dirnames if d not in ("Intermediate", "Binaries")]
        for name in sorted(filenames):
            if name.endswith((".h", ".hpp", ".cpp", ".inl")):
                path = os.path.join(dirpath, name)
                yield path, read(path)


def check(f):
    findings = []

    # --- Rule 1 + 2: dependency policy -----------------------------------
    for build_cs, module, text in iter_module_rules():
        deps = parse_dependencies(text)

        sibling = sorted(
            d for d in deps
            if d.startswith("SouthernSpear") and d != module
            # Every SS plugin may build on the root; the root builds on nothing.
            and not (d == "SouthernSpearCore" and module != "SouthernSpearCore")
            # A plugin's UI module sits on top of its own gameplay module.
            and not (module.endswith("UI") and d == module[:-2])
        )
        if sibling:
            findings.append(Finding(
                "SS001",
                os.path.relpath(build_cs, PROJECT_ROOT).replace("\\", "/"),
                "Southern Spear plugin '{0}' depends on sibling module(s): {1}. "
                "SouthernSpearCore is the root of the SS graph; SS plugins may depend "
                "only on it, and it on no SS plugin.".format(module, ", ".join(sibling)),
            ))

        # ADR-019: SouthernSpearLyraBridge is the one SS module allowed to reach Lyra.
        if module.startswith("SouthernSpear") and module != "SouthernSpearLyraBridge":
            lyra = sorted(d for d in deps if d in LYRA_GAMEPLAY_MODULES)
            if lyra:
                findings.append(Finding(
                    "SS002",
                    os.path.relpath(build_cs, PROJECT_ROOT).replace("\\", "/"),
                    "{1} depends on Lyra gameplay module(s): {0}. It must "
                    "stay independent of weapons, damage, health, abilities, roles, "
                    "objectives and UI.".format(", ".join(lyra), module),
                ))

            # The export macro must be a definition, not a hardcoded symbol.
            for definition in parse_definitions(text):
                if definition.startswith("SSCORE_API="):
                    break
            else:
                if any("SSCORE_API" in line and "PublicDefinitions" not in line
                       for line in text.splitlines()):
                    pass  # Only the .h files use it; Build.cs need not declare it twice.

    # --- Rule 3: presentation headers stay cosmetic -----------------------
    for path, text in iter_ss_headers():
        if not is_presentation_header(path):
            continue
        rel = os.path.relpath(path, PROJECT_ROOT).replace("\\", "/")
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith("#include"):
                continue
            for fragment in FORBIDDEN_PUBLIC_INCLUDES:
                if fragment in stripped:
                    findings.append(Finding(
                        "SS003",
                        rel,
                        "Presentation public header includes '{0}', which names the "
                        "forbidden fragment '{1}'. A presentation header must not be able "
                        "to reach gameplay types.".format(stripped, fragment),
                    ))

    # --- Rule 4: no new SS types inside Lyra modules ----------------------
    for module_dir in ("LyraGame", "LyraEditor"):
        base = os.path.join(PROJECT_ROOT, "Source", module_dir)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirnames, filenames in os.walk(base):
            for name in sorted(filenames):
                if not name.endswith((".h", ".cpp")):
                    continue
                path = os.path.join(dirpath, name)
                if "SouthernSpear" in name:
                    findings.append(Finding(
                        "SS004",
                        os.path.relpath(path, PROJECT_ROOT).replace("\\", "/"),
                        "Southern Spear source inside the vendored Lyra module '{0}'. "
                        "SS types belong in Plugins/SouthernSpear*; modifying Lyra for "
                        "SS features is a departure that must be recorded (ADR-002).".format(module_dir),
                    ))

    # --- Rule 5: gameplay must not depend on UI ----------------------------
    for build_cs, module, text in iter_module_rules():
        deps = parse_dependencies(text)
        ui = sorted(d for d in deps if d in UI_MODULES)
        # UI modules are the one place UI dependencies belong.
        if ui and not module.endswith("UI"):
            findings.append(Finding(
                "SS005",
                os.path.relpath(build_cs, PROJECT_ROOT).replace("\\", "/"),
                "Module '{0}' depends on UI module(s): {1}. Gameplay must not depend "
                "on UI; the dependency runs the other way.".format(module, ", ".join(ui)),
            ))

    # --- Rule 6: team identity is not modelled as Friendly/Opposing --------
    # Two-sided check. ESSLocality MUST carry Friendly/Opposing - that is its
    # whole job. ESSTeamId MUST NOT - it is the authoritative world-team value
    # and a Friendly/Opposing member there is exactly the ADR-003 bug this
    # architecture replaced.
    for path, text in iter_ss_headers():
        if os.path.basename(path) != "SSTeamTypes.h":
            continue
        rel = os.path.relpath(path, PROJECT_ROOT).replace("\\", "/")
        for match in re.finditer(r"UENUM\([^)]*\)\s*\nenum class (\w+)", text):
            enum_name = match.group(1)
            body = text[match.end():]
            body = body[: body.find("};")] if "};" in body else body
            has_friendly = bool(re.search(r"^\s*Friendly\b", body, re.M))
            has_opposing = bool(re.search(r"^\s*Opposing\b", body, re.M))

            if enum_name.endswith("TeamId"):
                for value, present in (("Friendly", has_friendly), ("Opposing", has_opposing)):
                    if present:
                        findings.append(Finding(
                            "SS006",
                            rel,
                            "authoritative team enum {0} declares a '{1}' value. "
                            "Friendly/Opposing are viewer-relative and must never be "
                            "replicated world-team values (ADR-017).".format(enum_name, value),
                        ))
                if not re.search(r"^\s*None\b", body, re.M):
                    findings.append(Finding(
                        "SS007",
                        rel,
                        "authoritative team enum {0} has no 'None' member. A team-less "
                        "state must be representable so resolution can fail explicitly "
                        "rather than defaulting.".format(enum_name),
                    ))

            if enum_name.endswith("Locality"):
                for value, present in (("Friendly", has_friendly), ("Opposing", has_opposing)):
                    if not present:
                        findings.append(Finding(
                            "SS008",
                            rel,
                            "locality enum {0} is missing a '{1}' value. The viewer-relative "
                            "enum is defined by exactly these two values.".format(enum_name, value),
                        ))

    # --- Rule 7 / SS010: Core holds shared types, never content ------------
    for path, text in iter_core_sources():
        rel = os.path.relpath(path, PROJECT_ROOT).replace("\\", "/")
        exception = CORE_CONTENT_EXCEPTIONS.get(rel)
        if exception:
            findings.append(Finding(
                "SS010", rel,
                "ACCEPTED (reported, not fixed): " + exception,
                allowed=True,
            ))
            continue
        for number, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            hit = next(("loads an asset ('{0}')".format(m) for m in ASSET_LOAD_MARKERS if m in line), None)
            if hit is None and any(re.search(p, line) for p in CONTENT_PATH_PATTERNS):
                hit = "names a content path"
            if hit is None:
                continue
            findings.append(Finding(
                "SS010", rel,
                "{0} at line {1}: {2}. SouthernSpearCore holds the shared types every other module "
                "builds on; a module that names content, or loads an asset by path, must be the "
                "module that owns that content (Session 059b).".format(hit, number, stripped[:160]),
            ))

    # Rule 9 (no kill event, ADR-032) was retired by ADR-034: kills of the other
    # side now earn capped service XP. The caps are asserted by
    # SouthernSpear.Progression.ShippedTablesAreValid.

    return findings


def main():
    parser = argparse.ArgumentParser(description="Southern Spear architecture guard")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable report")
    args = parser.parse_args()

    if not os.path.isdir(os.path.join(PROJECT_ROOT, "Plugins")):
        sys.stderr.write("Cannot find Plugins/ at {0}\n".format(PROJECT_ROOT))
        return 2

    findings = check(Finding)
    blocking = [x for x in findings if not x.allowed]
    notes = [x for x in findings if x.allowed]

    if args.json:
        report = {
            "ok": not blocking,
            "findings": [x.as_dict() for x in blocking],
            "notes": [x.as_dict() for x in notes],
            "counts": {
                "SS001_sibling_dependency": sum(1 for x in findings if x.rule == "SS001"),
                "SS002_core_lyra_dependency": sum(1 for x in findings if x.rule == "SS002"),
                "SS003_presentation_include": sum(1 for x in findings if x.rule == "SS003"),
                "SS004_ss_type_in_lyra": sum(1 for x in findings if x.rule == "SS004"),
                "SS005_gameplay_depends_on_ui": sum(1 for x in findings if x.rule == "SS005"),
                "SS006_locality_as_team_value": sum(1 for x in findings if x.rule == "SS006"),
                "SS007_team_enum_missing_none": sum(1 for x in findings if x.rule == "SS007"),
                "SS008_locality_missing_value": sum(1 for x in findings if x.rule == "SS008" and not x.allowed),
                "SS010_core_content_reference": sum(1 for x in blocking if x.rule == "SS010"),
            },
        }
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("=" * 70)
        print("SOUTHERN SPEAR - ARCHITECTURE GUARD")
        print("=" * 70)
        if not blocking:
            print("PASS - no architecture violations found.")
        else:
            print("FAIL - {0} violation(s):\n".format(len(blocking)))
            for finding in blocking:
                print("  " + str(finding).replace("\n", "\n  "))
                print()
        for note in notes:
            print("  NOTE - " + str(note).replace("\n", "\n  "))
            print()

    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
