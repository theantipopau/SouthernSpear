# Sourced Asset Review — `Content/Sourced/` (2026-09-26)

A drop of about 2.4 GB (286 files) was added to `Content/Sourced/`. This review follows the
non-negotiable content rules (ADR-016, ADR-020, `ASSET_REGISTER.md`, `LICENCE_REGISTER.md`): nothing is
imported until its licence is recorded. **No file from this drop has been imported, and none has been
committed.** `Content/Sourced/` is git-ignored, so it cannot reach either repository by accident.

The only licence-related file in the whole drop is an author credit in `M4_alt/source/Archive.zip`
(`read me.txt`: author name, e-mail and ArtStation link). There are no licence texts anywhere else.

## Verdicts

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
| `Environmental/*` (Bingie Bingie, Cape Liptrap, Petty Beach, Ross River NT, Split Point VIC) | Photogrammetry scans of real Australian places, some named "Sketchfab" | **PROMISING — needs licence** | Sketchfab scans are often CC-BY or CC0, which would be usable with attribution. The Sketchfab page URL and licence are needed for each one. |
| `Environmental/forest` | Fir-forest FBX plus images scraped from the web (hash filenames, `carve.photos` background removal) | **REJECT textures / BLOCKED model** | Scraped images have unknown rights. Fir forest is also not an Australian biome. |

> **Note on the environment scans:** ADR-013 decided that maps are built original and third-party
> environments are not used. Even with a clean CC licence, using these scans in the game needs a new
> ADR superseding ADR-013 for look-development or terrain reference. As visual reference they are fine now.

## What *is* allowed now

- **Visual reference.** Looking at these, or at any photo, for proportions, silhouette and mood while
  building *original* models in Blender (ADR-020) is fine. Their geometry, UVs and textures must not be
  copied, traced or reused.
- **Clearing an item.** Give the source URL and licence for an item. If the terms allow commercial use and
  modification, it gets `ASSET_REGISTER.md` and `LICENCE_REGISTER.md` entries. It is then adapted:
  - renamed to fictional A-series or CDS/MAF names;
  - stripped of real markings;
  - recoloured away from Multicam, Auscam or other real patterns.

## Recommended actions (producer)

1. Delete the two game rips (`F89Minimi/…bruen-mk9*`, `F88/AUG-CS2`). Keeping them on disk inside the
   project is itself a risk.
2. For the environment scans, send the Sketchfab page URL for each one. They are the most useful items in
   the drop: real Australian terrain for Dry River look-development.
3. For the gloves, helmet, grenades and soldiers, send the source URL and licence, or treat them as
   reference only.

## Addendum 2026-09-27 — `Content/Sourced/ADF/` (ADFRC addons)

About 1,681 files (43 MB) copied from the ADFRC Arma 3 repository: 1,256 `.paa` textures, 240 `.rvmat`
materials, configs, `.wss`/`.wav` sounds and `.rtm` animations. There are **0 models** (no `.p3d`, `.fbx` or `.obj`).
**Verdict: not usable.**

- Licence: APL-SA (Arma games only, non-commercial, share-alike), or the ADFRC Developer Licence for
  protected legacy work. Neither permits use in an Unreal game.
- Configs name other authors (Brucey, Exer, Growlor, Louetta), whose work is theirs alone (DEV_LICENSE 1.1).
- The content is ADF-branded (EF88/F88/F89/Minimi/HK/SR25, AMCU/Auscam camouflage), which ADR-016 forbids anyway.
- Anything the producer personally authored can be relicensed to Southern Spear with a written
  sole-author statement. Arma-format textures and animations would still need rework.

The folder stays git-ignored, and nothing was imported.
