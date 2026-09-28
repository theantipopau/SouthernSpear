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

## Content and licensing rules (ADR-035: free-to-play; real names allowed; every project asset cleared)

- **Free product, cleared assets (ADR-035, producer).** Southern Spear is free to play. Every asset the project
  holds is cleared for use: Fab (ADR-028), other free sources, and the ADF Re-Cut pack from its creators (L-0021,
  blanket permission), including converted and derived work. **Do not hold anything back for a licence check.**
  Still record provenance in `Docs/ASSET_REGISTER.md` / `Docs/LICENCE_REGISTER.md` (for the credits screen) and
  honour CC BY credit lines.
- **Real names are allowed** in code, data, UI, docs and the site: real weapon names (EF88, F89, M4, HK416,
  Glock, Minimi …), the Australian Army, its ranks and insignia (ADR-034), ADF equipment and camouflage. The
  current A-series names (A88, A89, A4, A416, A417, A25, A9) and fictional units (**3 ACR**, **MAF** — Murasian
  Armed Forces, **CMECU**) remain in use until deliberately renamed.
- **Still standing (not licence questions):** never claim endorsement by the ADF, Defence or the Australian Army,
  and keep the fictional-work disclaimer. **MAF** is a competent conventional force, never
  insurgents/terrorists/militia/ethnic/religious/real-nation. No *America's Army* content (L-0008) and no ripped
  commercial-game assets (L-0007): neither comes from a cleared source.
- **Accepted risk R-57:** creators' permission covers their work, not third-party trademarks or Commonwealth
  emblems. The producer accepts this. If anyone objects, the fix is a rename or a swap.
- **Art pipeline (ADR-020):** script-built in Blender (`Tools/Blender/`); weapons as static meshes on Lyra sockets, gear skinned to the Lyra mannequin.
- A88 and its MAF counterpart share **one** gameplay definition; only cosmetics differ.
- **Redistribution, not licence, keeps raw packs out of git:** `Art/ADFRC/*`, `Art/ADFRC_Player/*`, `Content/Sourced/`
  and Fab packs stay git-ignored (size, and R-14: Epic content isn't republished). Only their `.md` files are tracked.
- Never invent release dates, versions, downloads, player counts or testimonials (site or docs).
- Paid dependencies and architecture changes need producer approval.

## Architecture (enforced by `Tools/validate_architecture.py`)

| Module | Role | May depend on |
|---|---|---|
| `Plugins/SouthernSpearCore` | `ESSTeamId {None,TeamOne,TeamTwo}` (authoritative, replicated), `ESSLocality {Friendly,Opposing}` (local only, **never replicated**), `FSSViewerContext`, `FSSTeamIdentity::ResolveLocality`, stable ids, tags, settings | engine only — **no SS plugin, no Lyra** |
| `Plugins/SouthernSpearTeam` | Cosmetic-only faction presentation; stateless `FSSFactionPresentationResolver` (viewer sees own team as 3 ACR, other as MAF) | Core only |
| `Plugins/SouthernSpearObjectives` | ADR-018 Objective Assault: pure `FSSObjectiveRules`, replicated `ASSObjectiveActor`, `ASSObjectiveAssaultDirector` (server round loop, idle-bot steering); team via `IGenericTeamAgentInterface` (Lyra ids 1/2 → TeamOne/TeamTwo). ADR-031 Section Assault on the same director (`RulesMode`, `?Rules=Section`): pure `FSSSectionAssaultRules`, replicated `FSSMatchState` | Core, AIModule — **no Team, no Lyra** |
| `Plugins/SouthernSpearProgression` | ADR-032: `FSSServiceRecord` (schema v1), `ISSPersistenceProvider` + dev-only `FSSLocalDevPersistence` (JSON, `Saved/SouthernSpear/Profiles`), pure `FSSProgressionRules` (ranks, capped awards, migration), `USSProgressionSettings` (ranks/awards in `DefaultGame.ini`), server `USSProgressionServerSubsystem` → `USSServiceRelay` → client `USSPlayerProfileSubsystem` | Core only — **no Lyra, no UI** |
| `SouthernSpearObjectivesUI` | Objective HUD: pure `FSSObjectiveHudModel` (viewer-relative text/tone, neutral Team One/Two vantage without a team), C++-built `USSObjectiveStatusWidget`, `USSObjectiveHudSubsystem` (adds it for the local player) | Objectives, Core, UMG — **no Lyra**; gameplay never depends on it (SS005) |
| `SouthernSpearObjectivesEditor` (editor module) | Python-callable authoring helpers (`SetGameFeatureComponentGrants`, `SetPropertyFromText`) | GameFeatures, Core |
| `Plugins/GameFeatures/SSExp_ObjectiveAssault` | Content-only Game Feature + experience `B_SS_ObjectiveAssault` | ShooterCore, Objectives |
| `Plugins/SouthernSpearUI` | ADR-023 player HUD, match menu (Esc), front end (`L_SS_FrontEnd`, RULES choice, profile line), loading screen; reads `USSLocalHudState` / `USSLocalProfileState` (Core), which the bridge / Progression fill | Core, UMG — **no Lyra** |
| `Plugins/SouthernSpearLyraBridge` | ADR-019: the **only** SS module allowed to depend on Lyra. Client `USSViewerTeamTintSubsystem` (own team sage, other OPFOR clay, via `ResolveLocality`); future SS health/ammo HUD | Core, LyraGame — **nothing may depend on it** |
| `Source/`, other `Plugins/` | Vendored Lyra — **do not modify**; any departure needs an ADR + `Docs/LYRA_ADOPTION.md` entry | — |

Rules: ADR-004 — presentation may never expose/modify damage, health, ammo, recoil, movement, collision,
hitboxes, abilities, authority, roles or objectives. ADR-017 — resolution fails loudly, never defaults to a
side; spectators/replays need an explicit authorised vantage. Gameplay logic is C++; Blueprints configure.
Export macros: `SSCORE_API`, `SSTEAM_API`, `SSOBJ_API`, `SSOBJUI_API`, `SSPROG_API` (aliased in each `Build.cs`).
Extend the guard when adding a module (SS001 sibling deps — a `<Module>UI` may depend on `<Module>`; SS002 no-Lyra list; SS003 presentation includes; SS005 only `*UI` modules may use UMG/CommonUI; SS009 was retired by ADR-034).
Cross-module traffic goes through Core subsystems: `USSRespawnGate` (single-life roster, director ↔ bridge), `USSServiceEventSubsystem` (service events → progression), `USSLocalProfileState` (profile → UI), `USSServiceRankComponent` (replicated service level on the player state → scoreboard).
Ranks (ADR-034): Australian Army PTE→GEN as service levels 1–100 in `[/Script/SouthernSpearCore.SSRankSettings]`; insignia drawn by engine-free `SSInsigniaRaster.h`. Preview and check without Unreal: `python Tools/Progression/rank_preview.py` (g++).

## Build and test (run from repo root; Git Bash)

```bash
python Tools/validate_architecture.py
"/e/Unreal/UE_5.8/Engine/Build/BatchFiles/Build.bat" SouthernSpearEditor Win64 Development "-Project=E:/SouthernSpear/SouthernSpear.uproject" -WaitMutex
"/e/Unreal/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" "E:/SouthernSpear/SouthernSpear.uproject" -nullrhi -unattended -nosplash -nosound -NoLoadingScreen -stdout "-ExecCmds=Automation RunTests SouthernSpear;Quit" -TestExit="Automation Test Queue Empty"
python Tools/verify_dressing.py
```

- `-NoLoadingScreen` keeps Lyra's loading screen off headless test viewports (its ensure failed the network smoke test).
- Tests: `SouthernSpear.Core.*` (9), `SouthernSpear.Presentation.*` (6), `SouthernSpear.Objectives.*` (14, incl. `.Hud.*`; Session 048 adds `.Section.*` ×8 and `.Hud.SectionAssault`), `SouthernSpear.Progression.*` (6), `SouthernSpear.Core.Ranks.*` (3, Session 049), `SouthernSpear.Core.Weapons.*` (2, Session 050). Count
  `Result={Success}` in the log; declare intentionally-logged errors with `AddExpectedError`.
- Bare test worlds: use `World->GetWorldSettings()->NotifyBeginPlay()` (no GameMode → `World->BeginPlay()` does nothing).
- Guard negative test: copy `Tools/` + SS plugins to the scratchpad, inject violations, expect exit 1. Never leave
  real source in a deliberately broken state.
- `-game` runs print only Display+ to stdout; read `Saved/Logs/SouthernSpear.log` for `LogSSObjectives`.
- In Git Bash prefix map-path args with `MSYS_NO_PATHCONV=1` (e.g. `/Game/Maps/L_DryRiver_01`).
- Rendered check without touching the desktop: add `-SSShotAt=45` to a windowed `-game` run → `Saved/Screenshots/WindowsEditor/SSShot.png`.
  Never screen-capture the desktop (it can grab the user's other windows).
- Scripted console commands after the pawn exists: `-SSExecAt=14 "-SSExec=EnableCheats|DamageSelf 20"` (`-ExecCmds` runs at startup, too early).
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
3. `light_dryriver.py` (sun, sky atmosphere, sky light, fog, post-process; `SS_Light_*`, idempotent) → `Build/dryriver_lighting_report.json`
4. `setup_objective_assault.py` (GFD, experience, objectives, director, extra starts, default experience) → `Build/objective_assault_setup.json`
5. `build_dryriver_nav.py` (authoritative: path + dressing solidity; re-saves the map by design) → `Build/dryriver_nav_report.json`

Blender source: `Tools/Blender/dryriver_blockout.py`, `dryriver_dressing.py`; shared spec `Tools/Common/dryriver_spec.py`.

## Weapons pipeline (ADR-020)

`blender --background --factory-startup --python Tools/Blender/<a88_rifle|a89_support>.py` (shared helpers `ss_weapon_kit.py`) → `Art/Weapons/<NAME>/SM_<NAME>.fbx`, then
`UnrealEditor-Cmd ... -ExecutePythonScript=E:/SouthernSpear/Tools/Unreal/setup_weapons.py` → mesh, `MI_A88_*`, `B_SS_A88`
(`ASSHeldItemVisualActor`, +90° yaw offset cancels Lyra's -90° attach), `WID_SS_A88`/`ID_SS_A88` (copies of Lyra's
rifle definitions, pointed at ours). The starting loadout is data: `Config/DefaultGame.ini` `[/Script/SouthernSpearLyraBridge.SSLoadoutSettings]`.
`Content/Sourced/` is git-ignored (size and redistribution) but **cleared for use** (ADR-035), including the ADFRC extraction at `Content/Sourced/ADF_Extracted/` (L-0021).

## Unreal Python gotchas (all learned the hard way)

- `unreal.Rotator` positional order is **(roll, pitch, yaw)** — always use keywords.
- Layout CSVs are Blender **metres**, Y mirrored: Unreal = `(x*100, -y*100, z*100)` cm.
- `line_trace_single` returns a bare `HitResult` on hit and `None` on miss (not a tuple).
- Traces hit nothing in a freshly loaded editor world until `BUILDPATHS` has run.
- Holding a map reference (`load_asset`) across `load_map` → fatal "World Memory Leaks".
- `EditDefaultsOnly` props (e.g. `LyraWorldSettings.DefaultGameplayExperience`) and non-BlueprintType structs
  (`FGameFeatureComponentEntry`, `FGameFeatureAbilitiesEntry`) need `SSObjectivesEditorLibrary` helpers.
- Lyra types that aren't exported (`ULyraQuickBarComponent`, `ULyraTeamDisplayAsset`, `ULyraInventoryItemDefinition`): use `FindObject<UClass>` + UFUNCTION reflection in the bridge, never `StaticClass()`.
- `StaticMesh.sockets` is protected in Python: use `find_socket`. Hidden C++ props: `SSObjectivesEditorLibrary.get/set_property_as/from_text`.
- Some classes aren't module attributes: use `unreal.load_class(None, "/Script/Module.Class")`.
- `-nosound` makes Lyra weapon audio print on-screen Blueprint errors (`WeaponAudioFunctions.EarlyReflections`); not a defect.
- Engine Toolset Python import errors in logs are unrelated noise.

## VibeUE editor services (dev tool, `Plugins/VibeUE`, MIT, git-ignored clone)

VibeUE's services are plain `BlueprintCallable` statics, so our `-ExecutePythonScript` commandlets call them
directly: **no MCP server or open editor is needed.** Use them before hand-writing reflection hacks:
`unreal.AnimGraphService` (AnimBP state machines, blend spaces, layered blend, two-bone IK, slots),
`AnimSequenceService` (bone transforms per frame, notifies, curves, root motion), `AnimMontageService`,
`SkeletonService` (compatible skeletons, retarget modes, blend profiles, sockets), `BlueprintService`
(graphs, components, variables, compile), `MaterialService`/`MaterialNodeService`, `UVMappingService`,
`FoliageService`, `LandscapeService`, `ActorService`, `AssetDiscoveryService` (unattended import/delete).
Method list: `Build/vibeue_python_api.json` (regenerate by `dir(unreal.<Service>)`). Per-domain how-tos and
common mistakes: `Plugins/VibeUE/Content/Skills/<domain>/SKILL.md` (read the one for the task first).
Editor-only: never reference it from runtime modules or game content. The `.uproject` marks it `Optional`,
so a clone without the plugin still opens. Its web tools (Fab, OpenStreetMap, DuckDuckGo) are not used.

## Git, LFS, publishing

- Binary assets (`.uasset .umap .fbx .blend .png .jpg`) are LFS. Push with `GIT_LFS_SKIP_PUSH=1 git push`
  (Epic content must not be republished; remote holds pointers only, R-14). Verify staged binaries are pointers.
- **Stage explicit paths, never `git add -A`**: Fab or Sourced packs can land in `Content/` at any time and must stay git-ignored until adapted (ADR-021). Check `git status` for new `Content/` folders first.
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
pointers only · R-15 level pass-1 self-check reports failure · R-16 win streaks / spawn proximity to OBJ B ·
R-56 Session 049 C++ (ranks, insignia, kill XP) unverified by build (R-50, Session 048, closed: 52/52) · R-57 accepted: third-party marks and emblems (ADR-035).
