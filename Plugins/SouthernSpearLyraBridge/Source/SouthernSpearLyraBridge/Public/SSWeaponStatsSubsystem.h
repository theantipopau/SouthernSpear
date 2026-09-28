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
 *
 * Each instance is adjusted once. RoundsPerMinute is in the table but not applied yet: Lyra keeps the fire
 * interval in its fire-ability Blueprint (Tools/Unreal/probe_weapon_fire.py finds it).
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

	TSet<TWeakObjectPtr<UObject>> DoneItems;
	TSet<TWeakObjectPtr<UObject>> DoneInstances;
	float Accumulator = 0.f;
	bool bWarnedSpread = false;
};
