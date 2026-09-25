# ASSET NAMING STANDARDS — Southern Spear

**Document ID:** `Docs/ASSET_NAMING_STANDARDS.md`
**Status:** Baseline — Phase 0
**Last updated:** 2026-09-26

---

## 1. Conventions

| Element | Convention | Example |
|---|---|---|
| Prefix | `SS_` | `SS_WPN_AKServiceRifle` |
| Type token | 2–4 letter code | `WPN`, `CHR`, `ANM`, `SND`, `MFX`, `UI_`, `MAP`, `DF`, `DT` |
| Separator | `_` | `SS_WPN_AKServiceRifle` |
| Words | PascalCase within a token | `SS_WPN_ServiceRifle` |
| Variants | Suffix with a number | `SS_WPN_ServiceRifle_01` |

**Always `SS_` first.** This makes every Southern Spear asset greppable, and makes it trivial to audit for an asset that arrived without a register entry.

---

## 2. Type Codes

| Code | Category | Example |
|---|---|---|
| `CORE` | Shared / core | `SS_CORE_Material_MulticamOriginal` |
| `CHR` | Characters | `SS_CHR_Helmet_01` |
| `WPN` | Weapons | `SS_WPN_ServiceRifle_01` |
| `EQP` | Equipment | `SS_EQP_FieldDressing_01` |
| `ANM` | Animations | `SS_ANM_Idle_Prone_01` |
| `SND` | Audio | `SS_SND_GunfireExterior_01` |
| `MFX` | Niagara / VFX | `SS_MFX_MuzzleFlash_01` |
| `UI` | Interface | `SS_UI_W_Badge_Medic` |
| `MAP` | Maps | `SS_MAP_DryRiver_01` |
| `TRN` | Training | `SS_TRN_Range_01` |
| `DF` | Data asset | `SS_DF_Weapon_AKServiceRifle` |
| `DT` | Data table | `SS_DT_ProgressionCurve` |
| `DEV` | Developer-only | `SS_DEV_DebugHUD` |

---

## 3. Folder Rule

**The asset name repeats the folder path.** This is the single strongest anti-collision convention in UE and makes a moved asset obvious.

```
Content/SouthernSpear/Weapons/Rifles/Service/
    SS_WPN_ServiceRifle_01.uasset        <-- Weapons/Rifles/Service -> WPN_ServiceRifle
```

A mismatch between the asset name and its path is a review rejection, because it is the mechanism by which duplicate copies of the same asset appear in a project.

---

## 4. Suffix Conventions

| Suffix | Use |
|---|---|
| `_01`, `_02` | Iterations / variants |
| `_SM`, `_MD`, `_LG` | Skeletal mesh LODs |
| `_MF` | Material function |
| `_MI` | Material instance |
| `_MAT` | Material |
| `_T` | Texture |
| `_N` | Normal map |
| `_R` | Roughness |
| `_M` | Metallic |
| `_AO` | Ambient occlusion |
| `_D` | Decal |
| `_BP` | Blueprint |
| `_DA` | Data asset |
| `_DT` | Data table |
| `_FL` | Flow material |
| `_C` | Curve |
| `_P` | Physics asset |

---

## 5. Blueprint Conventions

- **One concept per Blueprint.** A Blueprint that is "the whole character" is a review rejection (brief requirement: no monolithic character/controller/gamemode/UI Blueprint).
- **Authoring Blueprints live in the owning plugin's content folder**, not loose in `Content/`.
- **C++ owns behaviour; Blueprints configure.** A Blueprint must never be the authoritative implementation of damage, scoring or progression.
- Common prefixes: `BP_` (blueprint), `WBP_` (widget blueprint), `BP_SS_` (Southern Spear authored).

---

## 6. Vendor Assets

Third-party content is **segregated and never renamed**:

```
Content/SouthernSpear/Vendor/<Publisher>/<PackName>/...
```

- **Never** reorganise vendor content destructively. Reorganisation breaks the ability to verify against the original pack, which is exactly what a licence audit needs.
- Renaming a vendor asset breaks the link to its licence record. Leave vendor names alone.
- Every vendor asset is registered in `LICENCE_REGISTER.md` with publisher, source and licence class.

---

## 7. Placeholder Naming

Placeholders are **visibly** placeholders and are named so:

```
SS_PLACEHOLDER_WPN_ServiceRifle_01
```

The `PLACEHOLDER` token means:
- The asset is not final.
- It does not ship.
- CI can count remaining placeholders for the release gate (CP-10).

---

## 8. Blender Source Conventions

Blender files follow the same naming, with the DCC suffix:

```
SS_WPN_ServiceRifle_01_HI.blend        <-- high poly (authoring)
SS_WPN_ServiceRifle_01_LO.blend        <-- low poly (game)
SS_WPN_ServiceRifle_01_UV.blend        <-- UV layout / bake
```

Standards (from `TECHNICAL_DESIGN_DOCUMENT.md` §12.2):
- Metric units · +Y forward, +Z up
- Transforms applied
- Non-destructive modifiers where practical
- UV sets · texture baking · collision meshes · LODs
- **Source `.blend` retained in Git LFS** — the FBX is a derivative, not the source
- Export presets documented in `Tools/Blender/`

Blender 5.2.2 LTS. Not on `PATH` — use `Tools/Blender/venv.ps1` or the absolute path.

---

## 9. Data Asset Naming

```
SS_DF_Weapon_AKServiceRifle           <-- Data asset
SS_DT_ProgressionCurve                <-- Data table
SS_DT_GameplayTags                    <-- Gameplay tags
SS_DF_Role_Medic
SS_DF_Rank_Sergeant
SS_DF_Layer_DryRiver_ObjectiveAssault_Day
SS_DF_TrainingModule_Induction
SS_DF_Commendation_FirstResponder
```

Data assets are named by the **concept they define**, not by the file format.

---

## 10. Gameplay Tags

```
SS.Team.Friendly
SS.Team.Opposing
SS.Weapon.Rifle
SS.Weapon.Support
SS.Role.Rifleman
SS.Role.Medic
SS.Qualification.Induction
SS.Qualification.Weapons
SS.Qualification.SupportWeapons
SS.Qualification.FieldSkills
SS.Qualification.Leadership
SS.Damage.Head
SS.Damage.Torso
SS.Damage.Limb
SS.Stance.Stand
SS.Stance.Crouch
SS.Stance.Prone
```

Tags are hierarchical, `SS.`-rooted, and never reused with a different meaning. A tag that has shipped is **frozen**.

---

## 11. Automated Checks

CI verifies:
- [ ] Every `.uasset`/`.umap` in `Content/SouthernSpear/` starts with `SS_` (exceptions: `Vendor/` — untouched)
- [ ] Every asset has a matching `ASSET_REGISTER.md` row
- [ ] Every third-party asset has a `LICENCE_REGISTER.md` row
- [ ] Placeholder count is reported; **non-zero blocks a release build**
- [ ] No `Lyra` or `Shooter` prefix on any new `SS_`-scoped type
