# Asset inventory evidence — 2026-10-01

Read-only machine snapshot for the asset-register review. This is a local inventory, not a reproducible package manifest: the VaultCache and engine install are not versioned, and project totals include untracked/shared-worktree files. Per-pack map dependencies remain separately defined by `Docs/PACK_MANIFEST.md` and `Tools/verify_packs.py`.

## FabLibrary

Root: `E:\SouthernSpear\Content\Downloaded\VaultCache\FabLibrary`.

- 50 physical listing directories; 675 files; 25,051,328,336 bytes (about 23.3 GiB).
- `listings_v1.db`: 57 catalog rows, including 51 `local_listing` rows. Catalog rows are not one-to-one with physical payload folders: some are tool/plugin or Vault-pointer records, and some have no matching folder.
- Recursive sidecar scan: 22 `metadata` files, including UTF-16-encoded files; 10 report `isAiForbidden=true`, 12 report `false`. 28 physical listing folders have no `metadata` sidecar. Missing sidecar/value is recorded as **unverified**, not false.
- One local catalog entry, *Old Abandoned Rusty Cars*, has `isAiGenerated=true` in addition to its `isAiForbidden=false` value. This is recorded marketplace metadata, not a project-use decision.
- The full listing-by-listing catalogue, observed formats, seller/flag values where present, and cache-only versus installed/in-use dispositions are in [ASSET_REGISTER.md §4.9m](../ASSET_REGISTER.md).

Notable high-volume or distinct cache-only payloads found: *Faymere River Village* (OBJ and 228 BMP textures; approximately 21.9 GB), *Trailer Park* (archive plus 96 images), two distinct *Large Fallen Tree* listings, OBJ/GLB/glTF/Unity/Blender-format exports, weapon-animation and mocap packs, medical/character props, barricades, sandbags, corrugated wall sets, wire, mud and debris scans. These are cache discoveries, not claims that they are imported or used by a map.

The *S.W.A.T. Operator Special Remaster* listing identifies third-party CC-BY contributors for components: Bobeer (gloves), VassKacsoHunor (NVGs), Simon Coenen (helmet), Bzovius (uniform), Albin (boots), Shedmon (balaclava), and h1ggs (VECTOR). Preserve these source/credit details if the listing is used. *FSB Operator* also describes clothing derived from other Sketchfab authors; retain the listing's source notes if used. Neither character listing was identified as installed in the project snapshot.

## Other VaultCache and project Content

- `Content/Downloaded/VaultCache`: 30 immediate directories, 7,366 files, 58,343,692,654 bytes (about 54.3 GiB), including FabLibrary. The remaining 29 top-level entries contain a mixture of installed content chunks, tools and cache-only content; not all are Fab listings or map dependencies.
- A cache-only `VisAI - Community - Modern AI Framework` entry was found. No matching installed root/plugin was identified under project `Content/` or `Plugins/`.
- Project `Content/`: 29,437 files / 118,405,659,191 bytes (about 110.27 GiB) in this snapshot. This includes vendor packs, source/review trees and concurrent untracked worktree content; it is not a tracked-file total.
- Root-level installed content packs and their local counts/sizes are listed in [ASSET_REGISTER.md §4.9n](../ASSET_REGISTER.md). The map dependency subset is the 14-pack scope of `PACK_MANIFEST`, not a full Content/VaultCache inventory.
- `Content/WaterPlane`: 34 local files, 145,799,364 bytes. One known tracked/reference asset is `Lake/Textures/T_MediumWaves_N.uasset`; 33 other files were untracked in the shared checkout during this review. `Content/Splash` contained untracked `Splash.bmp` and `Splash.uasset`; provenance and intended use were not independently established. These shared-worktree observations were not modified.
- Tracked Quantum retarget prototype meshes/material assets live in `Plugins/GameFeatures/SSExp_ObjectiveAssault/Content/Characters/QuantumProto/`, not solely under project `Content/`. The project has tracked ADFRC DPCU source/output imagery and the generated tileable camo texture; the original source texture itself is not asserted to be mounted unchanged on the active Quantum body. In-game visual capture remained pending.
- Tracked A-series weapon assets span seven game-feature roots: A88 (30 assets), A88G (30), A89 (28), A4 (64), A416 (48), A25 (49), and A9 (22): 271 tracked assets total, including 151 `T_` textures and 82 `MI_` material instances. Presence in source control does not prove each texture/material is runtime-selected or visually verified.
- `Content/Sourced/` is a segregated mixed source/review collection, not a game-use manifest. ADR-035 clears acquired project assets for F2P use, but explicitly excluded ripped commercial-game material remains out of scope; raw-source handling is distinct from in-game use.

## Unreal Engine foundation

Install: `E:\Unreal\UE_5.8`, UE 5.8.3, CL 58210709, branch `++UE5+Release-5.8`, Installed Build.

| Area | Files | Bytes / approximate size |
|---|---:|---:|
| `Engine/Content` | 40,056 | about 1.47 GiB |
| `Engine/Plugins` | 113,127 | about 20.10 GiB; 901 `.uplugin` descriptors |
| `FeaturePacks` | 9 | about 2.2 MiB |
| `Templates` | 5,880 | about 0.99 GiB |

`SouthernSpear.uproject` declares 95 plugin entries (84 enabled, 11 disabled). Engine plugin/content presence alone does not mean a plugin is enabled or shipped; for example the engine has a Fab plugin directory, but this is not evidence of Fab being active in this project. A scan of tracked `.uasset`/`.umap` package references found 126 persistent `/Engine/` package paths across 1,953 referrer edges; 15 engine package paths were referenced by project maps or Southern Spear Game Feature content. Transient Interchange/editor-import references were excluded from the persistent count. Examples of actual engine references are `/Engine/BasicShapes/Cube`, `/Engine/BasicShapes/Cylinder`, `/Engine/EngineMaterials/DefaultPhysicalMaterial`, `/Engine/EngineMaterials/FlatNormal`, `/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud_Inst`, `/Engine/EngineResources/DefaultTexture`, and `/Engine/Maps/Templates/OpenWorld`. Engine foundation is covered by L-0002; this inventory does not enumerate the entire engine file-by-file.

## Method and interpretation

Counts and byte totals are filesystem observations from recursive directory enumeration; catalog rows were read from the local SQLite database; metadata sidecars were found recursively and decoded with BOM-aware UTF-8/UTF-16 handling. No deep file hashing, asset rewriting, import, deletion, manifest regeneration, or writes to VaultCache, project content, or the engine were performed for this inventory. Folder presence, plugin descriptor presence, seller flags, AI metadata and a package reference are distinct facts; none alone establishes that an asset is selected in a shipping build.

**Producer direction:** acquired assets intended for Southern Spear are free to use in this free-to-play game (ADR-028/ADR-035; reaffirmed 2026-10-01). This is project-specific clearance, not a universal statement about marketplace terms. Preserve applicable credits, no-endorsement and content-ethics rules, and do not redistribute raw vendor source packs. The no-ripped-commercial-game-source rule remains separate from the producer's approval of acquired legitimate project assets.
