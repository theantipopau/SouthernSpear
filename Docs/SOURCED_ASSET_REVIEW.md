# Sourced Asset Review — `Content/Sourced/` (historical review; current disposition 2026-10-01)

> **Current producer direction (ADR-028/035, reaffirmed 2026-10-01):** assets acquired or held for Southern Spear are cleared for use in this free-to-play game, including acquired content whose seller terms/metadata are missing or more restrictive. This project-specific direction supersedes the per-item `BLOCKED`, `REJECT`, “commercial use” and “needs licence” assessments below **when those assessments were based only on licensing/provenance**. It does not claim a universal marketplace licence, authorize redistribution of raw source packs, approve an item as imported/game-used, reverse the specific Electric Dreams decline, or allow ripped commercial-game assets. Preserve source, credit and attribution details and the no-endorsement/content-ethics rules. The remaining rows are a dated intake record, not the operative clearance register; see `LICENCE_REGISTER.md` and `ASSET_REGISTER.md`.

A drop of about 2.4 GB was originally added to `Content/Sourced/`; the dated 2026-09-27 inventory measured 2,895 files (~4.62 GB). `Content/Sourced/` remains a segregated source/review area, not a game-used asset manifest. The two CC BY scans Split Point and Bingie Bingie were copied unchanged into the credited Vendor source folder (`Content/SouthernSpear/Vendor/SAVollgger/`) for import review; the later inventory still does not identify them as imported into Unreal or placed in a map. Separate ADFRC-derived project assets are registered under `ASSET_REGISTER.md` §4.9g; their presence does not mean the raw extraction was imported wholesale.

The 2026-09-27 scan of the original mixed drop found one licence-related file: an author credit in `M4_alt/source/Archive.zip` (`read me.txt`: author name, e-mail and ArtStation link); no other licence texts were found in that scan. This historical observation does not describe the separate ADFRC trees or later producer clearance.

## Historical per-item assessment (2026-09-27; read with the current producer-direction notice above)

| Folder | What it is | Verdict | Why |
|---|---|---|---|
| `F89Minimi/source/call-of-duty-mwiii-2023-bruen-mk9.zip`, `Bruen Mk9.*` | Model extracted from *Call of Duty: Modern Warfare III* | **REJECT — delete** | Ripped commercial game asset (Activision). Never redistributable. |
| `F88/AUG-CS2` | Model extracted from *Counter-Strike 2* | **REJECT — delete** | Ripped commercial game asset (Valve). |
| `F88/OldF88 with animations` | "AugA1 Assault Rifle – Animated" FBX of a real rifle | **BLOCKED** | Unknown source and licence. It is also a replica of a real weapon: ADR-016 needs original A-series designs, not real ones. Reference only. |
| `HK416` | High-poly replica of a real manufacturer's rifle | **BLOCKED** | Unknown licence. Manufacturer likeness and trade dress (the rules forbid manufacturer marks and CAD). Reference only. |
| `AK47` (`AKM.fbx`), `M4_main`, `M4_alt` | Replicas of real rifles | **BLOCKED** | No licence (M4_alt has an author credit but no terms). Real-weapon replicas. Reference only unless the author grants a licence *and* the model is changed into an original design. |
| `Insurgent` (`Maga.fbx` + gear textures) | Character labelled "insurgent" | **BLOCKED** | Unknown licence. The "insurgent" framing contradicts ADR-016 (MAF is a conventional force, never insurgents). |
| `Soldier1` (`model.glb`), `Soldier2` (`Mark_1.zip`) | Soldier characters | **BLOCKED — needs provenance** | Unknown source and licence. Must also be checked for real insignia, flags and camouflage patterns. |
| `Helmet` (`Untitled.glb`, texture named `flipy_…`) | Helmet, likely AI- or scan-generated | **BLOCKED — needs provenance** | Unknown generator and terms. |
| `Gloves` (`Hands.fbx`, PBR set), `Grenades` | Gear | **BLOCKED — needs provenance** | Unknown source and licence. Could be usable if the licence permits. |
| `Environmental/bingie-bingie`, `Environmental/splitpoint-victoria` | Sketchfab photogrammetry scans of Australian places | **CLEARED / SOURCE STAGED** | Sketchfab pages confirm CC BY 4.0; exact asset/source/author and attribution records: L-0013/L-0014 and `ASSET_REGISTER.md`. Original OBJ/MTL/JPEG files copied unchanged into `Content/SouthernSpear/Vendor/SAVollgger/`. Not yet UE-imported or game-ready. |
| `Environmental/rossriver-nt` | Sketchfab scan of Ross River, NT | **CLEARED / NOT STAGED** | CC BY 4.0 confirmed at the matching Sketchfab model page; see L-0015. Import/adaptation awaits asset-register row and separate staging request. |
| `Environmental/cape-liptrap` | Sketchfab scan | **REJECT** | CC BY-NC-ND; commercial and derivative restrictions disallow project use. |
| `Environmental/pettybeach` | Unknown scan | **BLOCKED** | No verifiable source page or licence yet. |
| `Environmental/forest` | Fir-forest FBX plus images scraped from the web (hash filenames, `carve.photos` background removal) | **REJECT textures / BLOCKED model** | Scraped images have unknown rights. Fir forest is also not an Australian biome. |

> **Use limits:** ADR-021 allows licensed third-party environment assets as dressing, while keeping map layouts original. The two staged scans are high-density photogrammetry; treat them as review/reference assets until scale, import/materials, topology, LOD/Nanite, collision, and runtime performance are checked. The map layout must not be taken from either scan.

## Historical handling guidance (2026-09-27; permission holds superseded where based only on source terms)

- **Visual reference.** For items that are still blocked, unknown, or prohibited, use visual inspection only; do not copy or reuse their geometry, UVs, or textures.
- **Licensed assets.** Items whose exact source and terms are confirmed as commercially usable may be staged/imported under `Content/SouthernSpear/Vendor/<Publisher>/<Pack>/` with their original filenames, attribution and licence terms preserved. The Split Point and Bingie Bingie sources above are staged this way; no adapted or game-ready derivative has been made.
- **Adaptation.** A cleared item that ADR-021 permits to be adapted gets both register entries before use. Adaptation must fit the fictional setting (for weapons, reshape into original A-series designs; remove real marks; avoid real camouflage patterns). Do not destructively rename/reorganize vendor originals; track every derivative separately.

## Historical recommendations (2026-09-27; current status clarified)

1. **Still standing:** keep the two ripped commercial-game assets (`F89Minimi/…bruen-mk9*`, `F88/AUG-CS2`) excluded under L-0007/L-0008. The producer's acquired-asset clearance does not include game rips.
2. The two staged OBJ scans were candidates for a temporary Unreal technical review (scale, texture binding, normals, performance, LOD/Nanite). Their current status remains source-staged, with no later Unreal import/game placement identified in this review; inspection is technical diligence, not a licence gate.
3. Page URLs and source terms for Petty Beach, gloves, helmet, grenades and soldiers were requested for provenance/credit records. Missing source-page data is not a project-use hold under ADR-035; no specific current game use is asserted here.
4. Ross River is recorded as CC BY 4.0 under L-0015. The older “stage only after a separate request” phrasing is not a permission requirement; project selection, provenance registration, and any applicable credit remain separate from F2P clearance.

## Historical addendum — `Content/Sourced/ADF/` (ADFRC addons; 2026-09-27 inventory)

> This subsection's “not usable,” licensing and no-import conclusions are historical. ADR-035 and the producer's ADFRC team permission recorded in L-0021 clear acquired ADFRC assets for Southern Spear's F2P project use. Retain the format/provenance findings and raw-source handling distinction; do not treat the older restrictions as current permission holds.

About 1,681 files (43 MB) copied from the ADFRC Arma 3 repository: 1,256 `.paa` textures, 240 `.rvmat`
materials, configs, `.wss`/`.wav` sounds and `.rtm` animations. There are **0 models** (no `.p3d`, `.fbx` or `.obj`).
**Historical verdict: not usable (superseded for project use by ADR-035).**

- Rights: APL-SA applies to material released under its terms (Arma-only, non-commercial, share-alike). ADFRC's `ASSETS_LICENSE.md` and `DEV_LICENSE.md` impose additional restrictions on protected legacy models and define contributor/maintainer rights; the developer agreement is not an end-user licence and grants no Southern Spear reuse rights.
- Sampled configs name multiple contributors (including Brucey, Exer, Growlor and Louetta). Those metadata strings do not establish who owns or can license each associated asset; `DEV_LICENSE.md` states contributors retain ownership of their contributions.
- The content is ADF-branded (EF88/F88/F89/Minimi/HK/SR25, AMCU/Auscam camouflage). That was recorded as a historical art/policy objection; ADR-035 later permits producer-directed real names, marks and camouflage in this F2P project, subject to no-endorsement, attribution and content-ethics rules.
- A specific item may be relicensed only by its verified rights holder(s), with upstream and third-party rights accounted for; a producer sole-author statement alone does not clear collaborative or upstream work. Arma-format textures and animations would still need rework.

The `Content/Sourced/ADF/` folder stays git-ignored, and none of its content was imported. Its earlier inventory of zero `.p3d` models applies only to that folder; it does not describe the separate expanded extraction below.

## Historical addendum — `Content/Sourced/ADF_Extracted/` (ADF Re-Cut expansion; 2026-09-27 inventory)

> The extraction details and upstream text below document what was observed at the time. Any blanket conclusion that the ADFRC tree cannot be used in Southern Spear because upstream terms are non-commercial/Arma-only is superseded by the project-specific producer clearance and team permission in ADR-035/L-0021. The tree's raw-source quarantine/redistribution handling remains distinct from permission to use acquired assets in the game.

This is a distinct, expanded ADFRC Arma-content tree. It has since grown and now carries its own `README.md` and `_tools/` (converter sources). Measured inventory is **7,928 files / ~17 GB** (536 `.p3d`, 2,489 `.png`, 2,500 `.paa`, 330 `.rtm`, 257 `.wss`/`.wav`, 854 `.rvmat`, 37 `.uasset`), against 7,748 files claimed in its README. The README documents the two acquisition sources below, which corrects the earlier note that the acquisition path was undocumented. No per-item licence grant ships with the files. Sampled source configs identify an ADF Re-Cut / ADFRC content family, but do not establish the provenance or rights for every extracted file. This review is metadata-level only: model, texture and animation binaries were not opened, previewed, imported or converted.

### Provenance as documented by the tree's own README

The extraction's `README.md` records two sources, both dated 2026-09-27:

1. **Source pack** — `Content/Sourced/ADF`, the ADFRC config/source distribution. Its 1,256 `.paa` files were Git LFS pointer stubs; real image data was fetched from the repository's LFS and decoded to PNG.
2. **Workshop mod** — the local Arma 3 install's `!Workshop\@ADF Re-Cut [Beta]\addons` folder (15 `.pbo` archives, 5.8 GB), unpacked in full.

Source 2 is decisive for the model question. It is the **binarised Workshop release**, which is exactly the channel ADFRC's `ASSETS_LICENSE.md` and `DEV_LICENSE.md` §2.4 restrict: end users may use the mod for personal, non-commercial purposes and may **not** extract, repack or redistribute its models. Every `.p3d` in `Models/` came from there, because the README correctly notes the GitHub repository ships no models at all.

The README itself states that the 3D models "may not be extracted, reused in other projects, or used commercially" and asks that the model clause be verified before importing anything. It also records a claim that the assets were provided for this game. That claim is a producer-side statement, not a grant from the rights holders, and it does not displace the terms above.

### Inventory observed (representative, not exhaustive)

- Top-level folders: `Animations/`, `Models/`, `Source/`, `Textures/`, `Workshop/`.
- `Models/ADF_Weapons/adfrc_ef88/` contains `ADFRC_EF88.p3d`, `ADFRC_EF88C.p3d`, and `ADFRC_EF88_SL40.p3d`; `Models/ADF_Weapons/adfrc_m4a5/` contains seven named M4A5 variants. Other directories include `adfrc_f88`, `adfrc_f88sa1`, `adfrc_f88sa2`, `adfrc_minimi`, `adfrc_hk416`, `adfrc_hk417`, `adfrc_SR25`, and other ADFRC weapon/gear categories.
- `Source/adfrc_ef88/` and `Source/adfrc_m4a5/` contain Arma `config.cpp`, model/config headers and `model.cfg`; sampled configs name authors including Brucey and reference Arma-specific skeletons, sound sets and file paths. EF88 reload folders contain `.rtm` gesture files; the broader `Animations/` tree also has source/workshop groupings.
- `Textures/` includes ADFRC-named texture sets; the EF88 tree has PNG color/normal/material maps. The `Workshop/ADF_Weapons/` subtree includes packaged `config.bin`/`texHeaders.bin`, `.p3d` files and asset categories. These formats and paths are not Unreal-ready and do not establish permission to convert them.

### Licence and provenance check

The public ADF Re-Cut Workshop page identifies item **2971219389** and states that ADF Re-Cut is under APL-SA with additional restrictions on original 3D models. It explicitly says not to extract, repack or reuse the team's models in other projects and that commercial use is not permitted. The linked ADFRC repository separates rights by asset type: `LICENSE.md` applies APL-SA to code/configs/scripts/textures; `ASSETS_LICENSE.md` describes protected legacy models, open-source models from other Arma mods, and models released under APL-SA. It says protected legacy models may not be extracted from the binarised Workshop release, modified, used for derivatives, redistributed separately or used in other media; permission to relicense those requires written agreement from the original creator. `DEV_LICENSE.md` confirms contributor ownership is retained. The official APL-SA text limits the grant to non-commercial, Arma-only purposes and requires share-alike for adaptations.

Sources checked 2026-09-27:

- ADF Re-Cut Workshop item 2971219389: https://steamcommunity.com/sharedfiles/filedetails/?id=2971219389
- ADFRC licence: https://github.com/IsoBones/ADFRC/blob/main/LICENSE.md
- ADFRC model-specific asset licence: https://github.com/IsoBones/ADFRC/blob/main/ASSETS_LICENSE.md
- ADFRC developer agreement: https://github.com/IsoBones/ADFRC/blob/main/DEV_LICENSE.md
- ADFRC model credits: https://github.com/IsoBones/ADFRC/blob/main/MODEL_CREDITS.md
- Official APL-SA terms: https://www.bohemia.net/en/licenses/arma-public-license-share-alike

**Historical verdict (superseded for project use): quarantine — no Southern Spear use.** The producer's later ADR-035 direction and ADFRC team grant recorded under L-0021 clear acquired ADFRC assets for Southern Spear's F2P game, including converted/derived project work; the older prohibition based on APL-SA/non-commercial/Arma-only terms is not an operative project-use hold. Keep the raw extraction segregated and do not redistribute it as a source pack. ADFRC-related source files, existing derivatives and current Game Feature usage are distinct states: import/adaptation must still be deliberate, registered and technically validated, and neither quarantine nor producer clearance by itself establishes game use. Do not infer individual contributor attribution from a class name; preserve the available source/team credits.

### Cross-reference to existing Southern Spear weapon intake

- `adfrc_ef88` names a real EF88-family weapon; it is distinct from the independent A88 source under `Art/Weapons/A88/New/` (L-0017 / R-21). Project clearance and asset identity are separate questions; see the current register entries.
- `adfrc_m4a5` names a real M4A5/AU family; it is distinct from `Art/Weapons/C4A1/` (R-22). Do not conflate their source paths or provenance.
- Other ADFRC-named models are source records, not automatic substitutes for A-series or MAF assets. Any selected adaptation remains an individual asset/use decision and should be registered; the producer's F2P clearance applies to project use.

### Player bodies in the extraction; dated conversion attempt and later output status

**No player/character body models exist in this extraction.** `Workshop/ADF_Units` contains **0 `.p3d`** and 13 `.paa`; the units pack ships only binarised configuration headers (`CDO/`, `RAR/`, `SASR/Groups.hpp`, `Infantry.hpp`, `TAG.hpp`) that configure vanilla Arma soldier bodies. There is no ADFRC character mesh to import.

What the tree does contain is **56 player-worn gear meshes** across `Models/ADF_Gear` and `Models/ADF_Gear_2`: helmets (`adfrc_pasgt`, `adfrc_teamwendy`, `Opscore_*`, `Brucey_exfil`, `exfil`, `brh`, `boonie`), facewear/balaclavas, NVGs (`pvs_optic`, `psq36_up/down`), field dress, a **Crye G3** uniform, plate carriers (`JPC_Base`, `Peacekeeper_RAR/SOCOM`, `vest_aircrew`), backpacks, and TBAS T2/T5 role vests (`tbas_T2_Rifleman*` etc.). These attach to a body rather than being one, and some carry real manufacturer/service identities (for example Crye Precision, Ops-Core, PASGT and Team Wendy). This is provenance/context, not a current prohibition: ADR-035 accepts producer-directed acquired real names and marks in the F2P project; maintain no-endorsement and credit practices.

**Historical conversion attempt (2026-09-27):** `Models_FBX/` in the source tree held **no model files** at that snapshot—only empty per-category directories and `_convert_log.txt`. The later project audit records 179 geometry-verified `.blend` outputs under `Art/ADFRC_BLEND/` and MLOD outputs under `Art/ADFRC_MLOD/` (L-0021). These working-library conversions are distinct from the historical empty `Models_FBX/` folder and do not mean the raw source tree was imported wholesale. The original failed-attempt log recorded:

```
P3D_Error: P3D - Invalid MLOD signature: b'ODOL'
```

The Arma 3 Object Builder addon used in that attempt reads the newer `MLOD` signature and rejected the sampled `ODOL` models. The log showed only three attempts (a weapon grip, a backpack, an ASLAV vehicle) before the run stopped. That is the observed state of that tool attempt, not the current conversion status. The README's suggested route required a different ODOL-capable path, which was subsequently used; see L-0021 for current working-library outputs and §4.9g of `ASSET_REGISTER.md` for separately registered game assets. Producer clearance governs project use, while conversion/import/runtime use remain distinct states.

### Operational hazard: 17 GB of loose assets inside `Content/`

`Content/Sourced/ADF_Extracted/` now holds ~10 GB of PNGs plus 37 `.uasset` files and the rest of the 17 GB tree **inside the Unreal content root**. The tree's own README warns that the editor will try to auto-import roughly 2,484 PNGs on next open. That risks a very long editor start and unwanted derived `.uasset` writes inside a git-ignored source folder. Tracked as **R-25**; the safe fix is to move the tree outside `Content/` (it is git-ignored by path either way) before the editor is next opened.

This addendum's extraction inventory is not a record of the entire project asset state: separately registered ADFRC-derived assets (including the AUG audio and character/weapon-related assets) exist in project/Game Feature paths. The raw extraction itself remains a segregated source tree and is not asserted here as wholesale imported or game-ready. The historical conversion/import observations above describe their dated tool state only.

## Addendum 2026-09-27 — Sketchfab licence lookup (ADR-021)

| Item | Sketchfab page | Licence | Result |
|---|---|---|---|
| Split Point, VIC | Stefan A Vollgger (`SAVollgger`), d95f3ad4… | CC BY 4.0 | **Cleared and source staged unchanged** (L-0013, ENV-001) |
| Bingie Bingie, NSW | Stefan A Vollgger (`SAVollgger`), b3cdf865… | CC BY 4.0 | **Cleared and source staged unchanged** (L-0014, ENV-002) |
| Ross River, NT | Jack M Simmons (`jack.simmons`), baeea992… | CC BY 4.0 | **Cleared, not staged** (L-0015; local untitled.zip matches page title and scan density) |
| Cape Liptrap, VIC | SAVollgger, 5b91377e… | CC-BY-NC-ND observed in the historical source lookup | Historical rejection based on source terms; producer ADR-035 later clears acquired/held assets for this project's F2P use. Preserve source terms/attribution and distinguish project clearance from universal licence rights. |
| Petty Beach (`Mission_00022…`) | not found by search | ? | Needs the page URL |
| Gloves, helmet, grenades, soldiers, insurgent, M4/AK | not identifiable by file name | ? | Need the page URLs |
