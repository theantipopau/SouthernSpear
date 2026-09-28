// Copyright Southern Spear. All Rights Reserved.

#include "SSSectionAssaultRules.h"

#include "SSObjectiveRules.h"
#include "SSTeamIdentityLibrary.h"

namespace
{
	bool IsValidSectionStep(float DeltaSeconds)
	{
		return FMath::IsFinite(DeltaSeconds) && DeltaSeconds > 0.f;
	}

	ESSRoundOutcome SectionOutcomeFor(ESSTeamId Winner)
	{
		switch (Winner)
		{
		case ESSTeamId::TeamOne:	return ESSRoundOutcome::TeamOneWon;
		case ESSTeamId::TeamTwo:	return ESSRoundOutcome::TeamTwoWon;
		default:					return ESSRoundOutcome::Draw;
		}
	}
}

FSSMatchState FSSSectionAssaultRules::NewMatch()
{
	FSSMatchState Match;
	Match.AttackingTeam = ESSTeamId::TeamOne;
	Match.Half = 1;
	return Match;
}

ESSTeamId FSSSectionAssaultRules::AttackerForRound(int32 RoundsPlayed, const FSSSectionRules& Rules)
{
	return RoundsPlayed < FMath::Max(1, Rules.RoundsPerHalf) ? ESSTeamId::TeamOne : ESSTeamId::TeamTwo;
}

FSSObjectiveState FSSSectionAssaultRules::StepAttackCapture(
	const FSSObjectiveState& State, ESSTeamId Attacker, int32 AttackersPresent, int32 DefendersPresent,
	float DeltaSeconds, const FSSCaptureRules& Rules)
{
	FSSObjectiveState Next = State;
	if (!State.bActive || State.IsCaptured() || !IsValidSectionStep(DeltaSeconds) || !FSSTeamIdentity::IsPlayableTeam(Attacker))
	{
		return Next;
	}

	const bool bAttackers = AttackersPresent > 0;
	const bool bDefenders = DefendersPresent > 0;
	Next.bContested = bAttackers && bDefenders;
	if (Next.bContested)
	{
		return Next; // frozen while both hold it
	}

	const float CaptureRate = 1.f / FMath::Max(Rules.CaptureSeconds, 1.f);
	if (bAttackers)
	{
		Next.CapturingTeam = Attacker;
		Next.Progress = FMath::Min(1.f, Next.Progress + CaptureRate * DeltaSeconds);
		if (Next.Progress >= 1.f)
		{
			Next.OwnerTeam = Attacker;
		}
		return Next;
	}

	// Defenders actively clear the point; an empty point only decays.
	const float Rate = bDefenders ? CaptureRate : 1.f / FMath::Max(Rules.DecaySeconds, 1.f);
	Next.Progress = FMath::Max(0.f, Next.Progress - Rate * DeltaSeconds);
	if (Next.Progress <= 0.f)
	{
		Next.CapturingTeam = ESSTeamId::None;
	}
	return Next;
}

ESSRoundEndReason FSSSectionAssaultRules::ResolveRound(
	bool bFinalObjectiveTaken, int32 AttackerRoster, int32 AttackersAlive, int32 DefenderRoster,
	int32 DefendersAlive, bool bTimeExpired, ESSTeamId Attacker, ESSTeamId& OutWinner)
{
	const ESSTeamId Defender = FSSTeamIdentity::GetOpposingTeam(Attacker);
	OutWinner = ESSTeamId::None;

	if (bFinalObjectiveTaken)
	{
		OutWinner = Attacker;
		return ESSRoundEndReason::ObjectiveTaken;
	}

	const bool bAttackersOut = AttackerRoster > 0 && AttackersAlive <= 0;
	const bool bDefendersOut = DefenderRoster > 0 && DefendersAlive <= 0;
	if (bAttackersOut && bDefendersOut)
	{
		return ESSRoundEndReason::MutualElimination;
	}
	if (bAttackersOut)
	{
		OutWinner = Defender;
		return ESSRoundEndReason::AttackersEliminated;
	}
	if (bDefendersOut)
	{
		OutWinner = Attacker;
		return ESSRoundEndReason::DefendersEliminated;
	}
	if (bTimeExpired)
	{
		OutWinner = Defender;
		return ESSRoundEndReason::TimeExpired;
	}
	return ESSRoundEndReason::None;
}

FSSMatchState FSSSectionAssaultRules::ApplyRoundResult(
	const FSSMatchState& Match, ESSTeamId Winner, ESSRoundEndReason Reason, const FSSSectionRules& Rules)
{
	FSSMatchState Next = Match;
	if (Match.bMatchOver || Reason == ESSRoundEndReason::None)
	{
		return Next;
	}

	if (Winner == ESSTeamId::TeamOne)
	{
		++Next.TeamOneRounds;
	}
	else if (Winner == ESSTeamId::TeamTwo)
	{
		++Next.TeamTwoRounds;
	}
	++Next.RoundsPlayed;
	Next.LastRoundReason = Reason;

	const int32 PerHalf = FMath::Max(1, Rules.RoundsPerHalf);
	const int32 ToWin = PerHalf + 1;
	if (Next.TeamOneRounds >= ToWin || Next.TeamTwoRounds >= ToWin || Next.RoundsPlayed >= PerHalf * 2)
	{
		Next.bMatchOver = true;
		Next.MatchWinner = Next.TeamOneRounds > Next.TeamTwoRounds ? ESSTeamId::TeamOne
			: Next.TeamTwoRounds > Next.TeamOneRounds ? ESSTeamId::TeamTwo : ESSTeamId::None;
		return Next;
	}

	Next.AttackingTeam = AttackerForRound(Next.RoundsPlayed, Rules);
	Next.Half = Next.RoundsPlayed < PerHalf ? 1 : 2;
	return Next;
}

void FSSSectionAssaultRules::StepRound(
	const FSSRoundState& Round, const FSSMatchState& Match, float DeltaSeconds, const FSSSectionInputs& Inputs,
	const FSSRoundRules& RoundRules, const FSSSectionRules& SectionRules,
	FSSRoundState& OutRound, FSSMatchState& OutMatch, FSSRoundEvents& OutEvents)
{
	OutRound = Round;
	OutMatch = Match;
	if (!IsValidSectionStep(DeltaSeconds) || Round.Phase == ESSRoundPhase::WaitingToStart)
	{
		return;
	}

	OutRound.PhaseTimeRemaining = FMath::Max(0.f, OutRound.PhaseTimeRemaining - DeltaSeconds);

	switch (Round.Phase)
	{
	case ESSRoundPhase::PreRound:
		if (OutRound.PhaseTimeRemaining <= 0.f)
		{
			OutRound.Phase = ESSRoundPhase::InProgress;
			OutRound.PhaseTimeRemaining = SectionRules.RoundSeconds;
			OutRound.ActiveObjectiveIndex = 0;
			OutEvents.bRoundStarted = true;
		}
		break;

	case ESSRoundPhase::InProgress:
	{
		const ESSTeamId Attacker = Match.AttackingTeam;
		OutMatch.TeamOneAlive = Inputs.TeamOneAlive;
		OutMatch.TeamTwoAlive = Inputs.TeamTwoAlive;

		// Only the attackers can own an objective; anything else is ignored.
		bool bFinalTaken = false;
		if (Inputs.ActiveObjectiveCapturedBy == Attacker && FSSTeamIdentity::IsPlayableTeam(Attacker))
		{
			(Attacker == ESSTeamId::TeamOne ? OutRound.TeamOneCaptures : OutRound.TeamTwoCaptures)++;
			if (OutRound.ActiveObjectiveIndex + 1 >= OutRound.NumObjectives)
			{
				bFinalTaken = true;
			}
			else
			{
				++OutRound.ActiveObjectiveIndex;
				OutEvents.bObjectiveAdvanced = true;
			}
		}

		const bool bAttackerIsOne = Attacker == ESSTeamId::TeamOne;
		ESSTeamId Winner = ESSTeamId::None;
		const ESSRoundEndReason Reason = ResolveRound(bFinalTaken,
			bAttackerIsOne ? Inputs.TeamOneRoster : Inputs.TeamTwoRoster,
			bAttackerIsOne ? Inputs.TeamOneAlive : Inputs.TeamTwoAlive,
			bAttackerIsOne ? Inputs.TeamTwoRoster : Inputs.TeamOneRoster,
			bAttackerIsOne ? Inputs.TeamTwoAlive : Inputs.TeamOneAlive,
			OutRound.PhaseTimeRemaining <= 0.f, Attacker, Winner);

		if (Reason != ESSRoundEndReason::None)
		{
			OutMatch = ApplyRoundResult(OutMatch, Winner, Reason, SectionRules);
			OutRound.Phase = ESSRoundPhase::PostRound;
			OutRound.Outcome = SectionOutcomeFor(Winner);
			OutRound.ActiveObjectiveIndex = INDEX_NONE;
			OutRound.PhaseTimeRemaining = OutMatch.bMatchOver ? SectionRules.PostMatchSeconds : RoundRules.PostRoundSeconds;
			OutEvents.bObjectiveAdvanced = false;
			OutEvents.bRoundEnded = true;
			OutEvents.bMatchEnded = OutMatch.bMatchOver;
		}
		break;
	}

	case ESSRoundPhase::PostRound:
		if (OutRound.PhaseTimeRemaining <= 0.f)
		{
			if (OutMatch.bMatchOver)
			{
				OutMatch = NewMatch();
			}
			OutMatch.TeamOneAlive = 0;
			OutMatch.TeamTwoAlive = 0;
			OutRound = FSSObjectiveRules::StartRound(OutRound, OutRound.NumObjectives, RoundRules, OutEvents);
		}
		break;

	default:
		break;
	}
}

const TCHAR* FSSSectionAssaultRules::LexReason(ESSRoundEndReason Reason)
{
	switch (Reason)
	{
	case ESSRoundEndReason::None:					return TEXT("None");
	case ESSRoundEndReason::ObjectiveTaken:			return TEXT("ObjectiveTaken");
	case ESSRoundEndReason::AttackersEliminated:	return TEXT("AttackersEliminated");
	case ESSRoundEndReason::DefendersEliminated:	return TEXT("DefendersEliminated");
	case ESSRoundEndReason::MutualElimination:		return TEXT("MutualElimination");
	case ESSRoundEndReason::TimeExpired:			return TEXT("TimeExpired");
	default:										return TEXT("Unknown");
	}
}
