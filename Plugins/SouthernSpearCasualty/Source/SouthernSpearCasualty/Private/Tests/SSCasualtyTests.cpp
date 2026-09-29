// Copyright Southern Spear. All Rights Reserved.
//
// Casualty rules (ADR-040): zones, the downed state, every treatment row, self-treatment being
// worse, the medic's kit, and no regeneration (IC-11). The checks live in SSCasualtyRuleChecks.h
// so Tools/Casualty/check_casualty_rules.py runs exactly the same ones outside Unreal.

#include "Misc/AutomationTest.h"

#include "SSCasualtyRuleChecks.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSCasualtyRulesTest, "SouthernSpear.Casualty.Rules",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)

bool FSSCasualtyRulesTest::RunTest(const FString& Parameters)
{
	const SSCasualtyChecks::FReport Report = SSCasualtyChecks::RunAll();
	for (const std::string& Failure : Report.Failures)
	{
		AddError(UTF8_TO_TCHAR(Failure.c_str()));
	}
	TestTrue(TEXT("the casualty checks ran"), Report.Checks > 50);
	return Report.Failures.empty();
}

#endif
