// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSKitSelection.generated.h"

class AController;

/** Soldier roles offered on the class selection screen. */
UENUM(BlueprintType)
enum class ESSKitRole : uint8
{
	Rifleman,
	Medic,
	MachineGunner,
	Sniper,
	Grenadier,
};

/**
 * Which kit each controller wants, and whether this map is a Special Forces map.
 * The class selection screen (SouthernSpearUI) writes requests; the Lyra bridge
 * grants the kit on spawn and respawns a player whose choice changed. Kits are
 * identical for both teams (ADR-016). Standalone and listen-server hosts only:
 * remote clients need a replicated request path (R-22).
 */
UCLASS()
class SSCORE_API USSKitSelection : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	void RequestKit(AController* Controller, ESSKitRole Role);

	/** The controller's chosen role, if it has chosen. */
	bool GetKit(const AController* Controller, ESSKitRole& OutRole) const;

	/** True once after a request, for the bridge to apply it. */
	bool ConsumeChange(const AController* Controller);

	/** Set by the bridge from its settings (maps listed as Special Forces). */
	bool bSpecialForcesMap = false;

	static constexpr int32 NumRoles = 5;

private:
	TMap<TWeakObjectPtr<const AController>, ESSKitRole> Choices;
	TSet<TWeakObjectPtr<const AController>> Pending;
};
