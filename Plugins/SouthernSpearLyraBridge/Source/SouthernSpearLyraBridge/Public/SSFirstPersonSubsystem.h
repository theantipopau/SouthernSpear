// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSFirstPersonSubsystem.generated.h"

/**
 * Client: puts the local player in first person on any Lyra hero pawn.
 * Wraps the camera component's mode delegate: Lyra's choice is kept only to
 * tell ADS (ability camera modes named *ADS*) from hip, and both map to the
 * Southern Spear first-person modes. Hides the local player's own head.
 * Presentation only; nothing replicates.
 */
UCLASS()
class SSBRIDGE_API USSFirstPersonSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

private:
	TWeakObjectPtr<APawn> HandledPawn;
};
