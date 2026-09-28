#!/usr/bin/env python3
"""Turn the ADF Re-Cut Arma config into a machine-readable item registry.

Why
---
The extraction produced 268 FBX, 2,494 textures and 165 clips, but nothing said
*which* config class owns which mesh, where a weapon's muzzle sits in model
space, which animation a weapon plays, or what a magazine holds.  All of that
lives in the addon's `.hpp` / `.cpp` / `.cfg` text, which nothing had read.

Arma config is a small C-like language: a preprocessor (object- and
function-like macros, `##` token pasting, includes, conditionals) feeding a
nested-class document format.  This runs the whole thing and emits JSON.

Pipeline
--------
1. Strip comments, honouring string literals.
2. Join `\\` line continuations, so a multi-line `#define` becomes one
   logical line.
3. Preprocess: `#define` (incl. function-like and `##`), `#include`,
   `#ifdef`/`#ifndef`/`#else`/`#endif`, `#undef`.  Includes resolve sibling
   first, then by basename across the corpus.  Macros expand per logical
   line, continuing onto the next if the parens are still open.
4. Parse the expanded text into a class tree with inheritance, properties and
   arrays.  Values keep both a raw and a normalised form.
5. Evaluate `__EVAL(expr)` and bare arithmetic so timings are numbers.
6. Pull out the families the integration guide cares about, and cross-link
   them against ASSET_MANIFEST.json so a class resolves to actual FBX, clips
   and sounds on disk.

Two of those links are multi-hop, because Arma never names a file directly:

  * audio    soundSetShot[] -> CfgSoundSets.X -> soundShaders[] ->
             CfgSoundShaders.Y -> samples[] -> a path with no extension
  * vehicle  .driverAction -> CfgMovesMaleSdr.States.<name> -> .file -> .rtm

Both are resolved and the results cross-referenced to the manifest.

Anything the parser could not consume is counted and reported rather than
silently dropped -- `unparsed_statements` in the summary.

Usage:  python config_registry.py [root] [out.json]
"""
import collections
import json
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else \
    r"E:\SouthernSpear\Content\Sourced\ADF_Extracted"
OUT = sys.argv[2] if len(sys.argv) > 2 else \
    os.path.join(ROOT, "_tools", "config_registry.json")
MANIFEST = os.path.join(ROOT, "ASSET_MANIFEST.json")

EXTS = (".hpp", ".cpp", ".cfg")
SCAN_ROOTS = ("Source", "Workshop")

# Property families worth surfacing, by role.
ATTACHMENT_POINTS = (
    "muzzleend", "muzzlepos", "cartridgepos", "cartridgevel",
    "chamberpos", "ejectionportpos", "grenadeEjectionPoint",
    "sightPos", "pipSightPos", "rearSightPoint", "frontSightPoint",
    "optic", "dispersion", "soundEffect",
)
ANIM_PROPS = (
    "selectionFireAnim", "selectionFireAnimAdd", "reloadAction",
    "reloadMagazineSound", "muzzleSwapAnimation", "adjustWeaponAnim",
    # CfgMoves states carry their rtm under `file`; the generic .rtm sweep below
    # catches those, but naming it keeps the family visible in the summary.
    "file",
)
# A vehicle names its crew animations as CfgMoves *state* names, not rtm paths.
# `driverAction = "Pilot_Plane_Transport_01"` resolves through
# CfgMovesMaleSdr.States.<name>.file to the actual clip, so these properties are
# the only vehicle -> animation edge in the config.
CREW_ACTION_PROPS = (
    "driverAction", "driverInAction", "driverGetInAction",
    "driverGetOutAction", "gunnerAction", "gunnerInAction",
    "gunnerGetInAction", "gunnerGetOutAction", "commanderAction",
    "commanderInAction", "getInAction", "getOutAction",
    "cargoAction[]", "cargoGetInAction[]", "cargoGetOutAction[]",
    "moveInCargo", "moveOutCargo",
)
TIMING_PROPS = (
    "magazineReloadSwitchPhase", "reloadTime", "reloadMagazineTime",
    "swapDelay", "muzzleSwapTime", "burstFireTime", "soundBurstDelay",
    "animationTime", "animSpeed", "magSize_", "magReloadTime",
)
MODEL_PROPS = ("model", "modelPath", "hit", "wreckModel", "modelAnim",
               "ammo", "pilotLight", "sound", "soundSet", "SoundSet")
SOUND_PROP_PREFIXES = ("sound", "bullet", "drySound", "reload", "closure",
                       "changeFiremode", "muzzle", "effect", "hit")

# Vanilla parents that identify what an ADFRC class actually is.
KIND_HINTS = (
    ("CfgWeapons", "weapon"),
    ("CfgVehicles", "vehicle"),
    ("cfgAmmo", "ammo"),
    ("cfgMagazines", "magazine"),
    ("CfgMoves", "move"),
    ("CfgSkeleton", "skeleton"),
    ("CfgSoundSets", "soundset"),
    ("CfgNonAircraft", "weapon"),
    ("CfgModels", "model_proxy"),
    ("CfgGlasses", "glasses"),
    ("CfgUnitInsignia", "insignia"),
    ("CfgSoundShaders", "sound_shader"),
    ("CfgPatches", "patch"),
    ("CfgCloudlets", "cloudlet"),
    ("CfgGesturesMale", "gesture"),
    ("CfgEditorSubcategories", "editor_subcategory"),
    ("Sounds", "sound"),
    ("CfgVehicleClasses", "faction"),
)
# The top-level classes that actually hold items.  Anything else at depth 0 is
# a bare fragment (a per-weapon base, a PhysX block) whose children are
# internals rather than items of their own.
CONFIG_ROOTS = frozenset((
    "CfgWeapons", "cfgweapons", "cfgWeapons", "CfgVehicles", "cfgvehicles",
    "cfgVehicles", "cfgAmmo", "CfgAmmo", "cfgMagazines", "CfgMagazines",
    "cfgMagazines", "CfgMoves", "CfgMovesBasic", "CfgMovesMaleSdr",
    "CfgSkeleton", "CfgSkeletons", "cfgSkeletons", "cfgClouds", "cfgCloudlets",
    "CfgCloudlets", "CfgSoundSets", "cfgSoundSets", "CfgSoundShaders",
    "cfgSoundShaders", "Sounds", "CfgModels", "cfgModels", "CfgPatches",
    "cfgPatches", "CfgGlasses", "cfgGlasses", "CfgUnitInsignia",
    "cfgUnitInsignia", "CfgGesturesMale", "cfgGesturesMale",
    "CfgNonAircraft", "cfgNonAircraft", "CfgVehicleClasses",
    "cfgVehicleClasses", "CfgEditorSubcategories", "cfgEditorSubcategories",
))

# Bare fragment classes: not under a config root, so only a name or a parent
# can identify them.  Checked after the transitive ancestor walk, because a
# fragment almost always chains to a vanilla base a few hops up.
NAME_HINTS = (
    ("Gustav_", "cloudlet"),
    ("Wheels", "vehicle_part"),
    ("Turrets", "vehicle_part"),
    ("asdg_", "weapon"),
    ("tbas_", "weapon"),
    ("CBA_", "weapon"),
    ("rhs_", "weapon"),
    ("adfrc_MLOK", "weapon"),
    ("adfrc_PIC", "weapon"),
)
# Suffix rules, for names whose parent is a vanilla class absent from the
# corpus (a 9x19 magazine derives from `16Rnd_9x21_Mag`, which no ADFRC file
# declares, so there is no chain to walk).
NAME_SUFFIX_HINTS = (
    ("_Mag", "magazine"),
    ("_Magazine", "magazine"),
    ("_grip_slot", "weapon"),
    ("_gripod_slot", "weapon"),
    ("_muzzle_snds", "sound"),
    ("_snds", "sound"),
)
# Substring rules, for the same reason: ADFRC_15rnd_9MM_BALL_G19 is a magazine
# but ends in the weapon it feeds, so no suffix catches it.
NAME_CONTAINS_HINTS = (
    ("VehicleSystemsTemplate", "ui_template"),
    ("_MEN_", "faction"),
    ("rnd_", "magazine"),
    ("Rnd_", "magazine"),
)
# CfgVehicles is a mixed bag: Arma files uniforms, backpacks, vests *and*
# vehicles in it, so a config-root match alone calls a plate carrier a
# vehicle.  These properties say what the class really is.  Checked before
# falling back to the config root.
CONTENT_HINTS = (
    ("uniformClass", "uniform"),
    ("nakedUniform", "uniform"),
    ("isbackpack", "gear"),
    ("maximumLoad", "gear"),
    ("vehicleClass", "vehicle"),
)
# Vanilla intermediates the corpus chains through but never declares.
IMPLICIT_KIND = (
    ("ItemCore", "item"),
    ("ItemCore_F", "item"),
    ("Air", "vehicle"),
    ("Ship", "vehicle"),
)
VANILLA_KIND = (
    ("Rifle_Base_F", "weapon"), ("Pistol_Base_F", "weapon"),
    ("Launcher_Base_F", "weapon"), ("HMG_Base", "weapon"),
    ("Binocular_Base_F", "weapon"), ("Weapon_Base_F", "weapon"),
    ("Man", "unit"), ("Soldier_F", "unit"),
    ("CAManBase", "unit"), ("CAModule", "unit"),
    ("CarBase", "vehicle"), ("TankBase", "vehicle"),
    ("HelicopterBase", "vehicle"), ("PlaneBase", "vehicle"),
    ("ShipBase", "vehicle"), ("StaticBase", "static"),
    ("BulletBase", "ammo"), ("ShellBase", "ammo"), ("RocketBase", "ammo"),
    ("Magazine", "magazine"),
    ("B_Soldier_base_F", "unit"), ("B_Soldier_diver_base_F", "unit"),
    ("B_AssaultPack_Base", "gear"), ("B_Kitbag_Base", "gear"),
    ("B_CarryAll_Base", "gear"), ("B_FieldDress_Base", "uniform"),
)


# --------------------------------------------------------------------------
# 1-2. text cleanup
# --------------------------------------------------------------------------
def strip_comments(text):
    """Remove // and /* */ comments, leaving string literals alone."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                if text[j] == '"':
                    j += 1
                    break
                j += 1
            out.append(text[i:j])
            i = j
            continue
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def join_continuations(text):
    return re.sub(r"\\[ \t]*\r?\n", " ", text)


# --------------------------------------------------------------------------
# 3. preprocessor
# --------------------------------------------------------------------------
DEF_RE = re.compile(
    r"^\s*#\s*define\s+(?P<name>[A-Za-z_]\w*)"
    r"(?:\((?P<params>[^)]*)\))?\s*(?P<body>.*)$")
INC_RE = re.compile(r'^\s*#\s*include\s+(?P<q>["<])(?P<path>[^">]+)[">]')
COND_RE = re.compile(r"^\s*#\s*(ifdef|ifndef|if|else|endif)\b\s*(.*)$")
UNDEF_RE = re.compile(r"^\s*#\s*undef\s+(?P<name>[A-Za-z_]\w*)")


class Macro(object):
    __slots__ = ("name", "params", "body", "src")

    def __init__(self, name, params, body, src):
        self.name = name
        self.params = params
        self.body = body
        self.src = src


class Preprocessor(object):
    def __init__(self, root, corpus_index):
        self.root = root
        self.corpus_index = corpus_index      # lower basename -> [paths]
        self.macros = {}
        self.includes_resolved = 0
        self.includes_unresolved = []
        self.max_include_depth = 0

    # -- macro expansion ---------------------------------------------------
    def expand(self, line):
        for _ in range(24):                  # bounded; macros are not recursive
            new = self._expand_once(line)
            if new == line:
                return new
            line = new
        return line

    def _expand_once(self, line):
        out = []
        i = 0
        n = len(line)
        while i < n:
            if line[i] == '"':
                j = i + 1
                while j < n:
                    if line[j] == "\\" and j + 1 < n:
                        j += 2
                        continue
                    if line[j] == '"':
                        j += 1
                        break
                    j += 1
                out.append(line[i:j])
                i = j
                continue
            m = re.match(r"[A-Za-z_]\w*", line[i:])
            if not m:
                out.append(line[i])
                i += 1
                continue
            word = m.group(0)
            start = i
            i += len(word)
            mac = self.macros.get(word)
            if mac is None or not mac.params:
                if mac is not None:
                    out.append(mac.body)
                else:
                    out.append(word)
                continue
            # function-like: needs '(' next
            j = i
            while j < n and line[j] in " \t":
                j += 1
            if j >= n or line[j] != "(":
                out.append(word)
                continue
            depth = 0
            k = j
            arg_start = j + 1
            args = []
            while k < n:
                if line[k] == '"':
                    k += 1
                    while k < n and line[k] != '"':
                        k += 2 if line[k] == "\\" else 1
                elif line[k] == "(":
                    depth += 1
                elif line[k] == ")":
                    depth -= 1
                    if depth == 0:
                        args.append(line[arg_start:k])
                        break
                elif line[k] == "," and depth == 1:
                    args.append(line[arg_start:k])
                    arg_start = k + 1
                k += 1
            if k >= n:
                out.append(line[start:])
                return "".join(out)
            body = self._substitute(mac, args)
            out.append(self.expand(body))
            i = k + 1
        return "".join(out)

    @staticmethod
    def _substitute(mac, args):
        params = [p.strip() for p in mac.params.split(",")] if mac.params else []
        vals = [a.strip() for a in args]
        mapping = dict(zip(params, vals))

        def arg_of(tok):
            return mapping.get(tok)

        # token pasting first: a##b
        def paste(m):
            left, right = m.group(1), m.group(2)
            lv = arg_of(left)
            rv = arg_of(right)
            lv = lv if lv is not None else left
            rv = rv if rv is not None else right
            return lv + rv

        body = re.sub(r"([A-Za-z_]\w*)##([A-Za-z_]\w*)", paste, mac.body)
        # then parameter substitution
        body = re.sub(r"##([A-Za-z_]\w*)",
                      lambda m: arg_of(m.group(1)) or m.group(1), body)
        body = re.sub(r"([A-Za-z_]\w*)##",
                      lambda m: arg_of(m.group(1)) or m.group(1), body)

        def sub(m):
            w = m.group(0)
            if w in mapping:
                return mapping[w]
            return w

        body = re.sub(r"[A-Za-z_]\w*", sub, body)
        # #x stringification
        body = re.sub(r'#\s*([A-Za-z_]\w*)',
                      lambda m: '"%s"' % mapping.get(m.group(1), m.group(1)),
                      body)
        return body.strip()

    # -- file walking ------------------------------------------------------
    def run_file(self, path, depth=0, seen=None):
        seen = seen if seen is not None else set()
        key = os.path.normcase(os.path.abspath(path))
        if key in seen or depth > 12:
            return []
        seen.add(key)
        self.max_include_depth = max(self.max_include_depth, depth)
        try:
            raw = open(path, "r", encoding="utf-8", errors="replace").read()
        except OSError as exc:
            self.includes_unresolved.append("%s: %s" % (path, exc))
            return []
        raw = join_continuations(strip_comments(raw))
        lines = raw.split("\n")

        out = []
        cond = []            # stack of (active, seen_true)
        buf = None
        buf_line = 0
        for lineno, line in enumerate(lines, 1):
            active = all(c[0] for c in cond)

            if buf is not None:
                buf += " " + line.strip()
                if buf.count("(") <= buf.count(")"):
                    if active:
                        out.append((buf_line, self.expand(buf)))
                    buf = None
                continue

            cm = COND_RE.match(line)
            if cm and not line.lstrip().startswith("#include"):
                kind = cm.group(1)
                if kind in ("ifdef", "ifndef"):
                    name = cm.group(2).strip()
                    val = name in self.macros
                    want = val if kind == "ifdef" else not val
                    parent = all(c[0] for c in cond)
                    cond.append((parent and want, want))
                elif kind == "if":
                    cond.append((all(c[0] for c in cond), True))
                elif kind == "else":
                    if cond:
                        top = list(cond[-1])
                        top[0] = (not top[1]) and all(c[0] for c in cond[:-1])
                        top[1] = True
                        cond[-1] = tuple(top)
                elif kind == "endif":
                    if cond:
                        cond.pop()
                continue

            if not active:
                continue

            s = line.strip()
            if not s:
                continue

            if s.startswith("#"):
                um = UNDEF_RE.match(s)
                if um:
                    self.macros.pop(um.group("name"), None)
                    continue
                dm = DEF_RE.match(s)
                if dm:
                    params = dm.group("params")
                    self.macros[dm.group("name")] = Macro(
                        dm.group("name"),
                        params if params and params.strip() else None,
                        dm.group("body").strip(),
                        "%s:%d" % (os.path.relpath(path, self.root), lineno))
                    continue
                im = INC_RE.match(s)
                if im:
                    target = self._resolve_include(im.group("path"), path)
                    if target:
                        self.includes_resolved += 1
                        out.extend(self.run_file(target, depth + 1, seen))
                    else:
                        self.includes_unresolved.append(
                            "%s:%d -> %s"
                            % (os.path.relpath(path, self.root), lineno,
                               im.group("path")))
                    continue
                continue

            # possible multi-line macro invocation
            if self._starts_call(s):
                buf = s
                buf_line = lineno
                if buf.count("(") > buf.count(")"):
                    continue
                out.append((buf_line, self.expand(buf)))
                buf = None
                continue

            out.append((lineno, self.expand(s)))
        if buf is not None and active:
            out.append((buf_line, self.expand(buf)))
        return out

    @staticmethod
    def _starts_call(s):
        m = re.match(r"^([A-Za-z_]\w*)\s*\(", s)
        return bool(m)

    def _resolve_include(self, inc, from_path):
        inc = inc.replace("\\", os.sep)
        cand = os.path.join(os.path.dirname(from_path), inc)
        if os.path.isfile(cand):
            return cand
        for base in (inc, inc + ".hpp", inc + ".cfg"):
            for p in self.corpus_index.get(os.path.basename(base).lower(), []):
                return p
        return None


# --------------------------------------------------------------------------
# 4-5. config parsing
# --------------------------------------------------------------------------
class CfgClass(object):
    __slots__ = ("name", "parents", "props", "children", "line", "source")

    def __init__(self, name, parents, line, source):
        self.name = name
        self.parents = parents
        self.props = collections.OrderedDict()
        self.children = []
        self.line = line
        self.source = source


class ConfigParser(object):
    TOKEN = re.compile(
        r'"(?:\\.|[^"\\])*"'      # string
        r"|[0-9]+[A-Za-z_]\w*"                  # digit-led ident, e.g. 50RD
        r"|[A-Za-z_]\w*"                       # ident
        r"|\d+\.\d*(?:[eE][-+]?\d+)?"           # float
        r"|\.\d+(?:[eE][-+]?\d+)?"
        r"|\d+"                                  # int
        r"|::|>>|<<|!=|==|<=|>=|[-+*/%(){}\[\];:,<>=&|!?^~-]"
    )

    def __init__(self, text, source, unparsed, unknown_calls=None):
        self.toks = self._tokenize(text)
        self.i = 0
        self.source = source
        self.unparsed = unparsed
        self.unknown_calls = unknown_calls if unknown_calls is not None else []

    def _tokenize(self, text):
        toks = []
        pos = 0
        while pos < len(text):
            m = self.TOKEN.match(text, pos)
            if not m:
                pos += 1
                continue
            toks.append(m.group(0))
            pos = m.end()
        return toks

    def peek(self, k=0):
        j = self.i + k
        return self.toks[j] if j < len(self.toks) else None

    def next(self):
        t = self.peek()
        if t is not None:
            self.i += 1
        return t

    def expect(self, tok):
        t = self.next()
        return t == tok

    def parse_document(self):
        roots = []
        while self.peek() is not None:
            before = self.i
            node = self.parse_statement(None)
            if node is not None:
                if isinstance(node, list):
                    roots.extend(node)
                else:
                    roots.append(node)
            if self.i == before:
                self.unparsed.append("%s: stuck at %r" % (self.source,
                                                          self.peek()))
                self.i += 1
        return roots

    def parse_statement(self, parent):
        t = self.peek()
        if t is None:
            return None
        if t == "class":
            return self.parse_class()
        if t == "enum":
            # C++ enum left behind in an ACE-compat header; not config, skip.
            while self.peek() is not None and self.peek() != "{":
                self.next()
            if self.peek() == "{":
                self.skip_balanced_braces()
            if self.peek() == ";":
                self.next()
            return None
        if t == "delete":
            self.next()
            name = self.next()
            if self.peek() == ";":
                self.next()
            return ("delete", name)
        return self.parse_property(parent)

    def parse_class(self):
        self.next()                                   # 'class'
        name = self.next() or "?"
        parents = []
        if self.peek() == ":":
            self.next()
            while True:
                nxt_p = self.peek()
                if nxt_p is None or nxt_p in ("{", ";", "}"):
                    break
                parents.append(self.next())
        nxt = self.peek()
        if nxt == ";":
            # `class X;` is a legal forward declaration in Arma config.
            self.next()
            return CfgClass(name, parents, 0, self.source)
        if nxt != "{":
            self.unparsed.append("%s: class %s had no body (saw %r)"
                                 % (self.source, name, nxt))
            return None
        self.next()                                   # '{'
        node = CfgClass(name, parents, 0, self.source)
        while True:
            t = self.peek()
            if t is None:
                self.unparsed.append("%s: unterminated class %s"
                                     % (self.source, name))
                break
            if t == "}":
                self.next()
                if self.peek() == ";":
                    self.next()
                break
            before = self.i
            if t == ";":
                # stray empty statement, e.g. the `;` that ended a macro call
                # we skipped over
                self.next()
                continue
            # A `NAME(...)` statement here is a macro the preprocessor could
            # not expand because it is never defined in the corpus.  Arma
            # tolerates these; skip the call and record it so the class body
            # still parses and the breakage is visible.
            m = re.match(r"^[A-Za-z_0-9]\w*$", t or "")
            if m and self.peek(1) == "(":
                macro_name = self.next()
                self.skip_balanced_parens()
                self.unknown_calls.append("%s: %s(...)"
                                          % (self.source, macro_name))
                continue
            child = self.parse_statement(node)
            if isinstance(child, CfgClass):
                node.children.append(child)
            elif isinstance(child, tuple) and child[0] == "delete":
                node.props.pop(child[1], None)
            if self.i == before:
                self.unparsed.append("%s: stuck in class %s at %r"
                                     % (self.source, name, self.peek()))
                self.i += 1
        return node

    def skip_balanced_braces(self):
        if self.peek() != "{":
            return
        depth = 0
        while self.peek() is not None:
            t = self.next()
            if t == "{":
                depth += 1
            elif t == "}":
                depth -= 1
                if depth == 0:
                    return

    def skip_balanced_parens(self):
        if self.peek() != "(":
            return
        depth = 0
        while self.peek() is not None:
            t = self.next()
            if t == "(":
                depth += 1
            elif t == ")":
                depth -= 1
                if depth == 0:
                    return

    def parse_property(self, parent):
        key = self.next()
        if key is None:
            return None
        if key in ("{", "}", ";"):
            self.i -= 1
            return None
        is_array = False
        if self.peek() == "[":
            self.next()
            if self.peek() == "]":
                self.next()
                is_array = True
        if self.peek() != "=":
            # bare statement, e.g. an identifier used as a value
            if is_array and parent is not None:
                parent.props.setdefault(key + "[]", [])
            return None
        self.next()                                   # '='
        value = self.parse_value()
        if self.peek() == ";":
            self.next()
        if parent is not None:
            parent.props[key + ("[]" if is_array else "")] = value
        return None

    def parse_value(self):
        t = self.peek()
        if t is None:
            return None
        if t == "{":
            return self.parse_array()
        if t.startswith('"'):
            self.next()
            return t[1:-1] if len(t) >= 2 else ""
        # arithmetic / bare expression
        parts = []
        depth = 0
        while self.peek() is not None:
            p = self.peek()
            if depth == 0 and p in (";", "}", ","):
                break
            if p in ("(", "["):
                depth += 1
            elif p in (")", "]"):
                depth -= 1
                if depth < 0:
                    break
            parts.append(self.next())
        raw = "".join(parts).strip()
        if not parts:
            return None
        if len(parts) == 1:
            tok = parts[0]
            if re.match(r"^\d+$", tok):
                return int(tok)
            if re.match(r"^-?\d*$", tok) and re.match(r"^-?\d+\.\d*(?:[eE][-+]?\d+)?$", tok):
                return float(tok)
            if re.match(r"^-?\d+\.\d*(?:[eE][-+]?\d+)?$", tok):
                return float(tok)
            if re.match(r"^[A-Za-z_]\w*$", tok):
                return tok
        num = evaluate(raw)
        if num is not None:
            return num
        return raw

    def parse_array(self):
        self.next()                                   # '{'
        out = []
        while True:
            t = self.peek()
            if t is None:
                break
            if t == "}":
                self.next()
                break
            if t == ",":
                self.next()
                continue
            v = self.parse_value()
            if v is None and self.peek() in (",", "}"):
                self.next()
                continue
            out.append(v)
        return out


def evaluate(expr):
    """Best-effort numeric evaluation of a config expression."""
    if expr is None:
        return None
    s = expr.strip()
    if not s:
        return None
    m = re.match(r"^__EVAL\s*\((.*)\)$", s, re.S)
    if m:
        s = m.group(1).strip()
    if not re.match(r"^[\d\s+\-*/().eE]+$", s):
        return None
    if not re.search(r"[+\-*/()]", s):
        return None
    # Arma config integers are decimal; Python 3 would reject a leading zero
    # as an invalid octal literal, which the macros rely on (BULLET_HIDE(028)).
    # The lookbehind keeps this off the fractional part of 0.00001, which must
    # stay a small epsilon rather than becoming 0.1.
    s = re.sub(r"(?<![\w.])0+(\d)", r"\1", s)
    try:
        v = eval(s, {"__builtins__": {}}, {})       # noqa: S307 - numeric only
    except Exception:  # noqa: BLE001
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return v
    return None


# --------------------------------------------------------------------------
# 6. extraction
# --------------------------------------------------------------------------
def ancestors(name, parents_of, limit=64):
    """All transitive parent names of `name`, nearest first.

    Arma fragments chain a long way before hitting a vanilla base --
    ADFRC_EF88_Black -> ADFRC_EF88_Base -> Rifle_Base_F -- so classifying on
    direct parents alone leaves most weapon variants "unknown".
    """
    out = []
    seen = set()
    frontier = list(parents_of.get(name.lower(), ()))
    while frontier and len(out) < limit:
        nxt = frontier.pop(0)
        if nxt in seen:
            continue
        seen.add(nxt)
        out.append(nxt)
        frontier.extend(parents_of.get(nxt.lower(), ()))
    return out


def kind_of(path, parents, parents_of, own_props):
    top = path.split(".")[0] if path else ""
    # Content first: CfgVehicles holds gear and uniforms as well as vehicles.
    for key, kind in CONTENT_HINTS:
        if key in own_props:
            return kind
    for key, kind in KIND_HINTS:
        if key.lower() in top.lower():
            return kind
    vanilla = {k: v for k, v in VANILLA_KIND}
    vanilla.update(IMPLICIT_KIND)
    for p in parents:                      # direct parent first
        if p in vanilla:
            return vanilla[p]
    # ancestors() is seeded on the class's own name, not the config root, so a
    # bare fragment (ADFRC_F9) still walks up its own chain.
    for p in ancestors(path.split(".")[-1], parents_of):
        if p in vanilla:
            return vanilla[p]
    name = path.split(".")[-1]
    for prefix, kind in NAME_HINTS:
        if name.startswith(prefix):
            return kind
    for suffix, kind in NAME_SUFFIX_HINTS:
        if name.endswith(suffix):
            return kind
    for frag, kind in NAME_CONTAINS_HINTS:
        if frag in name:
            return kind
    return "unknown"


def as_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def strings_in(v):
    return [x for x in as_list(v) if isinstance(x, str) and x]


def collect_registry(corpus, manifest):
    models = {os.path.splitext(os.path.basename(m.get("fbx", "")))[0].lower(): m
              for m in manifest.get("models", []) if m.get("fbx")}
    # clips is keyed by the decoded clip's JSON path
    clip_by_stem = collections.defaultdict(list)
    for key, val in (manifest.get("clips") or {}).items():
        stem = os.path.splitext(os.path.basename(key))[0]
        if stem:
            clip_by_stem[stem.lower()].append({
                "clip": key,
                "rig": (val or {}).get("rig"),
                "fbx": (val or {}).get("fbx"),
            })
    sound_by_stem = {os.path.splitext(os.path.basename(s["wav"]))[0].lower(): s
                     for s in manifest.get("sounds", []) if s.get("wav")}

    # name -> declared parents, merged across the whole corpus so a fragment can
    # be classified by walking up to whatever vanilla base it chains to.  The
    # merge matters: the first declaration of a name is often a parentless
    # forward declaration (`class ADFRC_G19_Base;` inside cfgweapons), so a
    # plain setdefault would strand the walk with no parents at all.
    #
    # Keys are lowercased because Arma class names are case-insensitive, and
    # the corpus relies on it: it declares `ADFRC_Soldier_base_F` but derives
    # `ADFRC_MD_AMCU_Soldier_Base` from `ADFRC_Soldier_Base_F`.
    parents_of = {}
    for info in corpus:
        got = parents_of.setdefault(info["name"].lower(), [])
        for p in info["parents"]:
            if p not in got:
                got.append(p)

    # Sound references are two-hop.  A weapon writes `hitMetal =
    # "ImpactMetalSabotBig"` -- the name of a class under `class Sounds` --
    # and that class is what carries the actual `.wss` / `.ogg` path.  This
    # index resolves the first hop so a weapon can be traced to a real WAV.
    sound_class = {}
    for info in corpus:
        if info["path"].split(".")[0].lower() not in ("sounds", "cfgsounds"):
            continue
        for key, val in info["effective"].items():
            for p in strings_in(val):
                low = p.lower()
                if low.endswith((".wss", ".ogg", ".mp3", ".wav")):
                    sound_class.setdefault(info["name"], set()).add(p)

    # Weapon -> audio is a three-hop chain in Arma:
    #   weapon.soundSet[]        -> CfgSoundSets.X
    #   soundSet.soundShaders[]  -> CfgSoundShaders.Y
    #   shader.samples[]         -> "\ADF\...\AUG_closeShot_01"  (no extension)
    # Each hop names a class; only the last one holds a file.  These two
    # indexes close the chain so a weapon resolves to real WAVs.
    soundset_shaders = {}
    for info in corpus:
        if info["path"].split(".")[0].lower() not in ("cfgsoundsets",
                                                     "cfgsoundsets"):
            continue
        for nm in strings_in(info["own_props"].get("soundShaders[]")):
            soundset_shaders.setdefault(info["name"], []).append(nm)
        for nm in strings_in(info["own_props"].get("soundShaders")):
            soundset_shaders.setdefault(info["name"], []).append(nm)

    shader_samples = {}
    for info in corpus:
        if info["path"].split(".")[0].lower() not in ("cfgsoundshaders",
                                                     "cfgsoundshaders"):
            continue
        for key in ("samples[]", "samples"):
            for entry in info["own_props"].get(key) or ():
                if isinstance(entry, list) and entry:
                    first = entry[0]
                elif isinstance(entry, str):
                    first = entry
                else:
                    continue
                if isinstance(first, str) and first:
                    shader_samples.setdefault(info["name"], []).append(first)

    # CfgMoves state name -> the rtm it plays.  A vehicle's crew animation is
    # only ever written as a state name (`driverAction = "..."`), so this
    # index is what turns a vehicle into a set of real clips.
    move_states = {}
    for info in corpus:
        if not info["path"].split(".")[0].lower().startswith("cfgmoves"):
            continue
        for val in info["effective"].values():
            for p in strings_in(val):
                if p.lower().endswith(".rtm"):
                    move_states.setdefault(info["name"], set()).add(p)

    registry = []
    counts = collections.Counter()
    item_counts = collections.Counter()
    # Resolving one soundset yields the same sample list every time, and the
    # same base class is declared in a dozen files, so memoise per name.
    set_cache = {}
    for info in corpus:
        props = info["effective"]
        own = info["own_props"]
        parents = info["parents"]

        attach = {k: v for k, v in props.items() if k in ATTACHMENT_POINTS}
        anims = {k: v for k, v in props.items() if k in ANIM_PROPS}
        timings = {k: v for k, v in props.items() if k in TIMING_PROPS}
        if "magSize" in props:
            timings["magSize"] = props["magSize"]

        hand = props.get("handAnim[]")
        rtm_paths = [x for x in strings_in(hand)
                     if x.lower().endswith(".rtm")]
        if rtm_paths:
            anims["handAnimRtm"] = rtm_paths
        for k, v in props.items():
            if k in anims:
                continue
            vals = strings_in(v)
            rtms = [x for x in vals if x.lower().endswith(".rtm")]
            if rtms:
                anims[k] = rtms

        mags = strings_in(props.get("magazines[]"))
        wells = strings_in(props.get("magazineWell[]"))
        modes = strings_in(props.get("modes[]"))

        # LinkedItems can sit at any depth (a grip macro puts it under
        # WeaponSlotsInfo > MuzzleSlot), so search the whole subtree.
        linked = {}

        def find_linked(node):
            for c in node["_children"]:
                if c["name"] in ("LinkedItems", "LinkedItemsUnder"):
                    for slot in c["_children"]:
                        linked.setdefault(slot["name"], {}).update(
                            {k: v for k, v in slot["effective"].items()})
                else:
                    find_linked(c)

        find_linked(info)
        slots = {}

        def find_slots(node):
            for c in node["_children"]:
                if c["name"] == "WeaponSlotsInfo":
                    for slot in c["_children"]:
                        slots[slot["name"]] = {
                            "parents": slot["parents"],
                            "allowedSlots": as_list(
                                slot["effective"].get("allowedSlots[]")),
                            "mass": slot["effective"].get("mass"),
                        }
                else:
                    find_slots(c)

        find_slots(info)

        models_ref = []
        for k in MODEL_PROPS:
            models_ref.extend(strings_in(props.get(k)))
        for v in props.values():
            models_ref.extend([x for x in strings_in(v)
                               if x.lower().endswith(".p3d")])
        models_ref = sorted(set(models_ref))

        # Own declarations only.  A vehicle's sound set is inherited by every
        # turret and hitpoint beneath it, so reading `effective` repeated the
        # same 60-entry array on ~1300 classes and inflated the report from
        # 295 distinct sound lists to 46368 references.
        sounds = []
        for k, v in own.items():
            kl = k.lower()
            if any(kl.startswith(pfx) for pfx in SOUND_PROP_PREFIXES):
                for s in strings_in(v):
                    sounds.append({"prop": k, "path": s})

        # cross-links
        res_models = []
        for m in models_ref:
            stem = os.path.splitext(os.path.basename(m))[0].lower()
            hit = models.get(stem)
            res_models.append({
                "config_path": m,
                "stem": stem,
                "fbx": hit.get("fbx") if hit else None,
                "matched": bool(hit),
            })
        res_clips = []
        for k, v in sorted(anims.items()):
            for p in (v if isinstance(v, list) else [v]):
                if not isinstance(p, str) or not p.lower().endswith(".rtm"):
                    continue
                stem = os.path.splitext(os.path.basename(p))[0].lower()
                res_clips.append({
                    "prop": k, "config_path": p,
                    "clips": clip_by_stem.get(stem, []),
                    "matched": bool(clip_by_stem.get(stem)),
                })
        # A weapon's audio runs through its soundset, three hops deep:
        #   soundSetShot[] -> CfgSoundSets.X -> soundShaders[] ->
        #   CfgSoundShaders.Y -> samples[] -> "\ADF\...\AUG_closeShot_01"
        # The property lives on a fire-mode class nested under the weapon, so
        # the subtree is swept and the result attributed to the owning item.
        # Only 6 of the 76 soundset names the corpus references are declared
        # here; the rest are vanilla A3 and stay unresolved by design.
        used = []
        set_names = []
        unresolved_sets = set()

        def find_sets(node, trail):
            here = ".".join(trail) or node["name"]
            for key, val in node["own_props"].items():
                if key.lower() == "soundsetshot[]":
                    for nm in strings_in(val):
                        set_names.append((here, nm))
            for ch in node["_children"]:
                find_sets(ch, trail + [ch["name"]])

        find_sets(info, [])
        for scope, setname in set_names:
            if setname not in set_cache:
                rows = []
                for sh in soundset_shaders.get(setname, ()):
                    for sample in shader_samples.get(sh, ()):
                        stem = os.path.splitext(
                            os.path.basename(sample))[0].lower()
                        hit = sound_by_stem.get(stem)
                        rows.append({
                            "shader": sh,
                            "sample": sample,
                            "wav": hit.get("wav") if hit else None,
                            "matched": bool(hit),
                        })
                set_cache[setname] = rows
            rows = set_cache[setname]
            if not rows:
                unresolved_sets.add(setname)
                continue
            # Reference the top-level `sound_sets` table by name rather than
            # copying the sample list: one base class is declared in a dozen
            # files, and inlining 486 samples each time tripled the report.
            used.append({
                "scope": scope,
                "sound_set": setname,
                "samples": len(rows),
                "wavs": sorted({r["wav"] for r in rows if r["wav"]}),
            })
        used.sort(key=lambda x: (x["scope"], x["sound_set"]))

        res_sounds = []
        for s in sounds:
            ref = s["path"]
            # First try the value as a literal audio path; if it is a class
            # name, follow it to the path that class declares.
            files = [ref] if ref.lower().endswith(
                (".wss", ".ogg", ".mp3", ".wav")) else sorted(
                sound_class.get(ref, ()))
            wavs, matched = [], False
            for f in files:
                stem = os.path.splitext(os.path.basename(f))[0].lower()
                hit = sound_by_stem.get(stem)
                if hit:
                    wavs.append(hit.get("wav"))
                    matched = True
            res_sounds.append({
                "prop": s["prop"],
                "config_path": ref,
                # Set when the value was a class name rather than a path.
                "sound_class": ref if files != [ref] else None,
                "files": files,
                "wav": wavs,
                "matched": matched,
            })

        # Crew animations bind by CfgMoves state name, at vehicle scope and on
        # each turret, so the whole subtree has to be swept.  Only *own*
        # properties count: `effective` is inherited, so reading it would
        # report the driver's action once per descendant class.
        crew = []
        state_names = set(move_states)

        def note(node, trail):
            for prop in CREW_ACTION_PROPS:
                for nm in strings_in(node["own_props"].get(prop)):
                    crew.append({
                        "prop": prop,
                        "scope": ".".join(trail) or node["name"],
                        "state": nm,
                        "known_state": nm in state_names,
                        "rtm": sorted(move_states.get(nm, ())),
                    })
            for c in node["_children"]:
                note(c, trail + [c["name"]])

        # Start at the item itself: `driverAction` is declared on the vehicle
        # class, not on a turret, so sweeping only the children missed it.
        note(info, [])

        parts_path = info["path"].split(".")
        # An item is either a direct child of a config root (CfgWeapons.X) or a
        # bare fragment class from a standalone .hpp that names a parent
        # (X : Rifle_Base_F).  Everything nested deeper is an internal: a fire
        # mode, a sound class, a slot, an animation.
        #
        # The grandparent has to be a real config root, otherwise the children
        # of a bare fragment (ADFRC_EF88_Base.WeaponSlotsInfo,
        # ADFRC_EF88_Base.Single, ADFRC_EF88_Base.LinkedItems) all get counted
        # as items in their own right.
        is_item = (
            (len(parts_path) == 2 and parts_path[0] in CONFIG_ROOTS)
            or (len(parts_path) == 1 and parents)
        )

        entry = {
            "name": info["name"],
            "path": info["path"],
            "config_class": parts_path[0],
            "kind": kind_of(info["path"], parents, parents_of, own),
            "is_item": bool(is_item),
            "parents": parents,
            "source": info["source"],
            "depth": info["depth"],
            "attachment_points": attach,
            "animations": anims,
            "timings": timings,
            "magazines": mags,
            "magazine_wells": wells,
            "fire_modes": modes,
            "linked_items": linked,
            "weapon_slots": slots,
            "crew_animations": crew,
            "models": res_models,
            "sounds": res_sounds,
            "sound_sets_used": used,
            "sound_sets_unresolved": sorted(unresolved_sets),
            "animation_clips": res_clips,
            "property_count": len(own),
            "own_properties": own,
        }
        registry.append(entry)
        if is_item:
            item_counts[entry["kind"]] += 1
            if attach:
                item_counts["item_with_attachment_points"] += 1
            if anims:
                item_counts["item_with_animations"] += 1
            if linked:
                item_counts["item_with_linked_items"] += 1
            if mags:
                item_counts["item_with_magazines"] += 1
            if any(m["matched"] for m in res_models):
                item_counts["item_with_model_match"] += 1
            if any(c["matched"] for c in res_clips):
                item_counts["item_with_clip_match"] += 1
            if crew:
                item_counts["item_with_crew_animations"] += 1
            if any(x["wavs"] for x in used):
                item_counts["item_with_sound_chain_match"] += 1
        counts[entry["kind"]] += 1
        if attach:
            counts["with_attachment_points"] += 1
        if anims:
            counts["with_animations"] += 1
        if linked:
            counts["with_linked_items"] += 1
        if mags:
            counts["with_magazines"] += 1
        if timings:
            counts["with_timings"] += 1
        if any(m["matched"] for m in res_models):
            counts["with_model_match"] += 1
        if any(c["matched"] for c in res_clips):
            counts["with_clip_match"] += 1
        if crew:
            counts["with_crew_animations"] += 1
        if any(s["matched"] for s in res_sounds):
            counts["with_sound_match"] += 1
        if any(x["wavs"] for x in used):
            counts["with_sound_chain_match"] += 1

    # soundset name -> its resolved sample list, emitted once.  Classes
    # reference these by name from `sound_sets_used`.
    table = {}
    for name, rows in set_cache.items():
        if not rows:
            continue
        table[name] = {
            "samples": rows,
            "sample_count": len(rows),
            "all_matched": all(r["matched"] for r in rows),
            "wav_count": len({r["wav"] for r in rows if r["wav"]}),
        }
    return registry, counts, item_counts, table


def main():
    files = []
    for top in SCAN_ROOTS:
        for dirpath, _d, names in os.walk(os.path.join(ROOT, top)):
            for n in sorted(names):
                if n.lower().endswith(EXTS):
                    files.append(os.path.join(dirpath, n))
    if not files:
        print("no config files under %s" % ROOT)
        return 1

    corpus_index = collections.defaultdict(list)
    for f in files:
        corpus_index[os.path.basename(f).lower()].append(f)

    manifest = {}
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as fh:
            manifest = json.load(fh)

    pp = Preprocessor(ROOT, corpus_index)
    unparsed = []
    unknown_calls = []
    roots = []
    per_file = []
    for f in files:
        rel = os.path.relpath(f, ROOT).replace("\\", "/")
        before = len(unparsed)
        lines = pp.run_file(f)
        text = "\n".join(t for _n, t in lines)
        # keep a line map so we can attribute classes to files
        starts = []
        off = 0
        for n, t in lines:
            starts.append((off, n, t[:60]))
            off += len(t) + 1
        parser = ConfigParser(text, rel, unparsed, unknown_calls)
        got = parser.parse_document()
        for r in got:
            roots.append(r)
        per_file.append({
            "file": rel,
            "logical_lines": len(lines),
            "top_level_classes": len(got),
            "unparsed": len(unparsed) - before,
        })

    # re-walk with an explicit payload shape for the extractor
    def rewalk(node, path, inherited):
        full = "%s.%s" % (path, node.name) if path else node.name
        merged = dict(inherited)
        merged.update(node.props)
        payload = {
            "name": node.name,
            "path": full,
            "source": node.source,
            "depth": full.count("."),
            "parents": [p for p in node.parents if p != "__DELETE__"],
            "own_props": dict(node.props),
            "effective": merged,
            "_children": [rewalk(c, full, merged) for c in node.children],
        }
        return payload
    trees = [rewalk(r, "", {}) for r in roots]
    flat2 = []
    def collect(t):
        flat2.append(t)
        for c in t["_children"]:
            collect(c)
    for t in trees:
        collect(t)

    registry, counts, item_counts, sound_sets = collect_registry(flat2,
                                                                 manifest)

    report = {
        "summary": {
            "config_files": len(files),
            "logical_lines": sum(p["logical_lines"] for p in per_file),
            "macros_defined": len(pp.macros),
            "includes_resolved": pp.includes_resolved,
            "includes_unresolved": len(pp.includes_unresolved),
            "max_include_depth": pp.max_include_depth,
            "top_level_classes": len(roots),
            "classes_total": len(flat2),
            "unparsed_statements": len(unparsed),
            "unknown_macro_calls": len(unknown_calls),
            "by_kind": dict(counts.most_common()),
            "items_by_kind": dict(item_counts.most_common()),
            "distinct_item_names": len({c["name"] for c in registry
                                        if c["is_item"]}),
        },
        "includes_unresolved": sorted(set(pp.includes_unresolved))[:80],
        "unparsed_samples": unparsed[:40],
        "unknown_macro_calls": sorted(set(unknown_calls))[:40],
        "files": per_file,
        "sound_sets": sound_sets,
        "classes": registry,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)

    print(json.dumps(report["summary"], indent=1))
    if pp.includes_unresolved:
        print("\nunresolved includes (first 10):")
        for i in sorted(set(pp.includes_unresolved))[:10]:
            print("   %s" % i)
    if unknown_calls:
        names = sorted({c.split(": ")[-1].split("(")[0] for c in unknown_calls})
        print("\n%d statements call a macro that is never defined in the "
              "corpus (upstream breakage, skipped): %s"
              % (len(unknown_calls), ", ".join(names[:20])))
    if unparsed:
        print("\nunparsed statements (first 10 of %d):" % len(unparsed))
        for u in unparsed[:10]:
            print("   %s" % u)
    print("\nreport: %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
