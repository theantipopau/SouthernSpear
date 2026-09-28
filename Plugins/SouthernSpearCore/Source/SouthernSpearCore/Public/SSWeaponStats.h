// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "SSWeaponStats.generated.h"

/**
 * One weapon's gameplay numbers (W1, Docs/WEAPONS_ANIMATION_PLAN.md), seeded from the source configs
 * (Docs/WEAPON_SOURCE_DATA.md). A weapon and its MAF counterpart share one row: only cosmetics differ.
 */
USTRUCT(BlueprintType)
struct FSSWeaponStats
{
	GENERATED_BODY()

	/** The A-series name, matched against the item definition (ID_SS_<Weapon>). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Weapon")
	FName Weapon;

	/** Cyclic rate. Applied once the fire ability exposes its interval (Tools/Unreal/probe_weapon_fire.py). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Weapon", meta = (ClampMin = "1"))
	int32 RoundsPerMinute = 600;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Weapon", meta = (ClampMin = "1"))
	int32 MagazineSize = 30;

	/** Full magazines carried besides the loaded one. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Weapon", meta = (ClampMin = "0"))
	int32 SpareMagazines = 4;

	/**
	 * Multiplier on the weapon's Lyra spread curve: the source dispersion relative to the service rifle
	 * (A88, 2.0 MOA). Pistols are relative to Lyra's pistol. 1 = unchanged.
	 */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Weapon", meta = (ClampMin = "0.1", ClampMax = "10.0"))
	float SpreadScale = 1.f;

	/** False for semi-automatic only (marksman rifle, pistol). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Weapon")
	bool bFullAuto = true;
};

/** The weapon table. Data, not code: Config/DefaultGame.ini [/Script/SouthernSpearCore.SSWeaponStatsSettings]. */
UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Southern Spear Weapon Stats"))
class SSCORE_API USSWeaponStatsSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Weapons")
	TArray<FSSWeaponStats> Weapons;
};

/** Pure weapon-table rules. */
struct SSCORE_API FSSWeaponStatsRules
{
	/** "ID_SS_A88_C" or "ID_SS_A88" -> "A88"; NAME_None for anything else. */
	static FName WeaponFromItemDefinition(const FString& ClassName);

	static const FSSWeaponStats* Find(FName Weapon, TConstArrayView<FSSWeaponStats> Table);

	/** The configured row for Weapon, or nullptr. */
	static const FSSWeaponStats* Find(FName Weapon);

	/** Seconds between shots at the cyclic rate. */
	static float FireIntervalSeconds(const FSSWeaponStats& Stats);

	/** Spare rounds carried: SpareMagazines full magazines. */
	static int32 SpareRounds(const FSSWeaponStats& Stats) { return FMath::Max(0, Stats.SpareMagazines) * FMath::Max(1, Stats.MagazineSize); }

	/** A usable table: names set and unique, rates 60..1500 rpm, magazines 1..300, spread scale 0.1..10. */
	static bool Validate(TConstArrayView<FSSWeaponStats> Table, TArray<FString>& OutErrors);
};
