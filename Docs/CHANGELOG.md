# CHANGELOG — Southern Spear

**Document ID:** `Docs/CHANGELOG.md`
**Purpose:** Rolling record of what was actually done, what was actually tested, and what is still open. Appended to at the end of every work session.
**Last updated:** 2026-09-26

> **This file records evidence, not narrative.** A line here means a command was run and its result observed. If something was not done, it is not claimed. Anything marked `NOT RUN` is genuinely outstanding, not quietly skipped.

---

## Status At A Glance

| | |
|---|---|
| Current phase | **Phase 0 — Audit & Architecture — COMPLETE** (gate G0.8 passed) |
| Buildable? | ✅ **Yes.** `SouthernSpearEditor` compiles clean |
| Playable? | ❌ **No.** Never opened in the editor; no map imported |
| Automation passing | 1 suite (blockout layout verification, 10/10) |
| Third-party assets in use | Lyra + UE only. Zero acquired assets |
| Commit count | 6 |

---

## Session 001 — 2026-09-26 — Phase 0: Audit, Architecture & Source Control

### COMPLETED

**Toolchain audit** — every claim backed by an executed command:
- UE **5.8.3** (CL 58210709, `++UE5+Release-5.8`) at `E:\Unreal\UE_5.8`
- Confirmed **Installed Build** via `Engine/Build/InstalledBuild.txt` → no engine-side C++, Lyra must be vendored
- VS Community 2022 **17.14.37710.0**, MSVC **14.44.35207** vs engine floor **14.44.34918** (thin margin, now CI-asserted)
- Blender **5.2.2 LTS**, Git **2.54.0**, git-lfs **3.7.1**
- Hardware: Ryzen 7 9800X3D (8c/16t), 31.2 GB RAM, RX 9070 XT
- Engine 5.8.3 **not** registered in the Epic Games Launcher → in-editor Fab cannot resolve it (risk R-03)

**Source control established**:
- Git repo on `main`, Unreal+Blender `.gitignore`
- Line endings pinned to LF with CRLF override for `.bat`/`.cmd`/`.ps1`
- Git LFS tracks `.uasset`/`.umap`/`.blend` and all binary art/audio types
- **LFS verified end-to-end** with `git check-attr`, not assumed

**Documents authored** (12 in `Docs/`): `PROJECT_AUDIT`, `GAME_DESIGN_DOCUMENT`, `TECHNICAL_DESIGN_DOCUMENT`, `ASSET_REGISTER`, `LICENCE_REGISTER`, `DEVELOPMENT_ROADMAP`, `TEST_PLAN`, `CODING_STANDARDS`, `ASSET_NAMING_STANDARDS`, `LYRA_ADOPTION`, `DECISION_LOG` (15 ADRs), `MAPS_DRYRIVER`.

**Lyra 5.8 obtained and verified**: 20 plugins, full C++ source, 55 prebuilt binaries. Declares `EngineAssociation: "5.8"`.

**Repository relocated** to `E:\SouthernSpear` (space-free) — ADR-014.

**Dry River vertical-slice blockout generated** from a written design spec — 162 objects, 8,944 faces, 4 gameplay markers.

### FILES CHANGED

Created: `README.md`, `.gitignore`, `.gitattributes`, `.github/workflows/build.yml`, `Docs/*` (12 files), `Tools/Blender/dryriver_blockout.py`, `Tools/Blender/verify_dryriver.py`, `Content/Art/Blockout/*` (blend, fbx, csv), `Source/SouthernSpear*.Target.cs`.

Vendored (untracked, awaiting the G0.8 commit): Lyra source, plugins, config, content.

### TESTING

| Check | Command | Result |
|---|---|---|
| LFS attribute resolution | `git check-attr filter diff merge text` | **PASS** — `.uasset`/`.blend` → `lfs`, `.md` → text |
| CI workflow validity | `python -c "yaml.safe_load(...)"` | **PASS** — after fixing a real bug (Windows paths in double-quoted YAML were parsed as escape sequences) |
| Lyra editor load | read `LyraStarterGame.log` | **PASS** — all 5 game features `[Registered, Active]`, **1 error total** (`LogPixelStreaming2RTC`, cosmetic), clean exit |
| Blockout generation | `blender -b --python dryriver_blockout.py` | **PASS** — 162 objects, 0 errors, after fixing 2 bugs |
| Blockout layout | `python Tools/Blender/verify_dryriver.py` | **PASS 10/10, exit 0** |
| LFS on new binaries | `git lfs ls-files` | **PASS** — fbx + blend tracked |
| **Gate G0.8 editor build** | `Engine\Build\BatchFiles\Build.bat SouthernSpearEditor Win64 Development` | ✅ **PASS — `Result: Succeeded`, 429 actions, 0 errors, 1188 s** |
| Dedicated server build | `Build.bat SouthernSpearServer ...` | **NOT RUN** |
| Project opens in editor | — | **NOT RUN** |
| NavMesh on Dry River | — | **NOT RUN** — needs the project opened |

### ASSETS

Created (all **class F**, original, no licence obligation):
- `SS_MAP_DryRiver_01_HI.blend` — source blockout
- `SS_MAP_DryRiver_01.fbx` — game import mesh
- `SS_MAP_DryRiver_01_Layout.csv` — gameplay marker positions
- `dryriver_blockout.py` — procedural generator
- `verify_dryriver.py` — layout verifier (CI)

Vendored (licence **L-0001**): Lyra Starter Game 5.8; Unreal Engine 5.8.3 (**L-0002**).

**Licence entries added**: L-0001 through L-0012.
**Third-party assets acquired**: **zero**. Electric Dreams considered and **declined** (ADR-013).
**Remaining placeholders**: all 15 weapons, 16 of 18 characters, 9 of 13 animations, all 13 audio, all 6 effects, 11 of 12 UI, 6 of 7 maps, all 10 data assets. Nothing is final.

### RISKS

| ID | Risk | Status |
|---|---|---|
| R-01 | Lyra may not target 5.8.3 | ✅ **CLOSED** — `EngineAssociation "5.8"`, runtime log exact build match |
| R-02 | Path contains a space | ✅ **CLOSED** — relocated to `E:\SouthernSpear` (ADR-014) |
| R-03 | Engine not Launcher-registered → Fab unavailable | 🔴 **OPEN** — also gates the abandoned Electric Dreams harvest |
| R-04 | MSVC margin over engine minimum is thin | 🟡 **OPEN** — CI asserts the version |
| R-05 | 31.2 GB RAM for editor + DS + 4 clients | 🟡 **OPEN** — affects the 4-client acceptance test |
| R-06 | E: has ~488 GB free | 🟡 **OPEN** — monitor as LFS objects accumulate |
| R-07 | UE 5.8.3 is recent; ecosystem may lag | 🟡 **OPEN** — verify every plugin on 5.8 |
| R-08 | Installed Build — no engine modules | 🟡 Accepted — all divergence is project-side |
| **G0.8** | Vendored fork has never compiled | ✅ **CLOSED — `Result: Succeeded`, 0 errors** |
| **P1-01** | Editor build does not prove the project *runs* | 🔴 **OPEN — project has never been opened** |

**Network risks:** none yet — no netcode exists.
**Licensing concerns:** insignia on legal hold (L-0003); ADF marks not licensed (L-0004); prohibited sources barred (L-0007, L-0008).

### DEFECTS FOUND AND FIXED

| Defect | Severity | How found |
|---|---|---|
| CI workflow YAML unparseable — Windows paths in double-quoted strings read as escape sequences | S1 — build-breaking | `yaml.safe_load` |
| **`RunUBT.bat` does not exist in UE 5.8.3** — documented as the build command in 5 files | **S1 — build-breaking** | **Actual build attempt; only `RunUBT.sh` exists. Correct entry point is `Build.bat`** |
| Blender 5.2 cone operator takes `radius1`/`radius2`, not `radius` | S2 | Script run → TypeError |
| **OBJ A 10 m off the Y centre line** — gave one team a shorter run to the opening contest | **S2 — gameplay balance** | **`verify_dryriver.py`** |
| **Spec distances did not match generated geometry** (claimed 62 m, actual 51.9 m) | **S2 — false documentation** | **`verify_dryriver.py`** |
| Objective order (sequential vs parallel) never specified, leaving balance ambiguous | S2 — design | Verifier could not assert fairness |

**Self-inflicted process errors (recorded honestly):** reported Lyra's core plugins as "missing" when they were one directory deeper (non-recursive glob); clobbered and then duplicated a section of `DECISION_LOG.md` through several rounds of careless line-editing. Both were corrected and committed rather than quietly patched over.

### NEXT ACTION

**Open the project in the editor for the first time** and confirm it loads under its new name with all game features active — then import the Dry River FBX and generate a NavMesh. This is the first moment the project will have been *run* rather than merely *built*, and it validates the last unproven assumption left over from the fork.

---

## Session 002 — 2026-09-26 — First Run, and a Hard Stop on the Dedicated Server

### COMPLETED

**Gate G0.10 PASSED — the project runs.** Risk P1-01 is closed. The vendored, renamed fork was launched headless for the first time:

```
Engine\Binaries\Win64\UnrealEditor-Cmd.exe SouthernSpear.uproject -nullrhi -unattended -nosplash -nosound -stdout
```

- Loads as `Running engine for game: SouthernSpear` on `5.8.3-58210709+++UE5+Release-5.8`
- Uses our renamed target receipt, `Binaries/Win64/SouthernSpearEditor.target`
- **All five game features reach `Ending state: Registered [Registered, Active]`** — `TopDownArena`, `ShooterCore`, `ShooterExplorer`, `ShooterMaps`, `ShooterTests`
- **Zero errors, zero fatals**
- Game feature DLLs resolve to the **vendored** tree at `E:\SouthernSpear\Plugins\GameFeatures\…`, confirming the original Lyra staging copy at `E:\Unreal\Lyra` is correctly inert

The last unproven assumption left over from the fork is now a proven one. `TECHNICAL_DESIGN_DOCUMENT.md` and `LYRA_ADOPTION.md` stand as written, with no further divergence needed.

**Gate G0.9 FAILED — and it is not fixable in-project.** Attempting the dedicated server target:

```
Build.bat SouthernSpearServer Win64 Development -Project=…\SouthernSpear.uproject -WaitMutex
→ Server targets are not currently supported from this engine distribution.
→ Result: Failed (OtherCompilationError)   Total execution time: 2.06 seconds
```

It failed in under three seconds, before compiling a single file, so it cannot be a source error. Traced to the root cause in the engine's own configuration:

- `Unreal.IsEngineInstalled()` is `true` (`InstalledBuild.txt` = `UE_5.8`)
- `UEBuildTarget.cs:1396` gates on `InstalledPlatformInfo.IsValid(…, InstalledPlatformState.Supported)`
- That reads `[InstalledPlatforms]` from the **engine's own** `Engine/Config/BaseEngine.ini:3996`
- The 28 declared configurations contain exactly two distinct values: `PlatformType="Editor"` and `PlatformType="Game"`. **No `Server` entry exists.**
- Corroborated by the absence of any `UnrealServer` binary or `.target` in `Engine/Binaries/Win64/`

**This engine install is a game/editor-only distribution.** Epic ships dedicated-server capability as a separate Launcher product, or it is present in a source build. No project-side setting can add it, and `SouthernSpearServer.Target.cs` is correct and ready for the day a server-capable engine exists.

**Risk R-06 closed.** E: re-measured at **475 GB free, 51 % used** of 954 GB. The earlier "488.6 GB, tightest volume" note was written before the 2.4 GB LFS clone landed; headroom is ample.

### FILES CHANGED

- `Docs/PROJECT_AUDIT.md` — added §6.1 (G0.9 failure, full root-cause trace) and §6.2 (G0.10 pass, evidence table); added **R-09**; struck R-06 as resolved; added producer question 5 with a costed recommendation
- `Docs/CHANGELOG.md` — this entry
- **`Docs/evidence/` (new directory, tracked)** — the gate evidence is version-controlled, because `Build/` is gitignored and these transcripts are the proof that G0.9 failed and G0.10 passed. A claim in a design document that cannot be re-checked is not a claim.
  - `G009_server_build_failure.txt` — G0.9 transcript
  - `G009_baseengine_installedplatforms_excerpt.txt` — the engine's own `[InstalledPlatforms]` whitelist
  - `G009_installedplatforms_primarysource.txt` — whitelist plus the `UEBuildTarget.cs` throw site
  - `G010_editorload_keylines.txt` — the 12 lines that decide G0.10
  - `G010_editorload_filtered.txt` — full editor log, telemetry DNS-failure spam stripped
- A directory junction `E:\Australian Army Game\SouthernSpear` → `E:\SouthernSpear` was created **outside the repository** so the agent's file tools can reach the relocated project. It is not tracked by git and is not part of the project.

### TESTING

| Command | Result |
|---|---|
| `Build.bat SouthernSpearServer Win64 Development -WaitMutex` | **FAIL** — refused by engine distribution, 2.06 s, 0 actions |
| `UnrealEditor-Cmd.exe SouthernSpear.uproject -nullrhi -unattended` | **PASS** — 5/5 game features active, 0 errors |
| `df -h E:` | 475 GB free |

### ASSETS

No new assets. Dry River FBX still **not imported**; NavMesh still ungenerated.

### RISKS

- **R-09 (NEW, HIGH)** — this engine distribution cannot build `TargetType.Server`. Directly blocks the vertical slice's own acceptance criterion ("packaged client → packaged dedicated server"), which the roadmap explicitly refuses to accept a listen server for. Escalated as producer question 5.
- **R-06** — **RESOLVED**, re-measured at 475 GB free.
- **P1-01** — **CLOSED** by G0.10.
- R-03, R-04, R-05, R-07, R-08 unchanged.

### DEFECTS FOUND

One, and it is an environment defect rather than a code defect:

- **Server target unavailable on the current engine install.** Found by attempting the build rather than assuming it would work — the `SouthernSpearServer.Target.cs` file had been written and committed in Phase 0 on the strength of Lyra's convention, and that assumption was simply untested until now. It would have surfaced only at vertical-slice sign-off, which is far too late. Found early, at the cost of one build invocation.

No project-side defects were found this session.

### NEXT ACTION

**Build the `SouthernSpearCore` plugin carrying the critical path** — `ESS_TeamId` (ADR-003, match-relative) and the `UFSSFactionPresentationSet` presentation resolver (ADR-004, structurally incapable of affecting gameplay). This work builds against the Editor target and is completely independent of how R-09 is resolved, so it proceeds while the producer decides.

---

## Session 003 — 2026-09-26 — Dry River Brought Into the Engine, and a Coordinate Bug

### COMPLETED

**Gate G1.1 PASSED. NavMesh generation is validated and P1-02 is closed.** The map is no longer a Blender file nobody has seen inside the engine — it is built, collisioned, navigable and saved, entirely from version-controlled scripts.

| Check | Result |
|---|---|
| FBX import | 162 blockout objects → one mesh `SS_MAP_DryRiver_01` (via Interchange) |
| Collision | `CTF_USE_COMPLEX_AS_SIMPLE`, profile `BlockAll` |
| Gameplay actors | 4 placed from the layout CSV (2 deployments, 2 objectives) |
| Map check | **0 errors, 0 warnings** |
| Nav bounds | Min (-13600, -9600, -1000) → Max (13600, 9600, 2600) cm |
| Tiles generated | **560** |
| **Path, DeployAlpha → DeployBravo (170 m)** | ✅ **verified, 2 path points** |
| Saved map | 248 KB vs 8.5 KB empty — navigation data is serialised |

The acceptance check is a **path query**, deliberately. A navmesh actor existed, and the build reported success, while the navmesh covered *nothing*. Only a non-empty `find_path_to_location_synchronously` result across the full map means what it says.

**Producer decision taken: obtain the Dedicated Server engine product** (route (a) in `PROJECT_AUDIT.md` §8). R-09 stays open until that engine is installed; no workaround will fake it.

### DEFECTS FOUND

**1. The Y axis was mirrored, silently swapping the two deployments.**

Blender is right-handed Z-up, Unreal is left-handed Z-up, so the FBX import mirrors Y. The layout CSV is Blender space, so `Unreal_Y = -Blender_Y`. Using it un-negated is invisible: Dry River is symmetric in Y, so the deployments simply swap ends and **every distance in the map spec still holds**, because a mirror preserves distance. A map that was subtly wrong in exactly the way nobody would notice by looking.

It was caught only by cross-checking the traced ground height against the heights the Blender generator recorded:

```
DeployAlpha ground z=64.3cm  vs CSV  34.3cm  (delta 30.0cm)
DeployBravo ground z=1332.0cm vs CSV 1302.0cm (delta 30.0cm)
```

The residual 30 cm is expected — the layout markers are 0.3 m boxes on the terrain, so a trace lands on the box top. The important part is that both deltas are equal and small; before the fix they were ~13 m and the two deployments had exchanged heights. **Pass 2 now asserts this delta stays under 150 cm and warns otherwise**, so the regression cannot return quietly.

**2. `MapCheck: PlayerStart_0 is a normal APlayerStart, replace with ALyraPlayerStart`.** Now uses `ALyraPlayerStart`; map check is clean.

**3. A cosmetic bug in the reporting code cost the entire constructed level.** `list(volume.get_actor_scale3d())` raised `TypeError: 'Vector' object is not iterable` *after* the actors were placed but *before* the save, so a map with no actors was left on disk and the second pass found nothing to work with. Pass 1 now saves in a `finally`, because a reporting bug must never cost the build.

### Five engine behaviours that made a one-pass build impossible

Each was found by reading engine source, not guessed. All are documented in `MAPS_DRYRIVER.md` §11.3.

| Symptom | Cause |
|---|---|
| Post-tick callback never fires | `-ExecutePythonScript` destroys the world as soon as the script returns |
| `navigation build is locked (flags: 0x20)` | `AsyncLoadLock` (`1 << 5`), released only on a tick. Overridden per-invocation, not in project config |
| `TotalNavBounds: IsValid=false` | `GatherNavigationBounds()` skips volumes failing `HasActorRegisteredAllComponents()`; a script-spawned brush never reaches that state. **A map load does** |
| Build succeeds in 0.00 s, zero tiles | The import task saved the mesh *before* collision was configured, so the `.uasset` had none. Pass 1 now saves it explicitly afterwards |
| Nav data present but inert | Spawning `RecastNavMesh` from script defers registration to a tick; the map load creates it properly |

Every step uses the same code path a person uses in the editor: place the volume, then Build Paths. **No workaround fakes anything.**

### FILES CHANGED

- **`Tools/Unreal/build_dryriver_level.py`** (new) — pass 1: level construction
- **`Tools/Unreal/build_dryriver_nav.py`** (new) — pass 2: nav build, path verification, ground-height cross-check
- **`.github/workflows/build.yml`** — both passes plus a hard assertion on the G1.1 report; `Build Dedicated Server` marked `continue-on-error` with the R-09 reason inline so CI is not permanently red over a known environment gap
- `Docs/MAPS_DRYRIVER.md` — new §11 (pipeline, coordinate transform, measured engine constants, verification table)
- `Docs/PROJECT_AUDIT.md` — new §6.3 (G1.1), gate table, P1-02 closed
- `Docs/CHANGELOG.md` — this entry
- `Docs/evidence/G011_*` (new, tracked) — keylines and both JSON reports
- `Content/Maps/L_DryRiver_01.umap` (new, LFS) — the level with baked navigation data
- `Content/Art/Blockout/SS_MAP_DryRiver_01.uasset` (new, LFS) — the imported blockout mesh, saved with collision

### TESTING

| Command | Result |
|---|---|
| Pass 1 — `build_dryriver_level.py` | **PASS** — level, 4 actors, mesh + collision saved |
| Pass 2 — `build_dryriver_nav.py` | **PASS** — 560 tiles, 2 path points, `ok=true` |
| Pass 2 re-run (idempotency) | **PASS** — identical result, so the pipeline is stable, not lucky |
| `MapCheck` | 0 errors, 0 warnings |

### ASSETS

- `Content/Maps/L_DryRiver_01.umap` — 248 KB, navigation data serialised
- `Content/Art/Blockout/SS_MAP_DryRiver_01.uasset` — 366 KB, complex-as-simple collision
- No third-party assets were used, so no new `LICENCE_REGISTER.md` entry is required.

### RISKS

- **P1-02** — **CLOSED** by G1.1.
- **R-09** — open, now with a chosen route: obtain the Dedicated Server engine product.
- No new risks. The two engine-distribution gaps found here (async nav lock, brush-volume registration) are recorded in `MAPS_DRYRIVER.md` §11 rather than the risk register, because both are worked around and neither threatens the project.

### NEXT ACTION

**Build the `SouthernSpearCore` plugin** carrying the critical path VS-01 → VS-05 → VS-06: `ESS_TeamId` (match-relative per ADR-003) and the `UFSSFactionPresentationSet` resolver (ADR-004, structurally incapable of affecting gameplay), with a CI static scan enforcing the separation. Unaffected by R-09.

---

## Open Threads

| Item | Blocked on | Owner |
|---|---|---|
| ~~First editor launch of the renamed project~~ | **CLOSED** — G0.10 passed | — |
| ~~NavMesh validation for Dry River~~ | **CLOSED** — G1.1 passed, 560 tiles, path verified | — |
| **Dedicated server target build (R-09)** | **Producer decision — this engine distribution cannot build Server targets at all. See `PROJECT_AUDIT.md` §6.1 and producer question 5** | **Producer** |
| Fab account / engine registration (R-03) | Producer decision | Producer |
| Second client machine for 4-client test (R-05) | Producer decision | Producer |
| Insignia legal clearance (L-0003) | Legal review | Producer |

---

## Conventions for Future Entries

One section per work session, newest at the bottom. Always:

- **COMPLETED** — exact changes, not intentions
- **FILES CHANGED** — created/modified/removed, with the vendoring status of anything untracked
- **TESTING** — command, result, or `NOT RUN`. No exceptions
- **ASSETS** — created/imported/licence entries/placeholders remaining
- **RISKS** — new risks get IDs continuing from R-08; closed risks are struck through, not deleted
- **DEFECTS FOUND** — with how they were found, since that is the real signal
- **NEXT ACTION** — exactly one, the highest-priority item
