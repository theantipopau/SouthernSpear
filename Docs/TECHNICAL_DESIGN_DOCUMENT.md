# TECHNICAL DESIGN DOCUMENT — Southern Spear

**Document ID:** `Docs/TECHNICAL_DESIGN_DOCUMENT.md`
**Status:** Baseline — Phase 0
**Last updated:** 2026-09-26
**Engine:** Unreal Engine 5.8.3 (Installed Build, `E:\Unreal\UE_5.8`)
**Foundation:** Lyra Starter Game 5.8 (`EngineAssociation: "5.8"`)

---

## 1. Foundation Decision

### 1.1 What we found

The Lyra sample obtained for this project declares:

```json
"EngineAssociation": "5.8"
```

Lyra is **version-matched to the installed engine**. This is the outcome gate **G0.8** anticipated, and it removes the primary architectural risk (that Lyra targets an older engine and would need a port). A compile is still required to confirm — compatibility is *declared*, not *proven*.

Lyra 5.8 ships with the plugins this design depends on, confirmed present in `LyraStarterGame.uproject`:

| Required capability | Lyra / engine plugin present | Reuse decision |
|---|---|---|
| Game Feature plugins | `GameFeatures` | **Adopt as-is** |
| CommonUI | `CommonUI`, `CommonGame`, `UIExtension` | **Adopt as-is** |
| Enhanced Input | `EnhancedInput` | **Adopt as-is** |
| Gameplay Ability System | `GameplayAbilities` | **Adopt as-is** |
| Replicated movement | `ShooterCore` | **Adapt** |
| Weapons / equipment | `ShooterCore` | **Adapt** |
| Character & animation | `ShooterCore` | **Adapt** |
| Teams | `ShooterCore` | **Adapt** |
| Spectating | `ShooterCore` | **Adapt** |
| Bots | `ShooterCore` | **Adapt** |
| Settings | `GameSettings`, `CommonUser` | **Adopt as-is** |
| Session handling | `ShooterCore` + OnlineFramework | **Adopt + extend** |
| Replication optimisation | `ReplicationGraph` | **Adopt as-is** |
| Behaviour trees | `GameplayStateTree`, `GameplayBehaviors` | **Adopt as-is** |
| Message routing | `GameplayMessageRouter` | **Adopt as-is** |
| Online services | `OnlineServicesOSSAdapter`, `OnlineServicesNull` | **Adopt behind our interface** |
| Subtitles | `GameSubtitles` | **Adopt as-is** |
| Automation tests | `ShooterTests`, `RuntimeTests` | **Adopt and extend** |

### 1.2 Integration model: fork-and-layer, not rewrite

**Decision: Lyra's source is vendored into this repository as a baseline snapshot. Southern Spear ships as new plugins layered on top. Lyra type names are preserved.**

Rejected alternatives:

| Alternative | Why rejected |
|---|---|
| Rename every Lyra type to a `SouthernSpear`/`SS` prefix | `ULyraGameState`, `FLyraGameplayTags` and friends are referenced by name inside binary `.uasset` files. Renaming the C++ types breaks every Blueprint, data asset and level that references them — silently, at load time. Cost is enormous; benefit is cosmetic. |
| Ignore Lyra, rebuild from scratch on GAS + Game Features | Discards a battle-tested ability set, replication graph, camera stack, weapon framework and settings system. Re-implementing these is months of work with worse results. Directly contradicts the brief. |
| Keep Lyra entirely external to the repo | The engine is an **Installed Build** — Lyra cannot live in the engine tree. It must be vendored for the project to build. |

**The practical consequence:** there will be `Lyra*` and `ShooterCore` identifiers in the codebase. This is intentional and is recorded as departure **D-01**. Our new code never uses those prefixes; all new types are `SS_` / `FSS` / `USS`.

### 1.3 Mandatory departure log

Every substantial departure from Lyra is recorded in `Docs/LYRA_ADOPTION.md` **before** the code is written. Initial entries:

| ID | Departure | Rationale |
|---|---|---|
| **D-01** | Lyra type names preserved, not renamed | Blueprint reference breakage; see §1.2 |
| **D-02** | Team presentation is a **client-side cosmetic resolver**; Lyra's team colour model is replaced | Colour-only team ID violates the accessibility and identification rules in GDD §3.2 |
| **D-03** | Weapon *data* is fully data-driven via `FSSWeaponDefinition`; Lyra's weapon assets are refactored behind it | Lyra hardcodes much weapon behaviour in assets; we need a tunable table |
| **D-04** | Progression lives in its own plugin with a **versioned persistence interface**, not Lyra's experience/asset model | Requirements demand explicit versioning and server authority |
| **D-05** | Dedicated server is a first-class target from Phase 0, not a later hardening step | Acceptance criteria require a packaged DS in the vertical slice |
| **D-06** | Vehicle gameplay excluded from the vertical slice | Vehicle networking must be proven before modes depend on it |

---

## 2. Repository & Module Layout

```
E:\SouthernSpear\                    (repo root — see PROJECT_AUDIT R-02 on the space in the path)
├── SouthernSpear.uproject
├── Config/
│   ├── DefaultEngine.ini
│   ├── DefaultGame.ini
│   ├── DefaultGameplayTags.ini
│   └── DefaultSouthernSpear.ini
├── Content/SouthernSpear/{Core,Characters,Weapons,Equipment,Animations,
│                          Audio,UI,Maps,Training,Effects,Data,Developer}
├── Content/SouthernSpear/Vendor/    (third-party content, segregated, never reorganised)
├── Source/
│   ├── SouthernSpearGame/           (thin main game module)
│   └── SouthernSpearEditor/         (editor tooling module)
├── Plugins/
│   ├── (Lyra baseline) AsyncMixin  CommonGame  CommonLoadingScreen  CommonUser
│   │                 GameFeatures GameSettings  GameplayMessageRouter
│   │                 GameSubtitles LyraExampleContent  ModularGameplayActors
│   │                 PocketWorlds  UIExtension  ShooterCore  ShooterMaps
│   │                 TopDownArena  ShooterTests  ...
│   └── (new, Southern Spear)
│       ├── SouthernSpearCore/
│       ├── SouthernSpearTeam/
│       ├── SouthernSpearWeapons/
│       ├── SouthernSpearCombat/        (damage, medical, suppression)
│       ├── SouthernSpearRoles/
│       ├── SouthernSpearProgression/
│       ├── SouthernSpearTraining/
│       ├── SouthernSpearObjectives/
│       ├── SouthernSpearOnline/
│       └── SouthernSpearUI/
├── GameFeatures/                      (experience plugins — data-configurable modes)
│   ├── SSExp_ObjectiveAssault/
│   ├── SSExp_SecureAndHold/
│   ├── SSExp_TrainingRange/
│   └── SSExp_ForwardOperatingBase/
├── Maps/                              (map content plugins, one per map)
│   ├── SSMap_DryRiver/
│   └── ...
├── Tools/                             (Blender/export/CI scripts)
├── Build/                             (Graphs, packaging profiles)
├── Docs/
└── .github/workflows/
```

### 2.1 Module rules (enforced at review)

1. **`SouthernSpearCore` depends on nothing of ours.** Every other plugin may depend on it; it depends on none of them. This prevents circular dependencies and keeps the dependency graph a DAG.
2. **A plugin may not include headers from a sibling plugin.** Depend on public headers only, or on an interface.
3. **No plugin may reference another plugin's content assets** except through a `UPrimaryDataAsset` and the Asset Manager.
4. **No `SS_` class may live in a Lyra module.** Conversely, no Lyra class may be modified without a corresponding `LYRA_ADOPTION.md` entry.
5. **Gameplay-affecting logic is C++.** Blueprints configure, animate, compose UI and tune. A Blueprint must never be the authoritative implementation of damage, scoring or progression.

### 2.2 Plugin dependency DAG

```
                 SouthernSpearCore
                        │
        ┌───────────────┼───────────────┬──────────────┐
        │               │               │              │
  SouthernSpearTeam  Weapons        Roles        Progression
        │               │               │              │
        └───────┬───────┴───────┬───────┘              │
                │               │                      │
          Combat ──────────────┘                      │
                │                                      │
           Objectives ──────────── Training ───────────┤
                                                          │
                                                    Online ─┘

        SouthernSpearUI depends on all of the above (presentation only)
        GameFeatures/* depend on Core, Team, Weapons, Combat, Objectives
```

---

## 3. The Team & Contextual Presentation System

The highest-risk system in the project. It must be provably cosmetic.

### 3.1 Data model

```cpp
// USS_TeamId.h  — the single source of truth for team identity
UENUM(BlueprintType)
enum class ESS_TeamId : uint8
{
    None     = 0,
    Friendly = 1,   // assigned per-match; the *local player's* team
    Opposing = 2,   // the other team
};
```

`ESS_TeamId` is **match-relative**, not faction-absolute. Team 0 in a match may be `Friendly` for player A and `Opposing` for player B. The faction is *derived*, never stored as an absolute "you are Australian".

### 3.2 Presentation resolution

```
FSSFactionPresentationSet (UPrimaryDataAsset)
├── Friendly
│   ├── SoldierMeshSet        (body, head, hair, helmet, carrier, webbing, pack, gloves, boots)
│   ├── UniformMaterialSet    (original multicam-style pattern + role variants)
│   ├── WeaponPresentationMap (WeaponId -> friendly model + sockets)
│   ├── InsigniaSet           (fictional unit flashes)
│   └── VoiceSet
└── Opposing
    ├── SoldierMeshSet        (mixed field clothing, chest rigs, distinct silhouette)
    ├── UniformMaterialSet
    ├── WeaponPresentationMap (same WeaponId -> AK-pattern models + sockets)
    ├── InsigniaSet           (fictional non-national markings)
    └── VoiceSet
```

Resolution flow:

```cpp
// USS_FactionPresentationResolver.h
class SOUTHERNSPEARTEAM_API UFSSFactionPresentationResolver
{
public:
    // Purely cosmetic. Given a local viewer's team and a target's team,
    // return which side of the set to use.
    static ESSLocality ResolveLocality(ESS_TeamId LocalTeam, ESS_TeamId TargetTeam);

    // Returns the presentation set for a given *world-relative* side.
    // Note the sign flip: internally a side is stored as Team0/Team1,
    // but resolved against the local viewer.
    static const UFSSFactionPresentationSet* ResolveForLocalViewer(
        const UObject* WorldContext, ESS_TeamId ViewerTeam, ESS_TeamId SubjectTeam);
};
```

### 3.3 The encapsulation guarantee

The resolver is a **pure lookup**. It has:
- No gameplay-facing return types (returns only mesh/material/audio/voice assets).
- No dependency on `UHealthComponent`, `UWeaponInstance`, `UAbilitySystemComponent`.
- No settable state, so it cannot be used to smuggle a gameplay value to a client.

A **static analysis rule** in CI greps the `SouthernSpearTeam` public headers for any inclusion of weapon, damage or ability headers outside an explicitly whitelisted test file. Presentation touching gameplay is a build failure, not a code-review note.

### 3.4 Symmetry guarantee

Gameplay data (damage, fire rate, capacity, speed, health) is keyed by `WeaponId`, which is **team-independent**. Presentation data is keyed by `(WeaponId, Locality)`. A test asserts that for every weapon, the gameplay struct resolved from a `FSSWeaponDefinition` is byte-identical regardless of the locality used to reach it.

### 3.5 Leak prevention

Every surface where a dead or spectating player might receive information is enumerated in `TEST_PLAN.md` §"Information leakage" and tested. Spectator mode is **friend-observer scoped by default**; free-fly spectating of the opposing team requires elevated permissions and is logged.

---

## 4. Weapons

### 4.1 `FSSWeaponDefinition`

A `UPrimaryDataAsset` covering every field the brief requires:

```cpp
UCLASS(BlueprintType)
class SOUTHERNSPEARWEAPONS_API UFSSWeaponDefinition : public UPrimaryDataAsset
{
    GENERATED_BODY()
public:
    // --- Identity -------------------------------------------------------
    FName WeaponId;                   // stable internal key
    FText DisplayName;

    // --- Reference data (separation enforced) ---------------------------
    FSSWeaponReferenceData Reference;  // calibre, magazine type, real-world
                                       // published figures, tuning-off
    FSSWeaponTuningData Tuning;        // ACTUAL gameplay values

    // --- Class ----------------------------------------------------------
    ESS_WeaponClass WeaponClass;      // Rifle, SupportWeapon, Pistol, Launcher...
    ESS_FireMode SupportedFireModes;  // bitmask: Semi, Auto, Burst

    // --- Capacity & rate ------------------------------------------------
    int32 MagazineCapacity;           // or belt capacity for support weapons
    float RoundsPerMinute;
    float MuzzleVelocity;             // abstract units, not real m/s

    // --- Reload ---------------------------------------------------------
    FSSReloadTimings ReloadTimings;   // Tactical, Empty, Partial

    // --- Ballistics -----------------------------------------------------
    FSSRecoilProfile Recoil;          // per-shot vertical/horizontal pattern
    FSSStabilityProfile Stability;    // base spread, per-stance, per-movement
    FSSDamageCurve Damage;            // location falloff by hit zone
    int32 PenetrationClass;

    // --- Presentation ---------------------------------------------------
    TSoftObjectPtr<USkeletalMesh> FirstPersonMesh;
    TSoftObjectPtr<USkeletalMesh> ThirdPersonMesh;
    TSoftObjectPtr<UAnimSequenceBase> AnimationSet;
    TArray<FName> OpticSockets;
    TArray<FName> MuzzleSockets;
    bool bSupportsBipod;

    // --- Networking -----------------------------------------------------
    FSSNetworkRelevancySettings Relevancy;
};
```

### 4.2 Reference data vs tuning data

`FSSWeaponReferenceData` holds real-world published specifications — calibre, magazine type, approximate published rates. `FSSWeaponTuningData` holds the **actual gameplay values**, which diverge freely from reality for game feel.

These are **separate structs for a legal reason**: reference data is descriptive and sourced, while tuning is original design work. They are never merged, and `Reference` is never read by gameplay code. A test asserts no gameplay function reads `Reference`.

### 4.3 Weapon instancing

`UFSSWeaponInstance` — per-spawn state (ammo, fire mode, chamber, bipod, suppression) driven by GAS abilities for fire, reload, ADS, and bipod deploy. Server-authoritative: the client requests, the server decides, the server replicates the state.

---

## 5. Damage, Medical & Suppression

```cpp
USTRUCT(BlueprintType)
struct FSSDamageResult
{
    FName HitZone;         // Head, Torso, Arm, Leg...
    float AppliedDamage;
    bool  bIncapacitated;   // went down rather than died
    float BleedRate;       // per second while down
    float StaminaDrain;
};
```

Rules:
- Damage is **only ever applied by the server** (`ApplyDamage` is authority-gated; the client sends a fire request, not a result).
- **Incapacitation**, not instant death, for torso/limb at low health.
- Bleeding starts on incapacitation; **stabilisation** stops it.
- Field dressing: slow, limited, cannot sprint, self-treatment has a worse outcome than medic treatment.
- **No in-round regeneration.** Enforced by test.
- Suppression: reduces stability, blurs the edges of vision, and is *informational* for the suppressed player and their squad (a suppressed enemy is easier to spot for their team) — this is a team-coordination mechanic, not a punishment.

### 5.1 Friendly fire

```cpp
UENUM(BlueprintType)
enum class ESS_FFConsequence : uint8 { None, Log, Warning, Escalate, Mute };
```

Escalation ladder is server-side, logged, and surfaced in the post-round summary. A quiet, escalating, logged consequence beats a loud ban nobody can appeal.

---

## 6. Roles, Progression & Persistence

### 6.1 Data-driven definitions

| Asset | Type | Purpose |
|---|---|---|
| `UFSSRoleDefinition` | `UPrimaryDataAsset` | Qualification prereqs, weapon options, equipment, team/squad limits, spawn rules, leadership permissions |
| `UFSSRankDefinition` | `UPrimaryDataAsset` | Rank id, display name, threshold, insignia, permissions |
| `UFSSProgressionCurve` | `UPrimaryDataAsset` | XP → account level curve |
| `DT_SS_ProgressionCurve` | `UDataTable` | Fine-grained XP award rules per event |
| `UFSSCommendationDefinition` | `UPrimaryDataAsset` | Name, criteria, rarity, award |
| `UFSSMapLayerDefinition` | `UPrimaryDataAsset` | Mode, TOD, weather, objectives, deployment, roles, vehicles, respawn model, tickets, AI config |
| `UFSTrainingModuleDefinition` | `UPrimaryDataAsset` | Module id, prerequisites, pass criteria, qualification granted |

**The entire progression curve is editable without recompiling.** This is an explicit requirement, satisfied by keeping no progression numbers in C++.

### 6.2 XP award rules

```cpp
USTRUCT(BlueprintType)
struct FSSXpAward
{
    ESS_ProgressionEvent Event;
    int32 Award;
    float MaxPerMatch = 1;    // prevents idle or farming accumulation
    bool  bRequiresObjectiveProgress = true;
};
```

**Per-match caps on every event.** This is how "do not reward time spent idle" and "do not reward farming AI" are actually enforced rather than merely intended. A test asserts no award rule has an uncapped or unlimited event.

### 6.3 Persistence — versioned, behind an interface

```
     Gameplay code
           │  (never calls SaveGame directly)
           ▼
   ISSPersistenceProvider   <-- C++ interface, in SouthernSpearProgression
           │
     ┌─────┴──────────┐
     ▼                ▼
FSSLocalDev      FSSOnlinePersistence
Persistence      (FUTURE — server-authoritative)
(SaveGame-backed,      │
 DEV ONLY)             └── validates, rejects, audits
     │
     ▼
FSSServiceRecord   (versioned payload, schema v1)
```

```cpp
UINTERFACE(BlueprintType)
class SOUTHERNSPEARPROGRESSION_API UISSPersistenceProvider
{
    GENERATED_BODY()
public:
    virtual bool LoadServiceRecord(FSSServiceRecord& OutRecord) = 0;
    virtual bool SaveServiceRecord(const FSSServiceRecord& Record) = 0;
    // Server-side validation hook. A local provider ALWAYS returns false
    // for authoritative claims, which is what prevents client-side forging.
    virtual bool ValidateProgressionClaim(const FSSProgressionClaim& Claim) = 0;
};
```

### 6.4 `FSSServiceRecord` schema v1

```cpp
USTRUCT(BlueprintType)
struct FSSServiceRecord
{
    UPROPERTY() int32 SchemaVersion = 1;
    UPROPERTY() FString PlayerId;
    UPROPERTY() FSSSettingsRecord Settings;
    UPROPERTY() TArray<FSSTrainingResult> TrainingResults;   // best per module
    UPROPERTY() TSet<FName> Qualifications;                 // earned, permanent
    UPROPERTY() int32 AccountXp;
    UPROPERTY() FSSRankProgress Rank;
    UPROPERTY() TArray<FSSCommendation> Commendations;
    UPROPERTY() FSSStatistics Statistics;
    UPROPERTY() TArray<FName> UnlockedCosmetics;
    UPROPERTY() FSSDisciplinaryState Disciplinary;          // populated by server later
};
```

Four properties of this model matter:

1. **Versioned from day one.** `SchemaVersion` plus a registered migration chain. Migrations run on load, so an old record never silently mis-reads.
2. **A qualification, once earned, is never revoked.** It lives in the local record, and the brief requires it is never invalidated by server unavailability.
3. **Client claims are untrusted.** `ValidateProgressionClaim` on a local provider returns false by construction. XP earned in a multiplayer match is awarded by the *server*, not from client telemetry.
4. **The local provider is explicitly labelled dev-only.** Building a production backend inside the Unreal client is prohibited; the interface exists so the implementation can be swapped without touching gameplay code.

---

## 7. Online Services

```cpp
class SOUTHERNSPEARONLINE_API ISSOnlineSession
{
public:
    virtual void CreateSession(const FSSSessionRequest& Request, FOnSessionReady OnReady) = 0;
    virtual void FindSessions(const FSSSessionQuery& Query, FOnSessionsFound OnFound) = 0;
    virtual void JoinSession(const FSSSessionHandle& Handle, FOnSessionReady OnReady) = 0;
    virtual void LeaveSession() = 0;
    virtual void ReportPlayer(const FSSPlayerReport& Report) = 0;
};
```

Implementations: `FSSOnlineServicesOSS` (EOS-backed), `FSSNullOnlineServices` (offline/dev). Gameplay code only ever sees `ISSOnlineSession`.

**Epic Online Services** is evaluated for authentication, lobbies, session discovery, invitations, player reports and cross-platform identity abstraction — behind this interface, so it can be replaced or supplemented.

---

## 8. Build, Package & CI

### 8.1 Build commands (the real ones)

```bash
# Editor target
Engine/Build/BatchFiles/RunUBT.bat SouthernSpearEditor Win64 Development -Project="%CD%\SouthernSpear.uproject" -WaitMutex

# Client
Engine/Build/BatchFiles/RunUBT.bat SouthernSpear Win64 Development -Project="%CD%\SouthernSpear.uproject" -WaitMutex

# Dedicated server  <-- required for acceptance
Engine/Build/BatchFiles/RunUBT.bat SouthernSpearServer Win64 Development -Project="%CD%\SouthernSpear.uproject" -WaitMutex
```

### 8.2 Targets

| Target | Platform | Type | Purpose |
|---|---|---|---|
| `SouthernSpearEditor` | Win64 Editor | Editor | Development |
| `SouthernSpear` | Win64 | Game | Packaged client |
| `SouthernSpearServer` | Win64 | Server | **Dedicated server** (no client code compiled in) |
| `SouthernSpearClient` | Win64 | Game | Thin client for low-spec validation |

**Client/server build separation is a security control**, not an optimisation: the dedicated server target must not link rendering, audio-device or UI code, so there is no client-side surface to attack.

### 8.3 CI pipeline

`.github/workflows/build.yml` runs on every push:

1. Assert MSVC version meets the engine floor (**risk R-04**).
2. `git lfs fsck` — catch corrupt LFS objects.
3. Build `SouthernSpearEditor` Win64 Development.
4. Build `SouthernSpearServer` Win64 Development.
5. Run automation tests (see `TEST_PLAN.md`).
6. Static check: presentation-must-not-touch-gameplay grep (§3.3).
7. Static check: no `.uasset`/`.umap` committed without a matching `LICENCE_REGISTER.md` entry.

---

## 9. Performance Budgets

Measured, not aspirational. Baselines to be confirmed in the vertical slice; these are the targets the project will be held to.

### 9.1 Client frame budget (1080p, RX 9070 XT target)

| Metric | Budget |
|---|---|
| Frame time | **16.6 ms** (60 fps) floor, **13.9 ms** (72 fps) stretch |
| Game thread | ≤ 8.0 ms |
| Render thread | ≤ 10.0 ms |
| GPU | ≤ 12.0 ms |
| Draw calls | ≤ 3,500 |
| Triangles | ≤ 4.0 M |
| Skeletal mesh cost | ≤ 6 ms GPU, ≤ 1.5 ms game thread |
| Texture memory | ≤ 1,200 MB |
| Shader complexity | ≤ 250 ALU, ≤ 4 texture samples per material |

### 9.2 Server budget (dedicated, 9800X3D)

| Metric | Budget |
|---|---|
| Server tick | ≤ 8.0 ms at 30 Hz |
| Replicated actors | ≤ 1,200 active, ≤ 200 always-relevant |
| Bandwidth (per client) | ≤ 60 KB/s down, ≤ 15 KB/s up at steady state |
| Player count per server | 32 baseline, 64 stretch |
| Dedicated-server memory | ≤ 12 GB at 64 players |
| Map load (travel) | ≤ 25 s from a cold server |

### 9.3 Measurement

Validated with Unreal Insights, Network Profiler, `stat unit`, `stat net`, `stat rhi`, and `NetEmulation` PIE profiles. **No performance claim is reported without an Insights trace or a stat capture attached.**

---

## 10. Security Model

| Threat | Control |
|---|---|
| Client-authoritative damage | Damage applied only on server; `ApplyDamage` authority-gated |
| Client-forged progression | XP awarded by server; local provider's `ValidateProgressionClaim` always false |
| Movement cheating | Server-authoritative movement validation; out-of-bounds state rejected |
| Inventory cheating | Server-owns inventory; client requests, server authorises |
| Rate-limit abuse | Server-side rate limiting on fire, reload, chat, ping, interaction |
| Name/chat injection | Sanitised, length-capped, profanity-filtered server-side |
| Admin abuse | Every admin action written to an append-only audit log |
| Secrets in repo | `.gitignore` blocks `.env`, keys, `.p12`, credentials |
| Client surface on server | Dedicated Server target excludes client-only modules |
| Anti-cheat | Pluggable integration point; status surfaced in the server browser |

---

## 11. Automation Test Strategy

UE Automation Framework (`IMPLEMENT_SIMPLE_AUTOMATION_TEST`), split into:

| Suite | Runtime | Covers |
|---|---|---|
| `Unit.*` | Seconds | Progression maths, rank thresholds, damage curves, role limits, save/load, migrations |
| `Network.*` | Minutes | Team presentation both directions, damage authority, weapon replication, reload interruption, objective replication |
| `Integration.*` | Minutes | Session discovery, join-in-progress, disconnect/reconnect, map travel, settings persistence |
| `Security.*` | Minutes | Invalid client requests, forged progression claims, rate limits |
| `Leak.*` | Minutes | Spectator, kill feed, post-round information leakage |

Network tests use `NetEmulation` PIE profiles (latency, jitter, packet loss) and a **real dedicated server process** for the acceptance criterion. A listen server is explicitly **not** accepted as proof.

---

## 12. Content Pipeline

### 12.1 Sourcing order (mandatory)

1. Can an existing project asset be legally reused?
2. Search Fab for a properly licensed asset.
3. Record asset, publisher, source URL, licence, modifications in `LICENCE_REGISTER.md`.
4. If none suitable → create an **original placeholder**.
5. Replace placeholders incrementally with original Blender production.
6. Never download from unverified ripping/redistribution sites.
7. "Free" ≠ unrestricted.
8. Preserve required attribution.
9. **Verify legal right to include in a packaged commercial product before depending on it.**

### 12.2 Blender standards

Metric units · consistent forward/up axes (+Y forward, +Z up) · applied transforms · `SS_<Type>_<Name>` naming · non-destructive modifiers · high/low-poly workflow · UV sets · texture baking · collision meshes · LODs · correct static vs skeletal determination · documented export presets · **source `.blend` retained in LFS** · FBX/glTF export tested before mass production.

Blender 5.2.2 LTS, not on `PATH`; scripts use the absolute path or `Tools/Blender/venv.ps1`.

---

## 13. Coding Standards

| Rule | Detail |
|---|---|
| Naming | `U`/`A`/`F`/`I`/`E` prefixes; `SS_` / `USS` / `FSS` / `ESS` for all new types |
| Header order | `*.generated.h` is always last |
| Module API | Every module exports `SOUTHERNSPEAR<NAME>_API` |
| Replicated vars | `UPROPERTY(Replicated)` + `GetLifetimeReplicatedProps`; use `DOREPLIFETIME_CONDITION` deliberately |
| RPCs | `Server`, `Client`, `NetMulticast` — always `_Implementation`; validate every payload server-side |
| Authority | Any function touching damage, ammo, score or progression asserts `HasAuthority()` |
| Logging | Declared `DEFINE_LOG_CATEGORY_STATIC` per module, `LogSSTeam` etc. |
| Comments | Explain *why*, never *what*. No commented-out code. |
| Include order | `CoreMinimal` → `CoreUObject` → engine → project, separated by blank lines |

Full detail: `Docs/CODING_STANDARDS.md`.

---

## 14. What Is Not Designed Yet

Deliberately deferred, with the trigger that will unblock each:

| Area | Unblocked when |
|---|---|
| Weapon tuning numbers | Netcode proven in the vertical slice |
| Suppression tuning curve | Suppression system measurable in-game |
| AI behaviour complexity | Player-vs-player networking stable |
| Vehicle netcode | Base replication stable; drives Convoy Interdiction |
| Final art direction | Placeholders proven in place |
| Production backend | Interface stable; never inside the client |
| Anti-cheat vendor selection | Threat model reviewed |

---

## 15. Immediate Next Steps

1. **Gate G0.8** — copy Lyra in, rename the `.uproject`, compile `SouthernSpearEditor`. Record the result verbatim.
2. Open `Docs/LYRA_ADOPTION.md` and log every divergence as it happens.
3. Stand up `SouthernSpearCore` with the service-record interface and the settings save, so the first automated tests have something to test.
4. Then the team presentation system, because it is the highest-risk and most specification-heavy component.
