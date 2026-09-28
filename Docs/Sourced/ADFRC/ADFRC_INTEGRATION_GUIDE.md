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
| `Source/`, `Workshop/` | 4,833 | 5.7 GB | Untouched original PBO payloads | Only for provenance |
| `_tools/` | 16 | 452 KB | Every script used to build this | Re-runnable |

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

257 `.wav` files, already decoded from Arma `.wss`. Import as SoundWave; the
channels/rate/duration for each are in `ASSET_MANIFEST.json → sounds`.

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
| `ue_manifest.py` | `ASSET_MANIFEST.json` |
| `paa2png.c` | `.paa` (DXT1/3/5, LZO mips) → PNG |
| `wss2wav.py` | `.wss` → `.wav` |
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
| 37 `.uasset` files (magic `0x9e2a83c1`) | Undecoded — not WSS, PAA, LZSS, zlib, lzma, bz2, or Ogg. Mostly audio-named; a few look like textures. Several have `.ogg` twins already extracted. |
| 1 config file fails to decode | `adfrc_f1grenade/config.bin`, unsupported value sign |
| No skinned meshes | By design — the pack ships static geometry only |
| LODs merged into single FBX | Split on import, build LOD groups manually |
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
```

---

*Generated from the extraction and conversion runs against ADFRC. Every count
in this document was verified against the filesystem at the time of writing.*
