// Copyright Southern Spear. All Rights Reserved.

#include "SSObjectiveHudModel.h"

#include "SSTeamIdentityLibrary.h"

#define LOCTEXT_NAMESPACE "SSObjectiveHud"

namespace
{
	FText FormatClock(float Seconds)
	{
		const int32 Total = FMath::Max(0, FMath::CeilToInt(Seconds));
		return FText::FromString(FString::Printf(TEXT("%d:%02d"), Total / 60, Total % 60));
	}

	bool HasViewer(ESSTeamId ViewerTeam)
	{
		return FSSTeamIdentity::IsPlayableTeam(ViewerTeam);
	}
}

FText FSSObjectiveHudModel::TeamWord(ESSTeamId Team, ESSTeamId ViewerTeam)
{
	if (!FSSTeamIdentity::IsPlayableTeam(Team))
	{
		return LOCTEXT("NoTeam", "No team");
	}
	if (!HasViewer(ViewerTeam))
	{
		return Team == ESSTeamId::TeamOne ? LOCTEXT("TeamOne", "Team One") : LOCTEXT("TeamTwo", "Team Two");
	}
	return Team == ViewerTeam ? LOCTEXT("Friendly", "Friendly") : LOCTEXT("Opposing", "Opposing");
}

ESSObjectiveHudTone FSSObjectiveHudModel::ToneFor(ESSTeamId Team, ESSTeamId ViewerTeam)
{
	if (!FSSTeamIdentity::IsPlayableTeam(Team) || !HasViewer(ViewerTeam))
	{
		return ESSObjectiveHudTone::Neutral;
	}
	return Team == ViewerTeam ? ESSObjectiveHudTone::Friendly : ESSObjectiveHudTone::Opposing;
}

FSSObjectiveHudModel FSSObjectiveHudModel::Build(const FSSRoundState& Round, const FSSObjectiveState* Active,
	const FText& ActiveName, ESSTeamId ViewerTeam)
{
	FSSObjectiveHudModel Model;
	const FText RoundText = FText::AsNumber(Round.RoundNumber);

	switch (Round.Phase)
	{
	case ESSRoundPhase::WaitingToStart:
		Model.Header = LOCTEXT("Waiting", "Waiting for the round");
		Model.PhaseLabel = LOCTEXT("WaitingShort", "Waiting");
		break;
	case ESSRoundPhase::PreRound:
		Model.Header = FText::Format(LOCTEXT("PreRound", "Round {0} starts in {1}"), RoundText, FormatClock(Round.PhaseTimeRemaining));
		Model.PhaseLabel = LOCTEXT("StartsIn", "Starts in");
		Model.Clock = FormatClock(Round.PhaseTimeRemaining);
		break;
	case ESSRoundPhase::InProgress:
		Model.Header = FText::Format(LOCTEXT("InProgress", "Round {0}  {1}"), RoundText, FormatClock(Round.PhaseTimeRemaining));
		Model.PhaseLabel = LOCTEXT("Assault", "Assault");
		Model.Clock = FormatClock(Round.PhaseTimeRemaining);
		break;
	case ESSRoundPhase::PostRound:
		if (Round.Outcome == ESSRoundOutcome::Draw)
		{
			Model.Header = FText::Format(LOCTEXT("Draw", "Round {0}: draw"), RoundText);
			Model.PhaseLabel = LOCTEXT("DrawShort", "Draw");
		}
		else
		{
			const ESSTeamId Winner = Round.Outcome == ESSRoundOutcome::TeamOneWon ? ESSTeamId::TeamOne : ESSTeamId::TeamTwo;
			Model.Header = FText::Format(LOCTEXT("Won", "Round {0}: {1} win"), RoundText, TeamWord(Winner, ViewerTeam));
			Model.PhaseLabel = FText::Format(LOCTEXT("WinShort", "{0} win"), TeamWord(Winner, ViewerTeam));
		}
		break;
	}

	// Scores keep a fixed order from the viewer: own side first.
	const ESSTeamId First = HasViewer(ViewerTeam) ? ViewerTeam : ESSTeamId::TeamOne;
	const ESSTeamId Second = FSSTeamIdentity::GetOpposingTeam(First);
	auto CapturesOf = [&Round](ESSTeamId Team) { return Team == ESSTeamId::TeamOne ? Round.TeamOneCaptures : Round.TeamTwoCaptures; };
	Model.Score = FText::Format(LOCTEXT("Score", "{0} {1} : {2} {3}"),
		TeamWord(First, ViewerTeam), FText::AsNumber(CapturesOf(First)),
		FText::AsNumber(CapturesOf(Second)), TeamWord(Second, ViewerTeam));

	Model.RoundLabel = FText::Format(LOCTEXT("RoundLabel", "Round {0}"), RoundText);
	Model.FirstSide = TeamWord(First, ViewerTeam);
	Model.SecondSide = TeamWord(Second, ViewerTeam);
	Model.FirstScore = CapturesOf(First);
	Model.SecondScore = CapturesOf(Second);
	Model.FirstTone = ToneFor(First, ViewerTeam);
	Model.SecondTone = ToneFor(Second, ViewerTeam);

	if (Round.Phase != ESSRoundPhase::InProgress || !Active || Round.ActiveObjectiveIndex == INDEX_NONE)
	{
		return Model;
	}

	Model.bShowObjective = true;
	Model.Progress = FMath::Clamp(Active->Progress, 0.f, 1.f);
	const FText Letter = FText::FromString(FString::Chr(TEXT('A') + FMath::Clamp(Round.ActiveObjectiveIndex, 0, 25)));
	const FText Count = FText::Format(LOCTEXT("Count", "{0}/{1}"), FText::AsNumber(Round.ActiveObjectiveIndex + 1), FText::AsNumber(Round.NumObjectives));

	FText Status;
	if (Active->bContested)
	{
		Status = LOCTEXT("Contested", "contested");
		Model.ProgressTone = ESSObjectiveHudTone::Contested;
	}
	else if (FSSTeamIdentity::IsPlayableTeam(Active->CapturingTeam))
	{
		Status = FText::Format(LOCTEXT("Capturing", "{0} capturing"), TeamWord(Active->CapturingTeam, ViewerTeam));
		Model.ProgressTone = ToneFor(Active->CapturingTeam, ViewerTeam);
	}
	else
	{
		Status = LOCTEXT("Neutral", "neutral");
	}
	Model.ObjectiveName = FText::Format(LOCTEXT("ObjName", "OBJ {0}  {1}"), Letter, ActiveName);
	Model.ObjectiveStatus = Status;
	Model.Objective = FText::Format(LOCTEXT("Objective", "OBJ {0}  {1}  ({2})  {3}"), Letter, ActiveName, Count, Status);
	return Model;
}

void FSSObjectiveHudModel::BuildChips(TConstArrayView<FSSObjectiveState> Objectives, int32 ActiveIndex, ESSTeamId ViewerTeam)
{
	Chips.Reset();
	for (int32 Index = 0; Index < Objectives.Num(); ++Index)
	{
		FChip& Chip = Chips.AddDefaulted_GetRef();
		Chip.Letter = FText::FromString(FString::Chr(TEXT('A') + FMath::Clamp(Index, 0, 25)));
		Chip.OwnerTone = ToneFor(Objectives[Index].OwnerTeam, ViewerTeam);
		Chip.bActive = Index == ActiveIndex;
	}
}

#undef LOCTEXT_NAMESPACE
