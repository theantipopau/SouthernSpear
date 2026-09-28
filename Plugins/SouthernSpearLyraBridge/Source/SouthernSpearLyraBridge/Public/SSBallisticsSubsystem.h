// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/EngineSubsystem.h"
#include "SSBallisticsSubsystem.generated.h"

/**
 * Bullet penetration (ADR-026, D-09): registers the Lyra ranged-weapon hook. The hook measures the
 * blocking surface's thickness along the shot (a reverse trace against that component only) and
 * applies FSSPenetrationRules (Core). Landscape and characters are never penetrated.
 */
UCLASS()
class SSBRIDGE_API USSBallisticsSubsystem : public UEngineSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;
};
