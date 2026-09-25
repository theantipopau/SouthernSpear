# Southern Spear

**An original Australian-themed tactical multiplayer FPS built in Unreal Engine 5.8.**

> ### ⚠️ Fictional entertainment project
> Southern Spear is an **original work**. It is **not** endorsed, developed, sponsored or approved by the **Australian Defence Force**, the **Department of Defence**, or the **Australian Army**. All units, insignia, operations, places and factions depicted are fictional. Any resemblance to real equipment or organisation is descriptive and not a reproduction.

---

## Status

**Phase 0 — Audit & Architecture — in progress.**

| | |
|---|---|
| Engine | Unreal Engine **5.8.3** (Installed Build) |
| Foundation | Lyra Starter Game **5.8** |
| C++ toolchain | Visual Studio Community 2022 **17.14.37710.0**, MSVC **14.44.35207** |
| DCC | Blender **5.2.2 LTS** |
| VCS | Git **2.54.0** + Git LFS **3.7.1** |
| **Playable build** | ❌ **None yet** |
| **Tests passing** | Toolchain audit only — see `Docs/TEST_PLAN.md` §13 |

> **Nothing in this project is implemented yet.** All content is a placeholder. No feature has been compiled, launched or tested. Any claim to the contrary is a defect in the report, not in the project.

---

## Design Pillars

1. **Deliberate, not twitch** — death is fast, *finding* a threat is the skill.
2. **Talk or lose** — the squad channel is the strongest weapon on the field.
3. **Roles earned, not selected** — qualifications gate every specialist role.
4. **Objective-focused** — the scoreboard is tickets and objectives, never kills.
5. **Symmetric rules, contextual appearance** — both teams are the same game with different visuals.

---

## Documentation

| Document | Contents |
|---|---|
| [`Docs/PROJECT_AUDIT.md`](Docs/PROJECT_AUDIT.md) | Toolchain audit with reproducible evidence; open risks |
| [`Docs/GAME_DESIGN_DOCUMENT.md`](Docs/GAME_DESIGN_DOCUMENT.md) | Pillars, factions, gameplay systems, training, progression, UX |
| [`Docs/TECHNICAL_DESIGN_DOCUMENT.md`](Docs/TECHNICAL_DESIGN_DOCUMENT.md) | Architecture, module layout, data design, security, performance budgets |
| [`Docs/DEVELOPMENT_ROADMAP.md`](Docs/DEVELOPMENT_ROADMAP.md) | Phases, gates, **vertical-slice backlog**, definitions of done |
| [`Docs/TEST_PLAN.md`](Docs/TEST_PLAN.md) | Full test matrix, net-emulation profiles, leak tests, execution record |
| [`Docs/ASSET_REGISTER.md`](Docs/ASSET_REGISTER.md) | Every required asset, its status and licence dependency |
| [`Docs/LICENCE_REGISTER.md`](Docs/LICENCE_REGISTER.md) | Every third-party dependency, licence class, legal holds |
| [`Docs/LYRA_ADOPTION.md`](Docs/LYRA_ADOPTION.md) | Adoption matrix and mandatory departure log |
| [`Docs/CODING_STANDARDS.md`](Docs/CODING_STANDARDS.md) | C++ conventions, replication and authority rules |
| [`Docs/ASSET_NAMING_STANDARDS.md`](Docs/ASSET_NAMING_STANDARDS.md) | Asset and DCC naming conventions |
| [`Docs/DECISION_LOG.md`](Docs/DECISION_LOG.md) | Architecture decisions with alternatives and consequences |

---

## Repository Layout

```
Config/            Engine and game configuration
Content/           .uasset / .umap  (Git LFS)
  SouthernSpear/   Core Characters Weapons Equipment Animations
                   Audio UI Maps Training Effects Data Developer
    Vendor/        Third-party content — segregated, never renamed
Source/            SouthernSpearGame, SouthernSpearEditor
Plugins/           Lyra baseline + SouthernSpear* plugins
GameFeatures/      SSExp_* experience plugins
Maps/              SSMap_* map content plugins
Tools/             Blender / export / CI scripts
Docs/              Design and technical documentation
```

---

## Legal Position

Southern Spear takes its design philosophy from *America's Army 2* and is an **original work**. The project does **not** copy, and must never copy, that game's source code, map layouts, mission names, UI, audio, dialogue, artwork or proprietary assets.

- **Licensed:** Unreal Engine 5.8.3 and Lyra Starter Game 5.8, under the Unreal Engine EULA.
- **On legal hold:** all rank and unit insignia are **original placeholders** pending review (`LICENCE_REGISTER.md` L-0003).
- **Not licensed and not used:** ADF / Australian Army name and marks (L-0004).
- **Prohibited:** manufacturer CAD, commercial game models, ripped assets, real camouflage textures (L-0007).
- **Fictional faction only:** the hostile faction is invented. It represents no real ethnic, religious, political or contemporary armed group.

**No third-party asset enters this repository without a `LICENCE_REGISTER.md` entry.** CI enforces it.

---

## Ground Rules

- **No claim without evidence.** Nothing is described as working unless it was compiled, launched and tested, with the command recorded.
- **Placeholders are never marked final.**
- **No invented test results.**
- **No listen server as proof of dedicated-server networking.**
- **No client-authoritative damage or progression.**
- **No paid dependencies without approval.**
- **No unlicensed content.**

---

## Building

```bash
# Editor
Engine/Build/BatchFiles/RunUBT.bat SouthernSpearEditor Win64 Development \
    -Project="%CD%\SouthernSpear.uproject" -WaitMutex

# Client
Engine/Build/BatchFiles/RunUBT.bat SouthernSpear Win64 Development \
    -Project="%CD%\SouthernSpear.uproject" -WaitMutex

# Dedicated server
Engine/Build/BatchFiles/RunUBT.bat SouthernSpearServer Win64 Development \
    -Project="%CD%\SouthernSpear.uproject" -WaitMutex
```

> These targets **do not exist yet.** The project has not been imported from Lyra. See gate G0.8 in `Docs/DEVELOPMENT_ROADMAP.md`.

---

## Next Action

Complete the Lyra import and run **gate G0.8** — the first successful `SouthernSpearEditor` compile. No gameplay code is written until that gate produces a recorded result.
