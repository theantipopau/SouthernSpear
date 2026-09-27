// Copyright Southern Spear. All Rights Reserved.
//
// Bullet penetration rules (ADR-026, D-09).

#include "Misc/AutomationTest.h"

#include "SSBallistics.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSBallisticsPenetration, "SouthernSpear.Core.Ballistics.Penetration",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSSBallisticsPenetration::RunTest(const FString& Parameters)
{
	const FSSPenetrationTuning T;
	float Thin = 0.f, Thick = 0.f, Wall = 0.f, Bad = 0.f;
	TestTrue(TEXT("sheet metal (0.2 cm) is penetrated"), FSSPenetrationRules::Penetrates(0.2f, T, Thin));
	TestTrue(TEXT("a 20 cm surface is penetrated"), FSSPenetrationRules::Penetrates(20.f, T, Thick));
	TestFalse(TEXT("a 21 cm wall stops the bullet"), FSSPenetrationRules::Penetrates(21.f, T, Wall));
	TestFalse(TEXT("an invalid thickness stops the bullet"), FSSPenetrationRules::Penetrates(-1.f, T, Bad));
	TestTrue(TEXT("thicker loses more damage"), Thick > Thin);
	TestTrue(TEXT("damage lost stays in range"), Thin >= T.MinDamageLost && Thick <= T.MaxDamageLost);
	TestEqual(TEXT("a stopped bullet loses everything"), Wall, 1.f);
	return true;
}

#endif
