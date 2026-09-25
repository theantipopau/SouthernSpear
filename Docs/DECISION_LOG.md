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

**Status:** Accepted
**Date:** 2026-09-26

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

**Context.** The brief requires a fictional insurgent/militia presentation, and prohibits any real ethnic, religious, political or contemporary conflict group, and any derogatory imagery or stereotypes.

**Decision.** The opposing faction (working name *Kestrel Militia*) is invented: invented insignia, invented unit names, an internally consistent backstory, and a visual design driven by **kit and silhouette** rather than ethnic or cultural coding.

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

## Open Decisions

| ID | Question | Needed by |
|---|---|---|
| ADR-013 | Repository path: relocate to remove the space in `Australian Army Game`? | Before packaging |
| ADR-014 | Online services: EOS vs Steam vs custom, and in what order? | Phase 5 |
| ADR-015 | Anti-cheat: vendor, platform-provided, or bespoke? | Phase 5 |
| ADR-016 | Match size: 16, 32 or 64 baseline? | Phase 4, after performance profiling |
| ADR-017 | Whether to retain or drop Lyra's third example experience (Exploder) | Phase 1 |
