#!/usr/bin/env python3
"""
Unity-build name clash checker for the Southern Spear plugins.

Unreal merges a module's .cpp files into one translation unit (a "unity" or "jumbo" build), so two
files that each define the same name with internal linkage - inside an anonymous namespace, or as a
file-scope `static` - are fine when compiled separately and a redefinition error when compiled
together.  This project has been caught by that three times (the last one, `IsValidStep` in
`SSObjectiveRules.cpp` and `SSSectionAssaultRules.cpp`, is recorded in the Session 048 changelog).

It also flags the cheap half of the same class of problem: a local variable that hides a name which is
actually visible where it is declared - a file-scope name declared in the same file (the Session 048
`Settings` case, MSVC C4459) or a member of the class the local is defined in (MSVC C4458). Both are
errors under Unreal's shadow-variable policy. A member of some *other* class is not a shadow: the local
cannot hide it, and a qualified call names it anyway.

    python Tools/check_unity_names.py            # exit 1 on a clash
    python Tools/check_unity_names.py --json     # machine-readable report

Pure stdlib, no editor, no build.  Negative test: Tools/test_check_unity_names.py.
"""

import argparse
import json
import os
import re
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_PREFIX = "SouthernSpear"

IDENT = re.compile(r"[A-Za-z_]\w*")
# A line that starts with one of these is a statement or a type, never a declaration whose name
# matters for the shadow check.
STATEMENT_KEYWORDS = {
    "if", "else", "for", "while", "switch", "case", "default", "break", "continue", "goto", "do",
    "return", "throw", "try", "catch", "delete", "new", "using", "typedef", "template", "friend",
    "public", "private", "protected", "namespace", "static_assert", "sizeof", "decltype", "co_await",
    "co_return", "co_yield", "UE_LOG", "check", "checkf", "ensure", "ensureMsgf", "verify",
    "TRACE_CPUPROFILER_EVENT_SCOPE", "SCOPE_CYCLE_COUNTER", "CSV_SCOPED_TIMING_STAT",
}
# Member function definitions: `Type Class::Method(` - group 1 is the class, group 2 the method.
MEMBER_FUNCTION = re.compile(r"\b([A-Za-z_]\w*)(?:\s*<[^;{}()]*>)?\s*::\s*([A-Za-z_]\w*)\s*\(")
ANONYMOUS_NAMESPACE = re.compile(r"^namespace\s*(\{)?\s*$")


def strip_code(text):
    """Remove comments and literals, keeping newlines, so line structure survives."""
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                if text[i] == "\n":
                    out.append("\n")
                i += 1
            i += 2
        elif c in "\"'":
            quote = c
            i += 1
            while i < n and text[i] != quote:
                if text[i] == "\\":
                    i += 1
                i += 1
            i += 1
            out.append('""' if quote == '"' else "''")
        else:
            out.append(c)
            i += 1
    return "".join(out)


def lines_with_depth(text):
    """[(brace depth at the start of the line, line)] - correct for this codebase's Allman style."""
    rows = []
    depth = 0
    for line in text.splitlines():
        rows.append((depth, line))
        depth += line.count("{") - line.count("}")
    return rows


def continuation_flags(rows):
    """Per line: True when the line continues a declaration opened on an earlier line.

    A signature or a call split across lines, e.g. `static TAutoConsoleVariable<int32> CVar("\n\tTEXT(...)`,
    puts its continuation lines at the same brace depth as the declaration.  Without this they read as
    declarations of their own - which turns "TEXT" and "MaxSaneCap" into names.
    """
    flags = []
    balance = 0
    open_line = False
    for _depth, line in rows:
        flags.append(open_line)
        balance += line.count("(") + line.count("[") - line.count(")") - line.count("]")
        if balance < 0:
            balance = 0
        open_line = balance > 0 or line.rstrip().endswith(("=", ",", "+", "-", "*", "/", "|", "&"))
    return flags


def anonymous_blocks(rows):
    """[(body depth, first line index, past-the-end index)] for every `namespace { ... }` block."""
    blocks = []
    i = 0
    while i < len(rows):
        depth, line = rows[i]
        if ANONYMOUS_NAMESPACE.match(line.strip()):
            if "{" in line:
                first = i + 1
            elif i + 1 < len(rows) and rows[i + 1][1].strip() == "{":
                first = i + 2
            else:
                i += 1
                continue
            body_depth = depth + 1
            end = first
            while end < len(rows) and rows[end][0] >= body_depth:
                end += 1
            blocks.append((body_depth, first, end))
            i = end
        else:
            i += 1
    return blocks


def enclosing_classes(rows):
    """Per line, the class whose member function defines it, or None.

    A local hides a member only when the member belongs to the class it is defined in (C4458).  A local
    in another class's method, or in a free function, hides nothing: `FSSCasingMotion::Step` is not
    visible to `USSShellEjectSubsystem::Tick`, which names it qualified.
    """
    out = [None] * len(rows)
    stack = []
    pending = None
    for index, (depth, line) in enumerate(rows):
        found = MEMBER_FUNCTION.search(line)
        if depth == 0 and found and not line.rstrip().endswith(";"):
            pending = found.group(1)
        out[index] = stack[-1] if stack else None
        for char in line:
            if char == "{":
                if pending is not None and not stack:
                    stack.append(pending)
                    pending = None
                else:
                    stack.append(out[index])
            elif char == "}":
                if stack:
                    stack.pop()
                if not stack:
                    pending = None
    return out


def declared_name(line, allow_function=True):
    """The identifier a declaration declares, or None.  Cheap by design: one line, one name.

    `allow_function` accepts `Type Name(...)` as a function declaration, which is what an anonymous
    namespace holds.  The shadow check turns it off, so `Super::BeginPlay()` and `AddRow(...)` - calls
    -    are not mistaken for the locals that would shadow those names.

    A declaration needs a type and a name, so a lone identifier before the delimiter is a USE of
    something, not a declaration of it: `Shared = 1;`, `Shared += 1;` and `Shared[0] = 1;` all
    assign to a file-scope variable, which hides nothing - there is no C4459 for that, the name is
    the one it already had.  Reading them as declarations made the real `GBodyFrameInWeapon` in
    SSHandIKProbeSubsystem.cpp look like it was shadowed by its own assignment.
    """
    stripped = line.strip()
    if not stripped or stripped[0] in "}#;":
        return None
    match = re.search(r"([\(\[]|=|;)", stripped)
    if not match:
        return None
    delimiter = match.group(1)
    if delimiter == "(" and not allow_function:
        return None
    names = IDENT.findall(stripped[:match.start()].split("::")[-1])
    if not names:
        return None
    if len(names) < 2 and delimiter != "(":
        return None
    name = names[-1]
    first = IDENT.match(stripped)
    if name in STATEMENT_KEYWORDS or (first and first.group(0) in STATEMENT_KEYWORDS):
        return None
    return name


def scan_file(text):
    """(internal-linkage names, member functions defined here, [(line, local name)]).

    Names with internal linkage are what a unity build merges: anonymous-namespace declarations and
    file-scope `static`s.  Member functions count only when *defined* here (`Type Class::Method(` at
    file scope), not when called, so the shadow check is not polluted by every `FMath::Clamp(...)`.
    Locals are declarations inside a function body, with the anonymous namespaces excluded - their
    declarations are at depth 1 too, but they are the very names the first half collects.
    """
    code = strip_code(text)
    rows = lines_with_depth(code)
    continued = continuation_flags(rows)

    names = []
    namespace_lines = set()
    for body_depth, first, end in anonymous_blocks(rows):
        for index in range(first, end):
            namespace_lines.add(index)
            if rows[index][0] == body_depth and not continued[index]:
                name = declared_name(rows[index][1])
                if name:
                    names.append(name)

    members = {}
    for index, (depth, line) in enumerate(rows):
        if depth != 0 or continued[index]:
            continue
        if re.match(r"^\s*static\s+", line):
            name = declared_name(re.sub(r"^\s*static\s+", "", line))
            if name:
                names.append(name)
        found = MEMBER_FUNCTION.search(line)
        if found:
            members.setdefault(found.group(1), set()).add(found.group(2))

    enclosing = enclosing_classes(rows)
    locals_found = []
    for index, (depth, line) in enumerate(rows):
        if depth < 1 or index in namespace_lines or continued[index]:
            continue
        first = IDENT.match(line.strip())
        if not first or first.group(0) in STATEMENT_KEYWORDS:
            continue
        name = declared_name(line, allow_function=False)
        if name:
            locals_found.append((index + 1, name, enclosing[index]))
    return names, members, locals_found


def module_sources(root):
    """[(plugin, module, [cpp paths])] for every module under Plugins/SouthernSpear*."""
    plugins_dir = os.path.join(root, "Plugins")
    if not os.path.isdir(plugins_dir):
        return []
    out = []
    for plugin in sorted(os.listdir(plugins_dir)):
        if not plugin.startswith(PLUGIN_PREFIX):
            continue
        source = os.path.join(plugins_dir, plugin, "Source")
        if not os.path.isdir(source):
            continue
        for module in sorted(os.listdir(source)):
            module_dir = os.path.join(source, module)
            if not os.path.isdir(module_dir):
                continue
            files = []
            for dirpath, dirnames, filenames in os.walk(module_dir):
                dirnames[:] = [d for d in dirnames if d not in ("Intermediate", "Binaries")]
                for name in sorted(filenames):
                    if name.endswith(".cpp"):
                        files.append(os.path.join(dirpath, name))
            if files:
                out.append((plugin, module, files))
    return out


def check_tree(root):
    """Every violation in root: {'kind', 'module', 'name', 'files'/'file'/'line', 'detail'}."""
    findings = []
    for plugin, module, files in module_sources(root):
        owners = {}
        for path in files:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
            names, members, locals_found = scan_file(text)
            for name in set(names):
                owners.setdefault(name, set()).add(path)
            known = set(names)
            relative = os.path.relpath(path, root).replace("\\", "/")
            for line, name, owner in locals_found:
                if name in known:
                    detail = ("local '{0}' in {1} hides the file-scope name '{0}' declared in the same "
                              "file (MSVC C4459, an error under Unreal's shadow-variable policy)")
                    arguments = (name, relative)
                elif owner and name in members.get(owner, ()):
                    detail = ("local '{0}' in {1} hides member '{0}' of {2}, the class it is defined in "
                              "(MSVC C4458, an error under Unreal's shadow-variable policy)")
                    arguments = (name, relative, owner)
                else:
                    continue
                findings.append({
                    "kind": "shadow",
                    "module": module,
                    "name": name,
                    "file": relative,
                    "line": line,
                    "detail": detail.format(*arguments),
                })
        for name, paths in sorted(owners.items()):
            if len(paths) > 1:
                findings.append({
                    "kind": "clash",
                    "module": module,
                    "name": name,
                    "files": [os.path.relpath(p, root).replace("\\", "/") for p in sorted(paths)],
                    "detail": "internal-linkage name '{0}' is defined in {1} files of module {2}; a "
                              "unity build merges them into one translation unit and it will not "
                              "compile".format(name, len(paths), module),
                })
    return findings


def main():
    parser = argparse.ArgumentParser(description="Southern Spear unity-build name clash check")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable report")
    parser.add_argument("--root", default=PROJECT_ROOT, help="repo root to scan (default: this one)")
    args = parser.parse_args()

    if not os.path.isdir(os.path.join(args.root, "Plugins")):
        sys.stderr.write("Cannot find Plugins/ under {0}\n".format(args.root))
        return 2

    findings = check_tree(args.root)
    clashes = [f for f in findings if f["kind"] == "clash"]
    shadows = [f for f in findings if f["kind"] == "shadow"]

    if args.json:
        print(json.dumps({"ok": not findings, "findings": findings, "counts": {
            "clash": len(clashes), "shadow": len(shadows)}}, indent=2, sort_keys=True))
    else:
        modules = len(module_sources(args.root))
        print("=" * 70)
        print("SOUTHERN SPEAR - UNITY-BUILD NAME CHECK")
        print("=" * 70)
        if not findings:
            print("PASS - no name clash across {0} module(s).".format(modules))
        else:
            print("FAIL - {0} clash(es), {1} shadow(s):\n".format(len(clashes), len(shadows)))
            for finding in findings:
                print("  " + finding["detail"])
                if finding.get("files"):
                    for path in finding["files"]:
                        print("      " + path)
                print()

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
