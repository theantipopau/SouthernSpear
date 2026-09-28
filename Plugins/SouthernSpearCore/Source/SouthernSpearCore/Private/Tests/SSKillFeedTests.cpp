// Copyright Southern Spear. All Rights Reserved.
//
// Kill feed rules (FSSKillFeedRules): trimming, lifetime, the local "you killed" pick, weapon names.

#include "Misc/AutomationTest.h"

#include "SSKillFeedState.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	FSSKillFeedEntry Entry(const TCHAR* Killer, double Time, bool bLocalKiller = false, bool bLocalVictim = false)
	{
		FSSKillFeedEntry E;
		E.Killer = Killer;
		E.Victim = TEXT("V");
		E.Time = Time;
		E.bLocalKiller = bLocalKiller;
		E.bLocalVictim = bLocalVictim;
		return E;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSKillFeedRulesTest, "SouthernSpear.Core.Hud.KillFeed",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSSKillFeedRulesTest::RunTest(const FString& Parameters)
{
	TArray<FSSKillFeedEntry> Entries;
	for (int32 Index = 0; Index < FSSKillFeedRules::MaxEntries + 3; ++Index)
	{
		FSSKillFeedRules::Add(Entries, Entry(*FString::FromInt(Index), Index));
	}
	TestEqual(TEXT("trimmed to MaxEntries"), Entries.Num(), FSSKillFeedRules::MaxEntries);
	TestEqual(TEXT("oldest dropped"), Entries[0].Killer, FString(TEXT("3")));

	const double Now = Entries.Last().Time + 1.0;
	TArray<FSSKillFeedEntry> Shown = FSSKillFeedRules::Visible(Entries, Now);
	TestEqual(TEXT("newest first"), Shown[0].Killer, Entries.Last().Killer);
	TestEqual(TEXT("expired hidden"), FSSKillFeedRules::Visible(Entries, Now + 100.0).Num(), 0);

	TArray<FSSKillFeedEntry> Local;
	FSSKillFeedRules::Add(Local, Entry(TEXT("Me"), 10.0, true));
	FSSKillFeedRules::Add(Local, Entry(TEXT("Other"), 11.0));
	const FSSKillFeedEntry* Recent = FSSKillFeedRules::RecentLocalKill(Local, 12.0);
	TestTrue(TEXT("local kill found"), Recent && Recent->Killer == TEXT("Me"));
	TestNull(TEXT("local kill expires"), FSSKillFeedRules::RecentLocalKill(Local, 10.0 + FSSKillFeedRules::LocalKillLifetime + 0.1));
	TArray<FSSKillFeedEntry> Suicide;
	FSSKillFeedRules::Add(Suicide, Entry(TEXT("Me"), 10.0, true, true));
	TestNull(TEXT("self-elimination is not a kill"), FSSKillFeedRules::RecentLocalKill(Suicide, 10.5));
	TestTrue(TEXT("self-elimination is a local death"), FSSKillFeedRules::RecentLocalDeath(Suicide, 10.5) != nullptr);

	TArray<FSSKillFeedEntry> Died;
	FSSKillFeedRules::Add(Died, Entry(TEXT("Them"), 20.0, false, true));
	FSSKillFeedRules::Add(Died, Entry(TEXT("Other"), 21.0));
	const FSSKillFeedEntry* Death = FSSKillFeedRules::RecentLocalDeath(Died, 22.0);
	TestTrue(TEXT("local death found behind newer entries"), Death && Death->Killer == TEXT("Them"));
	TestNull(TEXT("local death expires"), FSSKillFeedRules::RecentLocalDeath(Died, 20.0 + FSSKillFeedRules::LocalDeathLifetime + 0.1));
	TestNull(TEXT("no local death"), FSSKillFeedRules::RecentLocalDeath(Local, 12.0));

	TestEqual(TEXT("weapon name"), FSSKillFeedRules::WeaponShortName(TEXT("ID_SS_A88_C")), FString(TEXT("A88")));
	TestEqual(TEXT("weapon name, other"), FSSKillFeedRules::WeaponShortName(TEXT("ID_Rifle")), FString(TEXT("ID_Rifle")));
	return true;
}

#endif
