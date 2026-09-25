# ORIGINAL PROJECT BRIEF — Southern Spear

**Document ID:** `Docs/ORIGINAL_BRIEF.md`
**Status:** Frozen reference
**Recorded:** 2026-09-26
**Purpose:** Verbatim record of the brief this project was started from, so later design decisions can be traced back to their source and judged against what was actually asked for.

> This document is **immutable**. It is the requirement baseline. Later documents (`GAME_DESIGN_DOCUMENT.md`, `TECHNICAL_DESIGN_DOCUMENT.md`, `DEVELOPMENT_ROADMAP.md`) are interpretations of this brief. Where an interpretation deviates from this text, this text wins and the deviation must be recorded in `LYRA_ADOPTION.md` or `DECISION_LOG.md` as an explicit, justified departure.

---

## PREAMBLE

> **Fictional entertainment project.** Do not present this as endorsed, developed or approved by the Australian Defence Force, Department of Defence or Australian Army.

---

## PROJECT WORKING TITLE

Southern Spear

---

## HIGH-LEVEL CONCEPT

Create an original Australian-themed tactical multiplayer first-person shooter inspired by the design philosophy of classic America's Army 2:

- Deliberate, teamwork-focused infantry combat
- Low time-to-kill
- Limited HUD information
- Strong communication and role discipline
- Mandatory training before specialised roles become available
- Objective-based multiplayer rather than arcade-style kill farming
- Persistent player qualifications, commendations, service record and rank progression
- Both teams play as Australian soldiers from their own perspective
- The opposing team is presented through a contextual enemy-appearance system
- When players view the opposing force, they see a fictional insurgent or hostile militia faction using visually distinct clothing and AK-pattern weapon equivalents
- The game must remain an original work and must not copy source code, map layouts, mission names, UI, audio, dialogue, artwork or proprietary assets from America's Army

This is a fictional entertainment project. Do not present it as endorsed, developed or approved by the Australian Defence Force, Department of Defence or Australian Army.

---

## AVAILABLE SOFTWARE

- Unreal Engine is installed
- Blender is installed
- Git should be used for source control
- Git LFS should be configured for binary Unreal and Blender assets
- Fab assets may be used where their licences permit
- Lyra Starter Game may be evaluated as the project foundation

---

## FIRST ACTIONS

Before writing large amounts of code:

1. Inspect the current workspace.
2. Identify the installed Unreal Engine version.
3. Determine whether this is an empty repository or existing Unreal project.
4. Check whether Visual Studio, Rider or another supported C++ toolchain is available.
5. Produce: PROJECT_AUDIT.md, GAME_DESIGN_DOCUMENT.md, TECHNICAL_DESIGN_DOCUMENT.md, ASSET_REGISTER.md, LICENCE_REGISTER.md, DEVELOPMENT_ROADMAP.md, TEST_PLAN.md
6. Create the initial Git repository structure if one does not exist.
7. Configure an appropriate Unreal Engine .gitignore and Git LFS tracking.
8. Do not begin full content production until the architecture and vertical-slice plan have been documented.
9. Do not claim that an implementation works unless it has been compiled, launched and tested.

---

## TECHNICAL FOUNDATION

Evaluate using Lyra Starter Game as the architectural foundation rather than building every system from scratch.

Prefer Lyra where practical for: Modular Game Feature plugins, Enhanced Input, CommonUI, Gameplay Ability System, Multiplayer session handling, Team allocation, Spectating, Weapon and equipment foundations, Character animation foundations, Settings architecture, Online play, Bot support, Cross-platform-ready UI patterns.

Document any substantial departure from Lyra before implementing it.

Use: C++ for authoritative gameplay, networking, persistence interfaces and performance-critical systems; Blueprints for content configuration, animation integration, UI composition and designer-facing tuning; Data Assets or Data Tables for weapons, roles, qualifications, progression, maps and game-mode configuration; Primary Asset Labels and Asset Manager rules for controlled loading; Game Feature plugins to keep major systems modular.

Never place all functionality into one monolithic character, controller, game mode or UI Blueprint.

---

## CORE GAMEPLAY PRINCIPLES

**1. Tactical movement** — Walk, tactical jog, sprint, crouch. Optional supported prone if animation quality is acceptable. Lean left/right. Stance-sensitive weapon handling. Movement speed affects weapon stability and noise. Vaulting and mantling. No exaggerated sliding, bunny hopping or arcade movement. Server-authoritative movement validation.

**2. Weapon handling** — First-person and third-person representations. ADS. Semi-automatic and automatic fire modes. Magazine-based ammunition. Tactical reload and empty reload. Chamber state where practical. Recoil, sway, suppression and stamina effects. Muzzle flash, tracers, impact effects, directional audio. Weapon obstruction near walls. Bipod support. Replicated firing, reloads and equipment state. Server-authoritative hit validation. Configurable lag compensation. No client-authoritative damage.

**3. Damage and medical gameplay** — Low time-to-kill. Location-sensitive damage. Incapacitation rather than immediate death where appropriate. Bleeding and stabilisation. Basic field-dressing. Limited self-treatment. Teammate treatment or medic stabilisation. No magical health regeneration during a round. Spectator restrictions preventing information leaking. Friendly fire with configurable consequences. Team damage logging and escalating automated penalties.

**4. Communication** — Team voice, fireteam/squad voice, optional local proximity voice, text chat with team and system channels, radio-style subtitle/indicator support, intentionally limited contextual ping, muting/reporting/administration tools. Do not record voice without explicit consent and a documented privacy design.

---

## FACTIONS AND CONTEXTUAL APPEARANCE

Implement a server-authoritative faction presentation system. The player's own team appears as a fictional Australian conventional infantry force in an original multicam-style camouflage pattern. The opposing team is presented as a fictional hostile faction: mixed field clothing, chest rigs and improvised webbing, distinct silhouettes, AK-pattern rifles and appropriate support weapons, clear visual identification without relying solely on red or blue colour coding.

Critical requirements: both teams must have identical underlying gameplay opportunities unless a game mode explicitly defines asymmetry; the contextual visual system must never affect hitboxes, collision, damage or network identity; a replicated team identifier determines friendly and opposing presentation; test every spectator, replay, kill feed and post-round state for information leakage; never use a real ethnic, religious, political or contemporary conflict group as the hostile faction; avoid culturally derogatory imagery, language or stereotypes; use fictional insignia, names and backstory.

---

## AUSTRALIAN-INSPIRED PLAYER EQUIPMENT

**Friendly force:** EF88-style 5.56 mm bullpup service rifle; F89 Minimi-style 5.56 mm belt-fed support weapon; generic service pistol; smoke grenade; fragmentation grenade; field dressing; binoculars; role-dependent optics and equipment.

**Opposing force:** AK-pattern service rifle; AK-pattern support rifle or belt-fed light machine gun; generic sidearm; smoke grenade; fragmentation grenade; field dressing; binoculars.

Do not trace, rip or redistribute manufacturer CAD files, commercial game models or protected assets.

---

## WEAPON DATA ARCHITECTURE

Create data-driven weapon definitions containing at least: internal identifier; display name; weapon class; calibre; fire modes; magazine or belt capacity; rate of fire; reload timings; recoil profile; spread or stability parameters; damage curve; penetration class; muzzle velocity abstraction; audio references; first-person mesh; third-person mesh; animation set; optic sockets; muzzle sockets; bipod support; friendly presentation asset; opposing presentation asset; network relevancy settings.

Real-world published specifications may inform the starting values, but gameplay tuning must be maintained separately from source-reference data.

Do not add realistic instructions about manufacturing, modifying or unlawfully using real weapons. All implementation must remain within game simulation.

---

## CHARACTERS AND UNIFORMS

Create original male and female soldier base bodies; modular heads; hair options compatible with military headgear; helmets; eye protection; hearing protection; plate carriers; webbing; packs; gloves; boots; role-appropriate pouches; rank slides or fictionalised progression insignia where legally appropriate.

Use an original multicam-style material rather than copying a protected commercial camouflage texture exactly.

The character pipeline must support: shared skeleton where practical; first-person arms; full-body third-person mesh; retargeted locomotion; additive aiming; foot IK; hand IK; weapon-specific poses; animation LODs; mesh LODs; material instances; networked animation states.

---

## TRAINING SYSTEM

Build a substantial Training menu and qualification framework.

1. **Induction** — movement, interaction, HUD, stance, communication, rules of engagement
2. **Weapons qualification** — service-rifle familiarisation, controlled pairs, supported firing, reloading, fire-mode selection, qualification score
3. **Support weapon qualification** — F89-style handling, bipod deployment, suppression exercise, ammunition management, qualification score
4. **Field skills** — navigation, observation, identification of friendly and opposing forces, objective interaction, basic medical treatment
5. **Leadership qualification** — fireteam command, waypoint/order placement, radio communication, objective planning; available only after prerequisite progression

Training must be replayable, store best results, award qualifications, unlock specialised multiplayer roles, support offline use where possible, explain failure conditions clearly, include accessibility options, and never require a player to repeat completed training because a server is unavailable.

---

## MENU AND USER EXPERIENCE

Create a polished, controller-compatible menu using CommonUI where appropriate.

**Main menu:** Play, Training, Barracks, Service Record, Progression, Settings, Credits, Quit.

**Play menu:** Quick Play, Server Browser, Host Game, Training Server, Favourites, Recent Servers.

**Server browser filters:** Region, Latency, Map, Layer, Game mode, Player count, Available slots, Password protected, Anti-cheat status, Modded or official rules, Dedicated or listen server.

**Barracks:** Character customisation, uniform configuration, loadout inspection, qualification badges, rank display, weapon familiarisation, statistics, commendations.

**Settings:** Display, Graphics, Audio, Voice, Controls, Mouse sensitivity, Controller settings, Key bindings, Accessibility, Network, Gameplay preferences, Colour-vision options, Subtitle configuration, Motion reduction, Field of view, First-person camera movement, Privacy settings.

---

## MULTIPLAYER

The game is multiplayer-first.

Required architecture: dedicated-server support; listen-server support for development; server-authoritative game rules; replicated teams, roles, objectives, damage and equipment; session creation and discovery; passworded private servers; server browser; reconnection handling; join-in-progress rules; map travel; match warm-up; team assignment; role limits; ready system; round timer; scoreboard; post-round summary; server logging; administration commands; kick/temporary ban/permanent ban interfaces; configurable friendly-fire policies; network emulation tests for latency, jitter and packet loss.

Evaluate Epic Online Services for authentication, lobbies, session discovery, invitations, player reports, cross-platform identity abstraction. Keep the online-services layer behind an interface so it can be replaced or supplemented later.

---

## GAME MODES

1. **Objective Assault** — attackers complete sequential or parallel objectives, defenders protect them; limited respawns or round-based elimination
2. **Secure and Hold** — teams secure one or more tactical locations; ticket or round-based scoring
3. **Extraction** — locate, secure and extract an objective; defenders can reposition or deny routes
4. **Convoy Interdiction** — escort or stop a vehicle convoy; only after vehicle networking is stable
5. **Cooperative Training Operation** — human players versus AI; supports qualification practice and onboarding

---

## MAP AND LAYER SYSTEM

Every map must support multiple layers. A layer defines: game mode; time of day; weather; objective locations; team deployment areas; available roles; vehicle availability; respawn model; ticket allocation; environmental state; optional AI configuration.

1. **Dry River** — rural Australian training area, dry creek bed, scrub, farm structures, long sightlines and concealed approaches
2. **Red Ridge** — semi-arid ridgeline, radio installation, rocky terrain, strong elevation changes
3. **Ironbark** — eucalypt woodland, training compound, mixed close and medium engagement ranges, bushfire-safe fictional setting
4. **Port Wakefield** — fictional industrial port, warehouses, container yards, administrative buildings, maritime edge
5. **Wattle Creek** — small regional settlement, service station, houses, council facilities, drainage corridors

Do not reproduce a real military base, sensitive installation or operationally useful site layout.

Each map should initially have at least: an Objective Assault layer, a Secure and Hold layer, a Day layer, a Low-light layer.

Use World Partition only where map scale justifies it. Build smaller, polished maps before attempting very large environments.

---

## ROLES

Rifleman, Grenadier, Automatic Rifleman, Section Support Gunner, Medic, Marksman, Fireteam Leader, Section Commander.

Each role must define: qualification prerequisites; weapon options; equipment; team limit; squad limit; UI designation; spawn rules; leadership permissions.

---

## PROGRESSION AND AUSTRALIAN-INSPIRED RANKS

Create a respectful, gameplay-oriented progression system inspired by the structure of Australian Army ranks.

Enlisted progression: Recruit, Private, Private Proficient, Lance Corporal, Corporal, Sergeant, Staff Sergeant, Warrant Officer Class Two, Warrant Officer Class One.

Officer ranks may be reserved for seasonal, leadership or administrative progression rather than being granted merely for accumulating kills.

Progression must reward: objective completion; teamwork; reviving or stabilising teammates; effective leadership; communication commendations; completing qualifications; match completion; low team-damage rate; good conduct.

Progression must not primarily reward: kill/death ratio; grinding weak opponents; team stacking; repeated farming of AI; time spent idle.

Use separate concepts for: account level; displayed service rank; role qualifications; leadership eligibility; weapon qualifications; commendations; seasonal statistics.

The progression curve must be data-driven and adjustable without recompiling the game.

Do not directly copy official rank insignia without reviewing applicable legal and branding restrictions. Create original placeholder insignia until cleared for public release.

---

## AI AND OFFLINE SUPPORT

Create AI suitable for training ranges, cooperative missions, filling vacant development-server positions, and testing objectives and map flow.

AI should use cover, react to suppression, communicate abstractly, follow objectives, avoid perfect awareness, have configurable reaction times and accuracy, and operate through the same damage and objective systems as players.

Do not prioritise advanced AI ahead of stable player-versus-player networking.

---

## ASSET PRODUCTION PIPELINE

For every required asset: (1) check whether an existing project asset can be legally reused; (2) search Fab from within Unreal Engine for a properly licensed asset; (3) record the asset, publisher, source, licence and modifications in LICENCE_REGISTER.md; (4) if no suitable asset exists, create an original placeholder; (5) replace placeholders incrementally with original production assets created in Blender; (6) never download assets from unverified model-ripping or redistribution sites; (7) never assume "free" means unrestricted; (8) preserve attribution where required; (9) ensure every third-party asset can legally be included in a packaged commercial product before depending on it.

Blender standards: metric units; consistent forward and up axes; applied transforms; clean naming; non-destructive modifiers where practical; high-poly and low-poly workflow; UV sets; texture baking; collision meshes; LODs; skeletal or static mesh determined correctly; export presets documented; source .blend files retained; FBX or glTF export tested before mass production.

---

## CONTENT FOLDERS

Use a clear structure similar to: `Content/SouthernSpear/{Core,Characters,Weapons,Equipment,Animations,Audio,UI,Maps,Training,Effects,Data,Developer}`.

Keep external marketplace assets in clearly separated vendor folders. Do not reorganise vendor content destructively unless necessary.

---

## AUDIO

Create a coherent audio framework for: interior and exterior gunfire; distant gunfire tails; mechanical weapon sounds; bullet cracks and impacts; suppression; footsteps by surface; equipment movement; environmental ambience; radio filtering; UI feedback; voice indicators.

Use original, licensed or properly attributed audio only.

---

## ACCESSIBILITY

Include: rebindable controls; subtitles; adjustable subtitle size; colour-vision presets; non-colour objective indicators; adjustable reticle options; reduced camera shake; adjustable head bob; separate voice and effects volume; push-to-talk; hold and toggle alternatives; text scaling; menu narration feasibility assessment.

---

## SECURITY AND FAIR PLAY

Design for: server authority; input and movement validation; inventory validation; rate limiting; secure persistence calls; no secrets stored in the client repository; sanitised player names and chat; administration audit logs; configurable anti-cheat integration; build separation between client and dedicated server; no trust in client-submitted progression results.

---

## PERSISTENCE

Create a versioned persistence model for: player identifier; settings; training completion; qualifications; rank progression; commendations; statistics; unlocked cosmetics; disciplinary state if an online service is later implemented.

Begin with a local development implementation behind an interface. Do not build an insecure production backend inside the Unreal client.

---

## PERFORMANCE TARGETS

Define and document measurable budgets for: frame time; server tick performance; replicated actor counts; network bandwidth; draw calls; skeletal mesh cost; texture memory; shader complexity; map loading; dedicated-server memory.

Use Unreal Insights, Network Profiler and stat commands to validate performance.

---

## DEVELOPMENT PHASES

- **Phase 0: Audit and Architecture** — inspect tools and repository; select Unreal version; evaluate Lyra; establish source control; create design documents; define coding standards; define asset naming standards; build test strategy
- **Phase 1: Greybox Vertical Slice** — one playable map with two teams, contextual friendly/enemy presentation, one rifle per team, one objective mode, dedicated-server build, session creation and joining, basic settings menu, basic training range, round lifecycle, scoreboard, basic progression save
- **Phase 2: Infantry Combat** — EF88-style rifle, AK-pattern counterpart, F89-style support weapon, opposing support weapon, grenades, suppression, medical system, expanded movement, role limits, voice integration assessment
- **Phase 3: Training and Progression** — full training menu, qualification logic, rank progression, service record, barracks, commendations, role prerequisites
- **Phase 4: Maps and Layers** — additional maps, multiple layers, expanded environmental art, optimised map streaming, improved AI navigation
- **Phase 5: Online Hardening** — dedicated-server deployment documentation, online-services integration, reconnection, administration, reporting, anti-cheat assessment, load testing, security review
- **Phase 6: Content and Polish** — final character assets, final weapon assets, final animations, audio pass, accessibility pass, performance pass, packaging and release preparation

---

## VERTICAL-SLICE ACCEPTANCE CRITERIA

The first milestone is complete only when: a packaged client connects to a packaged dedicated server; two or more clients can join the same match; players are assigned to opposing replicated teams; each player sees their own side as the friendly Australian-inspired force; each player sees the opposing side as the fictional hostile faction; damage is processed by the server; one objective mode can be completed, failed and restarted; the round ends correctly; the scoreboard displays valid replicated data; a training qualification can be completed and saved; settings persist after restarting the client; the project compiles with no unexplained errors; multiplayer is tested with simulated latency and packet loss; no Marketplace or Fab asset has been used without a licence-register entry.

---

## AUTOMATED AND MANUAL TESTING

Create tests for: team presentation from both player perspectives; friendly-fire classification; damage authority; weapon replication; reload interruption; objective replication; qualification unlocking; progression persistence; rank thresholds; session discovery; join in progress; disconnect and reconnect; map travel; spectator information leakage; dedicated-server packaging; settings persistence; invalid client requests; high latency; packet loss; two-client and four-client PIE sessions.

---

## WORKING METHOD

Operate incrementally. For each development cycle: (1) state the specific objective; (2) identify files and assets to be modified; (3) create or update a small implementation plan; (4) make the smallest coherent change; (5) compile; (6) run relevant automated tests; (7) launch the project where possible; (8) test multiplayer from both team perspectives; (9) record results; (10) update documentation; (11) commit the working change with a clear commit message.

**Do not:** rewrite working systems without evidence; delete functional content merely to simplify implementation; introduce paid dependencies without approval; use unlicensed content; invent test results; mark placeholder work as final; build all planned maps before the vertical slice works; rely on a listen server as proof that dedicated-server networking works; implement progression exclusively on the client; copy America's Army assets, maps, UI, names or source code.

---

## REPORTING FORMAT

At the end of every work session, report: **COMPLETED** (exact changes made); **FILES CHANGED** (created, modified or removed); **TESTING** (commands or editor tests performed, results, failures or limitations); **ASSETS** (created, imported, licence entries added, remaining placeholders); **RISKS** (technical debt, network risks, performance concerns, licensing concerns); **NEXT ACTION** (the single highest-priority next development task).

---

## BRIEF COVERAGE

Tracking of where each brief requirement is addressed. Updated as work proceeds.

| Brief section | Where addressed | Phase |
|---|---|---|
| First actions 1–7 | `PROJECT_AUDIT.md`, this repo | **Done (Phase 0)** |
| First action 5 (7 documents) | `Docs/` | **Done (Phase 0)** |
| First action 9 (no unverified claims) | Enforced in `TEST_PLAN.md` §13 | Ongoing |
| Technical foundation | `TECHNICAL_DESIGN_DOCUMENT.md`, `LYRA_ADOPTION.md` | Phase 0 / Phase 1 |
| Core gameplay 1–4 | `GAME_DESIGN_DOCUMENT.md` §4 | Phase 1–2 |
| Factions / contextual appearance | `GAME_DESIGN_DOCUMENT.md` §3, `TECHNICAL_DESIGN_DOCUMENT.md` §3 | Phase 1 |
| Australian-inspired equipment | `ASSET_REGISTER.md` §4.2–4.3 | Phase 2+ |
| Weapon data architecture | `TECHNICAL_DESIGN_DOCUMENT.md` §4 | Phase 2 |
| Characters and uniforms | `ASSET_REGISTER.md` §4.4 | Phase 6 |
| Training system | `GAME_DESIGN_DOCUMENT.md` §5, `ASSET_REGISTER.md` | Phase 3 |
| Menu and UX | `GAME_DESIGN_DOCUMENT.md` §7 | Phase 1–3 |
| Multiplayer | `TECHNICAL_DESIGN_DOCUMENT.md` §7–8 | Phase 1, 5 |
| Game modes | `GAME_DESIGN_DOCUMENT.md` §4.6, `MAPS_DRYRIVER.md` | Phase 1–4 |
| Map and layer system | `GAME_DESIGN_DOCUMENT.md` §4.7, `MAPS_DRYRIVER.md` | Phase 1, 4 |
| Roles | `GAME_DESIGN_DOCUMENT.md` §4.5 | Phase 2–3 |
| Progression and ranks | `GAME_DESIGN_DOCUMENT.md` §6, `TECHNICAL_DESIGN_DOCUMENT.md` §6 | Phase 3 |
| AI and offline support | `GAME_DESIGN_DOCUMENT.md` §4.6 | Phase 3 |
| Asset production pipeline | `ASSET_REGISTER.md` §2, `LICENCE_REGISTER.md` | Phase 0, ongoing |
| Content folders | `ASSET_REGISTER.md` §3, `TECHNICAL_DESIGN_DOCUMENT.md` §2 | Phase 1 |
| Audio | `ASSET_REGISTER.md` §4.6 | Phase 6 |
| Accessibility | `GAME_DESIGN_DOCUMENT.md` §9 | Phase 3, 6 |
| Security and fair play | `TECHNICAL_DESIGN_DOCUMENT.md` §10, `TEST_PLAN.md` §7 | Phase 1, 5 |
| Persistence | `TECHNICAL_DESIGN_DOCUMENT.md` §6.3 | Phase 1, 3 |
| Performance targets | `TECHNICAL_DESIGN_DOCUMENT.md` §9 | Phase 1+ |
| Development phases | `DEVELOPMENT_ROADMAP.md` | Phase 0 |
| Acceptance criteria | `DEVELOPMENT_ROADMAP.md` §4.3 | Phase 1 |
| Testing | `TEST_PLAN.md` | Phase 1+ |
| Working method | `DEVELOPMENT_ROADMAP.md` §10–12, `CHANGELOG.md` | Ongoing |
