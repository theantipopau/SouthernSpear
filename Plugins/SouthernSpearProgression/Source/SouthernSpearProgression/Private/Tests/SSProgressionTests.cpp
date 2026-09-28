// Copyright Southern Spear. All Rights Reserved.
//
// Progression tests (ADR-032): the shipped rank and award tables, caps,
// record updates, schema migration and the dev persistence round trip.

#include "HAL/FileManager.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Guid.h"
#include "Misc/Paths.h"
#include "SSPersistence.h"
#include "SSProgressionRules.h"
#include "SSProgressionSettings.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	constexpr EAutomationTestFlags SSProgressionTestFlags =
		EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter;

	FSSXpAwardRule Rule(ESSServiceEvent Event, int32 Award, int32 Cap)
	{
		FSSXpAwardRule R;
		R.Event = Event;
		R.Award = Award;
		R.MaxPerMatch = Cap;
		return R;
	}

	/** A scratch directory under Saved/Automation, removed by the destructor. */
	struct FScratchDir
	{
		FString Path;
		FScratchDir()
		{
			Path = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Automation"), TEXT("SSProgression"), FGuid::NewGuid().ToString());
			IFileManager::Get().MakeDirectory(*Path, true);
		}
		~FScratchDir() { IFileManager::Get().DeleteDirectory(*Path, false, true); }
	};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSProgShippedTables, "SouthernSpear.Progression.ShippedTablesAreValid", SSProgressionTestFlags)
bool FSSProgShippedTables::RunTest(const FString& Parameters)
{
	// The tables in Config/DefaultGame.ini, exactly as the game loads them.
	const USSProgressionSettings* Settings = GetDefault<USSProgressionSettings>();
	TArray<FString> Errors;
	TestTrue(TEXT("award table valid"), FSSProgressionRules::ValidateAwards(Settings->Awards, Errors));
	for (const FString& Error : Errors)
	{
		AddError(Error);
	}
	TestTrue(TEXT("awards configured"), Settings->Awards.Num() > 0);

	// TDD 6.2: a test asserts that no award rule is uncapped.
	for (const FSSXpAwardRule& R : Settings->Awards)
	{
		if (R.Award > 0)
		{
			TestTrue(*FString::Printf(TEXT("%s is capped"), USSServiceEventSubsystem::LexEvent(R.Event)), R.MaxPerMatch >= 1);
		}
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSProgKillAwards, "SouthernSpear.Progression.KillAwards", SSProgressionTestFlags)
bool FSSProgKillAwards::RunTest(const FString& Parameters)
{
	// ADR-033: kills of the other side earn XP, capped per match, and a captured
	// objective is still worth more than a kill. A friendly kill never earns.
	const TArray<FSSXpAwardRule>& Awards = GetDefault<USSProgressionSettings>()->Awards;
	const FSSXpAwardRule* Kill = FSSProgressionRules::FindRule(ESSServiceEvent::EnemyKill, Awards);
	const FSSXpAwardRule* Objective = FSSProgressionRules::FindRule(ESSServiceEvent::ObjectiveCaptured, Awards);
	if (!TestNotNull(TEXT("kill award configured"), Kill) || !TestNotNull(TEXT("objective award configured"), Objective))
	{
		return false;
	}
	TestTrue(TEXT("a kill earns XP"), Kill->Award > 0);
	TestTrue(TEXT("kills are capped per match"), Kill->MaxPerMatch >= 1);
	TestTrue(TEXT("an objective is worth more than a kill"), Objective->Award > Kill->Award);
	const FSSXpAwardRule* FriendlyKill = FSSProgressionRules::FindRule(ESSServiceEvent::FriendlyKill, Awards);
	TestTrue(TEXT("a friendly kill never earns XP"), !FriendlyKill || FriendlyKill->Award < 0);

	FSSMatchTally Tally;
	int32 Earned = 0;
	for (int32 Index = 0; Index < Kill->MaxPerMatch + 25; ++Index)
	{
		Earned += FSSProgressionRules::GrantAward(Tally, ESSServiceEvent::EnemyKill, Awards);
	}
	TestEqual(TEXT("farming stops at the cap"), Earned, Kill->Award * Kill->MaxPerMatch);

	FSSServiceRecord Record;
	FSSProgressionRules::ApplyAward(Record, ESSServiceEvent::EnemyKill, Kill->Award);
	TestEqual(TEXT("kill statistic"), Record.Statistics.EnemyKills, 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSProgValidation, "SouthernSpear.Progression.ValidationCatchesBadTables", SSProgressionTestFlags)
bool FSSProgValidation::RunTest(const FString& Parameters)
{
	TArray<FString> E;
	TestFalse(TEXT("uncapped reward"), FSSProgressionRules::ValidateAwards({ Rule(ESSServiceEvent::RoundWon, 50, 0) }, E));
	E.Reset();
	TestFalse(TEXT("absurd cap"), FSSProgressionRules::ValidateAwards({ Rule(ESSServiceEvent::RoundWon, 50, 100000) }, E));
	E.Reset();
	TestFalse(TEXT("duplicate event"), FSSProgressionRules::ValidateAwards({ Rule(ESSServiceEvent::RoundWon, 50, 1), Rule(ESSServiceEvent::RoundWon, 5, 1) }, E));
	E.Reset();
	TestFalse(TEXT("None event"), FSSProgressionRules::ValidateAwards({ Rule(ESSServiceEvent::None, 5, 1) }, E));
	E.Reset();
	TestTrue(TEXT("uncapped penalty is fine"), FSSProgressionRules::ValidateAwards({ Rule(ESSServiceEvent::FriendlyKill, -100, 0) }, E));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSProgCaps, "SouthernSpear.Progression.Caps", SSProgressionTestFlags)
bool FSSProgCaps::RunTest(const FString& Parameters)
{
	const TArray<FSSXpAwardRule> Awards = { Rule(ESSServiceEvent::RoundWon, 50, 2), Rule(ESSServiceEvent::FriendlyKill, -30, 0) };
	FSSMatchTally Tally;
	TestEqual(TEXT("first win"), FSSProgressionRules::GrantAward(Tally, ESSServiceEvent::RoundWon, Awards), 50);
	TestEqual(TEXT("second win"), FSSProgressionRules::GrantAward(Tally, ESSServiceEvent::RoundWon, Awards), 50);
	TestEqual(TEXT("third win: capped"), FSSProgressionRules::GrantAward(Tally, ESSServiceEvent::RoundWon, Awards), 0);
	TestEqual(TEXT("no rule: nothing"), FSSProgressionRules::GrantAward(Tally, ESSServiceEvent::MatchWon, Awards), 0);
	for (int32 Index = 0; Index < 20; ++Index)
	{
		TestEqual(TEXT("a penalty always applies"), FSSProgressionRules::GrantAward(Tally, ESSServiceEvent::FriendlyKill, Awards), -30);
	}
	FSSMatchTally NextMatch;
	TestEqual(TEXT("a new match has a fresh cap"), FSSProgressionRules::GrantAward(NextMatch, ESSServiceEvent::RoundWon, Awards), 50);

	FSSServiceRecord Record;
	FSSProgressionRules::ApplyAward(Record, ESSServiceEvent::RoundWon, 50);
	FSSProgressionRules::ApplyAward(Record, ESSServiceEvent::RoundWon, 0);
	TestEqual(TEXT("XP added"), Record.ServiceXp, 50);
	TestEqual(TEXT("a capped event still counts as a statistic"), Record.Statistics.RoundsWon, 2);
	FSSProgressionRules::ApplyAward(Record, ESSServiceEvent::FriendlyKill, -500);
	TestEqual(TEXT("XP never below zero"), Record.ServiceXp, 0);
	TestEqual(TEXT("friendly kill recorded"), Record.Statistics.FriendlyKills, 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSProgIdsAndCallsigns, "SouthernSpear.Progression.IdsAndCallsigns", SSProgressionTestFlags)
bool FSSProgIdsAndCallsigns::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("path characters removed"), FSSProgressionRules::SanitisePlayerId(TEXT("../../etc/pass wd")), FString(TEXT("etcpasswd")));
	TestTrue(TEXT("nothing usable"), FSSProgressionRules::SanitisePlayerId(TEXT("/.\\:")).IsEmpty());
	TestEqual(TEXT("length capped"), FSSProgressionRules::SanitisePlayerId(FString::ChrN(100, TEXT('a'))).Len(), 64);

	TestTrue(TEXT("plain callsign"), FSSProgressionRules::IsValidCallsign(TEXT("Dingo 2-1")));
	TestFalse(TEXT("too short"), FSSProgressionRules::IsValidCallsign(TEXT("A")));
	TestFalse(TEXT("too long"), FSSProgressionRules::IsValidCallsign(TEXT("ABCDEFGHIJKLMNOPQ")));
	TestFalse(TEXT("markup refused"), FSSProgressionRules::IsValidCallsign(TEXT("<b>x</b>")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSProgPersistence, "SouthernSpear.Progression.PersistenceRoundTrip", SSProgressionTestFlags)
bool FSSProgPersistence::RunTest(const FString& Parameters)
{
	FScratchDir Dir;
	FSSLocalDevPersistence Store(Dir.Path);
	TestFalse(TEXT("the dev store is never authoritative"), Store.IsAuthoritative());

	FSSServiceRecord Out;
	FString Error;
	TestEqual(TEXT("missing record"), Store.LoadServiceRecord(TEXT("p1"), Out, Error), ESSRecordLoad::NotFound);

	FSSServiceRecord In;
	In.PlayerId = TEXT("p1");
	In.Callsign = TEXT("Dingo");
	In.ServiceXp = 1234;
	In.Statistics.RoundsWon = 7;
	In.Qualifications = { FName(TEXT("Induction")) };
	TestTrue(TEXT("saved"), Store.SaveServiceRecord(In, Error));
	TestFalse(TEXT("no temporary file left"), IFileManager::Get().FileExists(*(Store.PathFor(TEXT("p1")) + TEXT(".tmp"))));

	TestEqual(TEXT("loaded"), Store.LoadServiceRecord(TEXT("p1"), Out, Error), ESSRecordLoad::Loaded);
	TestEqual(TEXT("XP survives"), Out.ServiceXp, 1234);
	TestEqual(TEXT("callsign survives"), Out.Callsign, FString(TEXT("Dingo")));
	TestEqual(TEXT("statistics survive"), Out.Statistics.RoundsWon, 7);
	TestEqual(TEXT("qualifications survive"), Out.Qualifications.Num(), 1);
	TestEqual(TEXT("schema version"), Out.SchemaVersion, FSSServiceRecord::CurrentSchemaVersion);

	// A record from a newer build is refused and left exactly as it was.
	const FString Path = Store.PathFor(TEXT("p1"));
	const FString Newer = FString::Printf(TEXT("{\"schemaVersion\": %d, \"serviceXp\": 99999}"), FSSServiceRecord::CurrentSchemaVersion + 1);
	FFileHelper::SaveStringToFile(Newer, *Path);
	TestEqual(TEXT("newer schema refused"), Store.LoadServiceRecord(TEXT("p1"), Out, Error), ESSRecordLoad::FromNewerVersion);
	FString After;
	FFileHelper::LoadFileToString(After, *Path);
	TestEqual(TEXT("newer record untouched"), After, Newer);

	// Garbage is unreadable, and quarantine moves it aside rather than deleting it.
	FFileHelper::SaveStringToFile(TEXT("not json {"), *Path);
	TestEqual(TEXT("garbage unreadable"), Store.LoadServiceRecord(TEXT("p1"), Out, Error), ESSRecordLoad::Unreadable);
	const FString Aside = Store.QuarantineRecord(TEXT("p1"));
	TestFalse(TEXT("moved aside"), Aside.IsEmpty());
	TestTrue(TEXT("kept as a backup"), IFileManager::Get().FileExists(*Aside));
	TestFalse(TEXT("original path free for a new record"), IFileManager::Get().FileExists(*Path));

	// A v1 record (ADR-032) migrates to the current schema on load, keeping its XP.
	FFileHelper::SaveStringToFile(TEXT("{\"schemaVersion\": 1, \"playerId\": \"p1\", \"serviceXp\": 777}"), *Path);
	TestEqual(TEXT("v1 record loads"), Store.LoadServiceRecord(TEXT("p1"), Out, Error), ESSRecordLoad::Loaded);
	TestEqual(TEXT("... migrated to the current schema"), Out.SchemaVersion, FSSServiceRecord::CurrentSchemaVersion);
	TestEqual(TEXT("... XP kept"), Out.ServiceXp, 777);

	FFileHelper::SaveStringToFile(TEXT("{\"schemaVersion\": 0}"), *Path);
	TestEqual(TEXT("version 0 unreadable"), Store.LoadServiceRecord(TEXT("p1"), Out, Error), ESSRecordLoad::Unreadable);

	TestEqual(TEXT("unusable id"), Store.LoadServiceRecord(TEXT("../"), Out, Error), ESSRecordLoad::Unreadable);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
