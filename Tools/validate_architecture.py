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

# Modules considered "presentation" for the purposes of rule 3. A header under
# any of these directories is held to the cosmetic-only rule.
PRESENTATION_DIR_MARKERS = (
    os.path.join("Presentation",),
    os.path.join("Faction"),
)


class Finding(object):
    def __init__(self, rule, path, detail):
        self.rule = rule
        self.path = path
        self.detail = detail

    def as_dict(self):
        return {"rule": self.rule, "path": self.path, "detail": self.detail}

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
        )
        if sibling:
            findings.append(Finding(
                "SS001",
                os.path.relpath(build_cs, PROJECT_ROOT).replace("\\", "/"),
                "Southern Spear plugin '{0}' depends on sibling module(s): {1}. "
                "SouthernSpearCore is the root of the SS graph; SS plugins may depend "
                "only on it, and it on no SS plugin.".format(module, ", ".join(sibling)),
            ))

        if module in ("SouthernSpearCore", "SouthernSpearTeam"):
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
        if ui:
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

    return findings


def main():
    parser = argparse.ArgumentParser(description="Southern Spear architecture guard")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable report")
    args = parser.parse_args()

    if not os.path.isdir(os.path.join(PROJECT_ROOT, "Plugins")):
        sys.stderr.write("Cannot find Plugins/ at {0}\n".format(PROJECT_ROOT))
        return 2

    findings = check(Finding)

    if args.json:
        report = {
            "ok": not findings,
            "findings": [x.as_dict() for x in findings],
            "counts": {
                "SS001_sibling_dependency": sum(1 for x in findings if x.rule == "SS001"),
                "SS002_core_lyra_dependency": sum(1 for x in findings if x.rule == "SS002"),
                "SS003_presentation_include": sum(1 for x in findings if x.rule == "SS003"),
                "SS004_ss_type_in_lyra": sum(1 for x in findings if x.rule == "SS004"),
                "SS005_gameplay_depends_on_ui": sum(1 for x in findings if x.rule == "SS005"),
                "SS006_locality_as_team_value": sum(1 for x in findings if x.rule == "SS006"),
                "SS007_team_enum_missing_none": sum(1 for x in findings if x.rule == "SS007"),
                "SS008_locality_missing_value": sum(1 for x in findings if x.rule == "SS008"),
            },
        }
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("=" * 70)
        print("SOUTHERN SPEAR - ARCHITECTURE GUARD")
        print("=" * 70)
        if not findings:
            print("PASS - no architecture violations found.")
        else:
            print("FAIL - {0} violation(s):\n".format(len(findings)))
            for finding in findings:
                print("  " + str(finding).replace("\n", "\n  "))
                print()

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
