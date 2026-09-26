# CLAUDE.md — Southern Spear

Guidance for AI agents working in this repository. Read this first, then the docs listed under
**Start of every session**. Evidence over narrative: never report a result you did not execute.

## Project

Southern Spear is an original, fictional, Australian-inspired tactical multiplayer FPS.

- Unreal Engine **5.8.3** at `E:\Unreal\UE_5.8` (installed/Rocket build; **cannot build `TargetType.Server`**, see R-09)
- Lyra Starter Game 5.8 (vendored, unmodified), C++20, Blender 5.2.2 LTS, Git + Git LFS
- Repository: `E:\SouthernSpear`; phase: **Phase 1 vertical slice**, pre-alpha, nothing released
- Private code repo: `github.com/theantipopau/SouthernSpear`
- Public website repo: `github.com/theantipopau/southernspear-site` → https://theantipopau.github.io/southernspear-site/

## Start of every session

1. `git status`, `git log --oneline -10`, and review any uncommitted diff before changing anything.
2. Read the **latest session** in `Docs/CHANGELOG.md` (its single NEXT ACTION is the default task),
   then `Docs/PROJECT_AUDIT.md` risks, and any ADR in `Docs/DECISION_LOG.md` relevant to the task.
3. Check no `UnrealEditor*.exe` is running (`tasklist | grep -i unreal`) before builds or asset
   saves; a running editor/game locks DLLs and `.uasset` files and makes saves fail silently.

## Source-of-truth order (when documents disagree)

1. Accepted, non-superseded ADRs in `Docs/DECISION_LOG.md`
2. Verified evidence in `Docs/CHANGELOG.md` / `Docs/PROJECT_AUDIT.md`
3. `Docs/evidence/`
4. Current source and executed test results
5. Other design docs (GDD, TDD, MAPS_DRYRIVER, registers)
6. Historical material. **Never edit `Docs/ORIGINAL_BRIEF.md`** (immutable).

## Non-negotiable content rules

- **Fictional only (ADR-016).** Use: CDS (Commonwealth Defence Service), CLS (Commonwealth Land Service),
  ACR / **3 ACR**, 2 CG, SOR, **MAF** (Murasian Armed Forces — a competent conventional force; never
  insurgents/terrorists/militia/ethnic/religious/real-nation), **CMECU** uniform.
- **Weapons are A-series:** A88 (+C/G/M/T), A89, A4, A416, A417, A9. Real names (EF88, F89, M4, AK,
  Minimi…) only in internal research notes — never in code identifiers, data, UI or public docs.
- No ADF/Army branding, insignia, Rising Sun, mottos, colour patches; no Multicam or Auscam/Musorian copies
  (Multicam is a Crye Precision trademark). No America's Army content. No manufacturer logos/CAD/ripped assets.
- A88 and its MAF counterpart share **one** gameplay definition; only cosmetics differ.
- Before importing any asset: check `Docs/ASSET_REGISTER.md` **and** `Docs/LICENCE_REGISTER.md`, add entries.
- Never invent release dates, versions, downloads, player counts or testimonials (site or docs).
- Paid dependencies, legal-risk content and architecture changes need producer approval.

## Architecture (enforced by `Tools/validate_architecture.py`)

| Module | Role | May depend on |
|---|---|---|
| `Plugins/SouthernSpearCore` | `ESSTeamId {None,TeamOne,TeamTwo}` (authoritative, replicated), `ESSLocality {Friendly,Opposing}` (local only, **never replicated**), `FSSViewerContext`, `FSSTeamIdentity::ResolveLocality`, stable ids, tags, settings | engine only — **no SS plugin, no Lyra** |
| `Plugins/SouthernSpearTeam` | Cosmetic-only faction presentation; stateless `FSSFactionPresentationResolver` (viewer sees own team as 3 ACR, other as MAF) | Core only |
| `Plugins/SouthernSpearObjectives` | ADR-018 Objective Assault: pure `FSSObjectiveRules`, replicated `ASSObjectiveActor`, `ASSObjectiveAssaultDirector` (server round loop, idle-bot steering); team via `IGenericTeamAgentInterface` (Lyra ids 1/2 → TeamOne/TeamTwo) | Core, AIModule — **no Team, no Lyra** |
| `SouthernSpearObjectivesEditor` (editor module) | Python-callable authoring helpers (`SetGameFeatureComponentGrants`, `SetPropertyFromText`) | GameFeatures, Core |
| `Plugins/GameFeatures/SSExp_ObjectiveAssault` | Content-only Game Feature + experience `B_SS_ObjectiveAssault` | ShooterCore, Objectives |
| `Source/`, other `Plugins/` | Vendored Lyra — **do not modify**; any departure needs an ADR + `Docs/LYRA_ADOPTION.md` entry | — |

Rules: ADR-004 — presentation may never expose/modify damage, health, ammo, recoil, movement, collision,
hitboxes, abilities, authority, roles or objectives. ADR-017 — resolution fails loudly, never defaults to a
side; spectators/replays need an explicit authorised vantage. Gameplay logic is C++; Blueprints configure.
Export macros: `SSCORE_API`, `SSTEAM_API`, `SSOBJ_API` (aliased in each `Build.cs`).
Extend the guard when adding a module (SS001 sibling deps, SS002 no-Lyra list, SS003 presentation includes).

## Build and test (run from repo root; Git Bash)

```bash
python Tools/validate_architecture.py
"/e/Unreal/UE_5.8/Engine/Build/BatchFiles/Build.bat" SouthernSpearEditor Win64 Development "-Project=E:/SouthernSpear/SouthernSpear.uproject" -WaitMutex
"/e/Unreal/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" "E:/SouthernSpear/SouthernSpear.uproject" -nullrhi -unattended -nosplash -nosound -stdout "-ExecCmds=Automation RunTests SouthernSpear;Quit" -TestExit="Automation Test Queue Empty"
python Tools/verify_dressing.py
```

- Tests: `SouthernSpear.Core.*` (9), `SouthernSpear.Presentation.*` (6), `SouthernSpear.Objectives.*` (11). Count
  `Result={Success}` in the log; declare intentionally-logged errors with `AddExpectedError`.
- Bare test worlds: use `World->GetWorldSettings()->NotifyBeginPlay()` (no GameMode → `World->BeginPlay()` does nothing).
- Guard negative test: copy `Tools/` + SS plugins to the scratchpad, inject violations, expect exit 1. Never leave
  real source in a deliberately broken state.
- `-game` runs print only Display+ to stdout; read `Saved/Logs/SouthernSpear.log` for `LogSSObjectives`.
- In Git Bash prefix map-path args with `MSYS_NO_PATHCONV=1` (e.g. `/Game/Maps/L_DryRiver_01`).
- Live check: `UnrealEditor-Cmd ... "/Game/Maps/L_DryRiver_01?NumBots=8?RoundSeconds=60" -game -nullrhi ... -FORCELOGFLUSH`
  (without `-FORCELOGFLUSH` a timeout kill loses the log tail; URL also takes `PreRoundSeconds`/`PostRoundSeconds`).
- Source files are CRLF: Python `str.replace` edits must preserve `
` or they silently no-op — verify with grep.

## Dry River pipeline (order matters; see `Docs/MAPS_DRYRIVER.md`)

Each is `UnrealEditor-Cmd ... -nullrhi -unattended -nosplash -nosound -stdout
"-ini:Engine:[/Script/NavigationSystem.NavigationSystemV1]:bWaitForAsyncLoadingBeforeBuildingNavigationAutomatically=False"
"-ExecutePythonScript=E:/SouthernSpear/Tools/Unreal/<script>.py"`:

1. `build_dryriver_level.py` (its own pass-1 `ok=False` path check is known, R-15)
2. `dress_dryriver.py`
3. `setup_objective_assault.py` (GFD, experience, objectives, director, extra starts, default experience) → `Build/objective_assault_setup.json`
4. `build_dryriver_nav.py` (authoritative: path + dressing solidity; re-saves the map by design) → `Build/dryriver_nav_report.json`

Blender source: `Tools/Blender/dryriver_blockout.py`, `dryriver_dressing.py`; shared spec `Tools/Common/dryriver_spec.py`.

## Unreal Python gotchas (all learned the hard way)

- `unreal.Rotator` positional order is **(roll, pitch, yaw)** — always use keywords.
- Layout CSVs are Blender **metres**, Y mirrored: Unreal = `(x*100, -y*100, z*100)` cm.
- `line_trace_single` returns a bare `HitResult` on hit and `None` on miss (not a tuple).
- Traces hit nothing in a freshly loaded editor world until `BUILDPATHS` has run.
- Holding a map reference (`load_asset`) across `load_map` → fatal "World Memory Leaks".
- `EditDefaultsOnly` props (e.g. `LyraWorldSettings.DefaultGameplayExperience`) and non-BlueprintType structs
  (`FGameFeatureComponentEntry`, `FGameFeatureAbilitiesEntry`) need `SSObjectivesEditorLibrary` helpers.
- Some classes aren't module attributes: use `unreal.load_class(None, "/Script/Module.Class")`.
- Engine Toolset Python import errors in logs are unrelated noise.

## Git, LFS, publishing

- Binary assets (`.uasset .umap .fbx .blend .png .jpg`) are LFS. Push with `GIT_LFS_SKIP_PUSH=1 git push`
  (Epic content must not be republished; remote holds pointers only, R-14). Verify staged binaries are pointers.
- Never commit `Binaries/ Intermediate/ Saved/ DerivedDataCache/ Build/ __pycache__`, secrets or broken-guard changes.
- Commits end with the `Co-Authored-By` line given by the harness. Don't reset/clean/discard others' work.
- Website source is `Site/`; publish with `python Tools/publish_site.py` after the changelog is committed
  (`--build-only` to preview in `Build/site`; `.claude/launch.json` serves it on :8765).
- CI (`.github/workflows/build.yml`) runs on a self-hosted `ue-5.8` runner.

## Every session must end with

A new `Docs/CHANGELOG.md` session entry (above "Open Threads") containing: COMPLETED, FILES CHANGED,
TESTING (exact command, exit code, observed result, evidence path, NOT RUN items), ASSETS, RISKS
(new IDs continue from the latest), DEFECTS FOUND (with how found), and exactly **one** NEXT ACTION.
Save retained evidence under `Docs/evidence/`. Never mark PASS without execution; never claim
dedicated-server support while R-09 is open. Then commit, push, and publish the site.

## Open risks (check PROJECT_AUDIT for current state)

R-09 no Server target (engine distribution) · R-12 nav tile count unmeasured · R-14 GitHub holds LFS
pointers only · R-15 level pass-1 self-check reports failure · R-16 win streaks / spawn proximity to OBJ B.
