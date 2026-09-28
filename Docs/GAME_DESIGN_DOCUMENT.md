# GAME DESIGN DOCUMENT — Southern Spear

**Document ID:** `Docs/GAME_DESIGN_DOCUMENT.md`
**Status:** Baseline — Phase 0
**Last updated:** 2026-09-26

> **Fictional entertainment project.** Southern Spear is an original work. It is not endorsed, developed, sponsored or approved by the Australian Defence Force, the Department of Defence, or the Australian Army. All units, insignia, ranks-as-presented, operations, places and factions are fictional. Any resemblance to real equipment is descriptive, not a reproduction.

---

## 1. Design Pillars

Every gameplay decision traces to one of these five. If a feature serves none of them, it does not ship.

### P1 — Deliberate, not twitch
Death is fast and cheap. *Information* is expensive. Players die because they were out-positioned, out-observed or out-communicated with — not because of a reflex race. Time-to-kill is low; time-to-*be killed* is long, because locating a threat is the core skill.

### P2 — Talk or lose
The squad channel is the strongest weapon on the field. A fireteam that communicates defeats a fireteam with better aim. Systems reward coordination over individual performance: suppress so a teammate can move, call an enemy so a teammate can engage, bandage so a teammate can keep fighting.

### P3 — Roles earned, not selected
Nobody spawns as a medic. Qualifications are earned in training, stored in a persistent service record, and gate role access. This makes the training menu a real game system, not an optional tutorial.

### P4 — Objective-focused, not kill-focused
The scoreboard is tickets and objectives. Kills matter as a *means*, never as the score. Progression explicitly does not reward kill/death ratio.

### P5 — Symmetric rules, contextual appearance
Both teams are equal in capability. Teams differ in *how they look*, not how they play. The two factions are the same game with different presentation — an anti-cheat-neutrality and fairness guarantee, not an art constraint.

---

## 2. Player Experience — the 20-minute Loop

```
Front End  ->  Server Browser / Quick Play
                    |
                    v
          Match Warm-up (spawn protected, kits load)
                    |
                    v
          Deploy as a qualified role
                    |
        +-----------+-----------+
        |                       |
   Squad lives            Objective play
   (regenerating         (captures, holds,
    until ticket          denies, escorts)
    depletion)                 |
        |                       |
        +-----------+-----------+
                    |
                    v
        Round ends -> Scoreboard -> Post-round summary
                    |
                    v
        Commendations, XP, statistics recorded to service record
                    |
                    v
        Back to Front End (unlocks, ranks, new quals available)
```

The session is designed so that the **first five minutes of any match** are spent learning what the team is doing, and the **last five minutes** are spent finding out whether the plan worked.

---

## 3. The Faction & Contextual Presentation System

This is the signature system and the one with the strictest constraints.

### 3.1 The model

There is exactly **one** soldier simulation. Both teams instantiate the same pawn class, the same abilities, the same weapons data (with a different *presentation* asset), the same hitboxes, the same damage model.

| Layer | Australian Commonwealth Regiment (friendly) | Murasian Armed Forces (opposing) |
|---|---|---|
| Underlying pawn class | `SS_Soldier` | `SS_Soldier` |
| Hitbox / capsule / collision | Identical | Identical |
| Network identity (`PlayerState`, `TeamId`) | `ESSTeamId` TeamOne / TeamTwo (ADR-017) | `ESSTeamId` TeamOne / TeamTwo (ADR-017) |
| Weapon data (calibre, damage, RoF) | **Identical** | **Identical** |
| Visual mesh set | Original multicam-style field dress | Mixed field clothing, chest rigs |
| Weapon model | A88 Standard Service Rifle (3 ACR presentation) | Original MAF counterpart display mesh, same A88 gameplay definition |
| Insignia | Fictional unit flashes | Fictional non-national markings |

The replicated `ESSTeamId` is combined with the viewer's own team to derive a local `ESSLocality` (never replicated), which selects the **presentation layer** (ADR-017, `FSSFactionPresentationResolver`). Presentation is resolved *on the client for cosmetic reasons only* and is never consulted for gameplay.

### 3.2 Hard rules

1. **Presentation cannot affect gameplay.** A `USSTeamPresentationSubsystem` may return meshes, materials and sounds. It may not return a hitbox, a collision channel, a damage modifier, or a network owner. This is enforced by making the subsystem a pure cosmetic resolver with no gameplay-facing API.
2. **Symmetry is asserted by test.** An automated test runs the same engagement script for both teams and asserts equal outcome distributions. If a weapon or ability is asymmetric, it must be declared in the game mode as an explicit `FSSAsymmetricRule`.
3. **Identification never relies on colour alone.** Friendly/opposing is communicated by silhouette, insignia shape, weapon silhouette, and a small set of optional colour-vision-accessible objective markers — never by blue-vs-red alone. (Also an accessibility requirement; see §9.)
4. **The hostile faction is fictional.** It is not drawn from any real ethnic, religious, political, or contemporary armed group. No real insignia, flags, slogans, or unit names. Backstory is invented and internally consistent.
5. **Spectator, replay, kill feed, and post-round states are leak-tested.** See §8.3.

### 3.3 Hostile faction: *Murasian Armed Forces* (working name)

A fictional irregular armed group operating in a fictional country. Design intent: **readable, not caricature.** They are presented as competent enough to require real tactics, and visually distinct through *kit and silhouette* rather than through ethnic or cultural coding.

> Working name only. Final branding is subject to the legal review in §10.

---

## 4. Core Gameplay Systems

### 4.1 Movement

| State | Speed (relative) | Notes |
|---|---|---|
| Walk | 0.4× | Silent, precise weapon handling |
| Tactical jog | 1.0× | Default combat movement, moderate noise |
| Sprint | 1.6× | Weapon lowered, cannot fire, loud, high bloom on re-acquire |
| Crouch | 0.5× | Lowered profile, reduced spread |
| Prone | 0.15× | Optional; ships only if animation quality meets the bar |
| Lean | — | Left/right, capped, stance-aware |

Additional:
- **Vault and mantle** over low obstacles.
- **Stance-sensitive weapon handling** — different sway, recoil and reload poses.
- **Movement affects stability and noise**: speed scales both weapon bloom and footstep loudness. Sprinting while a teammate is suppressed is a real tactical error.
- **No sliding, bunny hopping, or arcade momentum.**
- **Server-authoritative movement validation**: the server simulates and rejects out-of-bounds state (teleports, speed hacks). Client prediction is reconciled against server authority.

### 4.2 Weapon handling

- First-person and third-person representations of the same weapon instance.
- ADS with per-weapon optic sockets; first-person arms IK to the optic.
- Semi and automatic fire modes, magazine capacity, tactical vs empty reload with distinct timings.
- Chamber state where it is mechanically plausible.
- **Recoil, sway, suppression, stamina.** Firing, sprinting and being suppressed all degrade stability.
- Muzzle flash, tracers, impacts, directional audio; weapon obstruction when the muzzle nears geometry.
- Bipod deployment for appropriate support weapons.
- **Server-authoritative hit validation. No client-authoritative damage, ever.**
- **Configurable lag compensation** — rewind window and smoothing are per-project settings, tunable, and default to a conservative value. Disabled entirely on dedicated servers configured as "no lag comp" for anti-cheat evaluation.

### 4.3 Damage and medical

Low time-to-kill, but death is not the only failure state.

- **Location-sensitive damage.** A centre-mass torso hit is survivable; a head hit is not.
- **Incapacitation** rather than instant death. A wounded soldier goes down, bleeds, and can be stabilised or finished.
- **Field dressing** — limited, slows the actor while used, cannot be applied while sprinting.
- **Self-treatment is strictly worse** than being treated. A medic stabilises faster and to a better outcome; this is the core reason qualifications matter.
- **No health regeneration during a round.** Health only returns between rounds, or via treatment on a downed teammate.
- **Bleeding and stabilisation** with visible state on the HUD, deliberately minimal.
- **Friendly fire** with configurable consequence: log → warning → escalating automated penalty → temporary mute. The escalation is the deterrent; the punishment is rarely the point.
- **Team damage log** on the server, surfaced in the post-round summary.

### 4.4 Communication

| Channel | Scope |
|---|---|
| Squad voice | Fireteam — the primary channel |
| Team voice | Full team |
| Proximity voice | Optional, off by default, local radius |
| Text | Team channel + system channel |
| Ping | **Deliberately limited** — a small fixed set of contextual pings, not a free drawing tool |

Plus: radio-filtered subtitle display so speech reads as radio traffic; mute / report / block tooling. **Voice is never recorded.** Any future recording feature requires explicit per-player opt-in, documented in `Docs/PRIVACY_DESIGN.md`, and is out of scope for the vertical slice.

### 4.5 Roles

Every role is gated behind a qualification, has a limit, and has defined permissions.

| Role | Qualification | Team limit | Notes |
|---|---|---|---|
| Rifleman | Induction | Unlimited | Everyone's baseline |
| Grenadier | Induction | — | Smoke and frags |
| Automatic Rifleman | Weapons Qual | — | Sustained fire |
| Section Support Gunner | Support Weapons Qual | 2 | Bipod, belt-fed |
| Marksman | Weapons Qual | 2 | Optic + precision |
| Medic | Field Skills | 2 | Revive and stabilise |
| Fireteam Leader | Leadership Qual | 1 per fireteam | Waypoints, orders |
| Section Commander | Leadership Qual | 1 per section | Objective planning |

Data-driven: each role is a `FSSRoleDefinition` in a Data Asset. Limits, equipment and permissions are tuned without recompiling.

### 4.6 Game modes

**Objective Assault** — sequential/parallel objectives; attackers take, defenders hold; limited respawns or round-based elimination.
*As built:* ADR-018 is the symmetric, unlimited-respawn version. **Section Assault** (ADR-031) is the round-based version: one life per round, one team attacks and one defends, sides swap at half time, first to five. Win by final objective or elimination; defenders win on time.
**Secure and Hold** — capture and hold tactical locations; ticket or round-based scoring.
**Extraction** — locate, secure and extract an objective; defenders reposition to deny routes.
**Convoy Interdiction** — escort or stop a convoy. **Explicitly deferred until vehicle networking is proven stable.**
**Cooperative Training Operation** — humans vs AI, supports qualification practice and onboarding.

### 4.7 Maps and layers

Six maps, at six different stages: **Red Gum Station** and **Dry River** are in the game;
**Selat Canal** and **Saltbush** are built and in production; **Bluestone** is an early build; and
**Ravenshoe Crossing** is a written design proposal with nothing built. The map designs and their
statuses are the source of truth in `Docs/MAPS_*.md` — not this list.

> **Original layout requirement.** No map may reproduce a real military base, sensitive installation, or any operationally useful site. Layouts are designed from the gameplay brief (sightlines, cover rhythm, rotation distances), not surveyed from any real location.

Each map ships with at least four layers: Objective Assault, Secure and Hold, Day, and a low-light variant. A **layer** bundles: game mode, time of day, weather, objectives, deployment zones, available roles, vehicles, respawn model, ticket allocation, environmental state, and optional AI config — all data, not code.

World Partition is used only where scale genuinely justifies it. Small, polished maps first.

---

## 5. Training & Qualification Framework

Training is a **core progression system**, not a tutorial. It is replayable, stores best results, and unlocks multiplayer roles.

| Module | Grants | Content |
|---|---|---|
| **1. Induction** | Basic rifleman access | Movement, interaction, HUD, stance, communication, ROE |
| **2. Weapons Qualification** | Automatic Rifleman, Marksman | Familiarisation, controlled pairs, supported firing, reloading, fire-mode selection, scored |
| **3. Support Weapons Qualification** | Section Support Gunner | F89-style handling, bipod deployment, suppression, ammunition management, scored |
| **4. Field Skills** | Medic | Navigation, observation, **friendly/opposing identification**, objective interaction, basic medical treatment |
| **5. Leadership Qualification** | Fireteam Leader, Section Commander | Fireteam command, waypoint/order placement, radio procedure, objective planning |

Principles:
- **Leadership is strictly gated behind prerequisites** — it cannot be reached by skill alone in a shooting range.
- **Identification training is explicit**, because the contextual appearance system is only safe if players are trained to read silhouettes and insignia rather than colour.
- **Failure conditions are stated clearly** before the exercise starts.
- **Completed training is never invalidated by server unavailability.** A player who earned a qualification keeps it, permanently, regardless of whether a training server is up.
- Accessibility options available throughout.

---

## 6. Progression & Ranks

### 6.1 Structure — six separate concepts

Keeping these separate is what stops progression collapsing into a kill counter.

| Concept | What it is |
|---|---|
| **Account level** | Broad experience, drives cosmetics and general access |
| **Service rank** | The displayed rank, earned through service behaviour |
| **Role qualifications** | Binary unlocks earned in training |
| **Leadership eligibility** | Gated by prerequisites, separate from rank |
| **Weapon qualifications** | Per-weapon certifications, earned in training |
| **Commendations** | Specific, named achievements |
| **Seasonal statistics** | Reset-scoped, for competitive comparison |

### 6.2 Ranks

Enlisted progression inspired by the *structure* of Australian Army ranks:

Recruit → Private → Private Proficient → Lance Corporal → Corporal → Sergeant → Staff Sergeant → WO2 → WO1

**Officer ranks are reserved.** They are granted for seasonal, leadership or administrative achievement — never for accumulating kills. A player cannot buy a commission with a kill count.

> **Legal note.** Rank insignia designs are **original placeholders** until legal and branding review clears them for public release. See `LICENCE_REGISTER.md` entry L-0003.

### 6.3 What progression rewards

Objective completion · teamwork · reviving and stabilising teammates · effective leadership · communication commendations · completing qualifications · match completion · low team-damage rate · good conduct

### 6.4 What progression explicitly does not reward

Kill/death ratio · grinding weak opponents · team stacking · repeatedly farming AI · time spent idle

Points that award XP for passive presence or for per-kill bonuses are a **review blocker** in code review.

### 6.5 Data-driven

The curve is a Data Table (`DT_SS_ProgressionCurve`) editable without recompiling. Rank thresholds, commendation definitions, and XP awards are all data.

---

## 7. Menu & UX

Main menu: **Play · Training · Barracks · Service Record · Progression · Settings · Credits · Quit**

- **Play** — Quick Play, Server Browser, Host Game, Training Server, Favourites, Recent Servers
- **Server browser filters** — region, latency, map, layer, game mode, player count, slots, password, anti-cheat status, official/modded rules, dedicated/listen
- **Barracks** — character customisation, uniform configuration, loadout inspection, qualification badges, rank display, statistics, commendations
- **Settings** — display, graphics, audio, voice, controls (mouse sensitivity, controller, rebinding), accessibility, network, gameplay, colour vision, subtitles, motion reduction, FOV, first-person camera movement, privacy

Built with **CommonUI** where appropriate, fully controller-navigable.

**The HUD is deliberately sparse.** Health is communicated by posture, breathing and movement before it is communicated by a bar. Ammunition is a number, not a widget. The HUD tells you what you need; it does not narrate the game for you.

---

## 8. Testing Requirements (design-level)

### 8.1 Design invariants to test
- Both teams have identical tactical opportunity.
- Every specialist role is qualification-gated.
- No in-round health regeneration.
- Damage is server-issued.

### 8.2 Training invariants
- Completing a qualification unlocks exactly its dependent roles.
- Leadership remains locked until prerequisites are met.
- A qualification is never lost due to server unavailability.

### 8.3 Information-leak tests
Spectator mode, replays, kill feed, and post-round screens must not reveal information a player should not have — dead-outs, or the opposing team's loadout state beyond what a live observer would know. Every spectator surface is a test case, not a review item.

---

## 9. Accessibility

Rebindable controls · subtitles with adjustable size · colour-vision presets · non-colour objective indicators · adjustable reticles · reduced camera shake · adjustable head bob · separate voice and SFX volume · push-to-talk with hold **and** toggle alternatives · text scaling · assessed menu narration.

**Accessibility is a design requirement, not a post-hoc pass.** In particular: the contextual appearance system must remain fully readable under every colour-vision preset, which is why §3.2 rule 3 forbids colour-only identification.

---

## 10. Legal & Ethical Constraints

Binding on all production:

1. **No copying of *America's Army 2*** — no source code, map layouts, mission names, UI, audio, dialogue, artwork or proprietary assets.
2. **No real-world weapon manufacturing guidance.** All weapon work is game simulation. Real published specifications may inform *starting* tuning values; gameplay tuning is maintained separately and is not a reproduction of any technical manual.
3. **No manufacturer CAD, commercial game models, or ripped assets.**
4. **Fictional hostile faction only.** No real ethnic, religious, political or contemporary conflict group. No derogatory imagery, language or stereotypes. Fictional insignia, names and backstory.
5. **No ADF endorsement implied.** Marketing, packaging and store listings must carry the fictional-work disclaimer.
6. **Original camouflage.** An original multicam-style material, not a reproduction of any protected commercial pattern.
7. **Rank insignia** are original placeholders pending legal clearance.

Every third-party asset must have a `LICENCE_REGISTER.md` entry **before** it enters the repository, and must be verified as permissible in a packaged commercial product.

---

## 11. What This Document Deliberately Leaves Open

| Question | Deferred to | Why |
|---|---|---|
| Weapon damage curves and TTK numbers | Tuning pass, post-vertical-slice | Numbers are worthless until the netcode is proven |
| Final map layouts | Phase 4 | One map must work first |
| AI sophistication | Phase 3+ | Player-vs-player networking is the priority |
| Convoy Interdiction | Phase 4+ | Vehicle networking unproven |
| Final art direction | Phase 6 | Placeholders first |

Vertical-slice scope is defined in `DEVELOPMENT_ROADMAP.md`.
