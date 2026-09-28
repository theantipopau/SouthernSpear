// Copyright Southern Spear. All Rights Reserved.
//
// Muzzle light (W3): the flash starts at its peak, falls off sharply and is gone at its duration; a pistol
// flash is dimmer and shorter than a rifle's, a 7.62x51 flash brighter and wider.

#include "Misc/AutomationTest.h"

#include "SSMuzzleLightSubsystem.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSMuzzleLightTest, "SouthernSpear.Bridge.MuzzleLight.Rules",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSSMuzzleLightTest::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("peak at the shot"), FSSMuzzleLightRules::Intensity(2000.f, 0.f, 0.05f), 2000.f);
	TestEqual(TEXT("a quarter at half time (quadratic fall)"), FSSMuzzleLightRules::Intensity(2000.f, 0.025f, 0.05f), 500.f, 0.01f);
	TestEqual(TEXT("dark at its duration"), FSSMuzzleLightRules::Intensity(2000.f, 0.05f, 0.05f), 0.f);
	TestEqual(TEXT("dark after it"), FSSMuzzleLightRules::Intensity(2000.f, 0.2f, 0.05f), 0.f);
	TestEqual(TEXT("no light for a zero duration"), FSSMuzzleLightRules::Intensity(2000.f, 0.f, 0.f), 0.f);
	TestTrue(TEXT("falls monotonically"),
		FSSMuzzleLightRules::Intensity(2000.f, 0.01f, 0.05f) > FSSMuzzleLightRules::Intensity(2000.f, 0.02f, 0.05f));

	const FSSMuzzleLightSpec Rifle = FSSMuzzleLightRules::SpecFor(TEXT("A88"));
	const FSSMuzzleLightSpec Pistol = FSSMuzzleLightRules::SpecFor(TEXT("A9"));
	const FSSMuzzleLightSpec Marksman = FSSMuzzleLightRules::SpecFor(TEXT("A25"));
	TestTrue(TEXT("pistol dimmer, smaller and shorter than a rifle"),
		Pistol.Candela < Rifle.Candela && Pistol.RadiusCm < Rifle.RadiusCm && Pistol.Seconds < Rifle.Seconds);
	TestTrue(TEXT("7.62x51 brighter and wider than 5.56"), Marksman.Candela > Rifle.Candela && Marksman.RadiusCm > Rifle.RadiusCm);
	TestTrue(TEXT("every flash is shorter than a frame at 20 fps"), Marksman.Seconds < 0.06f && Rifle.Seconds < 0.06f);
	return true;
}

#endif
