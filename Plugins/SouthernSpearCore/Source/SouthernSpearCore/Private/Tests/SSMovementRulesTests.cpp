// Copyright Southern Spear. All Rights Reserved.
//
// Tactical movement rules (ADR-024, LOCOMOTION_AUDIT §4 S1).

#include "Misc/AutomationTest.h"

#include "SSMovementRules.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSMovementGaitRules, "SouthernSpear.Core.Movement.GaitRules",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSSMovementGaitRules::RunTest(const FString& Parameters)
{
	const FSSMovementTuning T;
	const FVector2D Forward(1.f, 0.f), Strafe(0.f, 1.f), ForwardLeft(0.8f, -0.6f), Back(-1.f, 0.f);

	TestEqual(TEXT("default pace is a jog"), FSSMovementRules::ResolveGait(false, false, ESSStance::Stand, false, Forward, T), ESSGait::Jog);
	TestEqual(TEXT("walk when asked"), FSSMovementRules::ResolveGait(false, true, ESSStance::Stand, false, Forward, T), ESSGait::Walk);
	TestEqual(TEXT("sprint forward"), FSSMovementRules::ResolveGait(true, false, ESSStance::Stand, false, Forward, T), ESSGait::Sprint);
	TestEqual(TEXT("sprint at a slight angle"), FSSMovementRules::ResolveGait(true, false, ESSStance::Stand, false, ForwardLeft, T), ESSGait::Sprint);
	TestEqual(TEXT("no sprint sideways"), FSSMovementRules::ResolveGait(true, false, ESSStance::Stand, false, Strafe, T), ESSGait::Jog);
	TestEqual(TEXT("no sprint backwards"), FSSMovementRules::ResolveGait(true, false, ESSStance::Stand, false, Back, T), ESSGait::Jog);
	TestEqual(TEXT("no sprint while aiming"), FSSMovementRules::ResolveGait(true, false, ESSStance::Stand, true, Forward, T), ESSGait::Jog);
	TestEqual(TEXT("no sprint crouched"), FSSMovementRules::ResolveGait(true, false, ESSStance::Crouch, false, Forward, T), ESSGait::Jog);
	TestEqual(TEXT("no sprint standing still"), FSSMovementRules::ResolveGait(true, false, ESSStance::Stand, false, FVector2D::ZeroVector, T), ESSGait::Jog);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSMovementSpeedRules, "SouthernSpear.Core.Movement.SpeedRules",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSSMovementSpeedRules::RunTest(const FString& Parameters)
{
	const FSSMovementTuning T;
	const float Walk = FSSMovementRules::MaxSpeed(ESSGait::Walk, ESSStance::Stand, false, T);
	const float Jog = FSSMovementRules::MaxSpeed(ESSGait::Jog, ESSStance::Stand, false, T);
	const float Sprint = FSSMovementRules::MaxSpeed(ESSGait::Sprint, ESSStance::Stand, false, T);
	TestTrue(TEXT("walk < jog < sprint"), Walk < Jog && Jog < Sprint);
	TestTrue(TEXT("tactical pace: jog under 4 m/s, sprint under 6 m/s"), Jog <= 400.f && Sprint <= 600.f);
	TestTrue(TEXT("aiming caps the pace"), FSSMovementRules::MaxSpeed(ESSGait::Jog, ESSStance::Stand, true, T) <= T.AimingSpeed);
	TestTrue(TEXT("aiming never speeds up a walk"), FSSMovementRules::MaxSpeed(ESSGait::Walk, ESSStance::Stand, true, T) <= Walk);
	TestTrue(TEXT("crouch slower than jog"), FSSMovementRules::MaxSpeed(ESSGait::Jog, ESSStance::Crouch, false, T) < Jog);
	TestTrue(TEXT("crouch walk slower than crouch"), FSSMovementRules::MaxSpeed(ESSGait::Walk, ESSStance::Crouch, false, T)
		< FSSMovementRules::MaxSpeed(ESSGait::Jog, ESSStance::Crouch, false, T));
	TestTrue(TEXT("prone slowest"), FSSMovementRules::MaxSpeed(ESSGait::Jog, ESSStance::Prone, false, T)
		< FSSMovementRules::MaxSpeed(ESSGait::Walk, ESSStance::Crouch, false, T));
	TestTrue(TEXT("acceleration is deliberate (>= 0.35 s to jog pace)"), Jog / T.Acceleration >= 0.35f);
	return true;
}

#endif
