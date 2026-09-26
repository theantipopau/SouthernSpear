// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSFirstPersonSubsystem.generated.h"

class UStaticMeshComponent;

/**
 * Client: puts the local player in first person on any Lyra hero pawn.
 * Wraps the camera component's mode delegate: Lyra's choice is kept only to
 * tell ADS (ability camera modes named *ADS*) from hip, and both map to the
 * Southern Spear first-person modes. Hides the local player's own head and
 * shows the held weapon as a view model only the local player sees (hip and
 * aimed placements, look sway, walk bob). Presentation only; nothing replicates.
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
	void UpdateViewModel(APawn* Pawn, float DeltaTime);

	TWeakObjectPtr<APawn> HandledPawn;

	UPROPERTY(Transient)
	TObjectPtr<UStaticMeshComponent> ViewModel;

	/** Written by the camera-mode wrapper each frame (ADS vs hip). */
	TSharedRef<bool> bAiming = MakeShared<bool>(false);
	float AimAlpha = 0.f;
	FRotator LastControlRotation = FRotator::ZeroRotator;
	FVector SwayOffset = FVector::ZeroVector;
};
