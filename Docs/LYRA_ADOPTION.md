# LYRA ADOPTION & DEPARTURE LOG — Southern Spear

**Document ID:** `Docs/LYRA_ADOPTION.md`
**Status:** Open — gate G0.8 not yet run
**Last updated:** 2026-09-26

> **Mandatory rule:** *every* substantial departure from upstream Lyra is recorded here **before** the code implementing it is written. This log is the audit trail that lets a reviewer answer "why is this different from stock Lyra?" without reading the whole codebase.

---

## 1. Lyra Baseline

| Field | Value |
|---|---|
| Source | Lyra Starter Game, Epic Games |
| Version | 5.8 (`EngineAssociation: "5.8"`) |
| Licence | Unreal Engine EULA — see `LICENCE_REGISTER.md` L-0001 |
| Integration | **Fork-and-layer** — vendored into this repository, Southern Spear added as new plugins |
| Engine | UE 5.8.3 (Installed Build) |

---

## 2. Integration Decision

**Lyra is vendored as a baseline snapshot. Southern Spear ships as new plugins layered on top. Lyra type names are preserved.**

| Alternative | Verdict | Reason |
|---|---|---|
| Rename all Lyra types to `SS` | ❌ Rejected | Lyra types are referenced by name inside binary `.uasset` files. Renaming the C++ types breaks every Blueprint, data asset and level referencing them — silently, at load. Enormous cost, zero gameplay benefit |
| Rebuild from scratch on GAS/Game Features | ❌ Rejected | Discards a proven ability set, replication graph, camera stack, weapon framework, settings and bot system. Contradicts the brief |
| Keep Lyra outside the repo | ❌ Impossible | The engine is an **Installed Build**; Lyra cannot live in the engine tree. It must be vendored to build |
| Fork-and-layer | ✅ **Adopted** | Lowest risk, maximum reuse, and our new code is cleanly namespaced `SS_*` |

**Consequence:** `Lyra*` and `ShooterCore` identifiers exist in the codebase. This is intentional. All *new* code uses `SS_`/`USS`/`FSS`/`ESS` and never touches a Lyra type name.

---

## 3. Adoption Matrix

### 3.1 Adopt unchanged

| Capability | Plugin | Status |
|---|---|---|
| Game Feature plugin system | `GameFeatures` | Adopted as-is |
| CommonUI / CommonGame / UI extension | `CommonUI`, `CommonGame`, `UIExtension` | Adopted as-is |
| Enhanced Input | `EnhancedInput` | Adopted as-is |
| Gameplay Ability System | `GameplayAbilities` | Adopted as-is |
| Replication optimisation | `ReplicationGraph` | Adopted as-is |
| Significancy management | `SignificanceManager` | Adopted as-is |
| Settings architecture | `GameSettings`, `CommonUser` | Adopted as-is |
| Subtitles | `GameSubtitles` | Adopted as-is |
| Message routing | `GameplayMessageRouter` | Adopted as-is |
| Async patterns | `AsyncMixin` | Adopted as-is |
| Online services interface | `OnlineServicesOSSAdapter`, `OnlineServicesNull` | Adopted, wrapped |
| Automation test harness | `ShooterTests`, `RuntimeTests` | Adopted, extended |
| StateTree / behaviour trees | `GameplayStateTree`, `GameplayBehaviors` | Adopted as-is |

### 3.2 Adapt

| Lyra subsystem | Our use | Adaptation |
|---|---|---|
| Weapon framework | `ShooterCore` weapons | Data refactored behind `UFSSWeaponDefinition` (D-03) |
| Health / damage | `ShooterCore` health | Extended with incapacitation, bleeding, stabilisation (Phase 2) |
| Teams | `ShooterCore` team subsystem | Team model retained; **presentation model replaced** (D-02) |
| Character / pawn | `ShooterCore` pawn | Extended with role kit and presentation resolution |
| Animation | Lyra Manny/Quinn | Shared skeleton kept; original animations replace art (Phase 6) |
| Bots | `ShooterCore` bots | Routed through identical damage and objective systems (Phase 3) |
| Spectating | `ShooterCore` spectator | Hardened against information leakage (D-07) |
| Experience / game mode | `LyraGame` experience | New `SSExp_*` Game Feature plugins |
| Sessions | `OnlineFramework` | Wrapped behind `ISSOnlineSession` |

### 3.3 Replace

| Lyra subsystem | Replacement | Reason |
|---|---|---|
| Colour-based team identity | `UFSSFactionPresentationSet` + resolver | D-02 — colour-only identification violates accessibility and identification rules |
| Embedded progression | `SouthernSpearProgression` plugin | D-04 — needs explicit versioning and server authority |
| Listen-server-first flow | Dedicated-server-first | D-05 — acceptance requires a packaged DS |

---

## 4. Departure Log

### D-01 — Lyra type names preserved, not renamed

- **Category:** Structural
- **What:** All Lyra and `ShooterCore` type names remain as-is.
- **Why:** These types are referenced by name inside binary `.uasset` files. Renaming breaks content references silently at load.
- **Impact:** `Lyra*` identifiers remain in the codebase; all new code is `SS_*`.
- **Reversible:** Technically yes, at very high cost. Treated as permanent.
- **Logged:** Phase 0, TDD §1.2

### D-02 — Team presentation is a client-side cosmetic resolver

- **Category:** Gameplay / fairness / accessibility
- **Lyra provides:** Team identity expressed primarily through colour-coded materials and UI.
- **We provide:** `UFSSFactionPresentationResolver` — a **pure lookup** from `(viewer team, subject team)` to a presentation asset set. No gameplay-facing return types, no settable state, no dependency on weapon, damage or ability headers.
- **Why:** The brief requires that the contextual appearance system never affect hitboxes, collision, damage or network identity, and that identification never rely on colour alone (also an accessibility requirement).
- **Enforcement:** CI static scan — presentation headers must not include weapon/damage/ability headers outside a whitelisted test.
- **Symmetry:** Gameplay data is keyed by `WeaponId` and is team-independent. Asserted by test.
- **Logged:** Phase 0

### D-03 — Weapon behaviour is data-driven

- **Category:** Data architecture
- **Lyra provides:** Much weapon behaviour expressed in Blueprint assets.
- **We provide:** `UFSSWeaponDefinition` (`UPrimaryDataAsset`) covering all required fields, with `Reference` and `Tuning` structs kept separate.
- **Why:** Tuning must be adjustable without recompiling, and reference data must stay separable from original tuning for legal reasons.
- **Enforcement:** CI static scan — no gameplay function may read `Reference`; no gameplay constants in C++.
- **Logged:** Phase 0

### D-04 — Progression in a dedicated plugin with a versioned persistence interface

- **Category:** Persistence / security
- **Lyra provides:** Experience unlock and asset-driven unlock models.
- **We provide:** `SouthernSpearProgression` with `FSSServiceRecord` (schema v1), `ISSPersistenceProvider`, a dev-only local provider, and a migration chain.
- **Why:** Qualifications must be permanent, schema must be versioned, and client claims must be untrusted. `ValidateProgressionClaim` on the local provider returns false by construction.
- **Constraint:** No production backend inside the Unreal client.
- **Logged:** Phase 0

### D-05 — Dedicated server is a first-class target from Phase 0

- **Category:** Build / architecture
- **Lyra provides:** `LyraServer.Target.cs` exists, but Lyra's own development flow leans on listen servers and PIE.
- **We provide:** `SouthernSpearServer.Target.cs` built and packaged during the vertical slice, with client-only modules excluded.
- **Why:** The acceptance criteria require a packaged client connecting to a packaged dedicated server, and a listen server is explicitly not accepted as proof.
- **Logged:** Phase 0

### D-06 — Vehicle gameplay excluded from the vertical slice

- **Category:** Scope
- **Decision:** Convoy Interdiction and all vehicle networking are deferred until base replication is proven.
- **Why:** Vehicle networking is a distinct and substantial risk. Building modes on unproven vehicle netcode compounds risk.
- **Logged:** Phase 0

### D-07 — Spectating hardened against information leakage

- **Category:** Security / fairness
- **Lyra provides:** Spectator modes.
- **We provide:** Friend-observer spectating scoped to own team by default; opposing free-fly requires elevated permission and is audit-logged. No dead-outs. Leak-tested on every surface.
- **Why:** Explicit brief requirement, and a fairness property that must be enforced rather than reviewed.
- **Logged:** Phase 0

---

## 5. Vendor Patch Tracking

If upstream Lyra is ever updated, every local modification must be re-applied and re-logged. The **VENDORED** marker in `ASSET_REGISTER.md` records the pinned upstream revision.

| Item | Pinned revision | Modified |
|---|---|---|
| Lyra Starter Game 5.8 | Record on first import | Yes — pending G0.8 |

---

## 6. Open Questions

| Question | Owner | Resolved by |
|---|---|---|
| Does Lyra 5.8 compile cleanly on this exact engine build? | Lead programmer | Gate G0.8 |
| Which Lyra modules can be disabled without breaking the experience flow? | Lead programmer | Phase 1 |
| Is `ShooterCore` a hard dependency in 5.8, and can it be trimmed? | Lead programmer | Phase 1 |
| How much of the Lyra `Content/` is needed vs replaceable? | Technical art | Phase 1 |

---

## 7. Change Log

| Date | Entry | Detail |
|---|---|---|
| 2026-09-26 | Log created | D-01 … D-07 recorded as baseline departures |
| 2026-09-26 | G0.8 pending | Lyra download in progress; compile result not yet recorded |
