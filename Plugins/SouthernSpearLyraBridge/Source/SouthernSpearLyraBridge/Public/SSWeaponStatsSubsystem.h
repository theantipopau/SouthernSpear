// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSWeaponStatsSubsystem.generated.h"

/**
 * Applies the per-weapon table (Core USSWeaponStatsSettings, W1) to Lyra's weapons as they appear, so the
 * A-series stop being one shared rifle. Lyra is not modified: its types are reached by reflection.
 *
 * - Server: each new ID_SS_* item instance gets its magazine size, a full magazine and its spare rounds
 *   (Lyra.ShooterGame.Weapon.* stat tags, which replicate).
 * - Every machine: each new ranged weapon instance has its spread curve scaled by the row's SpreadScale,
 *   because Lyra computes spread where the shot is traced.
 * - Every machine: each weapon's own fire-ability instance (the ability spec's SourceObject is the weapon
 *   instance, LyraAbilitySet.cpp) gets FireDelayTimeSecs = 60 / RoundsPerMinute. The variable is the one
 *   Tools/Unreal/probe_weapon_fire.py found on Lyra's fire ability Blueprint.
 *
 * Each instance is adjusted once. Semi-automatic (bFullAuto = false) is not enforced yet: Lyra's rifle fire
 * ability repeats while held, and semi-auto needs a different ability (the pistol's) granted by the item.
 */
UCLASS()
class SSBRIDGE_API USSWeaponStatsSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

private:
	void ApplyAmmo(UWorld* World);
	void ApplySpread(UWorld* World);
	void ApplyFireRate(UWorld* World);

	TSet<TWeakObjectPtr<UObject>> DoneItems;
	TSet<TWeakObjectPtr<UObject>> DoneInstances;
	TSet<TWeakObjectPtr<UObject>> DoneAbilities;
	float Accumulator = 0.f;
	bool bWarnedSpread = false;
};
