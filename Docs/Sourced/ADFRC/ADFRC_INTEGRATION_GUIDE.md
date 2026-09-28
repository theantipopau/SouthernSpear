# ADF Re-Cut — Asset Integration Guide

**Audience:** any AI agent (or human) that needs to use the extracted Arma 3 *ADF Re-Cut (ADFRC)* assets inside an Unreal Engine 5 project, or in any other DCC tool.

**Root:** `E:\SouthernSpear\Content\Sourced\ADF_Extracted\`
**Upstream:** <https://github.com/IsoBones/ADFRC> · licence **APL-SA**
**Totals:** 9,522 files · 19 GB · 268 models · 2,494 textures · 614 materials · 13 rigs · 165 animation clips · 257 sounds

---

## 0. Read this first — the five rules

1. **Use `Models_UE/`, never `Models_FBX/`.** `Models_FBX` is the raw geometry pass with *no image bindings*; every material is an untextured placeholder. `Models_UE` is the same geometry re-exported with PNGs wired into each material's node tree.
2. **Everything is a static mesh.** All 268 models are Arma `ODOL` — no skinning, no armatures. There is no rigged character in this pack.
3. **Arma is metres, Unreal is centimetres.** Import with scale `0.01` or the asset arrives 100× too small.
4. **Texture channel semantics live in the filename suffix**, not in a sidecar file. Read `Textures/_ue_manifest.json` before importing anything.
5. **Animations need retargeting.** The 165 clips are bound to reconstructed BME human/vehicle rigs. They are not bound to a UE mannequin, and there is no skinned mesh here to bind to.

---

## 1. Directory map

| Path | Files | Size | What it is | Use it? |
|---|---:|---:|---|---|
| `Models_UE/` | 268 | 1.2 GB | **FBX with textures bound** | ✅ **Yes — this is the model set** |
| `Models_FBX/` | 268 | 1.2 GB | FBX, geometry only, no images | ⛔ Intermediate |
| `Models/` | 268 | 901 MB | Raw Arma `.p3d` (`ODOL`) | Reference only |
| `Textures/` | 2,494 | 9.7 GB | Decoded PNGs + `_ue_manifest.json` | ✅ Yes |
| `Materials_Text/` | 683 | 4.3 MB | Every `.rvmat` as readable text | ✅ Yes |
| `Animations/` | 509 | 91 MB | `.rtm` + decoded JSON + `Rig/` | Reference |
| `Animations_UE/` | 178 | 84 MB | **Skeleton + clip FBX** | ✅ Yes |
| `ASSET_MANIFEST.json` | 1 | 1.1 MB | **The registry — start here** | ✅ Yes |
| `Source/`, `Workshop/` | 4,842 | 5.7 GB | Untouched original PBO payloads | Only for provenance |
| `_tools/` | 27 | 2.9 MB | Every script used to build this | Re-runnable |

`Source/` is the original ADFRC source pack; `Workshop/` is the 15 unpacked Steam Workshop `.pbo` bundles. `Workshop/` contains the bulk of the unique content (weapons, vehicles, optics, gear).

---

## 2. How the three asset classes fit together

This is the part that is genuinely non-obvious, because **Arma does not store the relationship anywhere.**

```
  .p3d (geometry)                .rvmat (material)              .paa (texture)
        │                               │                             │
        │  material name string         │  stage table                │
        │  "P3D: <texture>              │  Stage1 = normal            │
        │       :: <material>.rvmat"    │  Stage5 = specular+metal    │
        ▼                               ▼                             ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  Models_UE/*.fbx  ──bound──▶  Textures/<path>/<name>_<suffix>.png   │
   └──────────────────────────────────────────────────────────────────────┘
```

### 2.1 The link is a *string*, and that is the whole trick

Arma 3 stores no object references. A mesh knows its material only because the
material's **name string** embeds the texture it wants:

```
P3D: heli_attack_03_body_indp_co.paa :: heli_attack_03_adds.rvmat
     └────────── texture ──────────┘   └────── material ──────┘
```

Across all 268 FBX this yields **1,524 material bindings** covering **444
distinct textures**. `bind_materials.py` parses that string, resolves the
texture name against `Textures/`, and infers the channel from the filename
suffix.

### 2.2 Channel semantics are encoded in the suffix

| Suffix | Count | Arma meaning | What we bind it to in UE |
|---|---:|---|---|
| `_co` | 691 | colour / diffuse | Base Color (sRGB on) |
| `_ca` | 410 | camo / albedo variant | Base Color (sRGB on) |
| `_nohq` | 410 | normal, 2-channel DXT5 | Normal Map (sRGB **off**, TC_Normalmap) |
| `_smdi` | 392 | specular+metal+dirtiness, packed | Roughness (sRGB off, TC_Masks) |
| `_as` | 331 | ambient smooth | Emissive (sRGB off, TC_Grayscale) |
| `_mc` | 7 | metallic mask | Metallic (sRGB off) |
| `_sm` | 2 | specular mask | Roughness (sRGB off) |
| `_ret` | 2 | weapon reticle | Emissive |
| *(no suffix, RGBA)* | 209 | insignia, labels, UI, decals | Base Color (sRGB on) |
| *(no suffix, greyscale)* | 1 | mask | Grayscale (sRGB off) |

Suffix matching walks **right to left**, so `foo_veh_nohq` resolves to
`nohq`, not `veh`.

### 2.3 What we could not resolve

| Case | Count | Treatment |
|---|---:|---|
| Procedural Arma material (`.rvmat` with no texture) | 96 | Synthesised Principled values from the material name (`iron_cast` → metallic 1.0; `glass` → alpha 0.25) |
| Inline flat colour in the material name, e.g. `#(argb,8,8,3)color(1.0,0.31,0.31,1.0,co)` | 76 | Parsed straight into Base Color |
| Engine-shipped texture (`a3\data_f\…`, `bis_klan`) | 2 | Neutral grey stand-in |
| Texture genuinely absent from the pack | 22 refs | Neutral grey, listed in `ASSET_MANIFEST.json → notes.unbound_textures` |

The 22 missing textures (e.g. `truck_02_kab_co`, `camonet_csat_stripe_desert_co`,
`optics_bg_square_ca`) have **no `.paa` anywhere in the source or Workshop
packs** — they are vanilla Arma content that ADFRC references but does not
ship. Those meshes render neutral grey, which is honest and visible in the log.

> **Naming trap:** filenames are case-insensitive on Windows. `Mag58.json` and
> `mag58.json` are different clips that collapse to one file. The pipeline
> disambiguates (`mag58__1.fbx`); a naive join will silently lose ~15 clips.

### 2.4 Texture verification — `texHeaders.bin`

Each addon ships a `texHeaders.bin`: BI's texture LOD dictionary (the P3D
`\0DHT` tag). It is a *second, independent* record of every texture's size,
written by the engine rather than by the PAA encoder, which makes it a usable
oracle for the PNG decode. `texheaders.py` parses it and cross-checks
everything:

| Check | Result |
|---|---|
| 12 files parse, declared record count == `.paa` name strings | 2,500 / 2,500 |
| Recorded mip offsets == the `.paa`'s own offset table | 2,500 / 2,500 |
| PNG dimensions == the `.paa` mip0 header | 2,500 / 2,500 |
| PNG format consistent with the PAA compression type | 2,500 / 2,500 |
| Completeness both ways vs the `.paa` on disk | 0 missing, 0 extra |

**Zero mismatches.** The decode is sound.

Three things the table told us that are worth knowing:

1. **The mip chain starts at mip1.** Where a chain is recorded it is
   `mip1 … mipN` — mip0's size is simply absent, so the largest recorded value
   is half the real texture size. Read the `.paa` mip0 header, not this table,
   when you want the top-level size.
2. **Chains exist for exactly the DXT1 textures.** 1,612 DXT1 textures have a
   recorded chain and all 888 DXT5 textures have none — no cross terms at all.
   That is a property of the format, not a parsing artefact.
3. **All 2,500 decoded PNGs are 8-bit RGBA**, including the 1,612 DXT1 ones.
   DXT1 carries at most 1 bit of alpha, so their alpha is binary and an RGB
   import in Unreal would be visually lossless and roughly a third cheaper in
   memory. 285 textures are non-square and 17 distinct sizes appear, up to
   4096×4096 — do not assume square or power-of-two on import.

Per-texture detail is in `_tools/texheaders_report.json`.

---

## 3. Materials — `Materials_Text/`

Arma ships materials in two forms and the pack uses both:

- **Plain text** (240 files) — readable Arma config scripts, e.g. `Source/adfrc_backpacks/data/Bullock.rvmat`
- **Binarised `\0raP`** (593 files) — the compact container
- **LZSS-compressed `\0raP`** (21 files) — a third variant used by `bma3`

`rap2txt.py` decodes all three. **683 of 684 decode** (the one failure is
`ADF_Weapons/adfrc_f1grenade/config.bin`, an unsupported value sign).

The output is an ordinary Arma config script:

```
class Stage1
{
    texture="ADF_Air\adfrc_apache\Data\heli_attack_03_adds_nohq.paa";
    uvSource="tex";
    ...
};
ambient[]={1,1,1,1};
specularPower=150;
```

Stage roles, confirmed by census: `Stage1` = normal, `Stage4` = ambient smooth,
`Stage5` = specular+metal+dirt, `Stage7` = base colour. Stage 2/3/6 are usually
inline `#(argb,…)color(…)` procedural terms.

**For Unreal:** the stage table is mostly redundant now — the FBX already has
its textures bound. Use `Materials_Text/` when you need the *parameters*
(`specularPower`, the colour terms) or when you are building materials from
scratch rather than importing the FBX.

`config.bin` files (69) decode the same way and contain the full mod config —
class hierarchies, weapon definitions, required-addon lists. They are **not**
UE assets, but they are the authoritative record of how the mod assembles
itself, and they resolve inheritance from vanilla Arma classes
(`B_Soldier_base_F`, `V_PlateCarrier1_blk`) that we record by name rather than
following.

---

## 4. Animations — the hard part

### 4.1 What was in the source

165 `.rtm` files, in two on-disk shapes:

- **BMTR v3/4/5** — per-bone **parent-relative** quat+position, optionally LZO-compressed phase block
- **RTM_0101** — per-bone **absolute** 3×4 matrices

Both are decoded to JSON under `Animations/`.

### 4.2 The problem: no skeleton exists

`.rtm` files contain a flat, ordered bone-name list and transforms. They contain
**no parent links** — Arma resolves those from a built-in BME skeleton that
ships with the game, not with the mod.

**Bone list order is not hierarchy order.** One rig stores `weapon, launcher,
rightarm, …`; another starts `spine, …`. A geometric nearest-neighbour search on
bone order produces garbage — it parented `head` to `lefthand` and `rightleg` to
`head`.

`rtm_rigs.py` therefore rebuilds the hierarchy from the **documented BME bone
naming convention** (spine chain, neck, arms with roll bones, legs, 5-digit
hands with 3 phalanges each, ~120 face bones, slots, attachments), with an
acyclic nearest-neighbour fallback for anything the rules miss. Result: **13
distinct rigs, all rooted at `pelvis`**, max depth 18–32, 231 distinct bone
names total.

The 15 residual "links over 0.95 m" are all **attachment bones** (`camera`,
`weapon`, `launcher`) which legitimately sit away from the hand or head they
hang off. That is expected, not a defect.

### 4.3 Rest pose

Frame 0 of an arbitrary clip is an *animation pose*, not a rest pose — a raised
arm reads as a 1.3 m "shoulder link". The rest pose is therefore the **mean
world position of every bone across every frame of every clip on the rig**.

### 4.4 Output

```
Animations/Rig/<rig>.json           skeleton: bones, parents, rest world, rest rotation
Animations/Rig/<rig>/<clip>.json    that clip, normalised to parent-relative locals
Animations/Rig/_rig_index.json      clip → rig map
Animations_UE/<rig>/<rig>_skeleton.fbx
Animations_UE/<rig>/<clip>.fbx      165 clips, all carrying a real AnimationStack
```

| Rig | Bones | Clips |
|---|---:|---:|
| `pelvis_spine_…_67b_0f7bb0` | 67 | 53 |
| `weapon_launcher_…_128b_1fee55` | 128 | 27 |
| `weapon_launcher_…_67b_398cd4` | 67 | 47 |
| `weapon_launcher_…_103b_6e5081` | 103 | 12 |
| *(8 more)* | 65–73 | 1–5 |

### 4.5 What this means for Unreal

The clips are **valid, correctly-parented, human-scale animation data** — but
they are bound to a BME rig, not to the UE mannequin, and this pack contains
**no skinned mesh** to attach them to. To use them you must:

1. Import `<rig>_skeleton.fbx` once, or map BME bone names onto your own skeleton.
2. Retarget each clip (BME `pelvis/spine1..3/neck1/leftuplegroll/…` has no direct UE Mannequin equivalent — build a mapping table).
3. Remember Arma animation `motion[]` is a per-clip root translation; the Blender exporter does **not** bake it into the root bone, so fast reloading/traverse clips may need the motion vector applied manually.

**Blender gotcha, if you rebuild this:** the FBX exporter silently omits the
animation stack unless `bake_anim=True`. Armature-only FBX exports, look fine,
and arrive in Unreal as static poses.

---

## 5. Importing into Unreal — the actual procedure

### 5.0 Move the folder out of `Content/`

`ADF_Extracted/` sits under `E:\SouthernSpear\Content\`, so Unreal will try to
auto-import 9.7 GB of PNGs and 2.4 GB of FBX on next editor open. Move it to a
staging path (e.g. `E:\SouthernSpear\Sourced\ADF_Extracted\`) and point the
Content Browser at it, or add an exclusion. Nothing inside is a valid UE asset
until you import it deliberately.

### 5.1 Textures

Textures first — the FBX references them by relative path.

1. Copy `Textures/` (or symlink) into your project.
2. Run, from the UE Python console:
   ```python
   import ue_apply_texture_settings
   ue_apply_texture_settings.run()
   ```
   This reads `Textures/_ue_manifest.json` and forces sRGB + compression per
   asset. **Without it, every normal map is double-gamma and every ORM map is
   treated as colour.**
3. Sanity check: `*_nohq` assets should have `sRGB = false` and
   `Compression Settings = Normalmap`.

### 5.2 Static meshes

| Setting | Value | Why |
|---|---|---|
| Import scale | **0.01** | Arma metres → UE cm |
| Skeletal Mesh | **off** | All models are static `ODOL` |
| Import Materials | on | Keeps the bound textures |
| Import Textures | on (or rely on 5.1) | — |
| Combine Meshes | off | Keeps LOD/selection separation |
| Generate Lightmap UVs | optional | Arma has no lightmap channel |

**LODs are merged.** A sampled FBX contains 3 `Geometry` records — the model and
its LODs are in one file as separate objects. Split them per-object on import
and build a **Static Mesh Editor LOD group**, or you lose the LOD chain.

### 5.3 Animations

1. Import the skeleton FBX for the rig you need, or map onto an existing skeleton.
2. Import each clip FBX as an animation-only import against that skeleton.
3. Expect to retarget — see §4.5.

### 5.4 Audio

266 `.wav` files, already decoded from Arma's two audio formats. Import as
SoundWave; channels/rate/duration for each are in
`ASSET_MANIFEST.json → sounds`.

| Source | Count | Decoded by |
|---|---:|---|
| `.wss` (the bulk of the pack) | 257 | `wss2wav.py` |
| `.ogg` (shipped alongside) | 9 | `ogg_to_wav.py` |

Every WAV keeps its source's native sample rate and channel count — the pack
mixes 8 kHz to 96 kHz, mono and stereo — so check `rate` before assuming
anything. The nine OGG-derived files carry `source: "ogg"` in the manifest plus
the originating `.ogg` path and its MD5.

**Clipping.** Lossy Vorbis decodes above 0 dBFS, which 16-bit PCM cannot hold,
so a few peaks are flattened. The manifest records the pre-clip level as
`source_peak_dbfs` and the affected fraction as `source_over_0dbfs_pct`, so you
can pull the gain back on import:

| File | Source peak | Samples over 0 dBFS |
|---|---:|---:|
| `carlgustav_shot` | +13.9 dBFS | 1.92 % |
| `carlgustav_reload` | +5.0 dBFS | 0.06 % |
| `MPP_Fast_Reload` | +2.9 dBFS | 0.10 % |

**`mag-58` is two different recordings.** It exists as both `MAG-58.wss`
(1.0 s, mono, 11 kHz — what Arma actually plays) and `mag-58.ogg` (2.4 s,
stereo, 44.1 kHz). Both are kept side by side. The manifest marks the `.wss`
version `source: "wss"` with a `name_conflicts_with_ogg` block so nobody picks
one by filename. `_tools/ogg_sounds.json` has the full per-file detail.

---

## 6. `ASSET_MANIFEST.json` — the registry

**Start here.** One file answering "what can I use, and what do I need first?"

```jsonc
{
  "summary": {
    "models_ue_fbx": 268,
    "materials_bound": 1524,
    "distinct_bound_textures": 444,
    "textures_total": 2494,
    "textures_by_channel": { "basecolour": 1140, "normal": 410, "orm_packed": 392, … },
    "materials_decoded": 614,
    "rigs": 13,
    "animation_clips": 165,
    "sounds_wav": 257
  },
  "notes": { "binding": "…", "scale": "…", "textures": "…", "rigs": "…",
             "unbound_textures": [ /* 22 names */ ] },
  "models":    [ { "fbx": "Models_UE/…", "materials": [ {texture, material} ],
                   "textures": [...] }, … ],
  "materials": [ { "material": "…", "source_rvmat": "…", "stages": [...] }, … ],
  "rigs":      [ { "rig": "…", "root": "pelvis", "bones": [...],
                   "skeleton_fbx": "…", "clip_fbx": [...] }, … ],
  "clips":     { "<source rtm json path>": { rig, frames, phase_start, … } },
  "sounds":    [ { "wav": "…", "seconds": 1.83, "channels": 1, "rate": 44100 } ]
}
```

A 30-line example an agent could run:

```python
import json
m = json.load(open("ADF_Extracted/ASSET_MANIFEST.json"))

# every model whose name mentions a weapon
for model in m["models"]:
    if "m4a5" in model["fbx"].lower():
        print(model["fbx"], model["material_count"], "textures")
        for t in model["textures"]:
            print("   ", t)

# every clip on a given rig
rig = next(r for r in m["rigs"] if r["bone_count"] == 67)
print(rig["skeleton_fbx"], len(rig["clip_fbx"]), "clips")
```

---

## 6.1 `config_registry.json` — what each item *is*

`ASSET_MANIFEST.json` says which files exist. `config_registry.json` says what
they mean: which config class owns which mesh, where a weapon's muzzle sits in
model space, which animation a weapon plays, what a magazine holds.

`_tools/config_registry.py` runs the Arma config language end to end —
comment stripping, `\` continuations, a full preprocessor (object- and
function-like macros, `##` pasting, `#x` stringification, `#include`,
`#ifdef`/`#else`/`#undef`), class-tree parsing with inheritance, and
`__EVAL()` arithmetic — then extracts the families below and cross-links them
against `ASSET_MANIFEST.json`.

```
218 config files · 73,736 logical lines · 200 macros · 43 includes resolved
9,927 classes (1,373 top level) · 0 unparsed statements
2,648 items, 1,444 distinct names (1,204 are repeat declarations — see §6.2)
```

`unparsed_statements: 0` is the number to watch: anything the parser could not
consume is counted and reported rather than silently dropped.

> **`ADFRC_CONFIG_REGISTRY.md` is the full reference for this registry** — the
> complete field-by-field schema, every extracted family with worked examples,
> the per-vehicle crew-animation table, and the maintenance constants. This
> section is the summary.

### What each class carries

```jsonc
{
  "name": "ADFRC_M4A5_556_Base",
  "path": "ADFRC_M4A5_556_Base",
  "config_class": "ADFRC_M4A5_556_Base",
  "kind": "weapon",              // see the kind table below
  "is_item": true,               // false for internals (fire modes, slots)
  "parents": ["Rifle_Base_F"],
  "source": "Source/adfrc_m4a5/M4A5.hpp",
  "attachment_points": {          // memory points, verbatim from the config
    "muzzleend": "konec hlavne", "muzzlepos": "usti hlavne",
    "cartridgepos": "nabojnicestart", "cartridgevel": "nabojniceend"
  },
  "timings": { "magazineReloadSwitchPhase": 0.48 },   // numbers, not strings
  "magazines": ["ADFRC_30Rnd_PMAG"],
  "fire_modes": ["Single", "FullAuto"],
  "linked_items": { "MuzzleSlot": { … } },            // any depth
  "weapon_slots": { "UnderBarrelSlot": { … } },
  "models":  [ { "config_path": "…", "stem": "…", "fbx": "Models_UE/…",
                 "matched": true } ],
  "animation_clips": [ { "prop": "handAnim[]", "config_path": "…\\EF88_static.rtm",
                         "clips": [ { "clip": "…json", "rig": "…", "fbx": … } ],
                         "matched": true } ],
  "sounds": [ … ], "sound_sets_used": [ … ],
  "own_properties": { /* every property this class declares itself */ }
}
```

`kind` values: `weapon` 1421, `uniform` 198, `model_proxy` 154, `vehicle` 109,
`unit` 77, `magazine` 75, `ammo` 72, `sound` 69, `item` 68, `insignia` 62,
`skeleton` 60, `sound_shader` 48, `cloudlet` 37, `soundset` 36, `glasses` 36,
`gear` 29, `patch` 28, `move` 26, `gesture` 11, `unknown` 10, `ui_template` 8,
`faction` 7.

Only 10 items are `unknown` — those derive from classes the pack never declares
(`muzzle_snds_M`, `ADFRC_MD_Green_TAGW_Rolled_Base`), so there is no chain to
walk. `unknown` 3258 in `by_kind` is the same 10 plus non-item internals.

### Cross-link coverage

| Edge | Refs | Matched to disk |
|---|---|---|
| class → FBX (`models`) | 2,673 | **1,953** (1,952 classes) |
| class → clip (`animation_clips`) | 1,267 | **1,267** — 100 % |
| class → soundset → shader → WAV | 243 | **243** — 100 % (24 distinct WAVs) |

Clip and audio coverage is total because both are closed chains inside the
pack. Model coverage is not: 720 references name a `.p3d` the pack never ships
(vanilla Arma weapons, or a mesh only present as a proxy).

### The two-hop and three-hop audio chain

A weapon never names an audio file. It names a *class*, three times over:

```
weapon.handAnim / fire mode .soundSetShot[]  →  CfgSoundSets.X
CfgSoundSets.X .soundShaders[]                →  CfgSoundShaders.Y
CfgSoundShaders.Y .samples[]                  →  "\ADF_Weapons\…\AUG_closeShot_01"
```

The last hop is a file path **with no extension**. `config_registry.py` follows
all three and matches the stem against the manifest; the resolved sets live once
in a top-level `sound_sets` table, and classes reference them by name from
`sound_sets_used` (inlining them tripled the file).

Only **6 of the 76** soundset names the pack references are declared in the
pack — the other 70 are vanilla A3 and are listed per class in
`sound_sets_unresolved` rather than guessed at.

### Vehicles and crew animation

A vehicle never names a clip either. It names a **CfgMoves state**:

```
CfgVehicles → Heli_Attack_03_base_F .driverAction = "Heli_Attack_03_pilot"
CfgMovesMaleSdr.States.Heli_Attack_03_pilot .file = "\ADF_Core\Anim\Heli_Attack_03_pilot.rtm"
```

`crew_animations` resolves that second hop and records the rtm and clip, with
the declaring scope so a turret's gunner action is distinguishable from the
driver's. This is the only vehicle→animation edge in the config: 5 items carry
one, covering 36 unique bindings of which 7 name a state the pack declares.
`known_state: false` means the state is vanilla A3
and absent from the pack (`GetInHigh`, `Heli_Attack_03_Gunner`).

### What the parser could not consume

| | Count | Note |
|---|---|---|
| Unparsed statements | **0** | — |
| Unknown macro calls | 60 | `Grip_Macro`, `circle_xx`, `circle2_xx` — never defined anywhere in the pack. Upstream breakage; each statement is skipped and listed in `unknown_macro_calls`. This is why some grips and the Gustav blast cloudlets are incomplete. |
| Unresolved includes | 4 | All `\z\aceax\addons\main\…` — external ACE, not shipped here. |
| Undecodable config | 1 | `Workshop/ADF_Weapons/adfrc_f1grenade/config.bin`, unsupported value sign |

### Four parser bugs worth knowing about

**Arma class names are case-insensitive, and the pack relies on it.** It declares
`ADFRC_Soldier_base_F` but derives `ADFRC_MD_AMCU_Soldier_Base` from
`ADFRC_Soldier_Base_F`. A case-sensitive parent walk breaks that chain silently
and the class falls out of every classification. Same for property names:
`soundSetShot[]` is spelled `soundsetshot[]`, `soundSetShot[]` and
`SoundSetShot[]` in different files.

**Forward declarations come first.** `class ADFRC_G19_Base;` appears inside
`cfgweapons` before the real definition elsewhere. A `setdefault`-style "first
parent wins" index strands the walk with no parents, so parents are *merged*
across the whole corpus.

**Classify by walking up, not by direct parent.** A weapon chains
`ADFRC_EF88_Black → ADFRC_EF88_Base → Rifle_Base_F`. Direct-parent matching
alone left 472 weapon variants as `unknown`.

**`CfgVehicles` is a mixed bag.** Arma files uniforms, backpacks and vests in it
alongside vehicles, so a config-root match alone called a plate carrier a
vehicle. Content properties (`uniformClass`, `isbackpack`, `maximumLoad`,
`vehicleClass`) are checked *first*. Doing this took unknown items from 1,989 to
10.

A related trap: `effective` (properties after inheritance) is fine for
single-valued lookups, but sweeping a subtree with it repeats every inherited
array once per descendant — that inflated sound references from 2,576 to 46,368
and the file from 11 MB to 17 MB. Subtree sweeps read **own** properties.

### Example

```python
import json
r = json.load(open("_tools/config_registry.json"))
by = {}
for c in r["classes"]:
    if c["is_item"]:
        by.setdefault(c["name"], c)

w = by["ADFRC_M4A5_556_Base"]
print(w["kind"], w["attachment_points"])
print(w["timings"], w["magazines"], w["fire_modes"])
print([m["fbx"] for m in w["models"] if m["matched"]])
print(list(w["weapon_slots"]))

# every weapon whose FBX exists
for c in r["classes"]:
    if c["is_item"] and c["kind"] == "weapon":
        hit = [m["fbx"] for m in c["models"] if m["matched"]]
        if hit:
            print(c["name"], "→", hit[0], c["timings"])
```

---

## 7. Provenance and licence — **read before shipping**

ADFRC is licensed **APL-SA** (Arma Public License). Per the Workshop page and
the pack's own `ASSETS_LICENSE.md`:

- **Open:** code, configs, textures.
- **Restricted:** the **3D models may not be extracted or reused commercially.**

The work here was done on the basis that the assets were provided directly for
the user's own game project. That does not override the upstream terms. Before
anything ships:

1. Log every asset in `Docs\LICENCE_REGISTER.md` and `Docs\ASSET_REGISTER.md`
   (required by this project's `CLAUDE.md`).
2. Record which Workshop `.pbo` each model came from — `Source/` vs
   `Workshop/ADF_Weapons/…` etc. The manifest's `pack` field gives this.
3. Treat the **geometry** as the restricted class and the **textures/configs**
   as the open class until written confirmation says otherwise.
4. `Models_UE/`, `Models_FBX/` and `Models/` are three copies of the same
   geometry. Do not re-publish all three; keep one.

---

## 8. Tooling — everything is re-runnable

`_tools/` holds every script. All are resumable (skip existing outputs) and all
take explicit paths.

| Script | Purpose |
|---|---|
| `bind_materials.py` | FBX → FBX with textures bound (channel from suffix) |
| `run_bind.sh` | Parallel driver for the above |
| `blender_models.py` | `.p3d` → FBX (A3OB), includes the degenerate-face bmesh fix |
| `rtm2json.py` | `.rtm` → JSON (BMTR v3/4/5 + RTM_0101, LZO) |
| `rtm_rigs.py` | Bone hierarchy + rest pose + local-space normalisation |
| `anim_to_fbx.py` | Rig + clips → armature + baked FBX |
| `run_anim.sh` | Parallel driver for the above |
| `texture_manifest.py` | `Textures/_ue_manifest.json` + the UE editor script |
| `rap2txt.py` | `\0raP` / LZSS-`\0raP` → readable config text |
| `texheaders.py` | `texHeaders.bin` → per-texture mip table; cross-checks every PNG |
| `ue_manifest.py` | `ASSET_MANIFEST.json` |
| `paa2png.c` | `.paa` (DXT1/3/5, LZO mips) → PNG |
| `wss2wav.py` | `.wss` → `.wav` |
| `ogg_to_wav.py` | `.ogg` → 16-bit PCM `.wav`, with level + conflict reporting |
| `config_registry.py` | The 218 `.hpp`/`.cpp`/`.cfg` files → `config_registry.json` (see §6.1) |
| `extract_pbo.py`, `extract_textures.py`, `extract_workshop_textures.py` | Stage-1 extraction |

### Two bugs worth knowing about

**Degenerate faces hang Blender.** Some ADFRC LODs contain faces with a
repeated vertex index (a self-loop, e.g. `[876, 876, 1581]`). Arma's engine
ignores these slivers; `bmesh.normal_update()` in A3OB spins forever on them, so
43 models hung. `blender_models.py` monkey-patches `P3D_LOD.pydata()` to
duplicate the offending vertex — geometry unchanged, face count preserved so
TAGG/selection indices stay valid.

**Blender 5.x action slots.** From 4.4 on, an `Action` owns *slots* and
keyframes only land in the slot that `animation_data.action_slot` points at.
Skip that assignment and the FBX exports cleanly with **no animation at all** —
indistinguishable from a correct export unless you count `AnimationStack`
records.

---

## 9. Known gaps

| Gap | Status |
|---|---|
| 22 texture references resolve to nothing (vanilla Arma content) | Neutral-grey stand-in; listed in the manifest |
| 26 `.rvmat` files reference `.tga` textures that exist nowhere in the pack | Broken upstream; no action possible |
| 37 `.uasset` files | **Solved — they are Unreal Engine 5.8 editor assets**, not an unknown format. `0x9e2a83c1` is the UE package tag; the payloads carry `++UE5+Release-5.8`, `/Script/Engine.Texture2D` / `.SoundWave`, and package paths like `/Game/Sourced/ADF/...` that map exactly onto this repo's `Content/Sourced/ADF/` (and `SouthernSpear.uproject` is `EngineAssociation 5.8`). 9 Texture2D + 28 SoundWave. They need no decoding — copy them in and they load. Content is largely redundant with the `.paa`/`.wss` set; the only genuinely new one is `exfil_co.uasset` (a UE-built 4 MB version of the helmet camo texture). |
| 1 config file fails to decode | `adfrc_f1grenade/config.bin`, unsupported value sign |
| 60 config statements use undefined macros | `Grip_Macro`, `circle_xx`, `circle2_xx` are called but never defined in the pack. Upstream breakage; the statements are skipped and listed in `config_registry.json` → `unknown_macro_calls`. Some grips and the Gustav blast cloudlets are therefore incomplete. |
| 4 includes point outside the pack | `\z\aceax\addons\main\…` (external ACE). `ADFRC_W1_ACEXT` parses without them. |
| 70 of 76 referenced soundsets are vanilla A3 | Not shipped here, so those weapon sounds do not resolve. Listed per class in `sound_sets_unresolved`. |
| 720 model references name a `.p3d` the pack does not ship | Vanilla Arma weapons, or meshes present only as a proxy. 1,953 of 2,673 refs resolve. |
| No skinned meshes | By design — the pack ships static geometry only |
| LODs merged into single FBX | Split on import, build LOD groups manually |
| Decoded PNGs sit in two different trees | 1,255 textures are at `Textures/<mod>/…` while 1,232 keep the `Textures/Workshop/<addon>/…` prefix the PBO unpack produced, and 13 match neither (6 extraction outputs kept the source extension in the name, e.g. `X.PAA.png`; 7 name a texture that lives in a different addon folder than the header table claims). Content is complete; only the path layout is inconsistent, so path-based tooling must not assume one shape. |
| `_smdi` packed channels not split | Bound whole to Roughness; split to ORM for accurate metal/rough |
| `motion[]` root translation not baked | Apply manually per clip if you need traverse/reload root motion |

---

## 10. Quick-start for an agent

```bash
cd /e/SouthernSpear/Content/Sourced/ADF_Extracted

# 1. What is available?
python -c "import json;print(json.dumps(json.load(open('ASSET_MANIFEST.json'))['summary'],indent=1))"

# 2. Find a model and everything it needs
python - <<'PY'
import json
m=json.load(open('ASSET_MANIFEST.json'))
for mo in m['models']:
    if 'm4a5' in mo['fbx'].lower():
        print(mo['fbx'])
        print('  materials:',[x['material'] for x in mo['materials']][:4])
        print('  textures :',mo['textures'][:6])
PY

# 3. Texture import settings
python -c "import json;d=json.load(open('Textures/_ue_manifest.json'));print(d['counts'])"
#    -> then run _tools/ue_apply_texture_settings.py inside Unreal

# 4. Animation rigs
python -c "import json;[print(r['rig'],r['bone_count'],r['root']) for r in json.load(open('ASSET_MANIFEST.json'))['rigs']]"

# 5. What each item IS — class, muzzle points, timings, magazines
python -c "import json;d=json.load(open('_tools/config_registry.json'));print(json.dumps(d['summary']['items_by_kind'],indent=1))"
python -c "import json;d=json.load(open('_tools/config_registry.json'));c=[x for x in d['classes'] if x['name']=='ADFRC_M4A5_556_Base' and x['is_item']][0];print(c['attachment_points'],c['timings'],c['magazines'])"
```

---

*Generated from the extraction and conversion runs against ADFRC. Every count
in this document was verified against the filesystem at the time of writing.*
