<p align="center"><img src="Docs/images/header.png" alt="Southern Spear" width="100%"></p>

# Southern Spear

Southern Spear is a free, community-developed, Australian-inspired tactical multiplayer
first-person shooter built on **Unreal Engine 5.8.3** and the **Lyra Starter Game 5.8**.
Players serve in 3 ACR, a battalion of the fictional Commonwealth Land Service, against the
fictional Murasian Armed Forces (MAF). Both teams are mechanically identical. Each player sees
their own team as 3 ACR and the other team as MAF (ADR-017).

**Status:** pre-alpha, Phase 1 (vertical slice). There is no playable release.

| | |
|---|---|
| Website | https://theantipopau.github.io/southernspear-site/ |
| Rolling changelog | [`Docs/CHANGELOG.md`](Docs/CHANGELOG.md) (one entry per working session) |
| Roadmap | [`Docs/DEVELOPMENT_ROADMAP.md`](Docs/DEVELOPMENT_ROADMAP.md) |
| Decisions | [`Docs/DECISION_LOG.md`](Docs/DECISION_LOG.md) (ADRs; ADR-016 terminology, ADR-017 team identity) |
| Verified state and risks | [`Docs/PROJECT_AUDIT.md`](Docs/PROJECT_AUDIT.md) |

## Repository layout

| Path | Contents |
|---|---|
| `Plugins/SouthernSpearCore` | Team identity (`ESSTeamId`), viewer-relative locality, validation, tags, settings. No Lyra or SS dependencies |
| `Plugins/SouthernSpearTeam` | Cosmetic-only faction presentation and the stateless 3 ACR / MAF resolver |
| `Plugins/GameFeatures/SSExp_*` | Southern Spear game-mode experiences |
| `Source/`, other `Plugins/` | Vendored Lyra 5.8 (unmodified; see `Docs/LYRA_ADOPTION.md`) |
| `Content/Maps/L_DryRiver_01` | Dry River vertical-slice map, generated from `Tools/` |
| `Tools/` | Blender and Unreal generators, the architecture guard and verifiers |
| `Site/` | Website source, published by `Tools/publish_site.py` |
| `Docs/` | Design, decisions, registers, evidence (`Docs/evidence/`) and brand images (`Docs/images/`) |

## Build and test

Engine: `E:\Unreal\UE_5.8`. Commands are run from the repository root.

```bat
python Tools\validate_architecture.py
E:\Unreal\UE_5.8\Engine\Build\BatchFiles\Build.bat SouthernSpearEditor Win64 Development -Project=%CD%\SouthernSpear.uproject -WaitMutex
E:\Unreal\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe %CD%\SouthernSpear.uproject -nullrhi -unattended -nosplash -nosound -NoLoadingScreen -stdout -ExecCmds="Automation RunTests SouthernSpear;Quit" -TestExit="Automation Test Queue Empty"
E:\Unreal\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe %CD%\SouthernSpear.uproject -nullrhi -unattended -nosplash -nosound -NoLoadingScreen -stdout -ExecCmds="Automation RunTests SouthernSpear.Network.Gameplay.TwoPlayerAuthoritySmoke;Quit" -TestExit="Automation Test Queue Empty"
python Tools\verify_dressing.py
```

The Dry River generation, dressing and navigation commands are in `Docs/MAPS_DRYRIVER.md` §10.

## Working rules

- Every working session appends an entry to `Docs/CHANGELOG.md`: COMPLETED, FILES CHANGED,
  TESTING (command, exit code, result, evidence, NOT RUN items), ASSETS, RISKS, DEFECTS FOUND,
  and exactly one NEXT ACTION. Nothing is marked PASS unless it was executed.
- After the changelog is committed, publish the site: `python Tools/publish_site.py`.
- Presentation is cosmetic only (ADR-004). The architecture guard enforces the module boundaries.
- Check `Docs/ASSET_REGISTER.md` and `Docs/LICENCE_REGISTER.md` before importing any asset.

## Source control

This repository is **private**. It vendors Lyra and Epic content, which must not be republished.
Binary assets are stored in Git LFS locally and are **not** pushed to GitHub (pushes use
`GIT_LFS_SKIP_PUSH=1`), so a fresh clone contains LFS pointers only. The public website lives
in a separate repository, `theantipopau/southernspear-site`, which contains no game content.

## Disclaimer

Southern Spear is an original work of fiction. It is not endorsed, sponsored, developed or
approved by the Australian Government, the Department of Defence, the Australian Defence Force
or the Australian Army. All organisations, units, forces and weapons in it are fictional. It is
not affiliated with America's Army. Unreal Engine and Lyra are provided by Epic Games under the
Unreal Engine EULA.
