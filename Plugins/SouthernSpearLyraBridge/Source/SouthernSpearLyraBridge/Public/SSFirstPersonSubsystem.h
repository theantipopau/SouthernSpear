// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSFirstPersonSubsystem.generated.h"

class UAnimSequence;
class USkeletalMeshComponent;
class UStaticMeshComponent;

/**
 * Client: puts the local player in first person on any Lyra hero pawn.
 * Wraps the camera component's mode delegate: Lyra's choice is kept only to
 * tell ADS (ability camera modes named *ADS*) from hip, and both map to the
 * Southern Spear first-person modes. Hides the local player's own head.
 *
 * View model (owner-only): first-person arms from the Fab FPS animation pack,
 * aligned so their head bone sits at the camera, playing idle / walk / run /
 * aim loops by movement, fire when the magazine count drops and reload when
 * the body's Lyra reload montage starts. The held weapon's static mesh rides
 * on the arms' ik_hand_gun bone; the body copy is hidden from the owner. Falls
 * back to a camera-attached weapon when the pack is missing. Presentation
 * only; nothing replicates.
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
	void UpdateArmsAnimation(APawn* Pawn, float DeltaTime);
	void Play(UAnimSequence* Sequence, bool bLoop);

	TWeakObjectPtr<APawn> HandledPawn;
	TWeakObjectPtr<class ACameraActor> FollowCamera; // ss.Debug.FollowBot

	UPROPERTY(Transient) TObjectPtr<USkeletalMeshComponent> Arms;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> ViewModel;
	UPROPERTY(Transient) TObjectPtr<UAnimSequence> Current;

	/** Written by the camera-mode wrapper each frame (ADS vs hip). */
	TSharedRef<bool> bAiming = MakeShared<bool>(false);
	float AimAlpha = 0.f;
	float OneShotRemaining = 0.f;
	float Recoil = 0.f;
	float ReloadAlpha = 0.f;
	int32 LastMagazine = -1;
	bool bReloadSeen = false;
	FRotator LastControlRotation = FRotator::ZeroRotator;
	FVector SwayOffset = FVector::ZeroVector;
};
