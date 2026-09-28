// Copyright Southern Spear. All Rights Reserved.
//
// Rank ladder and service levels (ADR-033): Australian Army ranks, Private to
// General, as levels 1-100, with insignia drawn from their descriptions.

#include "Misc/AutomationTest.h"

#include "Engine/Texture2D.h"
#include "SSServiceLevelMath.h"
#include "SSServiceRanks.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	constexpr EAutomationTestFlags SSRankTestFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter;

	FSSRankDefinition TestRank(const TCHAR* Id, int32 MinLevel)
	{
		FSSRankDefinition R;
		R.Id = Id;
		R.DisplayName = FText::FromString(Id);
		R.Abbreviation = FText::FromString(Id);
		R.MinLevel = MinLevel;
		return R;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSRanksShippedLadder, "SouthernSpear.Core.Ranks.ShippedLadder", SSRankTestFlags)
bool FSSRanksShippedLadder::RunTest(const FString& Parameters)
{
	// The ladder in Config/DefaultGame.ini, exactly as the game loads it.
	const USSRankSettings* Settings = GetDefault<USSRankSettings>();
	TArray<FString> Errors;
	TestTrue(TEXT("ladder valid"), FSSServiceRanks::Validate(Settings->Ranks, Settings->MaxLevel, Errors));
	for (const FString& Error : Errors)
	{
		AddError(Error);
	}
	TestEqual(TEXT("levels run to 100"), Settings->MaxLevel, 100);
	TestEqual(TEXT("Private to General: 17 ranks"), Settings->Ranks.Num(), 17);
	if (Settings->Ranks.Num() != 17)
	{
		return false;
	}
	TestEqual(TEXT("first rank"), Settings->Ranks[0].Id, FName(TEXT("Private")));
	TestEqual(TEXT("top rank"), Settings->Ranks.Last().Id, FName(TEXT("General")));
	TestEqual(TEXT("General is level 100"), Settings->Ranks.Last().MinLevel, 100);

	// The producer's example: Private at 1-4, Lance Corporal from 5.
	TestEqual(TEXT("level 4 is Private"), FSSServiceRanks::RankForLevel(4)->Id, FName(TEXT("Private")));
	TestEqual(TEXT("level 5 is Lance Corporal"), FSSServiceRanks::RankForLevel(5)->Id, FName(TEXT("LanceCorporal")));
	TestEqual(TEXT("level 99 is not General"), FSSServiceRanks::RankForLevel(99)->Id, FName(TEXT("LieutenantGeneral")));
	TestEqual(TEXT("level 100 is General"), FSSServiceRanks::RankForLevel(100)->Id, FName(TEXT("General")));
	TestNull(TEXT("level 0 (no record, e.g. a bot) has no rank"), FSSServiceRanks::RankForLevel(0));

	// Insignia: Private wears none; every other rank draws one.
	TestNull(TEXT("Private: no insignia"), FSSServiceRanks::InsigniaTexture(Settings->Ranks[0].Insignia));
	for (int32 Index = 1; Index < Settings->Ranks.Num(); ++Index)
	{
		TestNotNull(*FString::Printf(TEXT("%s has an insignia"), *Settings->Ranks[Index].Id.ToString()),
			FSSServiceRanks::InsigniaTexture(Settings->Ranks[Index].Insignia));
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSRanksLevelCurve, "SouthernSpear.Core.Ranks.LevelCurve", SSRankTestFlags)
bool FSSRanksLevelCurve::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("0 XP is level 1"), FSSServiceRanks::LevelForXp(0), 1);
	TestEqual(TEXT("negative XP is level 1"), FSSServiceRanks::LevelForXp(-50), 1);
	TestEqual(TEXT("a vast total stops at 100"), FSSServiceRanks::LevelForXp(int64(1) << 40), 100);
	for (int32 Level = 2; Level <= 100; ++Level)
	{
		const int64 Xp = FSSServiceRanks::XpForLevel(Level);
		if (Xp <= FSSServiceRanks::XpForLevel(Level - 1) || FSSServiceRanks::LevelForXp(Xp) != Level
			|| FSSServiceRanks::LevelForXp(Xp - 1) != Level - 1)
		{
			AddError(FString::Printf(TEXT("level curve breaks at level %d"), Level));
			return false;
		}
	}
	// Engine-free maths agrees with itself for other curves too.
	TestEqual(TEXT("linear curve"), SSServiceLevelMath::LevelForXp(250, 100.0, 1.0, 10), 3);
	TestEqual(TEXT("bad curve holds level 1"), SSServiceLevelMath::XpForLevel(5, 0.0, 1.0), 0LL);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSRanksValidation, "SouthernSpear.Core.Ranks.ValidationCatchesBadLadders", SSRankTestFlags)
bool FSSRanksValidation::RunTest(const FString& Parameters)
{
	TArray<FString> E;
	TestFalse(TEXT("empty ladder"), FSSServiceRanks::Validate({}, 100, E));
	E.Reset();
	TestFalse(TEXT("first rank above 1"), FSSServiceRanks::Validate({ TestRank(TEXT("A"), 2) }, 100, E));
	E.Reset();
	TestFalse(TEXT("levels must rise"), FSSServiceRanks::Validate({ TestRank(TEXT("A"), 1), TestRank(TEXT("B"), 1) }, 100, E));
	E.Reset();
	TestFalse(TEXT("duplicate ids"), FSSServiceRanks::Validate({ TestRank(TEXT("A"), 1), TestRank(TEXT("A"), 5) }, 100, E));
	E.Reset();
	TestFalse(TEXT("unreachable rank"), FSSServiceRanks::Validate({ TestRank(TEXT("A"), 1), TestRank(TEXT("B"), 101) }, 100, E));
	E.Reset();
	TestTrue(TEXT("good ladder"), FSSServiceRanks::Validate({ TestRank(TEXT("A"), 1), TestRank(TEXT("B"), 5) }, 100, E));

	const TArray<FSSRankDefinition> Ladder = { TestRank(TEXT("A"), 1), TestRank(TEXT("B"), 5), TestRank(TEXT("C"), 10) };
	TestEqual(TEXT("level 4"), FSSServiceRanks::RankIndexForLevel(4, Ladder), 0);
	TestEqual(TEXT("level 5 promoted on the threshold"), FSSServiceRanks::RankIndexForLevel(5, Ladder), 1);
	TestEqual(TEXT("level 50"), FSSServiceRanks::RankIndexForLevel(50, Ladder), 2);
	TestEqual(TEXT("level 0"), FSSServiceRanks::RankIndexForLevel(0, Ladder), INDEX_NONE);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
