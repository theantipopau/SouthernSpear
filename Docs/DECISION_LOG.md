# DECISION LOG — Southern Spear

**Document ID:** `Docs/DECISION_LOG.md`
**Status:** Open
**Last updated:** 2026-09-26

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

- **Fab** assets under the Fab Standard License (free or purchased), added to the project from the
  producer's Epic account. Licence class A.
- **Sketchfab** assets whose model page shows **CC0** (class A) or **CC-BY** (class B, credited). Not
  allowed: CC-BY-NC, CC-BY-ND, editorial-only, or any upload the uploader cannot own (game rips).
  CC-BY-SA needs a separate decision.

Every such asset needs a licence-register entry with its source URL **before** it is used, and is adapted
to the fiction: no real insignia, manufacturer marks, ADF branding or Multicam/Auscam patterns. Weapons
remain fictional A-series: a third-party weapon model may be used only after it has been reshaped into an
original design. Dry River's **layout** stays original (ADR-013, ADR-015); third-party assets may dress it
(materials, foliage, rocks, props).

**Consequences.** Raw packs stay git-ignored until adapted. Adapted assets follow the LFS rules (R-14),
and the Fab Standard License forbids redistributing source files publicly (the public site never
carries assets).

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

**Risk (recorded, accepted by the producer).** AMCU and ADF equipment designs belong to the Commonwealth
of Australia. A commercial release needs Defence permission, or a switch back to the fictional CMECU
pattern, which the pipeline keeps as a material swap. Tracked as R-27.

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
**Date:** 2026-09-28

**Context.** The producer asked for a map "re-creating the famous bridge crossing map from *America's Army
2*, with an Australian twist", built from the assets already in the project plus the Fab packs in
`Content/Downloaded/VaultCache/`. That request sits against four standing constraints: **L-0008**
(no *America's Army 2* content of any kind), **L-0007** (no commercial game models), **ADR-013** (maps
are built original; a third-party environment is never a base map) and **ADR-021** (licensed third-party
art may dress an original layout but never define one).

Two inventory findings shaped the decision.

**First, there is nothing to import.** All 18 content roots in the VaultCache are already installed in
`Content/`; the only unimported folder is a VFX pack. The cache is the Fab desktop staging area, not a
source of new map geometry.

**Second, there is no bridge to reuse.** A keyword sweep of all of `Content/` for bridge, gate, arch,
tunnel, pier, stone and wall returned 430 hits, every one of them Quarry Slate rock ledges, Singapore_Canal
stone *materials*, or Lyra audio. **No structural mesh exists in the project or in any installed pack.**
The only packs with buildings are Asian canal architecture (ruled out on look and culture, ADR-016) and
the Rural Australia pack, which has none at all.

**Decision.**

- **Ravenshoe Crossing** (`/Game/Maps/L_Ravenshoe_01`) is designed and built **original**: 300 × 200 m,
  a high-country granite gorge crossed by a **wrought-iron lattice-girder road bridge**, with a **stone
  road-gate house** whose arched road passage is the terminal objective. Design in `Docs/MAPS_RAVENSHOE.md`.
- The bridge, the gatehouse, the abutments and the gorge walls are **modelled by us** in Blender and are
  **Class F** (L-0011, ADR-020). Dressed with already-installed Class A packs by reference only.
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
- *Find a bridge mesh in the VaultCache* — not available. The sweep found none, so the question is moot.
- *Import the unimported VFX pack* — rejected as irrelevant. A VFX common pack has no map geometry.
- *Wait for a capture on Red Gum before designing another map* — rejected. Red Gum's stalemate is a
  balance problem in a 1 km open map, not a reason to stop designing small maps.

**Consequences.**
- The map adds **no new third-party dependency** and needs no new import; it is buildable from the
  project as it stands. That is deliberate — it is the strongest available answer to L-0008.
- Two original Blender generators are needed (`ravenshoe_bridge.py`, `ravenshoe_gatehouse.py`) plus a
  `Tools/Common/ravenshoe_spec.py` shared with the CI verifier, following the `dryriver_blockout.py`
  pattern.
- The inventory exposed a **pre-existing licence gap**: nine already-installed Fab packs, including
  `Scene_QuarrySlate` which this map builds on, had no row in either register. Corrected in this session
  as bookkeeping under **L-0016b**. No asset changed.
- The map is a **candidate fifth map** (`M-008`), not a replacement for Dry River as the slice test bed.
- Sizing, rotation distances, cover counts and sightlines are **design targets until the blockout is
  generated and measured**. Navigation must be baked in the interactive editor, and no cover or sightline
  figure may be quoted from a commandlet.

## ADR-028 — Every Fab asset is cleared for Southern Spear; no per-asset licence lookups

**Status:** Accepted (producer, 2026-09-28: "EVERY asset added via FAB is free for our use case ... no need to
keep looking it up"). Extends ADR-021.
**Date:** 2026-09-28

**Decision.** Any asset the producer adds from Fab (to the project, the engine or the Fab library cache) is
cleared for use in Southern Spear: a free-to-play game under the producer's revenue threshold. Agents do not
look up or confirm Fab licences per asset, and do not hold an asset back pending a licence check. The
licence register records each Fab asset by name as "Fab, cleared under ADR-028".

**Still applies (not licence questions):** the fiction rules (ADR-016: no real insignia, manufacturer
marks or real weapon names in game), a one-line credit for listings marked CC BY (collected in the
credits, not a blocker), raw packs stay git-ignored until adapted (ADR-021, R-14), and the public
website never carries asset files.

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

**Context.** Ravenshoe Crossing was delivered with four *constant* materials on the one structure the
map is named for. The geometry was good — 68 m lattice girder, 21 uprights a side, modelled because no
bridge mesh exists anywhere in the project or in any installed pack — and it rendered as flat colour,
because nothing in the project could put a surface on it. The Fab cache turned out to hold almost no
usable tiling textures: 23 of the 30 folders ship under ten images each, and those are mostly prop
albedos, not tileable PBR sets. The one genuinely good set in the project,
`Content/AutomotiveBridgeScene/` (319 assets of asphalt, concrete, rust and steel decal maps), is
**untracked, another agent's in-flight work**. Binding a committed map to it would leave the map
broken for anyone who checked out this commit without theirs.

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

## ADR-033 — Australian Army ranks as service levels 1–100, with insignia; kills earn capped XP

**Status:** Accepted (producer, 2026-09-28, in session): "mimic Australian Army rankings, private through to
general, even with their insignia (displayed in the scoreboard), like honor was for America's Army. XP is
gained through kills, objectives etc. ... highest rank is general 100 ... private might be 1–4, then at 5 it
goes to lance corporal", then "needs to be realistic", pointing to army.gov.au/about-us/ranks.
**Supersedes:** ADR-032's rank ladder and its no-kill-event rule (guard SS009, retired); GDD §6.2 "officer
ranks are reserved" and §6.4 "kills are not rewarded", for progression. **Extends:** ADR-016 by exception,
as ADR-025 did.
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

**Release gate — R-48.** The crown and the Coat of Arms are Crown and Commonwealth emblems, and the insignia
set as a whole is the Australian Army's. Using them was the producer's call for development, as ADR-025 was
for uniforms. **Before release** they need permission (Defence for the insignia; the Department of the Prime
Minister and Cabinet for the Coat of Arms), or the WO1 and crown devices are swapped for the fictional
CMECU/3 ACR ones. The swap is a change to `SSInsigniaRaster.h`, with no data or assets to replace.

**Known limit.** The level shown to other players comes from each player's own local record, which isn't
authoritative (R-46). It is display only and gates nothing. Server-authoritative records are Phase 5 work.
