// Copyright Southern Spear. All Rights Reserved.
//
// HUD hit direction bearing (USSLocalHudState::HitBearing).

#include "Misc/AutomationTest.h"

#include "SSLocalHudState.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSHudHitBearing, "SouthernSpear.Core.Hud.HitBearing",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSSHudHitBearing::RunTest(const FString& Parameters)
{
	const FVector Cam(100.f, 200.f, 50.f);
	// Camera facing +X (yaw 0): +Y is to the right in Unreal.
	TestTrue(TEXT("ahead"), FMath::IsNearlyEqual(USSLocalHudState::HitBearing(Cam, 0.f, Cam + FVector(1000.f, 0.f, 0.f)), 0.f, 0.1f));
	TestTrue(TEXT("right"), FMath::IsNearlyEqual(USSLocalHudState::HitBearing(Cam, 0.f, Cam + FVector(0.f, 1000.f, 0.f)), 90.f, 0.1f));
	TestTrue(TEXT("left"), FMath::IsNearlyEqual(USSLocalHudState::HitBearing(Cam, 0.f, Cam + FVector(0.f, -1000.f, 0.f)), -90.f, 0.1f));
	TestTrue(TEXT("behind"), FMath::IsNearlyEqual(FMath::Abs(USSLocalHudState::HitBearing(Cam, 0.f, Cam + FVector(-1000.f, 0.f, 0.f))), 180.f, 0.1f));
	// Camera turned to face +Y (yaw 90): a source at +Y is ahead, one at +X is to the left.
	TestTrue(TEXT("turned: ahead"), FMath::IsNearlyEqual(USSLocalHudState::HitBearing(Cam, 90.f, Cam + FVector(0.f, 1000.f, 0.f)), 0.f, 0.1f));
	TestTrue(TEXT("turned: left"), FMath::IsNearlyEqual(USSLocalHudState::HitBearing(Cam, 90.f, Cam + FVector(1000.f, 0.f, 0.f)), -90.f, 0.1f));
	TestTrue(TEXT("height ignored"), FMath::IsNearlyEqual(USSLocalHudState::HitBearing(Cam, 0.f, Cam + FVector(1000.f, 0.f, 800.f)), 0.f, 0.1f));
	return true;
}

#endif
