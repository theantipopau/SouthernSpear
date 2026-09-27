// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "SSKitSelection.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSLoadoutSubsystem.generated.h"

/** One role's kit: Lyra inventory item definitions, first is the primary. */
USTRUCT()
struct FSSKitDefinition
{
	GENERATED_BODY()

	UPROPERTY(Config, EditAnywhere, Category = "Loadout")
	ESSKitRole Role = ESSKitRole::Rifleman;

	/** Special Forces variant (used on maps listed in SpecialForcesMaps). */
	UPROPERTY(Config, EditAnywhere, Category = "Loadout")
	bool bSpecialForces = false;

	UPROPERTY(Config, EditAnywhere, Category = "Loadout", meta = (MetaClass = "/Script/LyraGame.LyraInventoryItemDefinition"))
	TArray<FSoftClassPath> Items;
};

/**
 * Loadouts (ADR-019): per-role kits, standard and Special Forces, granted into
 * Lyra's inventory and quick bar. Data, not code: Config/DefaultGame.ini.
 * Identical for both teams; only cosmetics differ by side (ADR-016).
 */
UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Southern Spear Loadout"))
class SSBRIDGE_API USSLoadoutSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	/** Fallback when no kit matches (and for maps without role kits). */
	UPROPERTY(Config, EditAnywhere, Category = "Loadout", meta = (MetaClass = "/Script/LyraGame.LyraInventoryItemDefinition"))
	TArray<FSoftClassPath> StartingItems;

	UPROPERTY(Config, EditAnywhere, Category = "Loadout")
	TArray<FSSKitDefinition> Kits;

	/** Map asset names (e.g. L_SelatCanal_01) that use the Special Forces kits. */
	UPROPERTY(Config, EditAnywhere, Category = "Loadout")
	TArray<FString> SpecialForcesMaps;

	/** Make the first item the active quick-bar slot. */
	UPROPERTY(Config, EditAnywhere, Category = "Loadout")
	bool bActivateFirstItem = true;

	const FSSKitDefinition* FindKit(ESSKitRole Role, bool bSpecialForces) const;
};

/**
 * Server: on each new pawn, clears the controller's quick bar and grants the
 * kit for its chosen role (USSKitSelection; bots get a random role once).
 * When a player picks a different class while alive, swaps the kit in place.
 */
UCLASS()
class SSBRIDGE_API USSLoadoutSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

private:
	void Grant(AController* Controller);

	TSet<TWeakObjectPtr<APawn>> HandledPawns;
	float Accumulator = 0.f;
};
