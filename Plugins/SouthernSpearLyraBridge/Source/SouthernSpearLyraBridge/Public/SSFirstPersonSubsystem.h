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
 * View model (owner-only, producer 2026-09-28 "arms view model"): gloved first-person arms from the
 * Fab M4 FPS pack (Tools/Unreal/setup_fp_arms.py), their FPS_Camera_j bone on the camera. Draw on a
 * weapon change, fire when the magazine count drops, reload (time-scaled to the body's Lyra reload
 * montage, the gameplay authority) when that montage starts; idle, walk bob, look sway and a lowered
 * sprint pose are procedural. The held A-series weapon's static mesh rides on the arms' weapon bone
 * (Main_j) at a grip transform measured from the idle pose (right hand on the grip, barrel toward the
 * left hand); the body copy is hidden from the owner. Falls back to a camera-held weapon when the
 * arms are missing. Presentation only; nothing replicates.
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

	/** Where the local player's shots visibly leave: the view model's Muzzle socket, or, looking through a
	 * magnified scope (view model hidden), a point just ahead of the eye. False when there is no view model. */
	bool GetViewModelMuzzle(FVector& OutLocation) const;

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
	/** Weapon relative to the arms' weapon bone, measured once from the idle pose (see .cpp). */
	FTransform GripOnWeaponBone = FTransform::Identity;
	bool bGripMeasured = false;
	/** Arms set in use: 0 rifle (Fab M4 pack), 1 pistol (Fab G17 pack; every pistol until it has its own). */
	int32 ArmsSet = 0;
	float SprintAlpha = 0.f;
	float BobPhase = 0.f;
	TWeakObjectPtr<class UStaticMesh> LastHeld;
	float Recoil = 0.f;
	float ReloadAlpha = 0.f;
	int32 LastMagazine = -1;
	bool bReloadSeen = false;
	FRotator LastControlRotation = FRotator::ZeroRotator;
	FVector SwayOffset = FVector::ZeroVector;
};
