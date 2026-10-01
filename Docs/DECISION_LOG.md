# DECISION LOG — Southern Spear

**Document ID:** `Docs/DECISION_LOG.md`
**Status:** Open
**Last updated:** 2026-10-01

Architecture decisions with their reasoning, alternatives and consequences. A decision without a recorded alternative is a decision nobody thought about.

---

## ADR-001 — Engine: Unreal Engine 5.8.3

**Status:** Accepted
**Date:** 2026-09-26

**Context.** One engine is installed on the machine: UE 5.8.3 (CL 58210709, `++UE5+Release-5.8`) as an Installed Build at `E:\Unreal\UE_5.8`.

**Decision.** Target 5.8.3 exclusively.

**Alternatives.**
- *Downgrade to 5.6/5.7* — would need a second engine install; the brief specifies Unreal is already available and Lyra 5.8 matches it.
- *Source build* — not possible here; the install is binary.

**Consequences.**
- Pinned to this engine version. Lyra 5.8 declares `EngineAssociation: "5.8"`, which matches.
- Cannot add engine C++ modules. All code is project-side.
- 5.8 is recent, so third-party ecosystem content may lag. Verify every plugin on 5.8 before adoption.
- C++ toolchain floor is MSVC 14.44.34918; installed is 14.44.35207 — a thin margin worth CI-asserting.

---

## ADR-002 — Foundation: Lyra 5.8, fork-and-layer

**Status:** Accepted (compile verification pending, gate G0.8)
**Date:** 2026-09-26

**Context.** The brief directs evaluating Lyra as the foundation. Lyra 5.8 is available and declares `EngineAssociation: "5.8"`, matching the installed engine.

**Decision.** Vendor Lyra into the repository; build Southern Spear as new plugins on top; preserve Lyra type names.

**Alternatives.**
- *Rename Lyra types to `SS`* — rejected: names are referenced inside binary `.uasset` files; renaming breaks content references silently.
- *Rebuild from scratch on GAS + Game Features* — rejected: discards a proven ability set, replication graph, camera stack, weapon framework and bot system.
- *Keep Lyra outside the repo* — impossible; an Installed Build cannot host a project in the engine tree.

**Consequences.**
- `Lyra*`/`ShooterCore` identifiers persist in the codebase. New code is strictly `SS_*`.
- Upstream updates require re-applying local changes; a pinned revision is recorded.
- Recorded as departure D-01.

**Open risk.** G0.8 must confirm Lyra actually compiles on this build. Declared compatibility is not proof. The architecture is plugin-modular, so a fallback is a subset of the plan rather than a rewrite.

---

## ADR-003 — Match-relative team identity

**Status:** SUPERSEDED by ADR-017 (2026-09-26)
**Date:** 2026-09-26

> **Superseded.** The *intent* of this decision is retained: presentation resolves only
> relative to the viewer. The *mechanism* is not. An identifier whose value depends on
> the observer cannot be replicated, used as a scoreboard key, compared for equality, or
> trusted by a server, and code that stores `Friendly` on a PlayerState produces a system
> where the server and its clients silently disagree about who is on which team. ADR-017
> keeps the guarantee and moves it out of the enum into a pure resolver. See ADR-017 for
> the full reasoning. This entry is retained, not deleted, as the record of what was tried.

**Context.** Both teams must be the same game with different presentation. Neither can be hardcoded as "the good guys".

**Decision.** `ESS_TeamId` is **match-relative** (`Friendly` = the local player's team, `Opposing` = the other). The faction is *derived* from a local viewer's team, never stored absolutely.

**Alternatives.**
- *Absolute factions* (`AUS` / `MILITIA` on the PlayerState) — rejected: makes client-side presentation resolvable without viewer context, and invites faction logic leaking into gameplay.

**Consequences.**
- Presentation resolution takes `(viewerTeam, subjectTeam)`.
- A client can only ever resolve presentation relative to itself, which is exactly the trust boundary the brief requires.
- Makes the symmetry test natural: run the same script for both teams and compare.

---

## ADR-004 — Presentation is structurally incapable of affecting gameplay

**Status:** Accepted
**Date:** 2026-09-26

**Context.** The brief requires that the contextual appearance system never affect hitboxes, collision, damage or network identity.

**Decision.** Enforce by construction, not by convention:
- The resolver returns only mesh/material/audio/voice assets.
- It has no settable state.
- It cannot include weapon, damage or ability headers.
- CI greps public presentation headers and fails on a violation.
- A test asserts identical gameplay data across factions.

**Alternatives.**
- *Code review only* — rejected: "don't do that" is not a control. An automated check is.
- *Runtime flag* — rejected: a flag can be set incorrectly and the failure would be invisible.

**Consequences.**
- Slight extra rigidity in the resolver's API. Worth it — this is the project's highest-risk fairness property.

---

## ADR-005 — Progression is data-driven, versioned, and server-trusted

**Status:** Accepted
**Date:** 2026-09-26

**Context.** Progression must be tunable without recompiling, must persist across versions, and must not be forgeable by a client.

**Decision.**
- All progression numbers live in `UPrimaryDataAsset`/`UDataTable`. **No progression constants in C++** (CI-enforced).
- `FSSServiceRecord` is versioned from day one with a registered migration chain.
- All progression is behind `ISSPersistenceProvider`.
- The dev local provider's `ValidateProgressionClaim` returns **false by construction**.
- XP awarded in a match is awarded by the **server**, not derived from client telemetry.
- Every XP award rule has a per-match cap — this is how "no idle farming" is enforced rather than intended.

**Alternatives.**
- *Client-side progression with server sync* — rejected outright by the brief ("no trust in client-submitted progression results", "never implement progression exclusively on the client").
- *Fixed schema, no versioning* — rejected: locks us into schema v1 forever, and a bad release is unrecoverable.

**Consequences.**
- A production backend is required eventually, but it lives behind the interface — **not inside the Unreal client**.
- Schema changes require a migration entry. Enforced by test.

---

## ADR-006 — Reference data separated from tuning data

**Status:** Accepted
**Date:** 2026-09-26

**Context.** Real-world published specifications may inform *starting* values, but gameplay tuning is original design work and must be maintained separately. Separating them is also a legal-hygiene measure.

**Decision.** `FSSWeaponDefinition` holds `FSSWeaponReferenceData` (descriptive, sourced) and `FSSWeaponTuningData` (actual gameplay values) as **separate structs**. No gameplay function may read `Reference` (CI-enforced).

**Alternatives.**
- *One struct with two sets of fields* — rejected: they diverge, and a merged struct invites gameplay code to read the wrong one.
- *No reference data at all* — rejected: designers and players legitimately want to know what a weapon is meant to represent.

**Consequences.**
- Slight verbosity in the asset. Prevents a real class of error and keeps the legal position clean.

---

## ADR-007 — Dedicated server validated as a separate process, never a listen server

**Status:** Accepted
**Date:** 2026-09-26

**Context.** Listen servers mask real networking problems and are explicitly not accepted as proof.

**Decision.** Acceptance requires a **packaged** dedicated server with **packaged** clients. CI builds the server target; nightly runs the packaged suite. The server target excludes client-only modules so there is no client surface to attack.

**Alternatives.**
- *PIE listen server for all testing* — rejected: does not exercise the real netcode path, and hides listen-server-specific bugs.
- *Accept PIE multi-client as sufficient* — rejected: insufficient for the acceptance criteria.

**Consequences.**
- Slower CI. Necessary — this is the milestone's core claim.
- Constrained by 32 GB RAM (PROJECT_AUDIT R-05): the 4-client DS run closes the editor.

---

## ADR-008 — Phase gating: no content production before the vertical slice

**Status:** Accepted
**Date:** 2026-09-26

**Context.** Maps, weapon models and animation are artist-time-expensive and system-risk-cheap. The expensive risks are netcode, authority, team presentation and persistence.

**Decision.** Phases 1–3 use **placeholders only**. Final art, audio and polish are Phase 6.

**Alternatives.**
- *Build the real rifle first* — rejected: if the team-presentation or netcode design changes, the asset is wrong and the time is lost.
- *Parallel art and systems* — rejected for now: with a small team, context-switching into art before the architecture is proven produces assets built on assumptions that Phase 1 will invalidate.

**Consequences.**
- Early phases look visually poor. This is correct and expected.
- Placeholders are **visibly** placeholders and are release-gated (CP-10).

---

## ADR-009 — Git LFS for all binary assets, LF line endings

**Status:** Accepted
**Date:** 2026-09-26

**Context.** Unreal `.uasset`/`.umap` and Blender `.blend` are opaque binaries; committing them raw bloats the repository and makes merges impossible.

**Decision.** Git LFS tracks all Unreal and Blender binary types (`.gitattributes`); `core.eol = lf` with CRLF overrides for `.bat`/`.cmd`/`.ps1`; CI runs `git lfs fsck`.

**Alternatives.**
- *Git without LFS* — rejected: unmergeable binaries, unbounded repo growth.
- *Keep `.blend` out of the repo* — rejected: the source file is the authoritative artwork. The FBX is a derivative.

**Consequences.**
- Every binary needs an LFS-quota plan. E: has 488.6 GB free (R-06).
- `git lfs fsck` in CI catches corruption before it propagates.

---

## ADR-010 — LFS tracking verified, not merely configured

**Status:** Accepted
**Date:** 2026-09-26

**Context.** A `.gitattributes` that does not actually route binaries through LFS is a silent failure that surfaces weeks later as an unusable repository.

**Decision.** Verify with `git check-attr` during setup, and keep the probe as a recurring CI check.

**Verified result:**
```
T_Probe.uasset:  filter: lfs  diff: lfs  merge: lfs  text: unset
Probe.blend:     filter: lfs  diff: lfs  merge: lfs  text: unset
Test.md:         filter: unspecified           text: set
```

**Consequences.** Configuration is proven, not assumed.

---

## ADR-011 — Hostile faction is entirely fictional

**Status:** Accepted
**Date:** 2026-09-26

**Context.** The brief requires a fictional fictional opposing force presentation, and prohibits any real ethnic, religious, political or contemporary conflict group, and any derogatory imagery or stereotypes.

**Decision.** The opposing faction (working name *Murasian Armed Forces*) is invented: invented insignia, invented unit names, an internally consistent backstory, and a visual design driven by **kit and silhouette** rather than ethnic or cultural coding.

**Alternatives.**
- *A generic "insurgent" look* — rejected: "generic" tends to converge on real-world stereotypes, which is exactly the failure mode to avoid.

**Consequences.** Requires genuine art direction effort to make the faction readable *without* leaning on cultural shorthand. This is the right trade.

---

## ADR-012 — Fictional-work disclaimer is binding on all output

**Status:** Accepted
**Date:** 2026-09-26

**Context.** The project is inspired by the design philosophy of *America's Army 2* and uses Australian-inspired ranks and equipment. There is a real risk of being read as official.

**Decision.**
- The game is never described as endorsed, developed, sponsored or approved by the ADF, the Department of Defence or the Australian Army.
- Rank insignia are **original placeholders** pending legal review (`LICENCE_REGISTER.md` L-0003).
- ADF name and marks are **not licensed** (L-0004) and are not used.
- All units, operations, places and maps are fictional.
- Every map is an original layout; no real base, sensitive installation or operationally useful site.
- No *America's Army 2* source code, map layout, mission name, UI, audio, dialogue or artwork.

**Consequences.** Branding and marketing copy require review before release (Phase 6, CP-12).

---

## ADR-013 — Maps are built original. Third-party environments are not used.

**Status:** Accepted (revised 2026-09-26)
**Date:** 2026-09-26

**Context.** An "Electric Dreams" environment pack was downloaded. Using a finished showcase environment as the vertical-slice map would be faster than greyboxing and would produce a better-looking first build.

**Decision.** **The pack is disregarded entirely.** Southern Spear builds its own maps. No third-party environment is used as a base map, as a source of harvestable art, or as a map layout reference.

**Alternatives.**
- *Use it as the vertical-slice map* — rejected. Map geometry is load-bearing: it drives sightlines, rotation distances and cover rhythm, all of which Phase 1 exists to tune. Starting from a fixed layout would mean tuning gameplay around an asset instead of building to a design.
- *Harvest generic modular pieces* — **initially adopted, then reversed.** Harvested art carries the source pack's visual signature, its licence obligations and its production assumptions, none of which belong in a shipping build. The production time saved is smaller than the integration and re-surfacing cost it creates.
- *Ignore the pack entirely* — **adopted.**

**Consequences.**
- All map geometry is original, authored in Blender from a gameplay-driven design spec (`Docs/MAPS_DRYRIVER.md`).
- The map layout carries the full original-work guarantee, reinforcing ADR-012 and the prohibition on reproducing any real installation.
- More upfront Blender work, and the vertical slice will look plainly greyboxed. Correct and expected (ADR-008).
- The licence risk attached to L-0012 disappears with the harvest. The entry stays on file as a record that the pack was considered and declined.

---

## ADR-014 — Repository relocated to a space-free path

**Status:** Accepted
**Date:** 2026-09-26

**Context.** The repository lived at `E:\Australian Army Game`. A space in a build path can break UnrealBuildTool, UAT and third-party tooling, and the failure typically surfaces at packaging time when it is most expensive to fix.

**Decision.** Relocate the repository to `E:\SouthernSpear` before vendoring Lyra, so the space never enters the build system.

**Alternatives.**
- *Keep the path and hope* — rejected: UE 5.8 mostly tolerates spaces, which is exactly what makes the eventual failure confusing. The fix is a one-time `git mv`-equivalent now versus a tooling migration later.
- *Rename the folder but keep 'Australian Army'* — rejected. The folder name would still read as an official ADF product, which ADR-012 forbids.

**Consequences.**
- The working directory is also renamed away from the game's subject, which is consistent with the fictional-work position.
- Done **before** the Lyra vendor step, so no build ever sees the old path.

---

## ADR-015 — The vertical-slice test bed is an original outback blockout

**Status:** Accepted
**Date:** 2026-09-26

**Context.** The vertical slice needs one playable map with two teams, an objective sequence and deployment zones. The options were a third-party environment (now excluded by ADR-013), a hand-built greybox, or a scripted blockout generated from a design spec.

**Decision.** Build **Dry River** as an original blockout authored in Blender from a written gameplay spec, then import it into Unreal. Every dimension in the map traces to a gameplay requirement — sightline length, rotation distance, cover density — and is recorded with its justification in `Docs/MAPS_DRYRIVER.md`.

**Alternatives.**
- *Hand-place the blockout in the UE editor* — rejected as the primary path. Slow, non-reproducible, and produces no reusable source asset. Blender is the authoritative source for art in this project anyway, so the source `.blend` must exist regardless.
- *UE Landscape / World Partition* — rejected for the vertical slice. Justified only for large maps (ADR-008); it adds a heightfield pipeline that proves nothing about netcode, teams or objectives.

**Consequences.**
- The map is reproducible: the script regenerates it, so a dimension can be changed and re-exported rather than nudged in the editor.
- The Blender source is version-controlled in LFS, satisfying the asset pipeline standard in `TECHNICAL_DESIGN_DOCUMENT.md` §12.2.
- Layout intent is reviewable as a document before it is reviewable as a level, which is the cheaper way to iterate on a greybox.

---

## ADR-016 — Canonical fictional organisations and uniform terminology

**Status:** Accepted
**Date:** 2026-09-26
**Supersedes:** the working names recorded in ADR-011 and throughout pre-2026-09-26 design documents

**Context.** The project began with placeholder organisation names (a generic "Australian Defence Service", an "Australian Service Regiment", a "Murasian Armed Forces" working title, and an "AMECU" uniform working title). Those names were never intended to ship. Three of them are actively unhelpful: the first two sit uncomfortably close to real Australian Defence naming, and "Murasian Armed Forces" encodes exactly the ethnic-militia framing ADR-011 exists to avoid. They are replaced with a settled fictional set.

**Decision.** The canonical fictional organisations are:

| Short | Name | Role |
|---|---|---|
| **CDS** | Commonwealth Defence Service | The fictional national military the player serves in |
| **CLS** | Commonwealth Land Service | Land-warfare component of the CDS; the infantry home |
| **ACR** | Australian Commonwealth Regiment | Primary conventional infantry formation; Phase 1 player force |
| **2 CG** | 2nd Commando Group | Fictional CLS special-operations formation; later phase |
| **SOR** | Special Operations Regiment | Fictional CLS special-operations formation; later phase |
| **MAF** | Murasian Armed Forces | The fictional contextual opposing force |
| **CMECU** | Commonwealth Multi-Environment Combat Uniform | Original fictional camouflage and uniform system |

The recommended Phase 1 player formation is **3rd Battalion, Australian Commonwealth Regiment (3 ACR)**, presented as "Rifleman, 3 ACR". Only the CLS is in scope for Phase 1; maritime and air service are explicitly out of scope until the infantry slice ships.

The MAF are presented as a **credible conventional military force**, not as terrorists, extremists, an ethnic or religious militia, or an imitation of any current conflict participant. Visual direction is original red-earth disruptive camouflage in ochre, rust, dark brown, muted burgundy and charcoal.

**Alternatives.**
- *Keep the working names and clarify later* — rejected. A name that reads as a real organisation stays that way through every intermediate build, and the "Murasian Armed Forces" framing is the precise stereotype ADR-011 prohibits.
- *Use obviously placeholder names* — rejected. They cannot be evaluated honestly in playtesting, and they push the real naming work to the end when it is most expensive.

**Consequences.**
- `Docs/ORIGINAL_BRIEF.md` retains its original wording as an immutable historical record; this ADR is the superseding authority for all active documents, code, data and UI.
- No Australian Defence Force emblem, corps badge, colour patch, Rising Sun, unit emblem, motto or battle honour is used or may be created. All insignia, mottos, rank devices and qualification badges are original work.
- Faction recognition must never depend on colour alone; silhouette, equipment arrangement, insignia shape and weapon silhouette carry it too.
- The CMECU is an original pattern. AMCU and commercial MultiCam are not reproduced, traced or approximated tile-for-tile.
- Renaming assets is done with redirectors and validation, never a blind mass rename of binaries.

---

## ADR-017 — Stable team identity, viewer-relative locality

**Status:** Accepted
**Date:** 2026-09-26
**Supersedes:** ADR-003

**Context.** ADR-003 defined `ESSTeamId` as *match-relative*, with the enum values themselves being `Friendly` and `Opposing` — that is, the value of a player's team depended on who was looking at it. That was a clean idea, and it does produce the trust boundary ADR-003 wanted. But it is unworkable as written: an identifier that means different things to different observers cannot be stored on a replicated PlayerState, cannot be used as a scoreboard key, cannot index an objective's owning team, and cannot be compared for equality in a kill-feed. Every one of those needs a value that means the same thing to everyone.

The failure mode is not hypothetical. Code that stores `Friendly` on a PlayerState produces a system where the server and two clients disagree about the same player's team, and nothing detects it.

**Decision.** Split the concept in two.

- **`ESSTeamId { None, TeamOne, TeamTwo }` is authoritative and replicated.** It names a team in the world and carries no alignment. `None` is a real, representable state so that resolution can fail explicitly rather than defaulting.
- **`ESSLocality { Friendly, Opposing }` is derived locally and never replicated.** Each client computes it from `(ViewerTeam, SubjectTeam)`. Two clients in the same match legitimately hold opposite values for the same pair of actors, and that is correct.
- Resolution goes through `FSSTeamIdentity::ResolveLocality`, which is pure, deterministic, and returns a `FSSLocalityResolution` that carries either a locality or a typed failure reason. It never defaults.
- Spectators and replays resolve through an explicit `FSSViewerContext` that must name an authorised vantage. A spectator that has not stated one gets **no** resolution, rather than one team's view being shown to the other.
- `ESSLocality` has no `None` member, so a default-constructed value is `Friendly`. The safety therefore lives in the API: callers must go through the resolver rather than default-constructing. This is recorded as a known sharp edge rather than left as a trap.

**Alternatives.**
- *Keep ADR-003's match-relative enum as written* — rejected for the reasons above. The intent (viewers may only resolve presentation relative to themselves) is preserved in full; only the *storage* of that intent moves from the enum to the resolver.
- *Absolute factions on the PlayerState* (`CDS` / `MAF`) — rejected, as in ADR-003. It makes presentation resolvable without viewer context and invites faction logic leaking into gameplay.
- *Add a `None` to `ESSLocality`* — rejected. It would be a safer default, but the published architecture fixes the two-value set, and adding a third would make every switch over it need a dead branch. The resolver API carries the safety instead.

**Consequences.**
- ADR-003's core guarantee is retained and strengthened: presentation still resolves only through an explicit `(viewer, subject)` pair, and now that pair is computed from two independently meaningful values.
- An automation test reflects over every class in `SouthernSpearCore` and fails if any replicated property has type `ESSLocality`, so the boundary holds structurally rather than by convention.
- `SouthernSpearCore` is the root of the SS dependency graph: it depends on no other Southern Spear plugin and on no Lyra module, so team identity cannot reach weapons, damage, health, abilities, roles, objectives or UI. `Tools/validate_architecture.py` enforces this statically and runs in CI.
- Kill-feed, scoreboard and post-round presentation must draw from `ESSTeamId` and resolve locality locally, never from a replicated locality value.

---

## Open Decisions

> Renumbered 2026-09-26. ADR-016 and ADR-017 were previously unused placeholders for
> Phase 5 questions; they are now taken by the two decisions recorded above, and the
> placeholders moved to ADR-018..ADR-021. No question was answered or dropped by the
> renumbering.

| ID | Question | Needed by |
|---|---|---|
| ADR-018 | Online services: EOS vs Steam vs custom, and in what order? | Phase 5 |
| ADR-019 | Anti-cheat: vendor, platform-provided, or bespoke? | Phase 5 |
| ADR-020 | Match size: 16, 32 or 64 baseline? | Phase 4, after performance profiling |
| ADR-021 | Whether to retain or drop Lyra's third example experience (Exploder) | Phase 1 |

### Resolved

| Former ID | Question | Resolution |
|---|---|---|
| ADR-013 | Repository path: relocate off a space-containing path? | Relocated — ADR-014 |
| ADR-013 | Electric Dreams: use as a base map or harvest art? | Declined entirely — ADR-013 |
| ADR-003 | Match-relative team identity | Superseded by ADR-017 — stable `ESSTeamId` plus locally derived `ESSLocality` |

---

## ADR-018 — Objective Assault vertical-slice rules and ownership

**Status:** Accepted
**Date:** 2026-09-26

**Context.** VS-12 and VS-13 need an objective and a round that can be won, fail and restart.
`MAPS_DRYRIVER.md` §4.1 and §6.1 fix the map side: two objectives, taken sequentially, contested by
both teams, with an equidistant opening. The GDD's attacker/defender wording assumes asymmetric
roles that the vertical slice does not have yet. Gameplay must stay free of Lyra types and
presentation (ADR-004, ADR-017) so it can be tested headless.

**Decision.**

- **Neutral, sequential objectives.** Every objective starts neutral. Only the active one can
  change. Capturing it locks it for the rest of the round and play moves to the next.
- **Capture is presence, not strength.** One uncontested player captures at the same rate as five.
  Both teams present freezes progress. An opposing team must neutralise existing progress to zero
  before building its own. An empty objective decays to zero.
- **Outcome.** The team that captures the final objective wins. If the round clock expires first,
  the round is a **draw** (the "fails" case). After a post-round hold, the round resets and restarts.
- **Ownership.** The pure rules (`FSSObjectiveRules`) hold all logic. `ASSObjectiveActor` and
  `ASSObjectiveAssaultDirector` in `SouthernSpearObjectives` run them on the server and replicate
  the results. Team membership is read through `IGenericTeamAgentInterface`, and the director maps
  Lyra's generic team ids (1, 2) to `ESSTeamId`. The module depends on SouthernSpearCore only.
- **Experience.** `SSExp_ObjectiveAssault` is a content-only Game Feature. Its experience reuses
  ShooterCore's pawn, input, HUD and Lyra's own two-team setup, spawning rules and bots. Director
  and objectives are placed in the map by `Tools/Unreal/setup_objective_assault.py`.

**Consequences.** Both teams are mechanically identical by construction. A symmetry test enforces
it: mirrored inputs give mirrored results. Respawn limits, elimination rules and attacker/defender
asymmetry are deferred and need their own ADR. Parallel objectives on Dry River are not allowed
until the OBJ B distance asymmetry in `MAPS_DRYRIVER.md` §6.1 is rebalanced.

## ADR-019 — SouthernSpearLyraBridge: the one guarded Lyra dependency

**Status:** Accepted (producer decision, 2026-09-26)
**Date:** 2026-09-26

**Context.** Viewer-relative team tint (ADR-017) and a Southern Spear health/ammo HUD need Lyra data
(team ids, attributes, equipment). Core, Team, Objectives and their UI must stay Lyra-free (SS002), and
Lyra stays unmodified (ADR-002).

**Decision.** A new plugin `SouthernSpearLyraBridge` is the **only** `SouthernSpear*` module that may
depend on `LyraGame`. It adapts Lyra to Southern Spear rules on the client and holds no gameplay rules of
its own. No Southern Spear module may depend on it (guard SS001), and SS002 now bars Lyra from every
other `SouthernSpear*` module. First use: `USSViewerTeamTintSubsystem`, which re-tints pawns from the
local viewer's side through `FSSTeamIdentity::ResolveLocality` (own team sage, other team OPFOR clay).
Viewers without a playable team keep Lyra's absolute colours. `ULyraTeamDisplayAsset` is not exported, so
the bridge sets Lyra's five team colour parameters directly.

**Consequences.** Lyra coupling is in one place, which can be replaced when Lyra is. The tint re-applies
every 0.5 s to stay on top of Lyra's own re-application (parameter sets only).

## ADR-020 — Original art built in Blender by script

**Status:** Accepted (producer decision, 2026-09-26)
**Date:** 2026-09-26

**Decision.** Character, weapon and gear art for the vertical slice is original, built by scripts in
`Tools/Blender/` (reproducible, reviewable, legally clean; licence class "original"). Weapons come first
(A88 family, A89, A4, MAF counterparts per ADR-016), as static meshes attached to Lyra's weapon
sockets so Lyra's animations keep working. Gear and uniforms (CMECU) come next, skinned to the Lyra
mannequin skeleton. Quality starts at placeholder and improves over time. Marketplace or commissioned
art is not used unless a later decision says so. No real-weapon CAD, brand marks, or copied patterns.


## ADR-021 — Licensed third-party art: free Fab and cleared Sketchfab assets

**Status:** Accepted (producer decision, 2026-09-27). Partly supersedes ADR-013 (no third-party
environments) and narrows ADR-020 (original art only).
**Date:** 2026-09-27

**Decision.** Alongside original Blender art (ADR-020), the project may use:

- **Fab and other assets acquired/held for Southern Spear** may be used in this free-to-play game under the producer's project-specific direction (ADR-028/035). This does not assert one universal marketplace licence or authorize redistribution of raw vendor source.
- Preserve known publisher, seller, source and attribution information as provenance/credits; missing metadata is explicitly unverified, not a permission hold.
- **Sketchfab source terms remain provenance.** Record actual terms and credit where available; the producer's ADR-035 direction governs the project's use. Commercial-game rips remain excluded, and Electric Dreams retains its separately declined disposition (ADR-013/L-0012).

Register each acquired/used item and its source information, and preserve the source-versus-derivative distinction. Art direction can prefer original designs and fictional presentation, but real names, equipment, camouflage and marks are not prohibited by ADR-035. Dry River's layout remains original under ADR-013/015; the producer has separately directed whole-pack map use for Red Gum and Bluestone.

**Consequences.** Follow the project's raw-source handling policy and keep vendor content from public source redistribution. This is a project handling direction, not a claim that every marketplace listing has identical terms.

**Execution note (2026-09-27).** Under ADR-021, the CC BY 4.0 Sketchfab scans Split Point and Bingie Bingie were staged unchanged as source files at `Content/SouthernSpear/Vendor/SAVollgger/`; see ENV-001/ENV-002 and L-0013/L-0014. Staging does not make them game-ready or imported Unreal assets. Their use still requires asset review and attribution; map layout remains original.

## ADR-022 — Red Gum Station: first playable map from the Fab "Rural Australia" pack; Fab soldier bodies

**Status:** Accepted (producer direction, 2026-09-27: "use the Rural Australia map as the base for our
first map"). Supersedes ADR-013/ADR-015's original-layout rule **for this map only** (Dry River stays
original). Extends ADR-021 to whole-map reuse and to character bodies.
**Date:** 2026-09-27

**Decision.**

- `L_RedGum_01` ("Red Gum Station") is built by `Tools/Unreal/build_redgum_level.py` from the Fab
  pack's `RuralAustralia_Example_01` (1 km landscape, single level, not World Partition). It is saved as
  a new map; the pack's own map is never saved. Objectives: Bore Pump, Homestead, Shearing Shed. Two
  deployments sit 560 m apart.
- Wire fences carry no collision, on the pack's two fence meshes. Pawns pass through (Lyra has no vault)
  and the fences do not split the nav mesh. The fence Blueprint rebuilds its components on load, so a
  per-instance change does not persist.
- `build_redgum_nav.py` builds navigation. It then moves any objective or deployment that cannot reach
  the centre objective, and fails unless every leg connects.
- Soldier bodies are Fab characters shown by `ASSCharacterPartActor` (SouthernSpearTeam). Each mesh
  follows Lyra's animated mannequin by bone name (leader pose); no retarget is needed because all
  three packs use UE-mannequin bone names. The viewer's own team is shown as 3 ACR (Quantum military
  character) and the other team as MAF. MAF uses parts of the "Modern Insurgent 7" pack chosen for a
  conventional uniform: head, hands, sweater, military trousers, shoes, plate carrier and beret. No
  balaclava, beard, pakol, scarf or other irregular gear (ADR-016). Pack names that say "insurgent"
  never appear in data, UI or public docs.
- Architecture: new `ISSLocalityPresentable` interface in Core, which the Lyra bridge calls. No new
  module dependencies; the guard passes.

**Consequences.** The map and the soldier Blueprints reference git-ignored Fab content, so a clone
needs the same packs added from Fab (R-19). The soldier looks still need a visual check for real
insignia or patches (R-20).

## ADR-023 — Southern Spear UI replaces Lyra's HUD, front end and loading screen

**Status:** Accepted (producer direction, 2026-09-27: "still has lyra stuff everywhere ... do a pass for the
ui/ux"). **Date:** 2026-09-27

**Decision.**

- New plugin `SouthernSpearUI` (Core and UMG only; no Lyra) holds the player HUD, match menu, front end
  (`ASSFrontEndGameMode` on `L_SS_FrontEnd`) and loading screen.
- The HUD data is `USSLocalHudState` in Core: plain values, client-only, never read by gameplay. Only the
  Lyra bridge writes it.
- Minimap and full map live in `SouthernSpearObjectivesUI`, because they draw objectives.
- The experience no longer uses Lyra's StandardHUD. Lyra's reticle, kill feed and nameplates are gone
  until Southern Spear equivalents exist.

**Consequences.** The Esc menu and M map read raw keys, not Enhanced Input actions; rebinding needs a
later pass. The UI is C++-built, so there are no Blueprint widget assets to maintain.

## ADR-024 — Locomotion rebuild: Southern Spear character, movement component and animation stack

**Status:** Accepted (producer, 2026-09-27: "let's do it", on `Docs/LOCOMOTION_AUDIT.md`).
**Date:** 2026-09-27

**Decision.** Follow the staged roadmap in `LOCOMOTION_AUDIT.md` §4:
- A C++ character `ASSCharacter` (child of `ALyraCharacter`) and `USSCharacterMovementComponent` in the
  Lyra bridge own tactical movement: gaits, stances, lean, momentum; replicated with saved moves.
  Lyra stays unmodified.
- First person moves onto the real body, with hands on the weapon (IK) and a procedural layer on top.
  The camera-held view model and the arms-pack code are removed.
- Full-body motion matching from Epic's Game Animation Sample (GASP), with weapon overlays adapted from
  Lyra's item layers.
- The Pose Search, Chooser and Motion Warping engine plugins are enabled when that stage lands.

**Consequences.** Movement values change (gameplay), so each stage ships automation tests. GASP is Epic
content: git-ignored, like the other Epic packs (R-14).

## ADR-025 — Real Australian Army look from the ADFRC set (producer override of ADR-016's pattern rule)

**Status:** Accepted (producer choice, 2026-09-27: "Real ADF look (ADFRC)").
**Date:** 2026-09-27

**Decision.** The friendly side (3 ACR, as each viewer sees their own team) wears ADF-style kit built from
the ADFRC set (L-0021: authorisation email from the mod team's author, `Docs/evidence/L0021_*`):
- Crye-style combat uniform;
- TBAS plate carriers and pouches;
- Ops-Core and Team Wendy helmets, bush hat, backpacks;
- **AMCU camouflage textures**.

The gear is re-rigged to the UE5 mannequin skeleton in Blender (`Tools/Blender/`), so the visible body is
the animated skeleton (audit F3).

**Overrides.**
- ADR-016's "no Auscam copies" rule, for the ADFRC AMCU textures only.
- The quarantine on converting ADFRC files, for the weapons (already in use) and the uniform and gear.

Unchanged:
- no unit insignia, badges, Rising Sun, mottos or colour patches: patch and flag decals are stripped;
- fictional unit names (3 ACR, MAF);
- MAF stays a conventional force with its own look.

**Historical risk statement — superseded by ADR-035.** The original ADR-025 described Defence permission or a CMECU swap as a commercial-release condition. ADR-035 later accepted acquired ADFRC assets for Southern Spear's F2P use and closed R-27 as a permission/substitution gate. Retain the no-endorsement disclaimer and provenance/credit records; no separate permission gate remains.

## ADR-026 — Two small, documented departures from Lyra: the hero class and bullet penetration

**Status:** Accepted (producer, 2026-09-28: "do it" to the proposed order, penetration via "a small documented Lyra hook").
**Date:** 2026-09-28

**Decision.** Lyra stays vendored and otherwise unmodified. Two departures are allowed, each logged in
`Docs/LYRA_ADOPTION.md` and re-applied by script if Lyra is ever updated:
1. **D-08: hero class.** `/Game/Characters/Heroes/B_Hero_Default` (Lyra content) is reparented from
   `ALyraCharacter` to `ASSCharacter` (bridge), by `Tools/Unreal/setup_tactical_movement.py`. Copies of the
   hero (`B_SS_Hero*`) broke Lyra Blueprints that identify the hero by class (for example
   `B_WeaponInstance_Base` casts to `B_Hero_ShooterMannequin`): bots never fired. The copies are deleted and the
   experience uses Lyra's `HeroData_ShooterGame` again.
2. **D-09: bullet penetration.** A narrow hook in `ULyraGameplayAbility_RangedWeapon` (not exported, so it
   cannot be subclassed from the bridge): hit traces continue through thin surfaces with reduced damage.
   Lyra's own code stays free of Southern Spear types.

**Why.** Both features need behaviour that Lyra only exposes by class identity or unexported code; the
alternatives (copying Lyra's hero and weapon chain) were tried for the hero and failed.

**Consequences.** Lyra updates need the two departures re-applied (script for D-08; code patch for D-09).

---

## ADR-027 — Ravenshoe Crossing: an original Australian gorge crossing, no third-party base

**Status:** Accepted (producer decision, 2026-09-28: "Snowy gorge + wrought-iron road bridge"; "scoping
doc + ADR + register rows").
**Date:** 2026-09-28 (inventory scope corrected 2026-10-01)

**Context.** The producer asked for a map "re-creating the famous bridge crossing map from *America's Army
2*, with an Australian twist", built from the assets already in the project plus the Fab packs in
`Content/Downloaded/VaultCache/`. The 2026-09-28 cache inventory was limited and its count claims below are historical, not a complete inventory. The 2026-10-01 recursive audit found additional FabLibrary listings, 29 other VaultCache roots and installed Content roots including `AutomotiveBridgeScene`; see `ASSET_REGISTER.md` §§4.9m–o. That request sits against four standing constraints: **L-0008**
(no *America's Army 2* content of any kind), **L-0007** (no commercial game models), **ADR-013** (maps
are built original; a third-party environment is never a base map) and **ADR-021** (licensed third-party
art may dress an original layout but never define one).

The original 2026-09-28 inventory and keyword sweep shaped the map's **original-design decision at that time**, but did not cover all cache and installed Content. They found no bridge asset selected for reuse in the Ravenshoe design then. The 2026-10-01 snapshot additionally found `AutomotiveBridgeScene` installed locally, but it is not among the 14-pack map dependency set and no use in Ravenshoe is established by this inventory. Therefore the original layout/bridge design remains the adopted decision; the old sweep must not be cited as proof that no bridge-like asset exists anywhere in the project or cache. Any future reuse would require a deliberate ADR/art-direction review and may dress, not define, the original map (ADR-013/ADR-021).

**Decision.**

- **Ravenshoe Crossing** (`/Game/Maps/L_Ravenshoe_01`) is designed and built **original**: 300 × 200 m,
  a high-country granite gorge crossed by a **wrought-iron lattice-girder road bridge**, with a **stone
  road-gate house** whose arched road passage is the terminal objective. Design in `Docs/MAPS_RAVENSHOE.md`.
- The bridge, the gatehouse, the abutments and the gorge walls are **modelled by us** in Blender and are
  **Class F** (L-0011, ADR-020). They are dressed with producer-cleared acquired packs by reference; any
  legacy “Class A” label describes source metadata, not the current project-use basis under ADR-035.
- **Only the design principle is taken from the reference**, and it is stated as such in the map document:
  a single chokepoint, a threshold-shaped terminal objective, a hard axial lane, flanking approaches, and a
  playable lower space. **No geometry is traced or approximated, no names are carried across, and no AA2
  asset is used.** The bridge is specifically a **lattice girder, not a masonry arch** — the reference's
  signature form is rejected on both provenance and gameplay grounds (a stone parapet is a dead lane; a
  lattice is a repeating cover rhythm).
- The 20 m maximum-open-crossing rule in `MAPS_DRYRIVER.md` §5 is **not** silently waived. The 68 m deck
  is recorded as the map's one deliberate exception, with four named mitigations that must exist in the
  blockout or the exception is unjustified.
- Objective A sits at **mid-span**, not at a bridgehead, because a bridgehead objective is 68 m closer to
  one deployment than the other and no amount of dressing repairs that. Objectives are **sequential A→B**,
  which is what makes the mid-span choice fair under `MAPS_DRYRIVER.md` §6.1.
- The **known northern overwatch asymmetry is recorded, not hidden**, with the same treatment Dry River
  §6.1 gives Bravo's advantage and the same rebalance rule (terrain only, never team capability, ADR-003).

**Alternatives.**
- *Reuse the *America's Army 2* layout and geometry* — rejected. Barred outright by L-0008 and L-0007.
- *Adopt the reference's stone-arch vocabulary* — rejected. It is the reference's most identifying feature,
  and a stone parapet is worse cover geometry than the lattice that replaces it.
- *Model a tropical timber trestle or an arid steel truss* — rejected. The trestle's piers fragment the
  deck into a pick-up-beat shooter space; the arid truss gives up the gorge depth that makes the second
  lane exist at all.
- *Select a third-party bridge/environment as the Ravenshoe base* — rejected. The original-map decision remains; the 2026-10-01 inventory surfaced an installed `AutomotiveBridgeScene` root but did not add it as a map dependency or establish it as a selected bridge asset.
- *Import a cache-only VFX pack as Ravenshoe geometry* — rejected as irrelevant. VFX content does not define the original map layout.
- *Wait for a capture on Red Gum before designing another map* — rejected. Red Gum's stalemate is a
  balance problem in a 1 km open map, not a reason to stop designing small maps.

**Consequences.**
- The map introduces no new third-party pack through its original structural mesh assets; it does have
  producer-cleared third-party dressing dependencies as listed in `PACK_MANIFEST` and `ASSET_REGISTER`.
  No new pack was claimed as imported specifically for the original bridge/gatehouse design.
- The original map geometry was buildable from project-authored sources; its dress layer references producer-cleared acquired packs as listed in `PACK_MANIFEST` and `ASSET_REGISTER`. The distinction supports the original-map decision under L-0008 without claiming the whole map is dependency-free.
- Two original Blender generators are needed (`ravenshoe_bridge.py`, `ravenshoe_gatehouse.py`) plus a
  `Tools/Common/ravenshoe_spec.py` shared with the CI verifier, following the `dryriver_blockout.py`
  pattern.
- The inventory exposed a **pre-existing licence gap**: nine already-installed Fab packs, including
  `Scene_QuarrySlate` which this map builds on, had no row in either register. Corrected in this session
  as bookkeeping under **L-0016b**. No asset changed.
- **Historical 2026-09-28 map-count decision:** Ravenshoe was then a candidate fifth map (`M-008`), not a replacement for Dry River as the slice test bed. It was subsequently built and registered; current implementation/readiness is in `MAPS_RAVENSHOE.md` and `ASSET_REGISTER.md` §4.9.
- Sizing, rotation distances, cover counts and sightlines are **design targets until the blockout is
  generated and measured**. Navigation must be baked in the interactive editor, and no cover or sightline
  figure may be quoted from a commandlet.

## ADR-028 — Acquired Fab assets are cleared for Southern Spear's free-to-play game

**Status:** Accepted (producer, 2026-09-28: "EVERY asset added via FAB is free for our use case ... no need to
keep looking it up"); reaffirmed 2026-10-01 under ADR-035. Extends ADR-021.
**Date:** 2026-09-28 (reaffirmed 2026-10-01)

**Decision.** Assets acquired/held for Southern Spear from Fab are producer-cleared for use in this free-to-play
game. This project-specific direction means no per-asset permission hold is required. Record available seller,
source, terms and attribution as provenance/credit information; missing metadata and `isAiForbidden` values do
not create holds. This is not a universal marketplace-licence assertion and does not authorize raw-source
redistribution. ADR-035 separately records the scope and exceptions.

**Still applies (not permission holds):** the no-endorsement disclaimer, content-ethics rules, applicable credits,
raw-source handling under ADR-021/R-14, and the prohibition on content from ripped commercial-game sources
(L-0007/L-0008). A specifically declined asset such as Electric Dreams (ADR-013/L-0012) remains excluded unless
a later producer decision explicitly changes that disposition.

**Map base.** On the same direction ("activate that african map"), `L_Bluestone_01` uses the Fab African Slate
Quarry scene as its base, as ADR-022 did for Red Gum; ADR-013's original-layout rule is superseded for that map only.

## ADR-029 — Third-party props are prepped in Blender before import, never imported raw

**Status:** Accepted (2026-09-28)
**Date:** 2026-09-28

**Decision.** Every third-party prop mesh enters the project through a Blender prep pass
(`Tools/Blender/prep_fab_props.py`) that measures the file, rescales it to real-world size, strips the
vendor's ground plane, re-pivots it base-at-z-0, and decimates it to a stated triangle budget. The
project holds the prepped copy; the vendor file in the Fab cache is never edited. Props then enter the
engine by reference, with the material applied as a **per-instance component override** rather than on the
mesh asset's slots.

**Why.** ADR-021 lets licensed art dress an original layout, but says nothing about the condition the art
arrives in. Measured on the 2026-09-28 delivery: the red car wreck authors at **27.3 × 21.0 × 11.2 m** and
**1,166,165 triangles** because it is a scan carrying a ground plane at roughly six times real scale; the
hand pump authors **5.85 m** tall. Imported raw, the map gets a 27 m car on a 6 m-wide bridge and a
person-sized obstacle that is four times human height. A 75 MB four-car pack was rejected for the same
reason: the single wreck covers the need at a third of the file size. The triangle budgets are the second
half — the compressor was rejected at 73,622 triangles for a 2.5 m prop, and 19,751 triangles for a flat
0.77 m debris piece is not a trade this map should make.

**The per-instance material rule.** On UE 5.8 every route to a `StaticMesh`'s material *slots* is a silent
no-op: writing into the array from `get_editor_property("static_materials")` mutates local copies, and
assigning it back with `set_editor_property` does not persist. The slots read back `[None, None]`. The
component override `StaticMeshComponent.set_material(i, mat)` is a real component property, survives a save
and reload, and is what actually renders. Props therefore carry their material per instance, and
`audit_ravenshoe.py` checks the component, not the asset.

**Verification, not assertion.** `Tools/Unreal/audit_ravenshoe.py` re-opens the saved `.umap` and measures:
the wreck at **z = 14.00 m** on a 14.00 m deck, inside the 7.5 m footprint, blocking, on an authored
`ScanPBR` instance, with all four VFX components holding live Cascade templates. **32/32 pass.** This is
load-bearing: an earlier version of the pass reported 26 actors placed and **0 errors** against a `.umap`
that was byte-for-byte unchanged, because `get_editor_world()` had handed it a blank untitled level. A pass
that reports success is not evidence; every placement in this project is checked from outside.

---

## ADR-030 — The bridge's surfaces are generated original textures, not an imported pack

**Status:** accepted, 2026-09-28. Extends ADR-029 and L-0011. Relates to M-008m, M-008n.

**Historical context (2026-09-28 design snapshot; inventory scope corrected 2026-10-01).** Ravenshoe Crossing was delivered with four *constant* materials on the one structure the map is named for. The selected original geometry is a 68 m lattice girder with 21 uprights a side. At the time, the project review had not selected or established a reusable bridge mesh; the 2026-10-01 inventory later found `Content/AutomotiveBridgeScene/` installed locally, but did not identify it as a Ravenshoe dependency or selected bridge asset. The authored bridge rendered as flat colour because its materials were not configured. The original Fab-cache sample counted 30 folders, 23 with fewer than ten images, mostly prop albedos rather than tileable PBR sets; the later recursive inventory found 50 FabLibrary folders and supersedes that sample as a cache-wide count. The review also identified `Content/AutomotiveBridgeScene/` (319 assets of asphalt, concrete, rust and steel decal maps) as untracked in the then-current checkout. Binding the committed map to that concurrent/untracked content would have left it broken for a checkout without those files; that historical reproducibility concern remains distinct from whether an installed pack exists.

**Decision.** Generate the surfaces. `Tools/Textures/make_ravenshoe_surfaces.py` authors four sets —
sealed gravel road, rusted ironwork, painted steel, coursed granite — from noise, on exactly the
ground the character camo sets already stand on (CH-TEX-001, ADR-016, L-0011). They are wired to the
project's own `M_SS_ScanPBR` as instances, so pack textures and generated textures feed one shader.

**Why not a Fab texture pack.** Three reasons, and the third is the one that decides it. Licensing is
manageable — ADR-028 clears Fab generally, and a register row would cover it. Fit is arguable: most
scan texture packs are European or North American in weathering and read wrong in Australian
high country. But a *tiling* texture is only useful if it tiles, and that is a property of the
generator, not of the marketplace. Buying a texture means accepting whatever the author made, and a
non-periodic one shows a hard grid the moment it is repeated across a 68 m deck.

**Two constraints enforced in the generator rather than left to eye.**

*A tiling map carries no low-frequency content.* The first gravel set had a wheel-wear crown baked in.
It looked good alone and would have come back every tile as stripes down the road. The crown was
removed; large-scale interest now comes from tiling the set at different scales.

*A seam test that is actually a seam test.* Three versions were wrong before one was right. An
absolute difference flags correct sets, because adjacent samples of a high-frequency field always
differ. A ratio against the *mean* interior step flags them too — the wrap is one sample pair out of a
thousand, and its step size varies hugely by chance, scoring a good set at 2.7. The test that holds is
the wrap step against the tile's own **99th percentile** of interior detail: a real discontinuity
exceeds the strongest thing already in the texture, and a merely busy one does not.

Granite needed a **bed joint**, not just perpends. The first version generated vertical joints only,
which is not coursed masonry — it is a wall of vertical strips, and it rendered as flat grey slabs.
Masonry is defined by the horizontal bed joint as much as by the perpends.

**Tiling is arithmetic, not taste.** The blockout unwraps with `cube_project(cube_size=2.0)`, so one
UV unit is **2 m**, and the terrain uses a planar projection at `v/4.0`, so one unit is 4 m. The first
table of tiling values assumed 0..1 UVs and produced 0.53 m tiles against a 7.5 m deck — a 1024 map
repeating every half metre, which is the same greybox problem wearing a texture. Values are now
`uv_metres_per_unit / target_tile_m`: 2.0 m for the road, 1.5 m for the ironwork, 0.9 m for the deck
structure, 1.2 m for the masonry.

**The running surface is its own slot.** The deck slab is a single box, so its top and its fascia
shared one material. They are now split by polygon into `Road` and `Deck` slots. The fault this
prevents is invisible from the deck, which is exactly why a verifier checks it: the Road slot's area
must equal deck width × span, and no Road face may be non-horizontal.

**Three pre-existing bugs this work exposed, all now fixed and all of the same shape.**

`import_ravenshoe.py` called `MaterialEditingLibrary.get_material_property`, which does not exist in
5.8. The call raised, was caught, and became a warning — so the "authored constant materials" had
never been configured. It also read `material_slot_name` as a `str` and called `.strip()` on a
`unreal.Name`, which aborted the whole slot loop, so **the mesh slot override had never run**. And it
called `set_actor_location` without the now-required `sweep` argument, so the NavMeshBoundsVolume was
never positioned. All three were reported as *warnings* on a pass whose summary said "0 errors".

The import was also not idempotent: it purged only `SS_Raven_`-prefixed actors, while objectives and
deployments are labelled `SS_MAP_Ravenshoe_*`. Every re-run added another objective and another
deployment — the audit read 2, then 4, then 6. It was invisible until the pass was run a second time.

**Run order is now load-bearing, and is stated in all three scripts.**
`import_ravenshoe` → `dress_ravenshoe_props` → `setup_ravenshoe_surfaces`. The import re-imports the
bridge FBX and re-spawns the geometry actors, which strips the per-instance overrides; run the
surfaces pass first and the next import silently returns the bridge to flat colours with the Road slot
on `WorldGridMaterial`, reporting no error. `audit_ravenshoe.py` asserts the overrides **on the saved
map**, which is the only place that failure can be caught rather than shipped.

**Verification.** `verify_ravenshoe.py` **53/53** in Blender (was 41) including twelve new probes that
ray-cast the built bridge and count members off its vertices; spec-only mode still runs in CI with no
Blender. `audit_ravenshoe.py` **35/35** on the re-opened `.umap`, 468 actors, and the import is
idempotent at 467–468 actors across repeated runs.

---

## ADR-031 — Section Assault: one life per round, attack and defend, first to five

**Status:** Accepted (producer, 2026-09-28, in session: "yep, sounds good" to the proposal of a
single-life, attack/defend round mode modelled on the *design philosophy* of America's Army 2's
main mode). Completes the item ADR-018 deferred ("respawn limits, elimination rules and
attacker/defender asymmetry ... need their own ADR").
**Date:** 2026-09-28

**Context.** Objective Assault (ADR-018) is symmetric and has unlimited respawns: both teams contest
neutral objectives, and a round lasts up to 15 minutes. The game this project takes its design
philosophy from was round-based: one team attacks and one defends, every player has one life per
round, and the dead watch until the round ends. That rule is what makes information worth more than
reflexes (GDD §1), and the current mode can't express it.

**Decision.** A second rule set, **Section Assault**, runs on the same director, objectives and maps.
It is chosen per match (`ASSObjectiveAssaultDirector::RulesMode`, or `?Rules=Section` on the map URL),
so every existing map can run it without asset changes.

| Rule | Value (data, `FSSSectionRules`) |
|---|---|
| Lives | **One per round.** A player eliminated mid-round is held out until the next round. A player who joins mid-round waits for the next one. |
| Sides | One team **attacks** and the other **defends**. Team One attacks in the first half and Team Two in the second, so the mode is symmetric **over a match** (ADR-017), not within a round. |
| Objectives | Taken in sequence, as in ADR-018, but **only the attackers capture**. Defenders on the point freeze it (contested). Defenders alone on it clear the attackers' progress at the capture rate. |
| Attackers win | Taking the final objective, or eliminating every defender. |
| Defenders win | Eliminating every attacker, or **the clock running out** (the "fails" case is now a defender win, not a draw). |
| Draw | Both teams eliminated in the same step. |
| Match | `RoundsPerHalf` = 4 by default: halves of four rounds, **first to five** wins. 4–4 after eight rounds is a drawn match. |
| Round clock | 300 s by default (`?RoundSeconds=` still overrides). Pre-round and post-round holds come from `FSSRoundRules`. |

Resolution order within one step: capture of the final objective, then mutual elimination, then
attacker elimination, then defender elimination, then time. A capture on the frame time runs out
counts, as in ADR-018. A side with nobody on its round roster can't be "eliminated" (a lone player
testing against an empty team isn't declared the loser).

**Ownership.**
- Pure rules: `FSSSectionAssaultRules` (`SouthernSpearObjectives`). No world, deterministic, tested.
- Server round loop: `ASSObjectiveAssaultDirector` (the same actor, branching on `RulesMode`), with
  replicated `FSSMatchState` (round score, attacking team, half, alive counts, last round's reason).
- Who is alive: `USSRespawnGate` (`SouthernSpearCore`, server). The director locks it with the round
  roster when play starts and unlocks it at the reset. The Lyra bridge reports each elimination to it.
- Holding the dead out: Lyra's own restart gate (`ULyraPlayerSpawningManagerComponent::ControllerCanRestart`)
  is private and non-virtual, and changing it would modify Lyra (ADR-002). The bridge's
  `USSDeploymentSpawningComponent` overrides the supported virtual `OnFinishRestartPlayer` instead:
  when the gate says a controller must stay out, the pawn Lyra just spawned is unpossessed and
  destroyed in the same server frame, before it can replicate. RE-DEPLOY is refused while the gate is locked.
- At the round reset the director restarts **every** pawnless controller, bots included, because
  Lyra's own respawn for them was suppressed during the round.

**Alternatives.**
- *Replace `B_LyraGameMode` with a C++ subclass that overrides `ControllerCanRestart`* — rejected for
  now. It changes `GlobalDefaultGameMode` for every map and discards whatever the Blueprint configures,
  which can't be checked without the editor. Revisit if the same-frame destroy shows any artefact.
- *Remove `GA_AutoRespawn` from the experience's ability set* — rejected: that's asset data, and it
  would fix the respawn model per experience instead of per match.
- *Ticket-limited respawns* — that's Secure and Hold (GDD §4.6), a separate mode.

**Consequences.**
- The existing Objective Assault behaviour is unchanged when `RulesMode` is `ObjectiveAssault` (the default).
- **Not in this decision:** spectating a living teammate after death (the dead player's view stays
  where they fell, under KILLED IN ACTION), a freeze on movement during pre-round, bomb/plant-style
  objectives, and map rotation at match end (the match restarts on the same map). Each is follow-up work.
- The objective HUD doesn't show attack/defend, the round score or alive counts yet. `FSSMatchState`
  replicates everything it needs.
- No *America's Army 2* content is used: this is a rule set, not a map, mission name, UI or asset (L-0008).

---

## ADR-032 — SouthernSpearProgression: service record, ranks and capped XP, server-awarded

**Status:** Accepted (producer, 2026-09-28, in session: "start wiring up the ranking system, and
player profile system"). Implements TDD §6.2–6.4 and decision D-04, with the deviations listed below.
**Date:** 2026-09-28

**Decision.** A new plugin, `Plugins/SouthernSpearProgression` (module `SouthernSpearProgression`,
export macro `SSPROG_API`), depends on `SouthernSpearCore` only, like every SS plugin (SS001, SS002).

- **Service record, schema v1** (`FSSServiceRecord`): schema version, player id, callsign, service XP,
  statistics, qualifications (earned, permanent) and commendations. Loading runs a migration step.
  A record from a *newer* schema is refused, not silently mis-read.
- **Persistence behind an interface** (`ISSPersistenceProvider`). The only implementation is
  `FSSLocalDevPersistence`: one human-readable JSON file per player under
  `Saved/SouthernSpear/Profiles/`, written to a temporary file and then moved over the original.
  It says `IsAuthoritative() == false`. It's **dev-only** (TDD §6.3 point 4). A corrupt file is kept as a
  `.corrupt` backup and the player starts a new record, with an error in the log.
- **Ranks and awards are data** (`USSProgressionSettings`, `Config/DefaultGame.ini`): the nine
  enlisted ranks from GDD §6.2 with their thresholds, and one award rule per service event.
- **Service events** (`ESSServiceEvent`, `USSServiceEventSubsystem`, in Core): objective captured,
  round won, round won and survived, match completed, match won, friendly kill. **There is no kill
  event and there can't be one** (GDD §6.4). Guard rule **SS009** fails the build if a `*Kill*` member
  other than `FriendlyKill` is added.
- **Caps.** Every positive award has a per-match cap (`MaxPerMatch` ≥ 1). A test fails if a rule has
  no cap. Penalties (negative awards, currently friendly kill) are **never** capped: the tenth team kill
  costs as much as the first. Service XP never goes below zero.
- **Server-awarded.** The server tallies events per player per match, applies the caps and sends each
  granted award to the owning client (`USSServiceRelay::ClientServiceAward`). The client applies it to
  its local record and saves. Bots earn nothing.
- **Profile display** goes through Core (`USSLocalProfileState`), because the UI modules may depend on
  Core only. The front end and HUD read callsign, rank, XP and the next threshold from it.

**Deviations from the TDD, and why.**
- *Config instead of `DT_SS_ProgressionCurve` / `UFSSRankDefinition` assets.* A config file is data
  and editable without recompiling, which is the requirement. It can be authored and reviewed as text
  (asset creation isn't possible in every working environment). The loadout (`SSLoadoutSettings`)
  already set this precedent. A DataTable can replace it behind the same settings class later.
- *One XP track, not account level plus service rank.* Rank is driven by service XP. Account level
  and cosmetics are deferred until there is something to unlock.
- *`ISSPersistenceProvider` is a plain C++ interface, not a `UINTERFACE`.* Nothing needs it in Blueprint,
  and this keeps it testable without UObjects.

**Known limit, stated plainly.** A local, non-authoritative record can be edited by its owner. That's
acceptable for development and explicitly **not** acceptable for release. Online persistence
(`FSSOnlinePersistence`, server-validated) is Phase 5 work and needs its own ADR.

---

## ADR-033 — Historical G3 texture decision (superseded in active appearance by ADR-042)

**Status:** Historical texture/use decision accepted 2026-09-28; active friendly body and camo routing are superseded by ADR-042 (2026-09-30). Retain the original technical findings as history.
**Date:** 2026-09-28
**Amends:** ADR-016 (the sentence "The CMECU is an original pattern. AMCU and commercial MultiCam are
not reproduced, traced or approximated tile-for-tile") and ADR-016's `CMECU` naming row.
**Supersedes:** L-0022's "Retune (Session 042)" note, which recorded the sets as noise-generated because
sampling the ADFRC material was out of bounds under ADR-016.

**Context.** The soldiers looked bad, and the cause was not the rig. The friendly and MAF bodies were
dressed with a 64x64 flat colour texture (`Art/Characters/ADF/T_ADF_Coyote.png`, `T_ADF_Olive.png`) —
roughly 35 px/m against the ~512 px/m a third-person character wants. Every other layer was fine: the
normal and specular/metal/dirt masks were already bound, the layout was already the G3 UV set, and the
skinning was already correct. One texture resolution was carrying the whole problem.

That fallback was deliberate. `Tools/Unreal/setup_adf_soldier.py` reached it by design, with the comment
"No Multicam (ADR-016)", because ADR-016 forbade using the ADFRC uniform textures. That prohibition was
a **house style rule, not a licence condition**, and it was wrong on the facts: L-0021 already records
that the ADF Re-Cut team granted **blanket 100% permission** across all credited authors, and line 442 of
the same register states plainly that **"The camo itself is Class F and carries no restriction."** The
mod team's own work was cleared all along; ADR-016 was the only thing in the way.

**Historical decision (superseded in active appearance by ADR-042 and in project-use policy by ADR-035).** ADR-016's camouflage clause was withdrawn in this historical decision. At that time, the proposed G3 implementation used ADFRC textures at source resolution. This is not the current body/material assignment: Quantum modules are active and their component-level DPCU-derived camo override is described by ADR-042 and ASSET_REGISTER CH-TEX-004.

- `Tools/Unreal/setup_adf_soldier.py` stops substituting the 64x64 flat colour and binds the real
  ADFRC `_co` / `_nohq` / `_smdi` set for every uniform slot, the way it already does for helmets, vests
  and weapons. The existing roughness split (matte 0.85 for fabric and webbing, 0.55 for hard items)
  is unchanged — it was correct and is what stops pouches rendering chrome-white under Lumen.
- The CMECU becomes the **ADFRC field-green** G3 set rather than an original pattern. `Crye_G3_Shirt_Green`
  and `Crye_G3_Pants_Green` are 4096x4096 and carry the folds, seams, pockets and stitching that the
  64x64 fallback threw away. **Green is chosen deliberately over the patterned variants**: it is the
  highest-resolution set available and it is plain dyed fabric, so the players read as ADF at a glance
  with no pattern question at all. The other variants (`DPD`, `DPN`, `GPU`, `MMP`, `MTS` at 2048^2, and
  the 4096^2 `AMC`/`Multicam` sets) remain available and are a per-slot choice, not a policy one.
- MAF keeps its generated red-earth camo. `make_maf_uniform.py` was written for ADR-016's "original
  disruptive pattern" direction, which remains the producer's stated visual intent for the opposing force
  (ADR-016: "original red-earth disruptive camouflage in ochre, rust, dark brown, muted burgundy and
  charcoal"). It is a deliberate faction distinction, not a licence workaround, and it is not amended.
- `Tools/Textures/make_character_textures.py` and the `T_SS_CMECU_*` / `T_SS_MAF_*` sets are retained for
  first-person arms and the UI, and are no longer the third-person soldier's uniform.

**Historical scope note (superseded by ADR-035).** The original entry treated marks and service patterns as project-use exclusions; the producer later accepted acquired assets containing them for the F2P game. Preserve this original technical/provenance analysis as history only. ADR-035 governs current use; R-27 is producer-accepted, not a branding-substitution release gate.

**Historical consequence (policy later updated by ADR-035).** The original text retained restrictions on ADF emblems, corps badges, colour patches and Rising Sun. ADR-035 subsequently accepted producer-directed acquired insignia/camouflage for the F2P project. Current rules are: no endorsement claim, observe content-ethics rules, preserve provenance/credits and do not redistribute raw source packs. ADR-042 governs the active Quantum appearance. `Art/ADFRC/*` remains ignored under source-handling policy, not because the game cannot use the assets.

---

## ADR-034 — Australian Army ranks as service levels 1–100, with insignia; kills earn capped XP

**Status:** Accepted (producer, 2026-09-28; current use confirmed by ADR-035): "mimic Australian Army rankings, private through to
general, even with their insignia (displayed in the scoreboard), like honor was for America's Army. XP is
gained through kills, objectives etc. ... highest rank is general 100 ... private might be 1–4, then at 5 it
goes to lance corporal", then "needs to be realistic", pointing to army.gov.au/about-us/ranks.
**Supersedes:** ADR-032's rank ladder and its no-kill-event rule (guard SS009, retired); GDD §6.2 "officer
ranks are reserved" and §6.4 "kills are not rewarded", for progression. **Extends:** ADR-016 by exception,
as ADR-025 did. (Numbered 034: ADR-033 was taken concurrently by the uniform-texture decision.)
**Date:** 2026-09-28

**Decision.**
- **Service level 1–100**, shown with the rank insignia on the scoreboard and front end, as honour was in
  America's Army. Level comes from service XP: `XpForLevel(n) = round(60 · (n−1)^1.9)`. Level 100 needs
  371,414 XP.
- **Seventeen ranks, Private to General**, per the Army's own rank list: PTE 1–4, LCPL 5–9, CPL 10–15,
  SGT 16–22, SSGT 23–28, WO2 29–34, WO1 35–40, 2LT 41–46, LT 47–53, CAPT 54–61, MAJ 62–69, LTCOL 70–77,
  COL 78–84, BRIG 85–90, MAJGEN 91–95, LTGEN 96–99, GEN 100. RSM-A (a single appointment) and Field
  Marshal (honorary) aren't levels. All of it is data: `[/Script/SouthernSpearCore.SSRankSettings]`.
- **Insignia are drawn in code** (`SSInsigniaRaster.h`, engine-free) from each rank's description, following
  the Army's devices: point-down chevrons, crown (St Edward's pattern) over chevrons for SSGT, crown for WO2,
  the Coat of Arms for WO1, pips (Order of the Bath star) in a column, crown and pips for field officers
  (Brigadier's three in a triangle), and crossed sword and baton for generals. They're silhouettes for a
  22 px scoreboard cell, not heraldic reproductions. There are no image files, so nothing needs importing
  or registering.
- **Kills earn XP** (`EnemyKill`, 10 XP, capped at 50 per match). Objectives still dominate: one capture
  (100 XP) is worth ten kills. A friendly kill costs 150 XP and is never capped.
- **Where it lives.** The ladder and curve are in Core (`USSRankSettings`, `FSSServiceRanks`), because the
  scoreboard (SouthernSpearUI) and progression both read them. The level travels client → server through
  `USSServiceRelay::ServerReportProfile` into a replicated `USSServiceRankComponent` on the player state.
  The same call carries the callsign (`ss.Callsign <name>`), which becomes the scoreboard name.

**Historical release-gate note — superseded by ADR-035.** This entry originally called for permission or a device swap before release. ADR-035 lifted that gate and records the producer's acceptance for the F2P game; preserve the no-endorsement disclaimer and content-ethics rules. No separate permission, legal-review or substitution gate remains under this decision.

**Known limit.** The level shown to other players comes from each player's own local record, which isn't
authoritative (R-53). It is display only and gates nothing. Server-authoritative records are Phase 5 work.

---

## ADR-035 — Free-to-play release: producer-cleared acquired assets and real names for this project

**Status:** Accepted (producer, 2026-09-28, in session): "this is a free to play product — so the use of real
names etc is okay. All assets obtained — levels, 3D objects — are free from Fab or other sources, or given to
me (ADFRC) from the original creators, so all can be used. This is a free product, so licensing should be
fine." Reaffirmed by the producer on 2026-10-01 during the full asset inventory review. Amends ADR-016, ADR-025, ADR-033 and ADR-034, and the matching entries in `LICENCE_REGISTER.md`.
**Date:** 2026-09-28 (reaffirmed 2026-10-01)

**Decision.**
1. **Southern Spear is a free-to-play product.** No paid content is planned. The producer's project-specific clearance governs assets acquired/held for this game; do not generalize it into a universal marketplace licence claim or imply that raw source packs may be redistributed.
2. **Real names are allowed** in code, data, UI, docs and the website. That covers real weapon names (EF88,
   F89, M4, HK416, Glock, Minimi …), the Australian Army, its ranks and rank insignia (ADR-034, drawn
   faithfully), ADF equipment names and service camouflage. The A-series names and the fictional
   organisations (3 ACR, MAF, CMECU …) are **not** withdrawn: they stay until someone chooses to rename,
   and a rename is a normal change, not an ADR.
3. **Assets acquired/held for Southern Spear are cleared for use in its F2P game.** This includes Fab (ADR-028), other acquired sources and the ADF Re-Cut grant (L-0021). No per-asset permission hold is required. Registers still record observed provenance and attribution/credit obligations; this is not permission to redistribute raw source packs or to use ripped commercial-game content (L-0007/L-0008).
4. **Release gates lifted:** R-27 (ADFRC branding substitution) and R-55 (Army insignia, crown and Coat of
   Arms) become **producer-accepted**, not blockers. L-0003's legal hold and L-0004's prohibition are lifted. This only changes the stated project-use decision; no universal rights opinion is implied.

**Still standing, because they are not licence questions:**
- **No endorsement claim.** The game doesn't present itself as made, approved or sponsored by the ADF,
  Defence or the Australian Army, and it keeps the fictional-work disclaimer. That statement is simply
  true, and it's what makes real names safe to use.
- **MAF portrayal** (LICENCE_REGISTER §5.3): a credible conventional force, never a real ethnic, religious
  or political group or a caricature. This is a content-ethics rule.
- **No *America's Army* content** (L-0008): none of it was obtained from any cleared source, so it isn't
  covered by this decision. Its design philosophy is fine, as ADR-031 already uses it.
- **No ripped commercial-game assets** (L-0007): again, not from a cleared source.
- **Engine and Lyra credits** (L-0001, L-0002) and CC BY credit lines still ship.

**Accepted risk, recorded once (R-57).** Third-party marks/emblems in acquired assets are retained as source and provenance context. The producer accepts their use in this specific F2P project under ADR-035; that is not a universal legal opinion or endorsement claim. Preserve source/credit records and the no-endorsement disclaimer. There is no pre-release permission, legal-review or mandatory substitution gate under this decision.

---

## ADR-036 — Historical soldier body direction: ADFRC G3 working baseline (superseded by ADR-042)

**Status:** Historical working-baseline decision; superseded by ADR-042 (2026-09-30), which selected Quantum for the friendly visible body and retained Manny for gameplay/pose. Preserve the findings below as historical context only. Clarification 2026-09-30: the friendly head configured in `setup_soldiers.py` is still the Fab Modern Insurgent 7 head; no matching ADFRC character head/body source has been identified.
**Date:** 2026-09-28 (clarified 2026-09-30)

**Context.** The friendly soldier is assembled from four meshes in `Tools/Unreal/setup_soldiers.py`:
`Modern_Insurgent_7/SK_Head` (Fab), then ADFRC's `SK_ADF_Uniform_G3`, `SK_ADF_Vest_TBAS` and
`SK_ADF_Helmet_OpsCore`. The uniform carries the arms — it is a full character, not a garment on a body
(108 bones, 23,187 verts, arm vertices split 4,590 shirt / 914 gloves). So the head comes from one pack
and the body from another, and the arms belong to neither the head nor the vest.

The mixed sources were a plausible explanation for the *assembled* rather than *worn* read, but this causal claim was not established by a controlled visual comparison. The producer also reported a mismatched look on the shoulders and neck. Separately, every part is parented onto **Lyra's** `SK_Mannequin` skeleton, so the soldier cannot own a bone (R-58).

The alternative was to switch to the Fab `SKM_QuantumCharacter` (3 ACR) as the body and dress it in ADFRC
gear, which gives a better-animated base at the cost of taming its 14 vendor material slots.

**Decision.**

1. **The ADFRC G3 uniform is the body baseline.** It carries the arms; the fitted ADFRC vest and helmet remain. The MAF keeps its own `SK_Head`; it is a separate conventional force with its own look (ADR-016, ADR-035). The friendly head must match the producer-approved body source, but no G3 head is established by this decision: `setup_soldiers.py` currently still assembles the Fab "Modern Insurgent 7" head, and the installed ADFRC source tree contains no character-body model. Resolve the head asset/fit from evidence before claiming a single-source head-to-body assembly or changing the configured mesh.
2. **The MAF stays a material variation of the same mesh**, as it already is
   (`SK_MAF_Vest_*`, `SK_MAF_Helmet_*`, and the green palette applied through
   `opposing_material_overrides`). This decision does not change that.
3. **Initial assessment (superseded by ADR-037):** `SKM_QuantumCharacter` was retired on the mistaken basis that its assembled mesh had 14 vendor-material slots. ADR-037 corrected this after the separate modular set was inspected; Quantum remains a viable, unapproved alternative and the 14-slot argument does not apply to its modules.
4. **Intended follow-up:** give the selected soldier body its own skeleton rather than Lyra's, if the fair comparison confirms the body direction and the implementation is validated. This is not authorized as an immediate mesh/skeleton switch.

**Why G3 was chosen as the working baseline.** The ADFRC gear is already fitted, textured and rigged to the G3 uniform (Session 049, `adf_soldier_setup.json`), making it the least disruptive baseline. That did not prove a matching ADFRC head asset exists or establish that the current mixed-source assembly is visually solved. ADR-037–039 subsequently corrected the claim that Quantum was retired and documented a viable modular/retarget prototype route; the producer should compare complete, similarly dressed and posed versions before a final body/skeleton choice.

**Historical consequence (superseded by ADR-042).** The G3 uniform/Modern Insurgent head were retired from the friendly visible assembly. Do not apply this historical G3 work plan as current direction; use `Docs/PLAYER_MODEL_PLAN.md` §1 and ADR-042 for the current Quantum/Manny boundary.

---

## ADR-037 — Historical Quantum modular-character assessment (superseded by ADR-042)

**Status:** Historical Quantum assessment and prototype proposal; superseded as a body-choice gate by ADR-042 (2026-09-30). Its technical findings are retained below. The old claim that the prototype was blocked on tooling is superseded by ADR-039's successful poseable-mesh path and ADR-042's active runtime retarget design.
**Date:** 2026-09-28

**Correction to ADR-036.** ADR-036 retired `SKM_QuantumCharacter` on the grounds that "its 14 slots all
sit on vendor materials". That is true of the **assembled** mesh, and the decision was made without
looking at `Content/QuantumCharacter/Mesh/Modules/`, which is a genuinely modular set of eight separate
meshes with one or two clean slots each:

`SKM_Head` (5 slots, incl. eyes and teeth) · `SKM_Arms` (1) · `SKM_Shirt_RolledUp_Blue` (1) ·
`SKM_Jeans` (1) · `SKM_Bulletproof_Bege` (1) · `SKM_Holster_Hard_Bege` (2) · `SKM_Drops_1_Bege` (1) ·
`SKM_Patch_Back` (1)

That is the shape Lyra's character-parts system wants, it gives the head from the same pack as the body
(what ADR-036 wanted), each module ships a **physics asset**, and the eight total 27 MB against 22 MB
for the three ADF parts. The pack also carries its own locomotion set on its own skeleton
(`A_MM_Idle/Walk_Fwd/Run_Fwd/Jump/Land/Fall_Loop`). **ADR-036 point 3 is therefore wrong and is
withdrawn**; nothing else in ADR-036 changes.

**The skeleton is the catch.** `SK_Military_Character_Skeleton` has **351 bones**: 159 share names with
Manny's 164, and **192 are Quantum-only** (fingers, toes, facial rig). The modules are therefore **not**
leader-pose compatible with Lyra's mannequin, and the articulated hands are the prize here — they are
what would finally give the W2 hand-grip work something to grip *with*.

**Decision.**

1. **Prototype the modules on Manny, with ADF camo on the shirt and jeans** (producer, 2026-09-28).
   Reversible; touches nothing committed; answers whether the Quantum silhouette and proportions beat
   the G3's.
2. **The prototype is currently blocked on tooling**, and this is the finding that matters:

   | Route | Result |
   |---|---|
   | Blender re-rig from source | **Not available.** The pack ships **230 `.uasset` and zero FBX/OBJ**, so there is no source mesh — the route that produced the ADFRC gear cannot be repeated. |
   | UE "Reparameterize Mesh" | **Not exposed** in UE 5.8 Python. `SkeletalMeshTools`, `SkeletalMeshEditorSubsystem`, `AnimationLibrary` and `EditorSkeletalMeshLibrary` have no such function. |
   | Export to FBX, re-rig in Blender | **Crashes the editor.** `SkeletalMeshExporterFBX` hard-asserts `MeshObject` (`SkinnedMeshComponent.cpp:4987`) inside `MeshMergeUtilities`, killing the commandlet with no Python traceback. Reproduced **with and without `-nullrhi`**, so it is not a headless artefact. |

3. **So the only route that does not need re-export is to adopt `SK_Military_Character_Skeleton` itself**
   and use the modules on it unmodified, with our own ABP. That is the larger risk ADR-036 §P2 already
   flagged, and it is **not** what point 1 authorised. It is a producer decision and is **not** taken
   here.

**Historical consequence (superseded by ADR-042).** Quantum is now the selected friendly visible body. This entry's analysis of source skeleton constraints remains historical/technical context; its G3-versus-Quantum choice and open-decision language no longer governs.

---

## ADR-038 — Leader pose does work for the Quantum modules; ADR-037's "not usable" is withdrawn, and three new candidate bodies assessed

**Status:** Historical technical assessment; its provisional body-choice language is superseded by ADR-042 (2026-09-30). The measured leader-pose and candidate-body findings remain useful context. ADR-039/042 later established the runtime retarget path; the following pre-prototype route recommendations are not current implementation status.
**Date:** 2026-09-28

### Correction to ADR-037

ADR-037 recorded the Quantum modules as "not leader-pose compatible" and the pivot as "blocked". **The
first half is wrong.** `SetLeaderPoseComponent` matches bones **by name**; bones the child has and the
leader does not are simply not driven, and hold their reference pose. The mesh renders and animates
correctly. The probe behind that claim tested "does the child have any bone the leader lacks" — 192 of
351 — and equated the answer with "unusable", which is not the test. On the real numbers, leader pose
would drive the **159 shared bones and leave 192 static**.

So the modules can be put on the pawn today with no export, no Blender work and no retargeter. The
real cost is the one both agents named: the **fingers stay straight**, which reads wrong on a rifle.
The retargeter route (an `IKRetargeter` asset plus a pose-copying Anim Blueprint, buildable headlessly)
is still the way to get articulated hands, and it needs no export either. **Neither route has been run.**

### The three candidate bodies (measured, `Build/probe_candidate_bodies.json`)

All three are in the Fab library cache as **source files**, which is the one thing better than Quantum:

| | Rig | Bones | Verts | Slots | Textures | Manny-compatible |
|---|---|---|---|---|---|---|
| **Free Pack – Male Base Mesh** (FBX, 496 KB) | **none** | 0 | 4,395 | 1 | **none** | n/a |
| **FSB Operator** (GLB, 86 MB) | Mixamo | 52 | 108,616 | 41 | yes | **0/52** |
| **SWAT Operator** (GLB, 106 MB) | Mixamo | 51 | 57,761 | 34 | yes | **0/51** |

Reading: **none of the three is better than what we have, and none is easier.**

- **Male Base Mesh is the worst of the three**, not the easiest: it has **no armature and no textures at
  all**. It would need a rig built from nothing, which is more work than renaming an existing one.
- **FSB Operator is the heaviest**: 108,616 verts for one soldier, 41 material slots to tame.
- **SWAT Operator is the best of the three** and still not good enough: 57,761 verts, 51 Mixamo bones
  with finger chains, 34 slots. Its mixamo naming means a scripted rename to Manny names — cheap, but
  the fingers would still not animate on a 164-bone leader, so it buys the same straight-finger problem
  as Quantum, with a worse texture and no modularity.
- **Faction and accuracy**: a SWAT operator and an FSB operator are both not an Australian Army soldier,
  and the SWAT pack's materials reference **KSVR**, a real Russian camouflage brand. ADR-035 keeps real
  names legal, but R-57 (accepted risk) covers trademarks — putting another nation's service camouflage
  on the *main player model* is an accuracy problem as well as a legal one.

**What a candidate would actually need to beat the G3:** a source rig already named to Manny (or
renameable), **articulated fingers**, a small number of clean material slots, neutral clothing to camo,
and proportions the fitted ADFRC gear still fits. Quantum is the only one of the four that has the
fingers, the modularity and clean slots; it fails on source files and bone names, and both of those are
cheaper to solve than any of the three new packs' problems.

**Historical outcome.** ADR-042 later selected Quantum as the friendly visible body and established the runtime retarget path. This comparison recommendation is superseded; final in-game visual confirmation remains pending.

## ADR-039: Quantum retarget is buildable headlessly, but not by the route ADR-037 assumed

**Status:** Historical technical decision; ADR-042 supersedes its body-selection context, while its UE 5.8 retarget/tooling findings remain relevant.

**The recommended route does not exist in UE 5.8.** `Build/probe_retargeter.json` records it:
`unreal.IKRetargeterFactory` is not exposed to Python, so an IKRetargeter asset cannot be created;
`unreal.AnimBlueprint` exposes no graph API, so `AnimNode_RetargetPoseFromMesh` cannot be placed; and
`USkeletalMeshComponentPostProcessAnimInstance` together with `UAnimInstance::NativeEvaluateAnimation`
- the historic C++ route to rewriting a pose - **have both been removed from the engine**. The
`PostProcessAnimInstance` property still exists on the component; its base class does not.
"FAnimInstanceProxy::Evaluate" survives but has no caller in the engine.

**What works headlessly** is `UPoseableMeshComponent`, which keeps a writable per-bone local pose and
composes it to component space itself. `ASSQuantumProtoStage` (SouthernSpearCore) uses it to retarget
the Quantum modules from the mannequin every frame, carrying the source bone's local **rotation** onto
the target bone's own local **translation** so Quantum keeps its own bone lengths.

**Leader pose remains the better mechanism where it applies.** Engine source
(`USkinnedMeshComponent::UpdateLeaderBoneMap`) confirms leader pose matches follower bones by name
across *different* skeletons, with bones missing from the leader falling back to the follower's own
reference pose. The G3 half of the stage therefore uses leader pose exactly as
`ASSCharacterPartActor` sets it.

**Two real bugs, caught by invariants rather than by eye.** `ProveRetarget` runs the same
`BuildBoneMap` and `EvaluateRetarget` the runtime runs, and checks that rest is a fixed point, that
motion propagates relatively, and that bone lengths survive. It found (1) that the first version copied
the source's *translation*, silently replacing the target's bone lengths, and (2) that deriving "motion
relative to the source's parent" from rest transforms treated a rest pose as a world transform and put
the hand **290 cm** from the body. A local transform already *is* the motion relative to the parent.

**The rigs differ, and the number matters.** Over the 159 bones the skeletons share by name, rest
positions agree to a median of 0.00 cm but rest *orientations* differ by up to **2.18 degrees**, which
compounds down six arm joints to **5.15 cm** of drift on `upperarm_tricep_r` and `upperarm_bicep_r`.
Excluding twist and IK helper bones from the chain map - what UE's own IK Retargeter does, because
those bones carry a deformation weighting rather than a joint - removes it. **37 bones excluded, 122
drive the body.** That is the concrete reason a chain map cannot be generated from bone names, and why
ADR-037 was right in substance if wrong in its stated reason. 214 bones under `hand_l`/`hand_r` take a
procedural grip curl, the flexion axis derived from each bone's own direction.

**Criterion 3, answered: the plate carrier fits.** Reference-pose bounds in centimetres - Quantum body
`SKM_QuantumCharacter` 55.4 x 22.3 x 91.7 against mannequin `SKM_Manny` 56.6 x 22.5 x 93.3. Within
**1.6 cm** on every axis and slightly smaller, so `SK_ADF_Vest_TBAS`, the helmet and the webbing all
still fit. **The plate carrier is not a cost of switching to Quantum.**

**Criterion 2, delivered.** `Tools/Textures/make_adfrc_camo.py` generates a tileable ADFRC disruptive
pattern whose palette is *measured* from `Crye_G3_Shirt_DPC_co` rather than invented - the failure that
rejected `make_g3_shirt_camo.py`. Chosen tones olive (72,72,55), brown (88,71,54), tan (120,110,98),
shadow (41,40,40). Two first-run bugs, both fixed: a renormalisation stretched the measured tones into
a saturated yellow-green and an orange, and the "greenest" and "darkest" cluster picks collided so a
four-tone pattern shipped as two. The vendor UV layout is untouched and the sheet is periodic, so it
cannot seam. Applied to shirt and trousers; head and arms keep their authored materials.

**Criterion 1, corrected twice.** The "capture stall" of Session 059 was never a stall: the capture
script violated two rules of `Docs/PLAYTEST_COMMANDS.md` (it used `UnrealEditor-Cmd.exe`, and passed
neither `-abslog` nor `-FORCELOGFLUSH`), so a killed run lost its log tail and the diagnosis was read
from the wrong file. The "stalls before any SS module loads" reasoning below was therefore built on
truncated evidence - though its conclusion was accidentally right that the prototype was not the cause.
With the documented recipe the capture works end to end. The first successful frame was black-but-for-
the-HUD because the map had been saved while the stage class still lived in Core (class failed to
resolve on load, so the authored camera and lights were dropped); re-saving the map against the Bridge
class fixed it. **There is now a screenshot** (`Docs/evidence/qproto/quantum_vs_g3_captured.png`,
Session 059c): both bodies on the plinth, same pose source, G3 left and Quantum right. The producer's
critique of it (no camo on the Quantum shirt, no hands, no vest/helmet, glossy plinth, waist-up framing,
FP glove mid-frame) stands as the definition of what the comparison still needs; four of those five
fixes are built into the stage, and the run that would show them crashes on a leader-pose ensure at
`SkinnedMeshSceneProxyDesc.cpp:455` when the soldier pawn spawns into the stage map. That crash is the
current boundary, not a fixed one.

**The composition order was wrong, and the proof could not have caught it.** Session 059 corrected
this. Unreal composes child component space as `Local * ParentComponentSpace` -
`UPoseableMeshComponent::FillComponentSpaceTransforms` says so in a comment and in the call
`FTransform::Multiply(Dest, Local, ParentCS)`. The prototype had it the other way round, which produced
the 144.4 cm "shoulder to hand" (a correct upperarm-plus-forearm span is **51.87 cm**) and the 0.0
shoulder and hip spans. `GetRefBonePose()` was always returning parent-relative transforms; only the
multiply order was wrong.

Worse, invariants A, B and C all compared the retarget against reference poses composed by the *same*
function that produced them, so **none of them could detect a wrong composition** - they were
self-referential, and "rest drift 0.0001 cm" was an artifact. A guard has been added for that class of
error: the proof now checks the composed reference pose against absolute human proportions (a forearm
20-35 cm, a head 55-80 cm above the pelvis) and fails the report outright if they are not. That check
immediately earned its keep by rejecting my own first band for the forearm, which I had wrongly assumed
was a wrist offset. After the fix, on all four modules: sanity passes, A drift 0.0001 cm, B 30.0 of
30.0 degrees applied, and C **27.2511 -> 27.2511 cm** - the bone length preserved exactly rather than
to within a tolerance. `Tools/validate_architecture.py` cannot catch this kind of error, and neither
could an eyeball; the lesson for the next proof is that a check must not share a function with what it
is checking.

**Placement.** `ASSQuantumProtoStage` was first written in `SouthernSpearCore` and has moved to
`SouthernSpearLyraBridge`. Core is the root of the SS dependency graph and holds the shared types every
other module uses; a capture harness that names specific Quantum and mannequin assets does not belong
there, even though it reaches no gameplay state. `Tools/validate_architecture.py` passed it in Core
because the guard inspects module dependencies, not what the code does.

**A real build break found on the way.** The **game target had never been built on this machine** and
did not compile: `SSObjectiveTests.cpp` and `SSSectionAssaultTests.cpp` passed `NAN` and `INFINITY` -
compile-time constants - into tests that are about non-finite values, which a game-target build folds
into constant arithmetic (MSVC C4756). Replaced with `std::numeric_limits<float>::quiet_NaN()` and
`infinity()`, which is also what those tests actually mean: a value the compiler cannot know.
`SouthernSpear Win64 Development` now builds and `SouthernSpear.exe` links.

**Historical consequences (superseded by ADR-042).** ADR-042 selected Quantum and the project now uses the described pose-retarget approach. The carrier-fit and tooling measurements remain context; old undecided-body language is no longer operative.

---

## ADR-040 — Casualty care: wounds, downed state, treatment, and the medic's kit

**Status:** ACCEPTED (producer, 2026-09-29), with the build order below. Adds a module (an architecture change under
CLAUDE.md) and sets the medical design numbers. Implements GDD §4.3 and roadmap IC-08 to IC-11.

**Context.** A fatal hit today is Lyra's: health reaches zero, the pawn dies, the respawn gate records an
elimination. GDD §4.3 asks for location-sensitive damage, incapacitation instead of instant death, bleeding,
stabilisation, limited field dressings, self-treatment strictly worse than a medic's, and **no health
regeneration during a round**. The producer holds a Fab first-aid kit (the IFAK, ASSET_REGISTER, `NOT_USED`) and
asked for a medic-dropped kit that players heal around.

**Decision.**

1. **A new gameplay module, `Plugins/SouthernSpearCasualty`** (`SSCASUALTY_API`), depending on Core only (no Lyra,
   no UI), like Objectives and Progression. It holds:
   - `FSSCasualtyRules`: pure, engine-light, fully unit-tested. States, zone multipliers, bleed, bleed-out,
     treatment outcomes.
   - `USSCasualtyComponent`: server-authoritative and replicated on the pawn. It holds the state, bleed rate,
     bleed-out remaining, dressings carried, and who is treating.
   - `ASSMedicalKit`: the dropped kit, replicated, with charges.
   - `USSCasualtySettings`: every number below, in `DefaultGame.ini`, so tuning never recompiles.

   The Lyra bridge is the only place that touches Lyra. It reads damage from `ULyraHealthComponent` and
   the hit bone from the hit result, holds Lyra's death at zero health while the casualty rules say "downed",
   and routes the interact input. `SouthernSpearUI` shows the state, and only shows it (ADR-004).

2. **States.** `Healthy → Wounded (bleeding) → Downed → {Stabilised → back up | Dead}`, all transitions on the
   server.
   - **Wounded:** a limb or torso hit adds bleed, and health drains at the bleed rate until it is dressed.
   - **Downed:** damage that would kill, or bleeding to zero, puts the soldier down instead. They can't move or
     fire, and a bleed-out timer runs. A head hit, or damage while already downed, kills outright ("finished").
   - **Dead:** the timer runs out or the soldier is finished. Only here does `USSRespawnGate::ReportElimination`
     fire. Being downed is not an elimination, so Section Assault's single-life rule counts deaths, not downs.

3. **Zones (IC-08), data:** head ×4.0 (and never downs: it kills), torso ×1.0, arms ×0.6, legs ×0.7. Limb hits
   add more bleed than torso hits.

4. **Treatment.** A hold-interact that the server times and that cancels on movement or damage. **Self-treatment
   is strictly worse**, so every outcome below is a property of *who* treats:

   | Action | Who | Time | Result |
   |---|---|---|---|
   | Field dressing | self | 6 s, walk speed, not while sprinting | stops bleeding; **no health returned** |
   | Field dressing | teammate | 4 s | stops bleeding; no health returned |
   | Stabilise a downed soldier | any teammate | 8 s | back up at 25 health, still bleeding lightly |
   | Stabilise a downed soldier | medic | 5 s | back up at 50 health, bleeding stopped |
   | Treat a wounded soldier | medic | 5 s | stops bleeding, restores to 75 health |

   Two dressings per soldier (medics carry six). "Medic" means the role, from its qualification (GDD §4.5). Until
   roles exist, a config flag makes every player a medic for testing.

5. **The medic's kit (producer request, reconciled with "no regeneration").** A medic can drop one kit: the Fab
   IFAK mesh, one per medic, 8 charges, removed after 3 minutes or when empty. It is a **treatment point, not a
   healing aura.** Health never rises passively near it. Within 2 m, a soldier can:
   - take a field dressing from it (1 charge; up to their carry limit), and
   - **treat themselves at the kit** (hold 8 s, 1 charge): stops bleeding and restores up to 60 health, which is
     still worse than a medic's 75.

   Every point of health still comes from an action someone takes, so GDD §4.3's rule holds, and the kit makes the
   medic valuable even while they're somewhere else. A passive heal aura was considered and rejected because it is
   regeneration by another name.

6. **No regeneration (IC-11) is tested.** An automated test runs a wounded, dressed soldier for 120 simulated
   seconds, with and without a kit nearby, and asserts health never rises without a treatment event. Lyra's
   own health component has no regeneration; the test keeps it that way.

**Asset.** The kit is the Fab IFAK. Its listing carries `isAiForbidden: true`, which the producer has overruled for
every asset (L-0016d). The rules and component don't depend on the art, so a missing mesh never blocks the system.

**Consequences.**
- The architecture guard gains the module (SS001/SS002: Core only). `validate_architecture.py` and CLAUDE.md are
  updated in the same change.
- New tests: `SouthernSpear.Casualty.*` (the rules: states, zones, each treatment row, kit charges, no regeneration).
- Build order: (1) the rules and tests, which can be written and checked remotely; (2) the component, kit and
  settings; (3) the bridge wiring into Lyra's health and interaction; (4) the HUD — bleed marker, downed
  bleed-out bar, "stabilising…" bar, and the kit's charges when near it.
- Out of scope here: friendly fire (IC-15), role limits (IC-14), carrying or dragging the wounded.

---

## ADR-041 — Wandarra's vendor doors are scenery until a server-owned door component exists

**Status:** Accepted
**Date:** 2026-09-30

**Context.** The MOUT kit's interactable door Blueprints (`BP_GlassDoors_Interactable`,
`BP_GreenDoors_Interactable`, `BP_WoodenDoor_Interactable`) are the only interactive content in any
installed pack, and Wandarra (M-009) is built from that kit. Wiring them up or not is a design
decision the map's first dressing pass had to make. Evidence gathered before deciding:

- The vendor Blueprints are **not clean**. `BP_GlassDoors_Interactable` ships with embedded compile
  errors referencing variables of its sibling (`Could not find a variable named "Left Door
  Rotation" in 'BP_GreenDoors_Interactable_C'` — strings read from the compiled asset). They are
  timeline-driven, client-local animations with no ownership model, which is exactly what ADR-004
  exists to keep out of gameplay: authority is a server property, and "doors that open for whoever
  asks locally" are a fairness hole on a tactical shooter (a defending player behind a door that is
  open on one client and closed on another).
- The project's interact input is **already claimed**. Lyra's `LyraGameplayAbility_Interact` /
  `IInteractableTarget` stack routes one interact action, and ADR-040 assigns it to casualty care
  (hold-interact to dress and stabilise). Two meanings on one input needs a priority scheme the
  project has not designed.
- What the doors are *for* on a training village is compound clearing: door control (open, clear,
  close behind) as a teachable skill. That needs the door's state to be server-known only where it
  matters for play — it does not need vendor timelines, sounds or handle animations.

**Decision.**

1. **This phase: the doors are placed as scenery, at two of the three compound/picket gates, never on
   building walls.** Two doors stand in the depot's side gate and the green's picket gate, where
   openings already exist in the fence lines (gate gaps narrowed to 2.4 m personnel width in
   `wandarra_spec.py`). The depot's main gate keeps an **open** 2.4 m gap on purpose: TeamOne spawns
   inside the compound and the navmesh bakes a closed door as a blocker, so the compound's walkable
   exit must never depend on an unwired scenery door. The doors are NOT placed on vendor buildings:
   the buildings have their doorways meshed in, their footprints are unmeasured (R-90), and a
   wall-mounted door BP can block a real doorway.

2. **Not wired into gameplay.** No input binding, no `IInteractableTarget` implementation, no
   interaction option. The vendor door BPs are referenced as placeable actors only, and the map
   must not depend on their script logic: any door that gameplay later needs is a thin
   **`USSDoorComponent`** (server-authoritative open state, replicated, `SouthernSpearObjectives`
   or Core module, Core-only dependencies per SS001/SS002) attached to a simple door actor the
   project owns. The vendor BPs' timelines, sounds and handles are presentation and stay out
   (ADR-004).

3. **Phase 2 path, if the training design asks for it:** build `SSDoorComponent` + a project-owned
   door actor that references the vendor door *meshes*, place those at the gates and building
   doors, resolve the interact-input conflict with casualty care explicitly (context by target
   type, or a modifier key), and gate it on a bot smoke test asserting door state replicates. The
   vendor BPs themselves remain unreferenced by gameplay code forever.

**Alternatives.**

- *Wire the vendor BPs into Lyra's interaction now* — rejected: places unowned vendor script
  inside the gameplay path (ADR-004's exact failure mode), ships known-broken Blueprints, and
  collides with the claimed interact input before casualty care has even landed its HUD.
- *Skip the doors entirely this phase* — rejected: door control is the compound-clearing skill the
  kit was chosen for; scenery doors at the gates teach the shape of the action in bot matches and
  cost nothing.
- *Keep the wide vehicle gates* — rejected for the two side gates: a 1–2 m door in an 8–10 m gap
  reads as a mistake. The main depot gate keeps its vehicle width; the personnel gates are 2.4 m.

**Consequences.**

- Wandarra's doors open for nothing this phase — recorded in `MAPS_WANDARRA.md` so no one reads
  the shut doors as a bug.
- The dressing pass (`dress_wandarra_awnings.py`) performs the R-90 bounds dump as it places, so
  footprint corrections land in the spec and a rebuild, not in actor nudges.
- The AwningKit meshes stay unused (the government-awning Blueprints cover the shopfront need); if
  a later pass wants awning *meshes*, they are referenced in place per ADR-021 like everything
  else in the pack.
- R-67 extends one line: vendor Blueprint logic (doors) is now load-bearing for nothing; if a
  future phase wires doors, the component path above is the only sanctioned route.

## ADR-042 — Quantum is the producer-selected friendly appearance; Manny remains the gameplay/pose source

**Status:** Accepted, amended 2026-10-01 (assembly change: see the amendment at the end of this entry)
**Date:** 2026-09-30

**Context.** The shipped friendly look — a Modern Insurgent 7 head on an ADFRC G3 uniform with ADFRC
vest and helmet (the assembly documented in Session 086) — reads as *assembled rather than worn*, and
the producer rejected it: "the mismatch of the other model doesn't look good." ADR-036–039 had held
the body switch behind a fully-dressed Quantum-vs-G3 comparison; the producer has now made the call
the comparison was for and chosen **Quantum** for the 3 ACR look, ending the comparison gate. The
technical facts the prototype sessions established still stand:

- Quantum ships on its own 351-bone skeleton (`SK_Military_Character_Skeleton`), never reparented to
  the mannequin (ADR-037/038). Leader pose cannot drive it: there is no shared bone chain.
- The project's retarget arithmetic is proven (`Docs/evidence/qproto/quantum_retarget_proof.json`:
  122 mapped bones, rest fixed-point drift 0.0001 cm, 30° probe propagates, bone lengths survive),
  with twist/IK helper bones excluded and the Quantum-only finger bones given a grip curl.
- The ADFRC vest and helmet are Manny-rigged and were measured to fit the Quantum torso within
  1.6 cm on every axis (Session 058 fit report), so they can stay leader-posed. The source-image and generated derivative are separate assets: tracked `T_ADFRC_DPC_camo.png` is imported as a texture and the tileable Quantum-shirt texture is generated by `Tools/Textures/make_adfrc_camo.py`; the unchanged source is not asserted to be the mounted garment texture.
- The pawn's body mesh — Lyra's Manny with the hand-IK component — is load-bearing for hit zones,
  damage, movement, weapon sockets and the hand-IK solve. Swapping it is a different project.

**Decision.**

1. **The viewer's own team is shown as the Quantum character** (shirt, jeans, arms, head — the four
   modules `setup_quantum_proto.py` maintains, carrying the ADFRC camo), rendered on Quantum's own
   skeleton. `ASSCharacterPartActor` retargets those modules **per tick from the pawn mesh's
   evaluated component-space pose** (locomotion, aim overlay and the hand-IK wrist included, because
   the pawn mesh is the pose authority the weapon and camera already follow). The bone map is built
   once per module mesh with the prototype's rest-pose tolerances (6% of standing height, 30°),
   cached, and re-derived only if the mesh changes.

2. **The gameplay skeleton does not change.** The pawn body remains the Manny-skeletoned
   `USSHandIKMeshComponent`: hit zones, damage, movement, sockets, the hand-IK solve and the weapon
   attachment path are untouched (ADR-004). The Quantum body is presentation, exactly as the G3
   pieces were, and the retarget copies the wrist rotation the hand IK produces — the Quantum hands
   hold the weapon without a second IK solve. Quantum bones with no Manny counterpart (fingers, some
   helpers) hold the vendor reference pose, fingers with the tuned grip curl.

3. **The ADFRC vest and helmet stay Manny-rigged and leader-posed**, layered over the Quantum body
   via the new `FriendlyLeaderPoseParts` (they measured within 1.6 cm on Quantum's torso). The G3
   uniform and the Modern Insurgent head leave the friendly look entirely. The MAF opposing look is
   unchanged in every part and material. This is the selected configuration; final in-game visual/camo acceptance is a separate pending verification, not evidence that the capture was completed.

4. **First person follows the part kind, not the mesh class.** The local player must never see their
   own body: body view hides the head bone on every attached skinned part (the Quantum head is its
   own component now), and the arms view-model path hides every attached *skinned* mesh — the
   Quantum modules are `UPoseableMeshComponent`s, which the previous `USkeletalMeshComponent`-only
   cast let through into the camera.

5. **Locality rules unchanged (ADR-017).** Parts stay hidden until the viewer's client resolves a
   locality; opposing viewers keep seeing the MAF look; nothing here is replicated.

**Alternatives.**

- *Keep the G3/Insurgent assembly until a fair comparison renders* — rejected by the producer: the
  comparison existed to inform this choice, and the current look is unacceptable now.
- *Swap the pawn's gameplay skeleton to Quantum* — rejected for this phase: it would re-open hit
  zones, damage, the hand-IK solve, weapon sockets and every Manny-authored animation layer at once,
  and ADR-004 forbids presentation work from carrying that risk. Revisit as its own decision if the
  cosmetic body proves out.
- *Author an IK Retargeter asset* — not available: 5.8 has no IKRetargeter Python factory and no
  AnimBlueprint graph API (Build/probe_retargeter.json), which is why the project already owns the
  component-space retarget the prototype proved.
- *Leader-pose the Quantum modules anyway* — impossible: cross-skeleton leader pose only maps
  same-named bones, and the Quantum rig's rest pose disagrees with Manny's exactly where it matters
  (the prototype measured metres of drift on shared names before the tolerance filter).

**Consequences.**

- R-58 concerns the Manny gameplay skeleton and the Quantum retarget/gear boundary, not the retired G3 visible-body assembly. Measure the active configuration before closing the risk.
- `setup_soldiers.py` writes the Quantum configuration (`friendly_parts` = the four QuantumProto
  modules, `friendly_leader_pose_parts` = ADFRC vest + helmet, `retarget_friendly_pose` = true) and
  `setup_character_textures.py` no longer authors friendly overrides (the modules carry their own
  materials). Both scripts must be re-run if `B_SS_Soldier` is regenerated.
- The class-select preview uses the in-game `B_SS_Soldier` child actor on the invisible Manny body,
  so its components perform the same runtime retargeting, material overrides and leader pose as the
  deployed character. This removes the former ad-hoc preview path; the resulting presentation still
  requires a fresh capture and producer acceptance (see R-58).
- The camo rides on component overrides (`FriendlyMaterialOverrides`), not on the module meshes:
  measured 2026-09-30, mesh-asset material slots are read-only from Python in 5.8, and the
  prototype-era script had reported ok while silently writing nothing (R-91). A camo pass that
  leaves the vendor material puts a blue civilian shirt in the game, as observed 2026-09-30.
- R-91 is closed as a pipeline defect (root cause measured, scripts fixed, asset read-back
  verified); the in-game confirmation is the producer's next capture.

### Amendment — 2026-10-01 (assembly only; the body-source decision above stands)

**Context.** The Quantum four-module assembly above was captured in the class-select preview and the
producer reviewed it directly: camouflage present, but "no helmet, no webbing and completely wrong
camouflage", then "a weird gap at the waist". The owner's direction for the friendly look is the
**ADFRC models and AMCU textures**. Two measurements decided how to act on that:

- The helmet was configured, visible and leader-posed in the same capture the producer read as
  helmetless: the preview was frozen at 35 % of `MM_Rifle_Idle_Hipfire`, a frame with the head pitched
down, so the bare crown sat in front of the helmet. The pose was the defect, not the gear.
- The pale band at the waist is the ADFRC G3 shirt sheet's own plain under-shirt panel: the fitted
  uniform's torso faces sample UV v 0.02–0.24 of `Crye_G3_Shirt_AMC_co.png`, which carries no
  camouflage (measured with `Tools/Blender/inspect_uniform_fit.py` and `Tools/Common/ss_sheet_probe.py`;
  the mesh is continuous — trunk faces in every 2.5 cm slab from 75 cm to 155 cm — so it is not a hole).

**Amendment.** The viewer's own team is shown as the **ADFRC G3 uniform, TBAS vest and OpsCore helmet**
(Manny-rigged, leader-posed, AMCU textures as authored, with the shirt sheet's flat under-shirt panel
repainted in pattern by `Tools/Textures/patch_adfrc_undershirt.py`), with the **Quantum head as the only
retargeted module**. Decision point 1's four-module assembly is therefore superseded, and so is the
`setup_quantum_proto.py` shirt/jeans camo as a *friendly* route. Everything else here is unchanged and
still governs: the pawn's body mesh remains Lyra's Manny and the pose authority, `ASSCharacterPartActor`
retargets the remaining module per tick with the same measured bone map, the gear stays leader-posed,
and ADR-004's hit zones, damage, movement, sockets and hand-IK solve are untouched. The Quantum head is
aligned by `FriendlyRetargetAnchor` (measured rest gap to the mannequin head: 0.0 cm on this assembly),
which exists so a differently proportioned module cannot drift out of gear fitted to the mannequin.

**Open.** This is an assembly change, not art acceptance: the producer has not yet reviewed this
assembly, the friendly head is still not an ADFRC asset (the source set has no character head), and the
repainted panel is a project derivative awaiting acceptance (R-92, R-93).
