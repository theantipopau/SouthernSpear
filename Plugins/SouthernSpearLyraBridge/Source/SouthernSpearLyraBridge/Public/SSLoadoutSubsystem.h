// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSLoadoutSubsystem.generated.h"

/**
 * Starting loadout granted to every pawn, in order, into Lyra's inventory and
 * quick bar (ADR-019). Data, not code: set in Config/DefaultGame.ini.
 * Identical for both teams; only cosmetics differ by side (ADR-016).
 */
UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Southern Spear Loadout"))
class SSBRIDGE_API USSLoadoutSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	/** Lyra inventory item definitions (Blueprint classes), e.g. ID_SS_A88. */
	UPROPERTY(Config, EditAnywhere, Category = "Loadout", meta = (MetaClass = "/Script/LyraGame.LyraInventoryItemDefinition"))
	TArray<FSoftClassPath> StartingItems;

	/** Make the first starting item the active quick-bar slot. */
	UPROPERTY(Config, EditAnywhere, Category = "Loadout")
	bool bActivateFirstItem = true;
};

/** Server: grants USSLoadoutSettings::StartingItems to each new pawn's controller. */
UCLASS()
class SSBRIDGE_API USSLoadoutSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

private:
	void Grant(AController* Controller);

	TSet<TWeakObjectPtr<APawn>> HandledPawns;
	float Accumulator = 0.f;
};
