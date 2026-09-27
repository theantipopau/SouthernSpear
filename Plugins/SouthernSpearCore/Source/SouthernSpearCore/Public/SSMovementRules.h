// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "SSMovementRules.generated.h"

/** How fast the soldier is trying to move (ADR-024). Jog is the default pace. */
UENUM(BlueprintType)
enum class ESSGait : uint8
{
	Walk,    // careful movement (hold Walk)
	Jog,     // default
	Sprint,  // hold Sprint, forward only, standing, not aiming
};

/** Body height (ADR-024). Prone is ruled here but has no animation yet (LOCOMOTION_AUDIT §5). */
UENUM(BlueprintType)
enum class ESSStance : uint8
{
	Stand,
	Crouch,
	Prone,
};

/**
 * Tactical movement tuning, centimetres and seconds. The target is weight and
 * deliberate pace: Ground Branch / America's Army 2, not arcade acceleration
 * or momentum-free stops (LOCOMOTION_AUDIT §1.1, §6).
 */
USTRUCT(BlueprintType)
struct SSCORE_API FSSMovementTuning
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Speed") float WalkSpeed = 160.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Speed") float JogSpeed = 360.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Speed") float SprintSpeed = 520.f;
	/** Aiming down sights caps the pace at a tactical walk. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Speed") float AimingSpeed = 220.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Speed") float CrouchWalkSpeed = 110.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Speed") float CrouchSpeed = 170.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Speed") float ProneSpeed = 70.f;

	/** Reaching jog pace takes ~0.4 s; stopping from it ~0.5 s (weight, momentum). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Feel") float Acceleration = 900.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Feel") float BrakingDeceleration = 720.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Feel") float GroundFriction = 5.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Feel") float AirControl = 0.08f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Feel") float JumpZVelocity = 380.f;

	/** Sprint needs the movement mostly forward: cos of the widest allowed angle (~40°). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Rules") float SprintForwardDot = 0.77f;
};

/** Pure movement rules (no engine state), shared by the movement component and tests. */
struct SSCORE_API FSSMovementRules
{
	/** The gait actually used, given what the player asks for and the situation. */
	static ESSGait ResolveGait(bool bWantsSprint, bool bWantsWalk, ESSStance Stance, bool bAiming,
		const FVector2D& MoveDirLocal, const FSSMovementTuning& Tuning);

	/** Top speed for a gait and stance, cm/s. */
	static float MaxSpeed(ESSGait Gait, ESSStance Stance, bool bAiming, const FSSMovementTuning& Tuning);
};
