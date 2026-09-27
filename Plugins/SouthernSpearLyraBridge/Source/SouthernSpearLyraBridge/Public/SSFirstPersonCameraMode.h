// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Camera/LyraCameraMode.h"
#include "SSFirstPersonCameraMode.generated.h"

/**
 * First-person camera (Southern Spear is an FPS; Lyra's shooter camera is
 * third-person). The view sits at the character's eyes, following the
 * control rotation. ADS uses the narrower subclass.
 */
UCLASS()
class SSBRIDGE_API USSFirstPersonCameraMode : public ULyraCameraMode
{
	GENERATED_BODY()

public:
	USSFirstPersonCameraMode();

protected:
	virtual void UpdateView(float DeltaTime) override;

	/** Bone the eye position is taken from. */
	UPROPERTY(EditDefaultsOnly, Category = "First Person")
	FName EyeBone = TEXT("head");

	/** Offset from the eye bone, in the control-rotation frame (forward, right, up). */
	UPROPERTY(EditDefaultsOnly, Category = "First Person")
	FVector EyeOffset = FVector(10.f, 0.f, 6.f);

	/** Multiplier on the player's field-of-view preference (aiming narrows it). */
	float FovScale = 1.f;
};

/** Aim-down-sights: same eye position, narrower field of view. */
UCLASS()
class SSBRIDGE_API USSFirstPersonADSCameraMode : public USSFirstPersonCameraMode
{
	GENERATED_BODY()

public:
	USSFirstPersonADSCameraMode();
};
