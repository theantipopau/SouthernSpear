// Copyright Southern Spear. All Rights Reserved.

#include "SSProgressionRules.h"

#include "Modules/ModuleManager.h"

DEFINE_LOG_CATEGORY(LogSSProgression);

IMPLEMENT_MODULE(FDefaultModuleImpl, SouthernSpearProgression)

#define LOCTEXT_NAMESPACE "SSProgression"

namespace
{
	/** Upper bound on any per-match cap: a cap in the thousands is no cap. */
	constexpr int32 MaxSaneCap = 100;
}

int32 FSSProgressionRules::ResolveRankIndex(int32 Xp, TConstArrayView<FSSRankDefinition> Ranks)
{
	int32 Found = Ranks.Num() > 0 ? 0 : INDEX_NONE;
	for (int32 Index = 0; Index < Ranks.Num(); ++Index)
	{
		if (Ranks[Index].MinServiceXp <= Xp)
		{
			Found = Index;
		}
	}
	return Found;
}

bool FSSProgressionRules::ValidateRanks(TConstArrayView<FSSRankDefinition> Ranks, TArray<FString>& OutErrors)
{
	const int32 Before = OutErrors.Num();
	if (Ranks.Num() == 0)
	{
		OutErrors.Add(TEXT("The rank ladder is empty."));
		return false;
	}
	if (Ranks[0].MinServiceXp != 0)
	{
		OutErrors.Add(FString::Printf(TEXT("The first rank '%s' starts at %d XP; it must start at 0."),
			*Ranks[0].Id.ToString(), Ranks[0].MinServiceXp));
	}
	TSet<FName> Seen;
	for (int32 Index = 0; Index < Ranks.Num(); ++Index)
	{
		const FSSRankDefinition& Rank = Ranks[Index];
		if (Rank.Id.IsNone())
		{
			OutErrors.Add(FString::Printf(TEXT("Rank %d has no Id."), Index));
		}
		else if (Seen.Contains(Rank.Id))
		{
			OutErrors.Add(FString::Printf(TEXT("Rank Id '%s' appears twice."), *Rank.Id.ToString()));
		}
		Seen.Add(Rank.Id);
		if (Rank.DisplayName.IsEmpty())
		{
			OutErrors.Add(FString::Printf(TEXT("Rank '%s' has no display name."), *Rank.Id.ToString()));
		}
		if (Index > 0 && Rank.MinServiceXp <= Ranks[Index - 1].MinServiceXp)
		{
			OutErrors.Add(FString::Printf(TEXT("Rank '%s' (%d XP) does not rise above '%s' (%d XP)."),
				*Rank.Id.ToString(), Rank.MinServiceXp, *Ranks[Index - 1].Id.ToString(), Ranks[Index - 1].MinServiceXp));
		}
	}
	return OutErrors.Num() == Before;
}

bool FSSProgressionRules::ValidateAwards(TConstArrayView<FSSXpAwardRule> Awards, TArray<FString>& OutErrors)
{
	const int32 Before = OutErrors.Num();
	TSet<ESSServiceEvent> Seen;
	for (const FSSXpAwardRule& Rule : Awards)
	{
		const TCHAR* Name = USSServiceEventSubsystem::LexEvent(Rule.Event);
		if (Rule.Event == ESSServiceEvent::None)
		{
			OutErrors.Add(TEXT("An award rule names no event."));
			continue;
		}
		if (Seen.Contains(Rule.Event))
		{
			OutErrors.Add(FString::Printf(TEXT("Event %s has more than one award rule."), Name));
		}
		Seen.Add(Rule.Event);
		if (Rule.Award == 0)
		{
			OutErrors.Add(FString::Printf(TEXT("Event %s awards 0 XP; remove the rule instead."), Name));
		}
		// GDD §6.4 / TDD §6.2: no uncapped reward. Penalties are exempt on purpose.
		if (Rule.Award > 0 && (Rule.MaxPerMatch < 1 || Rule.MaxPerMatch > MaxSaneCap))
		{
			OutErrors.Add(FString::Printf(TEXT("Event %s awards %d XP with MaxPerMatch %d; a reward needs a cap of 1..%d."),
				Name, Rule.Award, Rule.MaxPerMatch, MaxSaneCap));
		}
	}
	return OutErrors.Num() == Before;
}

const FSSXpAwardRule* FSSProgressionRules::FindRule(ESSServiceEvent Event, TConstArrayView<FSSXpAwardRule> Awards)
{
	for (const FSSXpAwardRule& Rule : Awards)
	{
		if (Rule.Event == Event)
		{
			return &Rule;
		}
	}
	return nullptr;
}

int32 FSSProgressionRules::GrantAward(FSSMatchTally& Tally, ESSServiceEvent Event, TConstArrayView<FSSXpAwardRule> Awards)
{
	const FSSXpAwardRule* Rule = FindRule(Event, Awards);
	if (!Rule || Rule->Award == 0)
	{
		return 0;
	}
	int32& Count = Tally.Earned.FindOrAdd(Event);
	if (Rule->Award > 0 && Count >= FMath::Clamp(Rule->MaxPerMatch, 0, MaxSaneCap))
	{
		return 0;
	}
	++Count;
	return Rule->Award;
}

void FSSProgressionRules::ApplyAward(FSSServiceRecord& Record, ESSServiceEvent Event, int32 XpDelta)
{
	const int64 Xp = int64(Record.ServiceXp) + XpDelta;
	Record.ServiceXp = int32(FMath::Clamp<int64>(Xp, 0, MAX_int32));

	FSSServiceStatistics& S = Record.Statistics;
	switch (Event)
	{
	case ESSServiceEvent::ObjectiveCaptured:	++S.ObjectivesCaptured; break;
	case ESSServiceEvent::RoundWon:				++S.RoundsWon; break;
	case ESSServiceEvent::RoundWonAlive:		++S.RoundsWonAlive; break;
	case ESSServiceEvent::MatchCompleted:		++S.MatchesCompleted; break;
	case ESSServiceEvent::MatchWon:				++S.MatchesWon; break;
	case ESSServiceEvent::FriendlyKill:			++S.FriendlyKills; break;
	default:									break;
	}
}

bool FSSProgressionRules::Migrate(FSSServiceRecord& Record, FString& OutError)
{
	if (Record.SchemaVersion < 1)
	{
		OutError = FString::Printf(TEXT("Service record schema version %d is not valid."), Record.SchemaVersion);
		return false;
	}
	if (Record.SchemaVersion > FSSServiceRecord::CurrentSchemaVersion)
	{
		OutError = FString::Printf(TEXT("Service record schema version %d is newer than this build (%d)."),
			Record.SchemaVersion, FSSServiceRecord::CurrentSchemaVersion);
		return false;
	}
	// The chain: one step per version, applied in order. v1 is the first schema.
	// if (Record.SchemaVersion == 1) { ...v1 -> v2...; Record.SchemaVersion = 2; }
	Record.ServiceXp = FMath::Max(0, Record.ServiceXp);
	return true;
}

FString FSSProgressionRules::SanitisePlayerId(const FString& PlayerId)
{
	FString Out;
	for (const TCHAR C : PlayerId)
	{
		if (FChar::IsAlnum(C) || C == TEXT('-') || C == TEXT('_'))
		{
			Out.AppendChar(C);
		}
	}
	return Out.Len() > 64 ? Out.Left(64) : Out;
}

bool FSSProgressionRules::IsValidCallsign(const FString& Callsign)
{
	const FString Trimmed = Callsign.TrimStartAndEnd();
	if (Trimmed.Len() < 2 || Trimmed.Len() > 16)
	{
		return false;
	}
	for (const TCHAR C : Trimmed)
	{
		if (!(FChar::IsAlnum(C) || C == TEXT(' ') || C == TEXT('-') || C == TEXT('_')))
		{
			return false;
		}
	}
	return true;
}

FText FSSProgressionRules::EventName(ESSServiceEvent Event)
{
	switch (Event)
	{
	case ESSServiceEvent::ObjectiveCaptured:	return LOCTEXT("EvObjective", "Objective captured");
	case ESSServiceEvent::RoundWon:				return LOCTEXT("EvRoundWon", "Round won");
	case ESSServiceEvent::RoundWonAlive:		return LOCTEXT("EvRoundWonAlive", "Survived the win");
	case ESSServiceEvent::MatchCompleted:		return LOCTEXT("EvMatchCompleted", "Match completed");
	case ESSServiceEvent::MatchWon:				return LOCTEXT("EvMatchWon", "Match won");
	case ESSServiceEvent::FriendlyKill:			return LOCTEXT("EvFriendlyKill", "Friendly kill");
	default:									return FText::GetEmpty();
	}
}

#undef LOCTEXT_NAMESPACE
