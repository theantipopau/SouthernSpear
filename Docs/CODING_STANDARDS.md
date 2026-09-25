# CODING STANDARDS — Southern Spear

**Document ID:** `Docs/CODING_STANDARDS.md`
**Status:** Baseline — Phase 0
**Last updated:** 2026-09-26

---

## 1. Language Standard

**C++20** (the engine default for UE 5.8). No `/std:` flags are added by project code.

Conventions follow the [Epic C++ Coding Standard](https://dev.epicgames.com/documentation/en-us/unreal-engine/coding-standard-in-unreal-engine). Where this document and Epic's differ, Epic's wins — consistency with the engine is more valuable than local preference.

---

## 2. Naming

| Kind | Prefix | Example |
|---|---|---|
| UObject class | `U` | `USSServiceRecord` |
| Actor class | `A` | `ASSObjectiveActor` |
| USTRUCT | `F` | `FSSWeaponDefinition` |
| Interface | `I` | `ISSPersistenceProvider` |
| Enum | `E` | `ESS_TeamId` |
| Gameplay tag | `SS.` | `SS.Team.Friendly` |

**All new Southern Spear types use the `SS` family:** `USS`, `ASS`, `FSS`, `ISS`, `ESS`. Lyra types keep their `Lyra`/`Shooter` prefixes — see TDD departure D-01.

**Never** use a `Lyra` or `Shooter` prefix on a new type. If a Lyra type must be extended, wrap it — do not subclass in place and do not add Lyra-prefixed members.

| Other | Convention | Example |
|---|---|---|
| Variables | `PascalCase` | `MagazineCapacity` |
| Private members | `PascalCase` + leading `_` | `_ReplicatedHealth` |
| Functions | `PascalCase` verb-first | `ResolvePresentationSet()` |
| Booleans | `b` prefix | `bSupportsBipod` |
| Files | Match the primary class | `SSTeamId.h` |
| UENUM values | `SCREAMING_SNAKE` | `ESS_TeamId::Opposing` |
| Delegates | `F` + `On` | `FOnSessionReady` |
| Namespaces | Avoid; prefer scoped types | — |

---

## 3. File Layout

```cpp
// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "SSTeamId.generated.h"   // <-- ALWAYS LAST INCLUDE

class ASSObjectiveActor;           // <-- forward declare, not include
```

Include order, blank line between each group:

1. `CoreMinimal.h`
2. `CoreUObject/Engine/GameplayTags/...` (engine)
3. Project headers
4. **`*.generated.h` — always last**

---

## 4. Modules

Every module exports an API macro:

```cpp
SOUTHERNSPEARTEAM_API
```

Module rules must:
- Use `PublicDependencyModuleNames` for public API only.
- Use `PrivateDependencyModuleNames` for implementation details.
- Never create a dependency cycle. `SouthernSpearCore` depends on **none** of our plugins.

---

## 5. Replication

```cpp
void ASSSoldier::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);

    DOREPLIFETIME(ASSSoldier, CurrentStance);
    DOREPLIFETIME_CONDITION(ASSSoldier, bIsDown, COND_SkipOwner);
}
```

Rules:
1. `UPROPERTY(Replicated)` **and** an entry in `GetLifetimeReplicatedProps`. One without the other is a defect.
2. Use `DOREPLIFETIME_CONDITION` deliberately — unconditional replication of everything is a bandwidth defect, not a style choice.
3. **Never replicate raw pointers to UObjects that can be destroyed.** Use `TObjectPtr`, weak object pointers or stable IDs.
4. Replicate **state**, never **events** derived from state. The client derives presentation from replicated state so it cannot diverge.

### RPCs

```cpp
UFUNCTION(Server, Reliable)                 // <-- validated in _Implementation
void ServerRequestFire(const FVector_NetQuantize& Origin, const FVector_NetQuantizeNormal& Dir);

UFUNCTION(Client, Reliable)
void ClientConfirmHit(const FSSDamageResult& Result);

UFUNCTION(NetMulticast, Unreliable)         // for cosmetic, frequent events only
void MulticastPlayMuzzleFlash();
```

- **Every** `Server` RPC re-validates its payload. Never trust a client-supplied value — including its own damage numbers.
- `Reliable` is rarely correct. Use it only where losing the packet is unacceptable; prefer `Unreliable` for cosmetic and high-frequency traffic.
- `NetMulticast` for anything the server does not need to confirm.

---

## 6. Authority

Any function that touches damage, ammunition, score, qualifications, XP or team assignment **asserts authority**:

```cpp
void UFSSWeaponInstance::ConsumeRound()
{
    checkf(GetOwnerRole() == ROLE_Authority, TEXT("ConsumeRound must run on the server"));
    ...
}
```

Client code **requests**; server code **decides**. This is not stylistic — it is the primary anti-cheat control (TDD §10).

---

## 7. Data

- Gameplay tuning lives in `UPrimaryDataAsset` / `UDataTable`, never in C++ constants. A static CI scan fails the build if a progression number appears in C++.
- Validate data assets in `PostLoad` or via an editor-time validator. A malformed data asset must fail loudly at load, not silently at gameplay time.
- Reference data and tuning data stay in separate structs (TDD §4.2). No gameplay function may read `Reference`.

---

## 8. Comments

```cpp
// GOOD - explains why
// Rewind is capped at 200ms; beyond that the ghost desyncs visibly and players
// report seeing hits they did not make.
constexpr float MaxRewindSeconds = 0.2f;

// BAD - restates the code
// Set MaxRewindSeconds to 0.2
constexpr float MaxRewindSeconds = 0.2f;
```

- Comment **why**, never **what**.
- **No commented-out code.** It rots. Delete it or fix it.
- `TODO` must name an owner and an issue: `// TODO(VAS): SS-1421 bipod friction curve`.
- Document the *invariant*, not the implementation: "presentation must never affect gameplay", not "we call GetMesh here".

---

## 9. Logging

```cpp
DEFINE_LOG_CATEGORY_STATIC(LogSSTeam, Log, All);
```

One category per module: `LogSSCore`, `LogSSTeam`, `LogSSWeapons`, `LogSSCombat`, `LogSSProgression`, `LogSSTraining`, `LogSSObjectives`, `LogSSOnline`, `LogSSAdmin`.

Never log player-supplied strings without sanitisation, and never log anything that would leak a hidden player's state into a public channel.

---

## 10. Error Handling

- `checkf` / `check` for **programmer errors** that must never occur in a shipping build.
- `ensureMsgf` for conditions that indicate a bug but should not crash a live server.
- `verify` for expensive checks, compiled out in `Shipping`.
- **Never** `try/catch`-style swallow a gameplay failure. A silently-ignored damage result is a security defect.

---

## 11. Performance

- No allocation in `Tick`. Use `TArray::SetNumUninitialized` / `Reserve` in `BeginPlay`.
- `Tick` disabled unless the actor actually needs it. `PrimaryActorTick.bCanEverTick = false` by default.
- Prefer `TObjectPtr<T>` over raw `T*` for UPROPERTYs.
- Blueprint-heavy loops over replicated data are a known desync source — keep gameplay logic in C++.

---

## 12. Review Checklist

- [ ] No `#if WITH_EDITOR` around gameplay logic that changes behaviour
- [ ] Every `Replicated` property has a lifetime entry, with a condition where appropriate
- [ ] Every `Server` RPC validates its payload
- [ ] Authority asserted on damage/ammo/score/progression paths
- [ ] No gameplay constants in C++ that should be data
- [ ] No commented-out code
- [ ] Comments explain *why*
- [ ] Module dependency rules respected (`Core` depends on nothing of ours)
- [ ] Any Lyra divergence recorded in `LYRA_ADOPTION.md`
- [ ] New asset added to `ASSET_REGISTER.md` **and** `LICENCE_REGISTER.md`
