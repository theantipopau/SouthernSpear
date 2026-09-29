# Casualty, step 3 — where Lyra 5.8 will let a downed pawn be kept alive

Read-only research. No code is proposed here, only the hooks that exist and the gates that
already exist around them. Every claim below carries `file:line` so it can be re-checked.

## What was read

| What | Where |
|---|---|
| Lyra game source | `E:\Unreal\Lyra\LyraStarterGame\Source\LyraGame\` |
| Engine (GameplayAbilities) | `E:\Unreal\UE_5.8\Engine\Plugins\Runtime\GameplayAbilities\Source\GameplayAbilities\` |
| Engine build | `Engine\Build\Build.version` — **5.8.3, CL 58210709, branch `++UE5+Release-5.8`** |

Lyra here is the UE 5.8.3 sample, so the version the producer asked for.

---

## a. How `ULyraHealthComponent` decides death, and every gate that can stop it

The chain is: health attribute → one-shot out-of-health event → a gameplay event → the death
ability → the death *state*. Each link has its own gate, and **the state is not set by the
event** — the event only wakes the ability.

**1. The attribute reaches zero.** `ULyraHealthSet::PostGameplayEffectExecute`
(`AbilitySystem/Attributes/LyraHealthSet.cpp:171-183`) fires when health has actually moved
(`GetHealth() != HealthBeforeAttributeChange`, line 171) and is zero or less while the latch
`bOutOfHealth` is clear (176). It broadcasts `OnOutOfHealth` with the full `&Data.EffectSpec` (178),
then sets the latch (182).

**2. The client mirrors it.** `ULyraHealthSet::OnRep_Health` (`LyraHealthSet.cpp:48-56`) runs the
same `<= 0.0f` test but broadcasts with **null instigator, null causer and a null spec** (53).
Anything that needs the damage context must therefore be listening on the server.

**3. The component listens.** `ULyraHealthComponent::InitializeWithAbilitySystem`
(`Character/LyraHealthComponent.cpp:80`) binds `HealthSet->OnOutOfHealth` to `HandleOutOfHealth`.

**4. `HandleOutOfHealth`** (`LyraHealthComponent.cpp:148-187`):

- The entire body is inside `#if WITH_SERVER_CODE` (150). **A client never sends the death
  event**; everything about death originates on the authority.
- Gate: `if (AbilitySystemComponent && DamageEffectSpec)` (151). If the ASC is null or the spec
  is null, the function does **nothing at all** and death is simply lost.
- It builds a `FGameplayEventData` (155) whose `EventTag` is
  `LyraGameplayTags::GameplayEvent_Death` (156), `Target` is the ASC's avatar (158),
  `OptionalObject` is the effect definition (159) and — the part that matters for casualty —
  `ContextHandle` is the **damage effect's own context** (160). Source and target tag containers
  (161-162) and the damage magnitude (163) come along too.
- `FScopedPredictionWindow` (165) then `AbilitySystemComponent->HandleGameplayEvent(...)` (166).
- Separately it broadcasts an `Lyra.Elimination.Message` verb message (171-185), the "eliminated"
  feed. **This fires on zero health too, not on death** — it is keyed to the out-of-health event,
  not to the death state, so it will fire for a pawn we choose to keep alive.

Note what it does *not* do: it never calls `StartDeath()`. Health reaching zero starts a *process*,
not a *state*.

**5. The death ability.** `ULyraGameplayAbility_Death`
(`AbilitySystem/Abilities/LyraGameplayAbility_Death.cpp`):

- Constructor: `InstancedPerActor` (17), **`ServerInitiated`** (18), `bAutoStartDeath = true` (20),
  and an `FAbilityTriggerData` on `GameplayEvent_Death` with `TriggerSource = GameplayEvent`
  (24-28). The ability is woken by exactly the event the component just sent.
- `ActivateAbility` (33-57): collects the abilities to spare, `Ability.Behavior.SurvivesDeath`
  (38-39), then cancels **every** ability except those (42), `SetCanBeCanceled(false)` (44),
  changes the activation group to `Exclusive_Blocking` (46, logs an error but carries on if it
  fails), then `if (bAutoStartDeath) StartDeath()` (51-53).
- `StartDeath` (70-79) calls into the component **only** when `GetDeathState() == NotDead` (74).
- `EndAbility` (59-68) unconditionally calls `FinishDeath()` (65) "in case the ability doesn't".

**6. The state.** `ULyraHealthComponent::StartDeath` (235-255) refuses unless
`DeathState == NotDead` (237), then sets `DeathStarted`, adds loose tag count 1 for
`Status.Death.Dying` (246), broadcasts `OnDeathStarted` (252) and forces a net update (254).
`FinishDeath` (257-277) refuses unless `DeathState == DeathStarted` (259), sets `DeathFinished`
and adds `Status.Death.Dead` (268). `DeathState` replicates with `OnRep_DeathState`
(`LyraHealthComponent.h:131`) and the client replays `StartDeath` / `FinishDeath` from the
replicated transition (`LyraHealthComponent.cpp:190-232`).

### Every gate that can stop a death, in the order it is met

| # | Gate | Where | Effect |
|---|---|---|---|
| 1 | `Gameplay.DamageImmunity` on the target, unless self-destruct | `LyraHealthSet.cpp:82-86` | Damage magnitude set to 0 and the execute returns false. Health never falls. |
| 2 | `Cheat.GodMode` on the target, unless self-destruct | `LyraHealthSet.cpp:91-95` | Same, magnitude 0. **`#if !UE_BUILD_SHIPPING`.** |
| 3 | Clamp to `[MinimumHealth, MaxHealth]` when damage becomes health | `LyraHealthSet.cpp:148` | With `MinimumHealth = 1.0`, health cannot reach 0. |
| 4 | `MinimumHealth = 1.0` when `Cheat.GodMode` or `Cheat.UnlimitedHealth` | `LyraHealthSet.cpp:113-120` (guard at 115) | **`#if !UE_BUILD_SHIPPING`.** Health floors at 1, so `OnOutOfHealth` never fires. |
| 5 | `ClampAttribute` on every write | `LyraHealthSet.cpp:221-231` (via 189, 196) | Health clamped to `[0, MaxHealth]`; MaxHealth floored at 1. |
| 6 | `bOutOfHealth` latch | `LyraHealthSet.cpp:176-182`, cleared at `216-218` | The event is **one-shot per out-of-health transition**, not per hit. |
| 7 | `#if WITH_SERVER_CODE` + `AbilitySystemComponent && DamageEffectSpec` | `LyraHealthComponent.cpp:150-151` | Client never fires; a null spec silently drops the death. |
| 8 | **No granted, activatable death ability** | `LyraGameplayAbility_Death.cpp:24-28` | `HandleGameplayEvent` has no failure return here — an event with no listener is dropped silently. |
| 9 | `ActivationGroup` / cancel checks in `UAbilitySystemComponent::TryActivateAbility` | engine GAS | A blocked or already-active death ability means the state is never set. |
| 10 | `DeathState != NotDead` | `LyraHealthComponent.cpp:237` | `StartDeath` is a no-op once dying/dead. |
| 11 | `GetDeathState() == NotDead` before the ability calls through | `LyraGameplayAbility_Death.cpp:74` | Second, independent no-op guard. |

**The single lever that actually decides "this pawn dies" is gate 8**: a `GameplayEvent.Death`
event reaching a granted, activatable `ULyraGameplayAbility_Death` on the authority. Gates 1-7
decide whether health reaches zero; gates 9-11 make the resulting transition idempotent. That
distinction is what makes (c) tractable.

---

## b. Where health is clamped

All of it is in `ULyraHealthSet`, and there are three separate layers.

**The attribute-level clamp — `ClampAttribute`** (`LyraHealthSet.cpp:221-231`): health to
`[0, MaxHealth]`, MaxHealth to at least 1. It is reached from two overrides:

- `PreAttributeBaseChange` (185-190) — catches changes to the *base* value.
- `PreAttributeChange` (192-197) — the ASC's last-chance hook before **any** write, modifier
  execution or direct set. This runs on both server and client and is the lowest-level,
  cheapest interception point in the whole health system.

**The execution-level clamps — `PostGameplayEffectExecute`** (108-183): damage becomes health at
148, healing becomes health at 154, and a direct health write is clamped at 160. All three use
`FMath::Clamp(value, MinimumHealth, GetMaxHealth())`, so `MinimumHealth` (113, raised to 1.0 at
120 under the dev cheats) is the floor for every path.

**The cross-attribute fixup — `PostAttributeChange`** (199-219): if MaxHealth drops below current
health, the ASC is told to override health down to the new maximum (206-211) — so **lowering
MaxHealth is a second, indirect way to force a pawn's health down**. And the `bOutOfHealth` latch
is cleared the moment health is positive again (215-218).

Worth knowing: `Health` is declared `HideFromModifiers` (`LyraHealthSet.h:74`), so it moves only
through executions. That is why the `Damage` and `Healing` meta-attributes exist and why the
clamping is concentrated in `PostGameplayEffectExecute` rather than in a modifier.

---

## c. Keeping a pawn alive at zero health, without editing Lyra

Four options, honest assessment of each.

**1. Override `StartDeath` on a subclass of `ULyraHealthComponent`. This is the one to use.**
`LyraHealthComponent.h:81` declares `UE_API virtual void StartDeath();` — it is explicitly
virtual. A subclass that overrides it and does not call `Super` leaves `DeathState` at `NotDead`,
so no `Status.Death.Dying` tag, no `OnDeathStarted` broadcast, and the death ability's own
`StartDeath` (`LyraGameplayAbility_Death.cpp:74`) then finds the state already correct and does
nothing either. Gate 10 and gate 11 both go quiet at once, which is exactly the pair that would
otherwise fight each other.

What it does **not** stop, and this is the part that matters for casualty:

- The `GameplayEvent.Death` event is still sent (`LyraHealthComponent.cpp:166`) and the death
  ability **still activates**. So the pawn's other abilities have still been cancelled
  (`LyraGameplayAbility_Death.cpp:42`) and the activation group is still `Exclusive_Blocking` (46).
  **A downed pawn is an actor with its kit cancelled and its activation group blocking.** Anything
  that must keep working on it — the treat, a crawl, a call for help — has to be tagged
  `Ability.Behavior.SurvivesDeath` or granted through a different route.
- The `Lyra.Elimination.Message` verb message still fires (171-185), so the kill feed will report
  an elimination for a pawn that is not dead. If the feed is wrong for casualties, that message is
  the thing to filter, not the death state.
- The component is a **default subobject** on `ALyraCharacter` (`Character/LyraCharacter.cpp:68`),
  so overriding means a character class change — our own hero pawn — not a runtime component swap.
  `FindHealthComponent` is a `FindComponentByClass` (`LyraHealthComponent.h:52`), so a subclass is
  found by all of Lyra's own call sites; nothing needs to know about it.

**2. An ASC-owned gameplay effect that holds a floor.** Cheapest if "downed" is not required and
all that is needed is a shield window (a medic's protect, a spawn protection). The tag is
`Gameplay.DamageImmunity` (`LyraHealthSet.cpp:16`, checked at 82) and it is an ordinary gameplay
tag, so an effect granted by our own code applies it. But it zeroes damage outright — the pawn
keeps its current health and never reaches 0, so no out-of-health event, no downed pose, nothing
for a casualty system to hang off. Right tool for invulnerability, wrong tool for a casualty.

**3. `Cheat.GodMode` / `Cheat.UnlimitedHealth`.** Recorded here so nobody rediscovers them later
as if they were intended: they are `#if !UE_BUILD_SHIPPING` blocks (`LyraHealthSet.cpp:90` and
`115`), they are debug facilities, they floor health at 1 rather than 0, and they do not compile
into a shipping build. Not a candidate for a shipping mechanic.

**4. Cancelling `GA_Death`. Does not work.** The ability is `ServerInitiated`
(`LyraGameplayAbility_Death.cpp:18`), so a client-side cancel cannot stop the server. Worse, by
the time anything could react, `ActivateAbility` has already run `CancelAbilities` on everything
else (42) and `SetCanBeCanceled(false)` (44). There is no window in which cancelling the death
ability is both possible and useful.

---

## d. How a damage event exposes the hit bone, and why a bot's damage arrives the same way

**The bone is on the `FHitResult` in the effect context, and it is reachable at the moment of
death.** Server-side chain:

1. The weapon ability traces and packages the hit.
   `AbilitySystem/../Weapons/LyraGameplayAbility_RangedWeapon.cpp:579-581` allocates a
   `FLyraGameplayAbilityTargetData_SingleTargetHit` and assigns the traced hit to its `HitResult`
   member. The struct (`AbilitySystem/LyraGameplayAbilityTargetData_SingleTargetHit.h:15`) derives
   from the engine's `FGameplayAbilityTargetData_SingleTargetHit`, whose `HitResult` is a full
   `FHitResult` — so `BoneName` and `MyBoneName` are on it, and `bHitReplaced` / `CartridgeID`
   (26-27) ride along.
2. `OnRangedWeaponTargetDataReady` (line 539) hands the handle to the ability's apply logic.
3. The engine copies the hit into the effect context:
   `FGameplayAbilityTargetData::AddTargetDataToContext`, engine
   `GameplayAbilityTargetTypes.cpp:68-87`, which at 80-82 does
   `if (HasHitResult() && !Context.GetHitResult())` then adds the hit result to the context (81).
4. From there the `FGameplayEffectContextHandle` carries it, and three Lyra sites read it:
   - `ULyraDamageExecution::Execute_Implementation`
     (`AbilitySystem/Executions/LyraDamageExecution.cpp:54`) takes `TypedContext->GetHitResult()`
     and pulls the actor, impact point, impact normal and both trace ends from it (67-75). It uses
     the **actor** for the team check (`CanCauseDamage`, 96) and the **impact point** for distance
     falloff (100-108). It does **not** read the bone — the bone is on the struct and simply
     unused by Lyra.
   - `ULyraHealthSet::PostGameplayEffectExecute` (`LyraHealthSet.cpp:124-125`) takes
     `Data.EffectSpec.GetEffectContext()` for instigator and causer.
   - `ULyraHealthComponent::HandleOutOfHealth` (`LyraHealthComponent.cpp:158-160`) receives the
     whole `FGameplayEffectSpec*` and puts its context on the death event payload
     (`Payload.ContextHandle`, 160).

**The practical consequence for casualty:** capture the bone at `OnOutOfHealth`, not later.
`OnDeathStarted` and `OnDeathFinished` carry only the owning `AActor*`
(`LyraHealthComponent.h:19`, the `FLyraHealth_DeathEvent` signature) — the effect spec is gone by
then. The single place where instigator, causer, magnitude, the damage spec and its context are
all simultaneously in hand is `HandleOutOfHealth` (`LyraHealthComponent.cpp:148`) and
`PostGameplayEffectExecute` (`LyraHealthSet.cpp:176-182`). One of those is where the hit bone has
to be picked up and stored.

**Bots are not a separate path.** `ALyraPlayerBotController` derives from `AModularAIController`
(`Player/LyraPlayerBotController.h:24`); the bots are spawned from the same `ULyraPawnData` hero
pawn as the player (`GameModes/LyraBotCreationComponent.h:33` gives the controller class, and the
pawn data is the shared hero asset), and `ALyraCharacter` creates the `ULyraHealthComponent` as a
default subobject for **every** pawn (`Character/LyraCharacter.cpp:68`). The bot pawn therefore
holds the same ASC, the same `ULyraHealthSet`, the same `LyraHealthComponent` and the same granted
weapon abilities, and its AI activates the same `ULyraGameplayAbility_RangedWeapon`, which runs the
same trace and produces the same target-data item. There is no AI-only damage path to special-case.
The only cosmetic differences on a bot hit are `CartridgeID` and `bHitReplaced`
(`LyraGameplayAbility_RangedWeapon.cpp:512-514`).

---

## e. How interact input reaches a pawn

**An ability, not an input tag, and not a component poll.**

- **There is no `InputTag.Interact` in Lyra 5.8.** The complete set of input tags is
  `InputTag.Move`, `InputTag.Look.Mouse`, `InputTag.Look.Stick`, `InputTag.Crouch`,
  `InputTag.AutoRun` (`LyraGameplayTags.cpp:21-25`). Nothing else exists.
- `ULyraGameplayAbility_Interact` is `ActivationPolicy = OnSpawn`
  (`Interaction/Abilities/LyraGameplayAbility_Interact.cpp:24`), `InstancedPerActor` (25),
  `NetExecutionPolicy = LocalPredicted` (26). **It is already running on every pawn from spawn**,
  holding no input tag, scanning on `InteractionScanRate = 0.1f` and `InteractionScanRange = 500`
  (`Interaction/Abilities/LyraGameplayAbility_Interact.h:48-52`) and publishing its findings into
  `CurrentOptions` (`.h:41`).
- The "press" is `TriggerInteraction()` (`.h:37`, `.cpp:78`), a `BlueprintCallable` on the ability.
  It takes `CurrentOptions[0]` (88), resolves the target with
  `UInteractionStatics::GetActorFromInteractableTarget` (91) and commits the interaction. **No C++
  in the sample calls it** — the only caller is a Blueprint interaction widget, which is not
  shipped as readable source here.
- The extension point for "this downed soldier can be treated" is therefore the same one the
  sample uses for its own interactables: implement `IInteractableTarget`
  (`Interaction/IInteractableTarget.h`) on the casualty and let the already-resident interact
  ability discover it. The candidate is described by `FInteractionOption`
  (`Interaction/InteractionOption.h`) and the scan is in
  `Interaction/Tasks/AbilityTask_WaitForInteractableTargets*.cpp`.

**The input-tag mechanism, for contrast, because it is the natural thing to reach for.**
`ULyraAbilitySystemComponent::AbilityInputTagPressed(InputTag)` and
`AbilityInputTagReleased(InputTag)` (`AbilitySystem/LyraAbilitySystemComponent.cpp:186`, `201`)
walk every activatable spec and match on
`AbilitySpec.GetDynamicSpecSourceTags().HasTagExact(InputTag)` (192, 207), adding the handle to
`InputPressedSpecHandles` / `InputHeldSpecHandles` (194-195). `ProcessAbilityInput` (216) then,
every frame, activates any spec whose policy is `WhileInputActive` and is in the held list
(232-245), and fires `OnInputTriggered` ones on the press. `ClearAbilityInput` is called
unconditionally when the ASC has `Gameplay.AbilityInputBlocked` (218-222) — worth knowing, because
that tag is how Lyra stops input during cutscenes and death.

**What this means for hold-to-treat.** Do not try to route the hold through `InputTag` — there is
no interact tag, and the interact ability is deliberately not a press-driven one. The treat should
be its own ability granted to the pawn with `ActivationPolicy = WhileInputActive`, so
`ProcessAbilityInput` drives it off the held list, with its own scan, its own target and its own
progress — a sibling of `ULyraGameplayAbility_Interact` rather than a bolt-on, because the
existing interact ability is already resident on every pawn and already owns the targeting widgets.
And because the death ability cancels everything not tagged `Ability.Behavior.SurvivesDeath`
(`LyraGameplayAbility_Death.cpp:42`), a treat that has to be usable on a **downed** pawn must be
tagged to survive death; a treat that only runs on a standing pawn does not.

---

## Summary of the hooks

| Need | Hook | Location |
|---|---|---|
| Keep a pawn at zero without dying | `virtual ULyraHealthComponent::StartDeath()` | `LyraHealthComponent.h:81` |
| Hold a health floor | `PreAttributeChange` on a `ULyraHealthSet` subclass | `LyraHealthSet.cpp:192-197` |
| Zero damage entirely (shield) | `Gameplay.DamageImmunity` tag | `LyraHealthSet.cpp:82` |
| The hit bone, with the damage | `FGameplayEffectSpec::GetEffectContext().GetHitResult()->BoneName` | context populated at engine `GameplayAbilityTargetTypes.cpp:80-82`; spec in hand at `LyraHealthComponent.cpp:148` |
| Instigator / causer / magnitude | same spec, same moment | `LyraHealthComponent.cpp:155-163` |
| Everything the pawn can still do while downed | `Ability.Behavior.SurvivesDeath` | `LyraGameplayAbility_Death.cpp:38-39` |
| A held input that drives an ability | `AbilityInputTagPressed/Released` + `WhileInputActive` | `LyraAbilitySystemComponent.cpp:186-245` |
| Make a casualty interactable | `IInteractableTarget` on the casualty | `Interaction/IInteractableTarget.h` |

## Things worth flagging to the producer

- **`Lyra.Elimination.Message` fires on zero health, not on death** (`LyraHealthComponent.cpp:171-185`).
  A kept-alive pawn will still be announced as eliminated. The kill feed needs a casualty rule.
- **A downed pawn has its kit cancelled and its activation group set to blocking** by the death
  ability before our override ever runs (`LyraGameplayAbility_Death.cpp:42`, `46`). The override
  stops the *state*; it does not undo the *ability teardown*.
- **The `Cheat.*` health tags are dev-only** (`#if !UE_BUILD_SHIPPING`, `LyraHealthSet.cpp:90`
  and `115`) and floor health at 1 rather than 0. They are not a casualty mechanism.
- **The `StartDeath` override requires a character class change**, because the component is a
  default subobject at `LyraCharacter.cpp:68`. `FindHealthComponent` finds a subclass unchanged,
  so no Lyra call site needs editing.
- **The hit bone is only in hand at `OnOutOfHealth`.** `OnDeathStarted` carries an `AActor*` and
  nothing else (`LyraHealthComponent.h:19`). Capture earlier or lose it.
