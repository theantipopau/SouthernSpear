# PROJECT AUDIT — Southern Spear

**Document ID:** `Docs/PROJECT_AUDIT.md`
**Status:** Baseline — Phase 0
**Last updated:** 2026-09-26
**Verification rule:** Every claim in this document is backed by a command actually executed on the build machine. Anything unverified is explicitly marked **UNVERIFIED**. No result in this project is ever reported without a reproducible command.

---

## 1. Purpose

This document records the objective state of the development machine and repository at project inception, so that later claims about the toolchain are auditable rather than assumed.

---

## 2. Audit Summary

| Area | Finding | Severity |
|---|---|---|
| Repository | Did not exist. Initialised this session on branch `main`. | Resolved |
| Unreal Engine | **5.8.3** installed at `E:\Unreal\UE_5.8` (Installed Build) | OK, with constraint |
| Lyra Starter Game | **Not bundled** with the engine. Being fetched separately. | Blocker — see §6 |
| C++ toolchain | Visual Studio Community 2022 **17.14.37710.0**, MSVC **14.44.35207** | OK |
| Windows SDK | **10.0.26100.0** | OK |
| Blender | **5.2.2 LTS** at `C:\Program Files\Blender Foundation\Blender 5.2` | OK |
| Git / LFS | Git **2.54.0.windows.1**, git-lfs **3.7.1** | OK |
| Project path | Relocated to `E:\SouthernSpear\` (space-free) | **RESOLVED** — see ADR-014 |
| RAM | **31.2 GB** — tight for editor + dedicated server + 4 clients | Risk |
| Engine registration | UE 5.8 is **not** registered in the Epic Games Launcher | **Risk** — affects Fab |

---

## 3. Repository State (before)

The workspace contained exactly one item and no version control:

```
$ pwd && ls -la
/e/SouthernSpear
drwxr-xr-x ... .
drwxr-xr-x ... ..
drwxr-xr-x ... .freebuff

$ git status
fatal: not a git repository (or any of the parent directories): .git
```

**Conclusion:** This is a greenfield project. There is no pre-existing Unreal project, no C++ source, no content, and no legacy code to preserve or migrate.

`.freebuff/` is local agent workspace metadata (a single `project-id` file) and is excluded from version control.

---

## 4. Installed Toolchain — Verified

### 4.1 Operating system

```
$ uname -a
MINGW64_NT-10.0-26200 hurleym 3.6.7-fb42d713.x86_64 ... Msys
```

Windows, build `26200`. Shell used for all commands is Git Bash (MSYS2). Native Windows paths are used for UE tooling because `Build.bat` / `Build.bat` require `cmd.exe`.

### 4.2 Unreal Engine

```
$ cat /e/Unreal/UE_5.8/Engine/Build/Build.version
{
	"MajorVersion": 5,
	"MinorVersion": 8,
	"PatchVersion": 3,
	"Changelist": 58210709,
	"CompatibleChangelist": 55116800,
	"IsLicenseeVersion": 0,
	"IsPromotedBuild": 1,
	"BranchName": "++UE5+Release-5.8"
}
```

| Property | Value |
|---|---|
| Version | **UE 5.8.3** |
| Changelist | 58210709 |
| Branch | `++UE5+Release-5.8` |
| Install path | `E:\Unreal\UE_5.8` |
| Layout | `Engine/` + `FeaturePacks/` + `Templates/` (Installed Build) |

**Critical constraint — this is an Installed Build, not a source build:**

```
$ ls /e/Unreal/UE_5.8/Engine/Build/InstalledBuild.txt
/e/Unreal/UE_5.8/Engine/Build/InstalledBuild.txt      <-- PRESENT
```

Consequences that constrain project architecture:

1. **We cannot add C++ modules to the Engine.** All game code must live in the project or its plugins.
2. **We cannot rebuild engine binaries.** Engine-level bug fixes are out of scope; workarounds must be expressed in project code.
3. **Lyra cannot be installed into the engine tree.** It must be copied into the project and adapted there.

### 4.3 Lyra availability — the Phase 0 blocker

```
$ find /e/Unreal/UE_5.8 -maxdepth 3 -iname "*Lyra*"
(no results)

$ ls /e/Unreal/UE_5.8/Templates | grep -i lyra
(no results)
```

Lyra is **not** shipped with the engine. Attempting to obtain it from source control fails:

```
$ gh repo view EpicGames/UnrealEngine-Lyra --json name,visibility
GraphQL: Could not resolve to a Repository with the name 'EpicGames/UnrealEngine-Lyra'. (repository)
```

Lyra is distributed by Epic through Fab / the Epic Games Launcher under the standard Unreal Engine EULA. There is no unauthenticated source.

**Obtained and verified.** Staged at `E:\Unreal\Lyra\LyraStarterGame` (5.2 GB, 20 plugins, full C++ source, 55 prebuilt binaries).

| Check | Result |
|---|---|
| `LyraStarterGame.uproject` → `EngineAssociation` | **`"5.8"`** — matches the installed engine |
| Runtime log `engineversion` | **`5.8.3-58210709+++UE5+Release-5.8`** — exact build match |
| Runtime log `buildversion` | `++UE5+Release-5.8-CL-58210709` — exact match |
| Plugin inventory | 20 `.uplugin` files present |
| C++ source | Complete (`ShooterCoreRuntime/Public` + `Private`, `LyraGame`, `LyraEditor`) |
| Prebuilt binaries | 55 DLLs shipped |
| Editor load | Launched, initialising (first-run shader compile) |

> **Correction logged.** An intermediate check during download reported `ShooterCore`, `ShooterMaps` and `TopDownArena` as missing. That was a **false negative** — the search used a non-recursive glob. They are present under `Plugins/GameFeatures/`. Recorded here so the audit trail is accurate.

All Lyra capabilities the architecture depends on are present: `GameFeatures`, `CommonUI`/`CommonGame`/`UIExtension`, `EnhancedInput`, `GameplayAbilities`, `ReplicationGraph`, `GameSettings`, `CommonUser`, `GameSubtitles`, `GameplayMessageRouter`, `AsyncMixin`, `OnlineServicesOSSAdapter`/`OnlineServicesNull`, `GameplayStateTree`, `GameplayBehaviors`, and the `ShooterTests`/`RuntimeTests` automation harness.

**Engine is not Launcher-registered.** The only entry in the Launcher's install list is an unrelated product:

```
$ cat /c/ProgramData/Epic/UnrealEngineLauncher/LauncherInstalled.dat
"InstallLocation": "D:\\EpicGames\\HellLetLooseG0WU4", "AppName": "3e02273b544..."
```

UE 5.8 is absent from that list. This means the in-editor **Fab plugin cannot see the Fab library for this engine version** — Fab matches sample projects against registered engine installs. Any future Fab asset acquisition therefore needs either the engine registered in the Launcher or manual download + `LICENCE_REGISTER.md` verification. Tracked as risk **R-03**.

### 4.4 Build entry point

**UE 5.8.3 on Windows has no `RunUBT.bat`.** Verified:

```
$ ls /e/Unreal/UE_5.8/Engine/Build/BatchFiles/*.bat
Build.bat   Clean.bat   GetDotnetPath.bat   GetMSBuildPath.bat
MakeAndInstallSSHKey.bat   Rebuild.bat   RunDotnet.bat   RunUAT.bat

$ ls /e/Unreal/UE_5.8/Engine/Build/BatchFiles/ | grep -i ubt
RunUBT.sh
```

`RunUBT.sh` is a **Linux/macOS** script and is not executable here. The correct Windows entry point is:

```
Engine\Build\BatchFiles\Build.bat <Target> <Platform> <Config> -Project=<path> -WaitMutex
```

> This was misdocumented in the README, the technical design document, the CI workflow and the roadmap before being caught by an actual build attempt. The same class of error as the earlier "missing Lyra plugins" reading: a plausible assumption that nobody executed. **The build command is verified, not remembered.** All documents now use `Build.bat`.

Direct `UnrealBuildTool.exe` remains available at `Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.exe` if finer control is ever needed.

### 4.5 C++ toolchain

```
$ ls "/c/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe" -latest -property installationVersion
17.14.37710.0

$ ls "/c/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC"
14.44.35207

$ ls "/c/Program Files (x86)/Windows Kits/10/Include"
10.0.26100.0

$ ls "/c/Program Files/Microsoft Visual Studio/2022/Community/VC/Auxiliary/Build/vcvars64.bat"
/c/Program Files/Microsoft Visual Studio/2022/Community/VC/Auxiliary/Build/vcvars64.bat
```

| Component | Version | Required by engine | Status |
|---|---|---|---|
| Visual Studio | Community 2022, **17.14.37710.0** | Yes | OK |
| MSVC toolset | **14.44.35207** | **>= 14.44.34918** | OK (margin +0.00010) |
| Windows SDK | **10.0.26100.0** | 10.0.26100 family | OK |
| `vcvars64.bat` | present | Yes | OK |
| .NET | **10.0.401** | Required by UBT | OK |

Engine-minimum toolchain check, read directly from the engine source:

```
$ grep -rn "older than 14.44" Engine/Source/Programs/UnrealBuildTool/Platform/Windows/VCToolChain.cs
Lines.Add($" * MSVC compiler version {...} older than 14.44.34918");
```

Installed `14.44.35207` clears the floor. **The toolchain is valid, but the margin is thin** — if UBT ever reports a compiler error, verify `msvc` was not silently downgraded. Tracked as risk **R-04**.

**Rider is not installed.** Visual Studio Community is the designated C++ IDE.

### 4.6 Blender

```
$ "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --version
Blender 5.2.2 LTS
	build date: 2026-09-15
```

**Blender 5.2.2 LTS.** Not on `PATH`; scripts must reference the absolute path or use a local `Tools/Blender/venv.ps1` wrapper.

### 4.7 Source control

```
$ git --version
git version 2.54.0.windows.1

$ git lfs version
git-lfs/3.7.1 (GitHub; windows amd64; go 1.25.1; git b84b3384)
```

Both current. GitHub CLI is authenticated to `theantipopau` (scopes: `gist`, `read:org`, `repo`, `workflow`) but has no access to Epic's private Lyra repository.

### 4.8 Hardware

| Component | Value |
|---|---|
| CPU | **AMD Ryzen 7 9800X3D** — 8 cores / 16 threads |
| RAM | **31.2 GB** |
| Discrete GPU | **AMD Radeon RX 9070 XT**, driver 32.0.31044.16 |
| Integrated GPU | AMD Radeon(TM) Graphics |

Assessment:
- CPU is excellent for both client development and a dedicated-server target.
- GPU is strong for UE5 title work and shader compilation.
- **32 GB RAM is the binding constraint.** The acceptance test "dedicated server + 4 clients" runs as 5 processes alongside the editor, which is not comfortable in 32 GB. Mitigation in `TEST_PLAN.md`: run dedicated server on the 16-thread CPU while clients are distributed, and close the editor during soak tests. Tracked as risk **R-05**.

### 4.9 Disk

| Volume | Free | Used |
|---|---|---|
| C: | 632.8 GB | 320.2 GB |
| D: | 556.2 GB | 1305.8 GB |
| E: | 488.6 GB | 465.3 GB |
| F: | 926.5 GB | 1867.9 GB |

E: (the engine and project volume) is the tightest at 488.6 GB free. Lyra alone expands to several GB; with Derived Data Cache, cooked content and a packaged client, a project working budget of **< 150 GB on E:** is the working ceiling. Tracked as risk **R-06**.

---

## 5. Source Control — Established This Session

| Item | Value |
|---|---|
| Repository root | `E:\SouthernSpear` (relocated from `E:\Australian Army Game` — ADR-014) |
| Default branch | `main` |
| `core.autocrlf` | `false` |
| `core.eol` | `lf` |
| Git LFS | `git lfs install --local` — hooks written |

Files created: `.gitignore` (Unreal + Blender + secrets), `.gitattributes` (LFS tracking for Unreal/Blender/binary types).

**Line endings are pinned to LF** with a `.gitattributes` override back to CRLF for `.bat`/`.cmd`/`.ps1`. Without this, Windows and any future Linux build agent produce whole-file diffs on every touch.

**LFS tracking verified end-to-end, not merely configured.** A probe file was created and its attributes resolved:

```
$ git check-attr filter diff merge text -- T_Probe.uasset Probe.blend Test.md
T_Probe.uasset: filter: lfs   diff: lfs   merge: lfs   text: unset
Probe.blend:    filter: lfs   diff: lfs   merge: lfs   text: unset
Test.md:        filter: unspecified                text: set
```

Binary assets route through LFS; text is not. Probe artefacts were removed. A `git lfs fsck` is run as part of CI.

---

## 6. Phase 0 Gate Status

| # | Gate | Status |
|---|---|---|
| G0.1 | Workspace inspected | **PASS** |
| G0.2 | Unreal version identified | **PASS** — 5.8.3 |
| G0.3 | Empty-vs-existing project determined | **PASS** — greenfield |
| G0.4 | C++ toolchain confirmed | **PASS** — VS 2022 17.14, MSVC 14.44.35207 |
| G0.5 | Blender confirmed | **PASS** — 5.2.2 LTS |
| G0.6 | Git repo + LFS established | **PASS** |
| G0.7 | Design documents authored | **PASS** — see `Docs/` |
| G0.8 | **Lyra fork compiles on UE 5.8.3** | ✅ **PASS** — see below |
| G0.9 | **Dedicated server target builds** | ❌ **FAIL — BLOCKED** — see §6.1 and R-09 |
| G0.10 | **Project loads under its new name** | ✅ **PASS** — see §6.2 |
| G1.1 | **Dry River builds with a valid NavMesh** | ✅ **PASS** — see §6.3 |
| G1.2 | **Dry River data-driven dressing** | ✅ **PASS** — 19/19 data checks, 290 actors placed — see §6.4 |
| G2.0 | **SouthernSpearCore builds; team identity and locality verified** | ✅ **PASS** — 9/9 automation tests — see §6.5 |
| G2.1 | **Architecture boundaries enforced by an automated guard** | ✅ **PASS** — guard fails on a deliberate violation — see §6.5 |

**Dry River navigation re-verification after the G2.0 change: NOT RUN.** The G2.0 work added a
plugin and changed no map or map-generation input, and the G1.1/G1.2 map artefacts are
byte-unchanged (`L_DryRiver_01.umap` still carries the timestamp of the last verified nav
pass), so there is no evidence of regression. That is an inference, not a test. A nav
re-run was started and interrupted during editor startup; the editor was killed before
the Python pass began, so it wrote nothing. It remains outstanding — see R-11.

### Gate G0.8 result — PASSED (2026-09-26)

The vendored fork, renamed to `SouthernSpear`, **compiles clean on UE 5.8.3 with no errors and no code changes to Lyra.**

```
Engine\Build\BatchFiles\Build.bat SouthernSpearEditor Win64 Development -Project=<...>\SouthernSpear.uproject -WaitMutex

Result: Succeeded
Total execution time: 1188.05 seconds
Errors: 0
```

**429 build actions** from a completely clean tree (all prebuilt binaries were deliberately excluded from the vendor step, so this was a genuine full rebuild, not a relink).

Produced:

| Artefact | Path |
|---|---|
| Game module | `Binaries/Win64/UnrealEditor-LyraGame.dll` |
| Editor module | `Binaries/Win64/UnrealEditor-LyraEditor.dll` |
| Target rules | `Intermediate/Build/BuildRules/SouthernSpearModuleRules.dll` |

> There is deliberately **no** `UnrealEditor-SouthernSpear.dll`. The target is ours; the modules remain `LyraGame`/`LyraEditor` per departure **D-01**. Renaming them would break the content references held inside binary `.uasset` files.

Consequences:
- The Lyra foundation is **confirmed**, not assumed. `TECHNICAL_DESIGN_DOCUMENT.md` stands as written.
- **Phase 1 is unblocked.**
- No divergence from upstream Lyra was needed, so no new entries were required in `LYRA_ADOPTION.md`. The only changes made were the project rename, three new target files, and one `GameName` line in `DefaultEngine.ini`.

The build-log transcript is retained at `Build/g08.log`.

### What G0.8 deliberately did not test

A successful compile is not a running game. Still outstanding before anything may be called "working":

- ~~The project has **never been opened in the editor** under its new name.~~ **Closed by G0.10 below.**
- ~~No map has been imported, so **NavMesh generation is still unvalidated**.~~ **Closed by G1.1 below.**
- No server or client binary has been built or launched. **The server binary cannot be built on this engine distribution — see G0.9.**
- No automation test has run.

---

## 6.1 Gate G0.9 result — FAILED, AND NOT FIXABLE IN-PROJECT (2026-09-26)

**The dedicated server target cannot be built from this engine installation. This is an engine-distribution limitation, not a project defect and not a mistake in `SouthernSpearServer.Target.cs`.**

Attempted and refused:

```
Engine\Build\BatchFiles\Build.bat SouthernSpearServer Win64 Development -Project=...\SouthernSpear.uproject -WaitMutex

LyraGameEOS and dynamic target options are disabled when packaging from an installed version of the engine
Server targets are not currently supported from this engine distribution.

Result: Failed (OtherCompilationError)
Total execution time: 2.06 seconds
```

The failure happens in **under three seconds, before a single C++ file is compiled**, so it cannot be a source error.

### Root cause, traced to the engine's own configuration

1. `Unreal.IsEngineInstalled()` is `true` — `Engine/Build/InstalledBuild.txt` contains `UE_5.8`.
2. `UEBuildTarget.cs:1396` calls `InstalledPlatformInfo.IsValid(RulesObject.Type, …, InstalledPlatformState.Supported)`.
3. `InstalledPlatformInfo` reads `[InstalledPlatforms]` from the **engine's own** `Engine/Config/BaseEngine.ini` (line 3996).
4. That section declares **28** configurations. The distinct `PlatformType` values across all of them are:

   ```
   PlatformType="Editor"
   PlatformType="Game"
   ```

   There is **no `PlatformType="Server"` entry anywhere in the whitelist.**
5. `IsValid` therefore returns `false`, and `UEBuildTarget.cs:1404` throws *"Server targets are not currently supported from this engine distribution."*

Corroborating evidence: there is no `UnrealServer*.target` or `UnrealServer` binary anywhere in `Engine/Binaries/Win64/`. The engine distribution does not ship the server target at all.

**This engine install is a game/editor distribution only.** Epic ships dedicated-server capability as a separate product from the Launcher, or it is present in a source build. It is not present here, and no project-side setting can add it.

Retained evidence (tracked in `Docs/evidence/`, because `Build/` is gitignored):
- `G009_server_build_failure.txt` — the full failure transcript
- `G009_baseengine_installedplatforms_excerpt.txt` — lines 3996–4008 of the engine's own `BaseEngine.ini`
- `G009_installedplatforms_primarysource.txt` — the whitelist plus the `UEBuildTarget.cs:1395–1415` throw site

### Consequence for the project's stated acceptance criteria

`DEVELOPMENT_ROADMAP.md` requires the vertical slice to be proven by a **packaged client connecting to a packaged dedicated server**, and explicitly refuses a listen server as proof. **That criterion is currently unsatisfiable on this machine.** This is escalated to the producer as open question 5. Tracked as **R-09**.

`SouthernSpearServer.Target.cs` is retained, correct, and ready to build the moment a server-capable engine is available. No workaround will be written that fakes a dedicated server.

---

## 6.2 Gate G0.10 result — PASSED (2026-09-26)

**Risk P1-01 is closed: the project loads under its new name with every game feature active.** This was the last unproven assumption inherited from the fork.

```
Engine\Binaries\Win64\UnrealEditor-Cmd.exe SouthernSpear.uproject -nullrhi -unattended -nosplash -nosound -stdout
```

| Check | Expected | Observed |
|---|---|---|
| Project identity | Loads as the renamed project | `LogInit: Display: Running engine for game: SouthernSpear` |
| Engine build | 5.8.3 CL 58210709 | `Build: ++UE5+Release-5.8-CL-58210709` / `Engine Version: 5.8.3-58210709+++UE5+Release-5.8` |
| Target receipt | Renamed target used | `Found matching target receipt: Binaries/Win64/SouthernSpearEditor.target` |
| Game feature plugins come from the **vendored** tree | `E:/SouthernSpear/Plugins/…` | `UnrealEditor-ShooterCoreRuntime.dll` loaded from `E:/SouthernSpear/Plugins/GameFeatures/ShooterCore/…` |
| `TopDownArena` | `[Registered, Active]` | ✅ |
| `ShooterCore` | `[Registered, Active]` | ✅ |
| `ShooterExplorer` | `[Registered, Active]` | ✅ |
| `ShooterMaps` | `[Registered, Active]` | ✅ |
| `ShooterTests` | `[Registered, Active]` | ✅ |
| Errors / fatals | 0 | **0** |

Two details worth recording:

- The game feature DLLs resolve to the **vendored** copies under `E:\SouthernSpear`, not the original Lyra staging directory at `E:\Unreal\Lyra`. The vendor step is therefore confirmed to be what actually runs, and the staging copy is correctly inert.
- The run did **not** exit cleanly: it was still in DDC maintenance and EOS config updates when the harness timeout terminated it, so there is no `LogExit: Exiting.` line. The **load itself is complete and error-free**; only the shutdown is missing. This is a harness artefact (`-ExecCmds="quit"` does not fire early enough during editor cold start), not a project defect, and it is recorded here rather than glossed over.

Retained evidence (tracked in `Docs/evidence/`, because `Build/` is gitignored):
- `G010_editorload_keylines.txt` — the 12 lines that constitute the entire pass/fail determination
- `G010_editorload_filtered.txt` — the full log with Epic telemetry DNS-failure spam removed (this environment cannot resolve `datarouter.ol.epicgames.com`; it is harmless and unrelated)

---

## 6.3 Gate G1.1 result — PASSED (2026-09-26)

**NavMesh generation is validated, and the map is built entirely from version-controlled scripts.** P1-02 is closed. The map is no longer a Blender file that nobody has seen inside the engine.

| Check | Expected | Observed |
|---|---|---|
| FBX import | 162 blockout objects as one mesh | `SS_MAP_DryRiver_01` (Interchange pipeline) |
| Collision | blocks movement and carries navigation | `CTF_USE_COMPLEX_AS_SIMPLE`, profile `BlockAll` |
| Gameplay actors | 2 deployments, 2 objectives | 4 placed from the layout CSV |
| Map check | no errors | **0 errors, 0 warnings** |
| Nav bounds | cover the 260 × 180 m map | Min (-13600, -9600, -1000) → Max (13600, 9600, 2600) cm |
| Tiles generated | non-zero | **560** |
| **Path, DeployAlpha → DeployBravo (170 m)** | **traversable** | ✅ **verified, 2 path points** |
| Saved map | contains serialised nav data | 248 KB vs 8.5 KB empty |

The acceptance check is deliberately a **path query**, not "a navmesh actor exists". A navmesh actor existed, and was reported as such, while the navmesh covered nothing at all. A non-empty `find_path_to_location_synchronously` result across the full map is the only check that means what it says.

### Defect found and fixed: the Y axis

**The layout CSV is Blender space; Unreal mirrors Y.** Using it un-negated silently **swaps the two deployments**. Because Dry River is symmetric in Y, nothing looks wrong — every distance in the map spec still holds, since a mirror preserves distance. This is the most dangerous class of bug in this map and it was caught only by cross-checking traced ground height against the recorded CSV heights. Pass 2 now asserts that delta and warns on regression. See `MAPS_DRYRIVER.md` §11.2.

Evidence: `Docs/evidence/G011_*`.

### Also fixed

`MapCheck` reported `PlayerStart_0 is a normal APlayerStart, replace with ALyraPlayerStart`. The level now uses `ALyraPlayerStart`, and map check is clean.

---

### 6.4 Gate G1.2 result — PASSED (2026-09-26)

Dry River dressing became a **data edit**. `Tools/Unreal/dress_dryriver.py` places 67 dressing
instances and 7 fence runs (expanded to 79 posts and 144 rails) from two CSVs, re-snapping
every item to the terrain by ray trace. 290 dressing actors are placed; the nav pass then
builds, so fences are present before navigation rather than after.

| Check | Result |
|---|---|
| `Tools/verify_dressing.py` | **19/19 PASS** — no Blender, no editor |
| Dressing placed | 67 (46 scrub, 10 barrel, 8 crate, 3 wreck) + 223 fence parts = **290 actors** |
| Collision at placement | **5/5** solid types, ray-verified |
| Dress report warnings | **6 → 0** (see Defects below) |
| NavMesh tiles | **560**, unchanged |
| Path, DeployAlpha → DeployBravo | still verified |

**Known limitation, R-10 (open).** Dressing collision does not survive a headless save and
reload: 5/5 solid at placement, 0/3 after reopening, 0/7 fence runs blocking. The nav pass
**reports** this as two failing steps plus a `WARN` and deliberately does **not** gate
`report["ok"]`. Dry River is traversable but its fences are not yet load-bearing cover.

Evidence: `Docs/evidence/G012_*`.

---

### 6.5 Gate G2.0 and G2.1 result — PASSED (2026-09-26)

`Plugins/SouthernSpearCore` now exists as the root of the Southern Spear dependency graph.

**G2.0 — build and behaviour.**

| Check | Result |
|---|---|
| `SouthernSpearCoreEditor` compile | **Succeeded**, 0 errors |
| Automation tests `SouthernSpear.Core.*` | **9/9 PASS** |
| `SouthernSpearCore` module startup | logged, no validation errors |
| Lyra Game Features on load | **5/5** `TopDownArena`, `ShooterCore`, `ShooterExplorer`, `ShooterMaps`, `ShooterTests` → `[Registered, Active]` |
| Project errors on load | **0** |
| Lyra source modified | **none** — ADR-002 preserved |

The 9 tests cover team validity, the full 2×2 locality matrix, safe failure on `None` and on
an out-of-range enum, determinism across repeats, spectator/replay vantage requirements,
stable ID validation and duplicate detection, team and Gameplay Tag validation, and native
tag registration.

**The two-concept split is enforced structurally, not by convention.** One test reflects over
every `UClass` in the module and fails if any `CPF_Net` property has type `ESSLocality`, so a
replicated locality cannot be added later without a test failing. `ESSTeamId` is the
replicated value; `ESSLocality` is derived per viewer.

**G2.1 — architecture guard.** `Tools/validate_architecture.py` (8 rules, stdlib only, ~1 s,
no editor) fails the build on: a sibling SS plugin dependency (SS001), a Lyra or gameplay
dependency in `SouthernSpearCore` (SS002), a gameplay include in a presentation public header
(SS003), an SS source file inside a Lyra module (SS004), a gameplay→UI dependency (SS005),
and `Friendly`/`Opposing` reappearing as authoritative team values (SS006), plus positive
checks that the team enum keeps a `None` member and the locality enum keeps both values.

The guard was **verified by deliberately breaking the build it guards**: a `Friendly` member
was added to the authoritative `ESSTeamId` and a `LyraGame` dependency was added to the
module, then the guard was run. It reported **both** violations and exited **1**. Both were
reverted, the guard re-run, and it exited **0**. The reverted source is byte-identical to the
pre-violation state (verified by `md5sum`). Evidence: `Docs/evidence/G020_*`.

**A false positive was found and fixed before that.** The first version of rule SS006 flagged
`ESSLocality` for declaring `Friendly`/`Opposing` — which is that enum's entire purpose. The
rule was wrong, not the code. It now applies the prohibition to the team enum only, and
inverts into a positive check for the locality enum.

---

## 7. Risks

| ID | Risk | Impact | Mitigation |
|---|---|---|---|
| **R-01** | ~~Lyra may not target 5.8.3~~ **RESOLVED** — `EngineAssociation: "5.8"`, runtime log confirms exact build match | — | Closed. Remaining work is the actual compile (G0.8) |
| ~~**R-02**~~ | **RESOLVED (ADR-014)** — repository relocated to the space-free path `E:\SouthernSpear` before Lyra was vendored, so no build ever saw a space | — | Closed |
| **R-03** | Engine not registered in Epic Games Launcher | In-editor Fab plugin cannot resolve this engine version, blocking compliant third-party asset acquisition | Register the engine in the Launcher, or acquire assets by manual download with mandatory `LICENCE_REGISTER.md` verification |
| **R-04** | MSVC margin over the engine minimum is ~0.0001 | A silent toolchain downgrade produces confusing build failures | CI asserts MSVC version; treat any compiler error as suspect-version first |
| **R-05** | 32 GB RAM for editor + DS + 4 clients | Cannot validate the 4-client acceptance test comfortably in one pass | Stagger client start, close the editor during soak, or run clients on a second machine (see §8) |
| ~~**R-06**~~ | ~~E: has 488.6 GB free~~ **RESOLVED 2026-09-26** — re-measured at **475 GB free / 51 % used** of 954 GB. The earlier 488.6 GB figure was measured before the 2.4 GB LFS clone landed; headroom is ample, not tight | — | Closed. Monitor only if a source-engine build is ever attempted (route (b) in §8) |
| **R-07** | UE 5.8.3 is a recent release | Ecosystem content and Fab assets may lag the engine | Prefer engine-native solutions; verify every plugin on 5.8 before adoption |
| **R-08** | Installed Build — no engine modules | Cannot patch engine C++ | All divergence is expressed in project/plugin code and documented |
| **R-09** | **This engine distribution cannot build Server targets at all** | The "packaged client → packaged dedicated server" acceptance criterion is unsatisfiable here. Blocks gate G0.9 and the vertical slice sign-off | Escalated as producer question 5. Resolve by obtaining a server-capable engine (Launcher *Dedicated Server* product, or a source build). Do **not** substitute a listen server — the roadmap forbids it. Interim: develop against the Game target's authority model, which is identical, and prove the DS at gate time |
| ~~**R-10**~~ | ~~Dry River dressing collision lost after save/reload~~ | **CLOSED Session 007 — never a collision bug.** Two checker defects (`blocked_cm` treated the bare `HitResult` UE returns on a hit as a miss; the "vertical" ray had zero length) hid a real placement defect: `dress_dryriver.py` built `unreal.Rotator(0, yaw, 0)`, and the positional order is (roll, pitch, yaw), so every non-zero-yaw post, rail and wreck was pitched over. Fixed; after re-dress and reload 3/3 sampled actors and 7/7 fence runs are solid. Evidence `Docs/evidence/R10_*` | CLOSED |

---
| ~~**R-11**~~ | ~~Dry River navigation not re-verified after the G2.0 change~~ | **CLOSED Session 006.** `build_dryriver_nav.py` re-run against the current binary: exit 0, level loaded, 1 nav bounds volume, 1 RecastNavMesh, path DeployAlpha→DeployBravo = 2 points. Evidence `Docs/evidence/R11_dryriver_nav_report.json`. Note: the script does not report a tile count, and no retained evidence file records the earlier "560 tiles"; that figure is unverified by evidence. The script re-saves the map by design (nav data), so the `.umap` hash changed | CLOSED |

## 8. Open Questions For The Producer

1. ~~**Repository path**~~ — **resolved**: relocated to `E:\SouthernSpear` (ADR-014).
2. **Second client machine** — available for true 4-client + dedicated-server testing? (R-05).
3. **Fab account** — is there a team account with an EULA-accepted licence seat, and will the engine be registered in the Launcher? (R-03). Note this **no longer governs the Electric Dreams pack**, which is declined outright by ADR-013 and was never imported (L-0012).
4. **Project path/naming** — **resolved**: `SouthernSpear`, both the code name and the folder name.
5. **How do we obtain a dedicated-server-capable engine?** (R-09 — the highest-priority open question.) This install is a game/editor-only distribution and cannot build `TargetType.Server` at all, so the vertical slice's own acceptance criterion cannot be met on it. Three routes, with materially different costs:
   - **(a)** Install the *Unreal Engine Dedicated Server* product for 5.8.3 from the Launcher. Requires an **Unreal Engine** licence seat, not a **Game** licence seat. Cheapest if the seat already exists; keeps the vendored fork and all toolchain assumptions intact.
   - **(b)** Build the engine from source. Adds roughly 250 GB and many hours, invalidates the vendored Lyra binaries (full recompile), and re-opens the MSVC/R-04 question against a different toolchain. Largest risk.
   - **(c)** Re-scope the acceptance criterion to a listen/host-authoritative harness for the slice, keeping a packaged-DS test as a *later* gate. Fastest to progress, but the roadmap currently forbids exactly this, so it is an explicit, documented deviation rather than a silent one.

   Recommendation: **(a)** if an Unreal Engine seat is available, else **(c)** with the deviation recorded in `DECISION_LOG.md` as a new ADR. **(b)** is not worth its cost for this project.

---

## 9. Reproducing This Audit

Every command in this document is read-only and safe to re-run:

```bash
uname -a
cat "/e/Unreal/UE_5.8/Engine/Build/Build.version"
ls "/e/Unreal/UE_5.8/Engine/Build/InstalledBuild.txt"
ls "/e/Unreal/UE_5.8/Templates" | grep -i lyra
ls "/e/Unreal/UE_5.8/Engine/Build/BatchFiles/"*.bat          # build entry point
gh repo view EpicGames/UnrealEngine-Lyra --json name,visibility
cat "/c/ProgramData/Epic/EpicGamesLauncher/LauncherInstalled.dat"
ls "/c/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC"
ls "/c/Program Files (x86)/Windows Kits/10/Include"
"/c/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe" -latest -property installationVersion
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --version
git --version && git lfs version
git lfs env
git check-attr filter diff merge text -- <some.uasset>
```
