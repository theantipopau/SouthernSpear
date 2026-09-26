// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSHudStateSubsystem.generated.h"

/**
 * Client: copies the local player's health, ammunition and held weapon name
 * from Lyra into USSLocalHudState (SouthernSpearCore) each frame, for the
 * Southern Spear HUD. Read-only toward Lyra; presentation only.
 */
UCLASS()
class SSBRIDGE_API USSHudStateSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
};
