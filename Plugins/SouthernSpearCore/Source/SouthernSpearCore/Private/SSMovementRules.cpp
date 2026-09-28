// Copyright Southern Spear. All Rights Reserved.

#include "SSMovementRules.h"

ESSGait FSSMovementRules::ResolveGait(bool bWantsSprint, bool bWantsWalk, ESSStance Stance, bool bAiming,
	const FVector2D& MoveDirLocal, const FSSMovementTuning& Tuning)
{
	// MoveDirLocal: movement direction in the character's frame (X forward, Y right).
	const FVector2D Dir = MoveDirLocal.GetSafeNormal();
	const bool bMostlyForward = !Dir.IsNearlyZero() && Dir.X >= Tuning.SprintForwardDot;
	if (bWantsSprint && Stance == ESSStance::Stand && !bAiming && bMostlyForward)
	{
		return ESSGait::Sprint;
	}
	return bWantsWalk ? ESSGait::Walk : ESSGait::Jog;
}

float FSSMovementRules::MaxSpeed(ESSGait Gait, ESSStance Stance, bool bAiming, const FSSMovementTuning& Tuning)
{
	switch (Stance)
	{
	case ESSStance::Prone:
		return Tuning.ProneSpeed;
	case ESSStance::Crouch:
		return Gait == ESSGait::Walk || bAiming ? Tuning.CrouchWalkSpeed : Tuning.CrouchSpeed;
	default:
		break;
	}
	if (Gait == ESSGait::Sprint)
	{
		return Tuning.SprintSpeed;
	}
	const float Pace = Gait == ESSGait::Walk ? Tuning.WalkSpeed : Tuning.JogSpeed;
	return bAiming ? FMath::Min(Pace, Tuning.AimingSpeed) : Pace;
}
