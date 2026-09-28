# ADF Re-Cut — the Config Item Registry

**What this is.** `ASSET_MANIFEST.json` answers *"which files exist?"*.
`config_registry.json` answers *"what are they?"* — which config class owns
which mesh, where a weapon's muzzle sits in model space, which animation a
weapon plays, what a magazine holds, and how a weapon's parts attach to it.

**Read this if you are** porting ADFRC content to Unreal, looking up what a
named weapon/vehicle/uniform actually is, or writing tooling that needs the
class hierarchy rather than the file listing.

**Provenance/licence warning first:** ADFRC is **APL-SA**. Code, configs and
textures are open; the **3D models may not be extracted or reused
commercially**. See §7 of `ADFRC_INTEGRATION_GUIDE.md`. Log provenance in
`Docs/LICENCE_REGISTER.md` and `ASSET_REGISTER.md` before shipping anything.

---

## 1. Quick start

```bash
cd /e/SouthernSpear/Content/Sourced/ADF_Extracted

# what does the corpus contain?
python -c "import json;print(json.dumps(json.load(open('_tools/config_registry.json'))['summary'],indent=1))"

# look up one item
python - <<'PY'
import json
r = json.load(open("_tools/config_registry.json"))
item = next(c for c in r["classes"]
            if c["name"] == "ADFRC_M4A5_556_Base" and c["is_item"])
print(item["kind"], item["attachment_points"])
print(item["timings"], item["magazines"], item["fire_modes"])
print([m["fbx"] for m in item["models"] if m["matched"]])
PY
```

Regenerate from scratch (about a second, no arguments needed):

```bash
python _tools/config_registry.py
# optional: python _tools/config_registry.py <extract-root> <out.json>
```

It is deterministic and re-runnable, and overwrites its output rather than
appending.

---

## 2. The parser

`_tools/config_registry.py` (~1,390 lines, stdlib only) runs the Arma config
language end to end. It is a real implementation, not a regex sweep.

| Stage | What it does |
|---|---|
| 1. Comment strip | `//` and `/* */`, **string-literal aware** so `"http://x"` survives |
| 2. Continuations | joins `\` line-ends, so a multi-line `#define` is one logical line |
| 3. Preprocessor | `#define` (object- **and** function-like), `##` token pasting, `#x` stringification, `#include`, `#ifdef`/`#ifndef`/`#else`/`#endif`, `#undef` |
| 4. Class parse | nested class tree with inheritance, properties, arrays; values keep raw **and** normalised forms |
| 5. Evaluate | `__EVAL(expr)` and bare arithmetic, so timings are numbers not strings |
| 6. Extract | the families in §4, cross-linked against `ASSET_MANIFEST.json` |

Include resolution is **sibling-first, then by basename across the corpus**;
max observed include depth is 2. Macros expand per logical line and continue
onto the next line while parentheses are still open.

### Verified results

```
config files          218   (154 .hpp + 26 .cpp + 38 .cfg; 93 in Source/, 125 in Workshop/)
logical lines      73,736   (Source 39,089 + Workshop 34,647)
macros defined        200
includes resolved      43   ·  unresolved 4 (external ACE)
top-level classes   1,373
classes total       9,927
unparsed statements    0   ← anything unconsumed is counted, never dropped
unknown macro calls   60
items              2,648   ·  1,444 distinct names
```

`unparsed_statements: 0` is the number to watch when changing the parser. If it
rises, something regressed — check `unparsed_samples` in the output.

---

## 3. The output schema

```
{
  "summary":              { counts, see §2 },
  "includes_unresolved":  [ "…hpp:14 -> \\z\\aceax\\…", … ],
  "unparsed_samples":     [ … ],          # empty while unparsed_statements == 0
  "unknown_macro_calls":  [ … ],
  "files":                [ { file, logical_lines, top_level_classes, unparsed } ],
  "sound_sets":           { "<name>": { samples, sample_count, all_matched, wav_count } },
  "classes":              [ … ]           # every class, flat, 9,927 entries
}
```

`classes` is a **flat list** in document order; `path` gives the nesting
(`CfgWeapons.ADFRC_EF88_Base.Single`), and `depth` the level. Every entry:

| Field | Meaning |
|---|---|
| `name`, `path`, `config_class` | identity; `config_class` is the top-level root |
| `kind` | what it is — see the table in §3.1 |
| `is_item` | `true` for a real item, `false` for an internal (§3.2) |
| `parents` | declared base classes, in declaration order |
| `source` | originating file, relative to the extract root |
| `depth` | 0 = top level |
| `property_count` | how many properties this class declares itself |
| `own_properties` | every property it declares, verbatim (normalised where numeric) |
| `attachment_points` | muzzle / cartridge / optic memory points |
| `timings` | reload and cycle timings, **numeric** |
| `magazines`, `magazine_wells`, `fire_modes` | lists of class names |
| `linked_items` | per-slot attachment rules, gathered from any depth |
| `weapon_slots` | declared slots, with `allowedSlots[]` and `mass` |
| `crew_animations` | vehicle crew bindings, resolved to rtm (§4.5) |
| `models` | `.p3d` references, cross-linked to FBX |
| `animation_clips` | `.rtm` references, cross-linked to decoded clips |
| `sounds` | direct sound references, with two-hop resolution |
| `sound_sets_used` | soundset names this class uses, by scope |
| `sound_sets_unresolved` | soundset names the pack never declares |
| `animations` | raw animation properties, before cross-linking |

### 3.1 `kind` values

Items only (2,648):

| kind | n | | kind | n |
|---|---|---|---|---|
| `weapon` | 1,421 | | `sound_shader` | 48 |
| `uniform` | 198 | | `cloudlet` | 37 |
| `model_proxy` | 154 | | `soundset` | 36 |
| `vehicle` | 109 | | `glasses` | 36 |
| `unit` | 77 | | `gear` | 29 |
| `magazine` | 75 | | `patch` | 28 |
| `ammo` | 72 | | `move` | 26 |
| `sound` | 69 | | `gesture` | 11 |
| `item` | 68 | | **`unknown`** | **10** |
| `insignia` | 62 | | `ui_template` | 8 |
| `skeleton` | 60 | | `faction` | 7 |
| `editor_subcategory` | 6 | | `vehicle_part` | 1 |

The 10 `unknown` items derive from classes the pack never declares
(`muzzle_snds_M`, `ADFRC_MD_Green_TAGW_Rolled_Base`), so there is no chain to
walk — not a parser limitation. In `summary.by_kind` the `unknown` figure is
much larger (3,258) because that histogram covers **all** 9,927 classes,
including internals. Filter on `is_item` to compare like with like.

### 3.2 `is_item` — why it matters

An **item** is a direct child of a config root (`CfgWeapons.X`) or a bare
fragment that names a parent (`X : Rifle_Base_F`). Everything nested deeper is
an *internal*: a fire mode, a sound class, a weapon slot, a CfgMoves state.

The grandparent must be a real config root. Without that test,
`ADFRC_EF88_Base.WeaponSlotsInfo`, `.Single` and `.LinkedItems` all counted as
items in their own right — 382 `LinkedItems` entries, no less.

**Always filter on `is_item` when counting.** The raw `classes` list is 9,927
long; only 2,648 are items.

---

## 4. The extracted families

Counts below are over items unless stated.

### 4.1 Attachment points — 31 items

Memory points naming a location in model space. Verbatim strings; Arma looks
them up in the ODOL skeleton, so they map to bones/attachments on import.

```jsonc
"attachment_points": {
  "muzzleend":      "konec hlavne",      // muzzle exit
  "muzzlepos":      "usti hlavne",       // muzzle origin
  "cartridgepos":   "nabojnicestart",    // cartridge ejection point
  "cartridgevel":   "nabojniceend"       // ejection velocity node
}
```

Also captured when present: `chamberpos`, `ejectionportpos`,
`grenadeEjectionPoint`, `sightPos`, `pipSightPos`, `rearSightPoint`,
`frontSightPoint`, `optic`, `dispersion`, `soundEffect`.

### 4.2 Timings — 32 items carry them; 262 classes report `reloadTime`

```jsonc
"timings": { "magazineReloadSwitchPhase": 0.48 }
```

Numeric, not strings — `__EVAL(60/215)` evaluates to `0.27906…` and
`magazineReloadSwitchPhase` is a real `float`. Also watched: `reloadTime`,
`reloadMagazineTime`, `swapDelay`, `muzzleSwapTime`, `burstFireTime`,
`soundBurstDelay`, `animationTime`, `animSpeed`, `magSize_`, `magReloadTime`.

`timings` is the **effective** (inherited) view, so 262 classes report
`reloadTime` and 464 report `magazineReloadSwitchPhase`; only 73 classes
*declare* `reloadTime` themselves. For "what did this class author?", read
`own_properties`.

**Magazine and fire-mode data** rides on the weapon, not the magazine:

```jsonc
"magazines":       ["ADFRC_30Rnd_aug_ef88"],
"magazine_wells":  ["CBA_556x45_STEYR"],
"fire_modes":      ["Single", "FullAuto", "single_medium_optics1", …]
```

`magazine_wells` is the most useful of the three: it is the **calibre**, so you
can match a magazine to a weapon without decoding the magazine's name.

### 4.3 Weapon slots and linked items — 83 / 674 items

```jsonc
"weapon_slots": {
  "CowsSlot":        { "parents": ["asdg_OpticRail1913"],
                       "allowedSlots": [901], "mass": 220 },
  "MuzzleSlot":      { … }, "UnderBarrelSlot": { … },
  "PointerSlot":     { … }, "GripodSlot":      { … }
}
```

`linked_items` is keyed by the `LinkedItems*` class name (e.g. `LinkedItemsOptic`,
`LinkedItemsUnder`) and merged from **any depth** — Arma nests these under
`WeaponSlotsInfo > MuzzleSlot`, not at the top level. The value carries every
property that class declared, so the attachment is explicit:

```jsonc
"linked_items": {
  "LinkedItemsOptic": { "item": "optic_MRCO", "slot": "CowsSlot",
                        "scope": 2, "author": "$STR_ADFRC_AUTHOR" }
}
```

### 4.4 Animation bindings — 41 items

```jsonc
"animation_clips": [
  { "prop": "handAnim[]",
    "config_path": "\\ADF_Weapons\\core\\data\\anims\\EF88_Vg_static.rtm",
    "clips": [ { "clip": "…/EF88_Vg_static.json", "rig": "spine_weapon_…", "fbx": … } ],
    "matched": true }
]
```

`handAnim[]` is the weapon's idle/handling pose — the single most useful
animation binding for a port, since it defines the weapon's grip and hand
positions. `selectionFireAnim`, `reloadAction` and `adjustWeaponAnim` are
*state names*, not paths, and are kept in `animations` un-cross-linked.

**1,267 of 1,267 rtm references match a decoded clip — 100 %.**

### 4.5 Vehicle crew animation — 5 items, 36 unique bindings

A vehicle never names a clip. It names a **CfgMoves state**:

```
CfgVehicles → Heli_Attack_03_base_F .driverAction = "Heli_Attack_03_pilot"
CfgMovesMaleSdr.States.Heli_Attack_03_pilot .file = "\ADF_Core\Anim\Heli_Attack_03_pilot.rtm"
```

```jsonc
"crew_animations": [
  { "prop": "driverAction",   "scope": "Heli_Attack_03_base_F",
    "state": "Heli_Attack_03_pilot", "known_state": true,
    "rtm": ["\\ADF_Core\\Anim\\Heli_Attack_03_pilot.rtm"] },
  { "prop": "gunnerAction",   "scope": "Turrets.MainTurret",
    "state": "Heli_Attack_03_Gunner", "known_state": false, "rtm": [] }
]
```

`scope` matters — a turret's gunner action is distinct from the driver's.
`known_state: false` means the state is **vanilla A3 and absent from the pack**
(`GetInHigh`, `Heli_Attack_03_Gunner`); the `rtm` is empty by design, not a
parse failure. Properties swept: `driverAction`, `driverInAction`,
`gunnerAction`, `gunnerInAction`, `gunnerGetIn/OutAction`, `commanderAction`,
`getInAction`, `getOutAction`, and the `cargo*` array forms.

Only **5 items** carry crew bindings, and only **7 of their 36 unique
(prop, scope, state) triples** name a state the pack declares:

| Item | Unique bindings | Resolve to an ADFRC rtm |
|---|---|---|
| `Heli_Attack_03_base_F` (Apache) | 6 | 2 — `driverAction`/`driverInAction` → `Heli_Attack_03_pilot` |
| `Plane_Transport_01_base_F` (C-130) | 11 | 5 — copilot + passenger turret actions |
| `Plane_Transport_01_infantry_base_F` | 13 | 0 (all vanilla A3 cargo/passenger states) |
| `Plane_Transport_01_vehicle_base_F` | 2 | 0 |
| `Turrets` (`vehicle_part`) | 4 | 0 |

The remaining bindings name vanilla A3 states (`GetInHigh`, `GetOutLow`,
`passenger_generic01_foldhands`, …) that ship with the base game, so a port
must source those from Arma itself or author replacements.

### 4.6 Audio — 9 items, via a three-hop chain

A weapon never names an audio file either. It names a class, three times:

```
weapon fire mode .soundSetShot[]   →  CfgSoundSets.X
CfgSoundSets.X .soundShaders[]     →  CfgSoundShaders.Y
CfgSoundShaders.Y .samples[]       →  "\ADF_Weapons\…\AUG_closeShot_01"
```

The last hop is a path **with no extension**. All three hops are followed and
the stem matched against the manifest.

```jsonc
// top-level table, stored once
"sound_sets": {
  "AUG_silencerShot_SoundSet": {
    "sample_count": 45, "wav_count": 5, "all_matched": true,
    "samples": [ { "shader": "AUG_Closure_SoundShader",
                   "sample": "\\ADF_Weapons\\…\\AUG_closure_01",
                   "wav": "Workshop/…/AUG_closure_01.wav", "matched": true }, … ] } }

// per class, by reference
"sound_sets_used": [ { "scope": "Single.SilencedSound",
                       "sound_set": "AUG_silencerShot_SoundSet",
                       "samples": 45, "wavs": [ … ] } ]
```

**243 of 243 samples resolve — 100 %**, covering 24 distinct WAVs. Only **6 of
the 76** referenced soundset names are declared in the pack; the other 70 are
vanilla A3 and appear in `sound_sets_unresolved` rather than being guessed at.

`sounds[]` on a class is the *direct* reference (e.g. `reloadMagazineSound[]`,
which does carry a path). `hitMetal = "ImpactMetalSabotBig"` is a class name
instead, and resolves via the `class Sounds` table when present.

---

## 5. Cross-link coverage

| Edge | Field | Matched |
|---|---|---|
| class → FBX | `models[].matched` | **1,953 / 2,673** (73 %) |
| class → decoded clip | `animation_clips[].matched` | **1,267 / 1,267** (100 %) |
| soundset → WAV | `sound_sets.*.all_matched` | **243 / 243** (100 %), 24 distinct WAVs |
| vehicle → rtm | `crew_animations[].known_state` | 7 of 36 unique bindings resolve to an ADFRC rtm |

Clip and audio are total because both chains close **inside** the pack. Model
coverage is not, and cannot be: 720 references name a `.p3d` the pack never
ships — vanilla Arma weapons, or meshes present only as a proxy. A `matched:
false` model reference usually means "use the vanilla A3 asset or a stand-in",
not "the extractor failed".

---

## 6. Arma config-language gotchas

These are the rules that cost the most time. Each one silently produced wrong
output rather than an error.

### 6.1 Class names are case-insensitive, and the pack relies on it

The pack declares `ADFRC_Soldier_base_F` but derives
`ADFRC_MD_AMCU_Soldier_Base` from `ADFRC_Soldier_Base_F`. A case-sensitive
parent walk breaks that chain and the class falls out of every classification
with no error. **Property names too:** `soundSetShot[]` is spelled
`soundsetshot[]`, `soundSetShot[]` and `SoundSetShot[]` in different files.
Match property names on a lowercased key.

### 6.2 Forward declarations come first, and the pack is duplicated

`class ADFRC_G19_Base;` appears inside `cfgweapons` *before* the real
definition elsewhere. A first-parent-wins index strands the walk with no
parents at all — **merge parents across the whole corpus** instead.

Relatedly, `Source/` and `Workshop/` are **not** byte-identical copies: of 25
same-basename config files, **0** are byte-identical, yet 426 item names appear
in both trees. The two trees are genuine variants, not a redundant copy — do not
deduplicate on filename. Of 2,648 items, **1,204 are repeat declarations** of
a name already seen (1,125 of them equivalent), so prefer grouping by `name`
and comparing, rather than trusting raw entry counts.

### 6.3 Classify by walking up, not by direct parent

A weapon chains `ADFRC_EF88_Black → ADFRC_EF88_Base → Rifle_Base_F`. Matching
direct parents alone left **472 weapon variants** as `unknown`.

### 6.4 `CfgVehicles` is a mixed bag

Arma files **uniforms, backpacks, vests and units** in `CfgVehicles` alongside
vehicles, so a config-root match alone calls a plate carrier a vehicle. Content
properties are checked **first**, in this order: `uniformClass`, `nakedUniform`,
`isbackpack`, `maximumLoad`, `vehicleClass`. Doing this took unknown items from
**1,989 to 10**.

### 6.5 `effective` (inherited) properties vs `own_properties`

`effective` merges a class with everything it inherits — correct for a
single-valued lookup, **wrong for a subtree sweep**. Sweeping with it repeats
every inherited array once per descendant: that inflated sound references from
2,576 to 46,368 and the output file from 11 MB to 17 MB. **Subtree sweeps must
read `own_properties`.**

### 6.6 Values that are not values

- Config integers are decimal, so a macro-generated `028` must become `28`
  before `eval`. The normalisation regex needs the lookbehind
  `(?<![\w.])0+(\d)` so it does **not** eat the `0.00001` epsilon (which must
  stay a small epsilon, not become `0.1`).
- `class X;` is a legal forward declaration, not a parse error.
- Class names may **start with a digit** (`class 50RD`).
- Arrays can nest: `samples[] = { {"path",1}, {"path",3} }` — the useful value
  is element `[0]` of each inner pair.
- One ACE-compat header contains a C++ `enum { … };` that must be skipped.

### 6.7 Macro gotchas

- `##` token pasting and function-like macros are both used and both required.
- `#include` resolves **sibling file first, then by basename across the corpus**;
  max depth observed is 2.
- **60 statements call macros that are never defined anywhere in the pack**
  (`Grip_Macro`, `circle_xx`, `circle2_xx`). This is upstream breakage, not a
  parser bug. Each is skipped and listed in `unknown_macro_calls`. Consequence:
  some grips and the Gustav blast cloudlets are incomplete — a missing grip is
  expected, not a regression.

---

## 7. Known gaps

| Gap | Status |
|---|---|
| **No magazine capacity** | The pack declares **no `capacity` property anywhere** (0 classes). `ADFRC_30Rnd_PMAG` is only ever named in a weapon's `magazines[]`. Round count must come from the name, from `magSize_` if present, or be authored by hand. |
| 60 statements use undefined macros | Upstream; see §6.7. Skipped and reported. |
| 4 includes unresolvable | All `\z\aceax\addons\main\…` — external ACE, not shipped. `ADFRC_W1_ACEXT` parses without them. |
| 1 config file undecodable | `Workshop/ADF_Weapons/adfrc_f1grenade/config.bin`, unsupported value sign (122). |
| 70 of 76 soundsets are vanilla A3 | Not shipped; listed per class in `sound_sets_unresolved`. |
| 720 model refs name an unshipped `.p3d` | Vanilla Arma content or proxy-only. |
| `handAnim` state names un-cross-linked | `selectionFireAnim` / `reloadAction` name CfgMoves states, but ADFRC declares almost no weapon-specific ones — they resolve to vanilla A3. |
| Two trees, same names | `Source/` and `Workshop/` are variants, not copies (§6.2). |

---

## 8. Maintenance notes

`config_registry.py` keeps its lookup tables at the top of the file:

| Constant | Purpose |
|---|---|
| `ATTACHMENT_POINTS` | memory-point property names |
| `ANIM_PROPS` | animation property names |
| `CREW_ACTION_PROPS` | vehicle crew-binding property names |
| `TIMING_PROPS` | timing property names |
| `MODEL_PROPS`, `SOUND_PROP_PREFIXES` | model/sound property names |
| `CONFIG_ROOTS` | top-level classes that hold items (gates `is_item`) |
| `KIND_HINTS` | config-root → kind |
| `CONTENT_HINTS` | **property → kind, checked before the config root** (§6.4) |
| `VANILLA_KIND`, `IMPLICIT_KIND` | vanilla base class → kind |
| `NAME_HINTS`, `NAME_SUFFIX_HINTS`, `NAME_CONTAINS_HINTS` | name-based fallbacks |

Adding a family means: add the property name, add a `strings_in()` sweep, and
add a counter to the `summary`. Keep the pattern — *own properties for
subtree sweeps, `effective` for single lookups* — or the output inflates.

Verification after any change:

```bash
python _tools/config_registry.py
# expect: unparsed_statements 0
# then re-check items_by_kind.unknown is still low, and
# animation_clips / sound_sets coverage are still 100 %
```

---

## 9. Related documents

| Document | Covers |
|---|---|
| `ADFRC_INTEGRATION_GUIDE.md` | The full integration story: directory map, asset classes, materials, animations, Unreal import procedure, licence, tooling, gaps. §6.1 summarises this registry. |
| `README.md` | Totals and layout at a glance |
| `ASSET_MANIFEST.json` | The file-level registry (models, textures, materials, rigs, clips, sounds) |
| `_tools/config_registry.py` | The parser; §8 lists the tables you edit to extend it |
| `_tools/` | Every script, all re-runnable and resumable |

---

*Every count in this document was read back out of `config_registry.json` at
the time of writing, not estimated.*
