// Copyright Southern Spear. All Rights Reserved.

#include "SSObjectiveRules.h"

#include "Modules/ModuleManager.h"
#include "SSTeamIdentityLibrary.h"

DEFINE_LOG_CATEGORY(LogSSObjectives);

IMPLEMENT_MODULE(FDefaultModuleImpl, SouthernSpearObjectives)

namespace
{
	bool IsValidStep(float DeltaSeconds)
	{
		return FMath::IsFinite(DeltaSeconds) && DeltaSeconds > 0.f;
	}
}

FSSObjectiveState FSSObjectiveRules::StepCapture(
	const FSSObjectiveState& State, int32 TeamOneCount, int32 TeamTwoCount,
	float DeltaSeconds, const FSSCaptureRules& Rules)
{
	FSSObjectiveState Next = State;
	if (!State.bActive || State.IsCaptured() || !IsValidStep(DeltaSeconds))
	{
		return Next;
	}

	const bool bOnePresent = TeamOneCount > 0;
	const bool bTwoPresent = TeamTwoCount > 0;
	Next.bContested = bOnePresent && bTwoPresent;
	if (Next.bContested)
	{
		// Frozen: neither team gains ground while both hold the objective.
		return Next;
	}

	const float CaptureRate = 1.f / FMath::Max(Rules.CaptureSeconds, 1.f);

	if (!bOnePresent && !bTwoPresent)
	{
		const float DecayRate = 1.f / FMath::Max(Rules.DecaySeconds, 1.f);
		Next.Progress = FMath::Max(0.f, Next.Progress - DecayRate * DeltaSeconds);
		if (Next.Progress <= 0.f)
		{
			Next.CapturingTeam = ESSTeamId::None;
		}
		return Next;
	}

	const ESSTeamId Present = bOnePresent ? ESSTeamId::TeamOne : ESSTeamId::TeamTwo;

	if (Next.CapturingTeam != ESSTeamId::None && Next.CapturingTeam != Present)
	{
		// The other team's progress must be neutralised before this team can
		// build its own. Any time left over after reaching zero is carried into
		// capture, so the result does not depend on frame boundaries.
		const float Needed = Next.Progress / CaptureRate;
		if (DeltaSeconds < Needed)
		{
			Next.Progress -= CaptureRate * DeltaSeconds;
			return Next;
		}
		DeltaSeconds -= Needed;
		Next.Progress = 0.f;
		Next.CapturingTeam = ESSTeamId::None;
		if (DeltaSeconds <= 0.f)
		{
			return Next;
		}
	}

	Next.CapturingTeam = Present;
	Next.Progress = FMath::Min(1.f, Next.Progress + CaptureRate * DeltaSeconds);
	if (Next.Progress >= 1.f)
	{
		Next.OwnerTeam = Present;
	}
	return Next;
}

FSSObjectiveState FSSObjectiveRules::ResetObjective(bool bActive)
{
	FSSObjectiveState State;
	State.bActive = bActive;
	return State;
}

FSSRoundState FSSObjectiveRules::StartRound(
	const FSSRoundState& Previous, int32 NumObjectives, const FSSRoundRules& Rules,
	FSSRoundEvents& OutEvents)
{
	FSSRoundState Next;
	Next.RoundNumber = Previous.RoundNumber;
	Next.NumObjectives = FMath::Max(0, NumObjectives);
	if (Next.NumObjectives == 0)
	{
		Next.Phase = ESSRoundPhase::WaitingToStart;
		return Next;
	}

	Next.RoundNumber = Previous.RoundNumber + 1;
	Next.Phase = ESSRoundPhase::PreRound;
	Next.PhaseTimeRemaining = Rules.PreRoundSeconds;
	OutEvents.bRoundReset = true;
	return Next;
}

FSSRoundState FSSObjectiveRules::StepRound(
	const FSSRoundState& State, float DeltaSeconds, ESSTeamId ActiveObjectiveCapturedBy,
	const FSSRoundRules& Rules, FSSRoundEvents& OutEvents)
{
	FSSRoundState Next = State;
	if (!IsValidStep(DeltaSeconds) || State.Phase == ESSRoundPhase::WaitingToStart)
	{
		return Next;
	}

	Next.PhaseTimeRemaining = FMath::Max(0.f, Next.PhaseTimeRemaining - DeltaSeconds);

	switch (State.Phase)
	{
	case ESSRoundPhase::PreRound:
		if (Next.PhaseTimeRemaining <= 0.f)
		{
			Next.Phase = ESSRoundPhase::InProgress;
			Next.PhaseTimeRemaining = Rules.RoundSeconds;
			Next.ActiveObjectiveIndex = 0;
			OutEvents.bRoundStarted = true;
		}
		break;

	case ESSRoundPhase::InProgress:
		// A capture is resolved before the clock: an objective taken on the
		// frame time expires still counts.
		if (FSSTeamIdentity::IsPlayableTeam(ActiveObjectiveCapturedBy))
		{
			(ActiveObjectiveCapturedBy == ESSTeamId::TeamOne ? Next.TeamOneCaptures : Next.TeamTwoCaptures)++;

			if (Next.ActiveObjectiveIndex + 1 >= Next.NumObjectives)
			{
				Next.Phase = ESSRoundPhase::PostRound;
				Next.Outcome = ActiveObjectiveCapturedBy == ESSTeamId::TeamOne
					? ESSRoundOutcome::TeamOneWon : ESSRoundOutcome::TeamTwoWon;
				Next.ActiveObjectiveIndex = INDEX_NONE;
				Next.PhaseTimeRemaining = Rules.PostRoundSeconds;
				OutEvents.bRoundEnded = true;
			}
			else
			{
				++Next.ActiveObjectiveIndex;
				OutEvents.bObjectiveAdvanced = true;
			}
		}
		else if (Next.PhaseTimeRemaining <= 0.f)
		{
			Next.Phase = ESSRoundPhase::PostRound;
			Next.Outcome = ESSRoundOutcome::Draw;
			Next.ActiveObjectiveIndex = INDEX_NONE;
			Next.PhaseTimeRemaining = Rules.PostRoundSeconds;
			OutEvents.bRoundEnded = true;
		}
		break;

	case ESSRoundPhase::PostRound:
		if (Next.PhaseTimeRemaining <= 0.f)
		{
			Next = StartRound(Next, Next.NumObjectives, Rules, OutEvents);
		}
		break;

	default:
		break;
	}
	return Next;
}

const TCHAR* FSSObjectiveRules::LexPhase(ESSRoundPhase Phase)
{
	switch (Phase)
	{
	case ESSRoundPhase::WaitingToStart:	return TEXT("WaitingToStart");
	case ESSRoundPhase::PreRound:		return TEXT("PreRound");
	case ESSRoundPhase::InProgress:		return TEXT("InProgress");
	case ESSRoundPhase::PostRound:		return TEXT("PostRound");
	default:							return TEXT("Unknown");
	}
}

const TCHAR* FSSObjectiveRules::LexOutcome(ESSRoundOutcome Outcome)
{
	switch (Outcome)
	{
	case ESSRoundOutcome::None:			return TEXT("None");
	case ESSRoundOutcome::TeamOneWon:	return TEXT("TeamOneWon");
	case ESSRoundOutcome::TeamTwoWon:	return TEXT("TeamTwoWon");
	case ESSRoundOutcome::Draw:			return TEXT("Draw");
	default:							return TEXT("Unknown");
	}
}
