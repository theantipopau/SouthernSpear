// Copyright Southern Spear. All Rights Reserved.
//
// Objective HUD model: text and tone come from replicated state and the
// viewer's team, never from a guessed side (ADR-017).

#include "Misc/AutomationTest.h"
#include "SSObjectiveHudModel.h"
#include "SSObjectiveRules.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	constexpr EAutomationTestFlags SSHudTestFlags =
		EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter;

	FSSRoundState InProgressRound()
	{
		FSSRoundState Round;
		Round.Phase = ESSRoundPhase::InProgress;
		Round.RoundNumber = 3;
		Round.NumObjectives = 2;
		Round.ActiveObjectiveIndex = 1;
		Round.PhaseTimeRemaining = 125.2f;
		Round.TeamOneCaptures = 1;
		return Round;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSHudViewerRelative, "SouthernSpear.Objectives.Hud.ViewerRelative", SSHudTestFlags)
bool FSSHudViewerRelative::RunTest(const FString& Parameters)
{
	FSSObjectiveState Obj = FSSObjectiveRules::ResetObjective(true);
	Obj.CapturingTeam = ESSTeamId::TeamTwo;
	Obj.Progress = 0.4f;
	const FText Name = FText::FromString(TEXT("Farmstead"));

	const FSSObjectiveHudModel One = FSSObjectiveHudModel::Build(InProgressRound(), &Obj, Name, ESSTeamId::TeamOne);
	TestEqual(TEXT("header"), One.Header.ToString(), FString(TEXT("Round 3  2:06")));
	TestEqual(TEXT("objective, seen by team one"), One.Objective.ToString(), FString(TEXT("OBJ B  Farmstead  (2/2)  Opposing capturing")));
	TestEqual(TEXT("score, own side first"), One.Score.ToString(), FString(TEXT("Friendly 1 : 0 Opposing")));
	TestTrue(TEXT("opposing tone"), One.ProgressTone == ESSObjectiveHudTone::Opposing);
	TestEqual(TEXT("progress"), One.Progress, 0.4f);

	const FSSObjectiveHudModel Two = FSSObjectiveHudModel::Build(InProgressRound(), &Obj, Name, ESSTeamId::TeamTwo);
	TestEqual(TEXT("same capture, seen by team two"), Two.Objective.ToString(), FString(TEXT("OBJ B  Farmstead  (2/2)  Friendly capturing")));
	TestEqual(TEXT("score from team two"), Two.Score.ToString(), FString(TEXT("Friendly 0 : 1 Opposing")));
	TestTrue(TEXT("friendly tone"), Two.ProgressTone == ESSObjectiveHudTone::Friendly);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSHudNoViewerIsNeutral, "SouthernSpear.Objectives.Hud.NoViewerTeamIsNeutral", SSHudTestFlags)
bool FSSHudNoViewerIsNeutral::RunTest(const FString& Parameters)
{
	FSSObjectiveState Obj = FSSObjectiveRules::ResetObjective(true);
	Obj.CapturingTeam = ESSTeamId::TeamOne;
	const FSSObjectiveHudModel Model = FSSObjectiveHudModel::Build(InProgressRound(), &Obj, FText::FromString(TEXT("X")), ESSTeamId::None);
	TestEqual(TEXT("no side guessed"), Model.Score.ToString(), FString(TEXT("Team One 1 : 0 Team Two")));
	TestTrue(TEXT("neutral tone"), Model.ProgressTone == ESSObjectiveHudTone::Neutral);

	Obj.bContested = true;
	const FSSObjectiveHudModel Contested = FSSObjectiveHudModel::Build(InProgressRound(), &Obj, FText::FromString(TEXT("X")), ESSTeamId::None);
	TestTrue(TEXT("contested wins over capturing"), Contested.ProgressTone == ESSObjectiveHudTone::Contested);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSHudPhases, "SouthernSpear.Objectives.Hud.Phases", SSHudTestFlags)
bool FSSHudPhases::RunTest(const FString& Parameters)
{
	FSSRoundState Round = InProgressRound();
	Round.Phase = ESSRoundPhase::PostRound;
	Round.ActiveObjectiveIndex = INDEX_NONE;
	Round.Outcome = ESSRoundOutcome::TeamTwoWon;
	const FSSObjectiveHudModel Won = FSSObjectiveHudModel::Build(Round, nullptr, FText::GetEmpty(), ESSTeamId::TeamOne);
	TestEqual(TEXT("loss seen by team one"), Won.Header.ToString(), FString(TEXT("Round 3: Opposing win")));
	TestFalse(TEXT("no objective after the round"), Won.bShowObjective);

	Round.Outcome = ESSRoundOutcome::Draw;
	TestEqual(TEXT("draw"), FSSObjectiveHudModel::Build(Round, nullptr, FText::GetEmpty(), ESSTeamId::TeamOne).Header.ToString(),
		FString(TEXT("Round 3: draw")));

	Round.Phase = ESSRoundPhase::PreRound;
	Round.PhaseTimeRemaining = 7.5f;
	TestEqual(TEXT("pre-round countdown"), FSSObjectiveHudModel::Build(Round, nullptr, FText::GetEmpty(), ESSTeamId::TeamOne).Header.ToString(),
		FString(TEXT("Round 3 starts in 0:08")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSHudChips, "SouthernSpear.Objectives.Hud.Chips", SSHudTestFlags)
bool FSSHudChips::RunTest(const FString& Parameters)
{
	TArray<FSSObjectiveState> States;
	States.Add(FSSObjectiveRules::ResetObjective(false));
	States[0].OwnerTeam = ESSTeamId::TeamOne;
	States.Add(FSSObjectiveRules::ResetObjective(true));

	FSSObjectiveHudModel Model = FSSObjectiveHudModel::Build(InProgressRound(), &States[1], FText::FromString(TEXT("B")), ESSTeamId::TeamTwo);
	Model.BuildChips(States, 1, ESSTeamId::TeamTwo);
	TestEqual(TEXT("one chip per objective"), Model.Chips.Num(), 2);
	TestEqual(TEXT("letters"), Model.Chips[1].Letter.ToString(), FString(TEXT("B")));
	TestTrue(TEXT("A held by the other side"), Model.Chips[0].OwnerTone == ESSObjectiveHudTone::Opposing);
	TestTrue(TEXT("B active, unowned"), Model.Chips[1].bActive && Model.Chips[1].OwnerTone == ESSObjectiveHudTone::Neutral);
	TestEqual(TEXT("structured clock"), Model.Clock.ToString(), FString(TEXT("2:06")));

	Model.BuildChips(States, 1, ESSTeamId::None);
	TestTrue(TEXT("spectator sees no side"), Model.Chips[0].OwnerTone == ESSObjectiveHudTone::Neutral);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSHudSectionAssault, "SouthernSpear.Objectives.Hud.SectionAssault", SSHudTestFlags)
bool FSSHudSectionAssault::RunTest(const FString& Parameters)
{
	// ADR-031: rounds won replace captures, the role is the viewer's, and the
	// alive counts read own side first. Both viewers see the mirror image.
	FSSMatchState Match;
	Match.TeamOneRounds = 3;
	Match.TeamTwoRounds = 1;
	Match.RoundsPlayed = 4;
	Match.Half = 2;
	Match.AttackingTeam = ESSTeamId::TeamTwo;
	Match.TeamOneAlive = 4;
	Match.TeamTwoAlive = 2;
	const FSSObjectiveState Obj = FSSObjectiveRules::ResetObjective(true);
	const FText Name = FText::FromString(TEXT("Farmstead"));

	FSSObjectiveHudModel One = FSSObjectiveHudModel::Build(InProgressRound(), &Obj, Name, ESSTeamId::TeamOne);
	One.ApplySectionAssault(InProgressRound(), Match, ESSTeamId::TeamOne);
	TestEqual(TEXT("own rounds first"), One.FirstScore, 3);
	TestEqual(TEXT("opposing rounds second"), One.SecondScore, 1);
	TestFalse(TEXT("Team One defends"), One.bViewerAttacking);
	TestEqual(TEXT("defend"), One.PhaseLabel.ToString(), FString(TEXT("Defend")));
	TestEqual(TEXT("own alive first"), One.Alive.ToString(), FString(TEXT("4 v 2")));
	TestEqual(TEXT("round in match"), One.RoundLabel.ToString(), FString(TEXT("Round 5")));

	FSSObjectiveHudModel Two = FSSObjectiveHudModel::Build(InProgressRound(), &Obj, Name, ESSTeamId::TeamTwo);
	Two.ApplySectionAssault(InProgressRound(), Match, ESSTeamId::TeamTwo);
	TestEqual(TEXT("mirror: own rounds first"), Two.FirstScore, 1);
	TestTrue(TEXT("Team Two attacks"), Two.bViewerAttacking);
	TestEqual(TEXT("attack"), Two.PhaseLabel.ToString(), FString(TEXT("Attack")));
	TestEqual(TEXT("mirror: own alive first"), Two.Alive.ToString(), FString(TEXT("2 v 4")));

	FSSObjectiveHudModel Spectator = FSSObjectiveHudModel::Build(InProgressRound(), &Obj, Name, ESSTeamId::None);
	Spectator.ApplySectionAssault(InProgressRound(), Match, ESSTeamId::None);
	TestTrue(TEXT("no team: no role guessed"), Spectator.Role.IsEmpty());
	TestEqual(TEXT("neutral vantage"), Spectator.PhaseLabel.ToString(), FString(TEXT("Team Two attack")));
	TestEqual(TEXT("neutral alive order"), Spectator.Alive.ToString(), FString(TEXT("4 v 2")));

	FSSRoundState Over = InProgressRound();
	Over.Phase = ESSRoundPhase::PostRound;
	Over.Outcome = ESSRoundOutcome::TeamOneWon;
	Match.bMatchOver = true;
	Match.MatchWinner = ESSTeamId::TeamOne;
	Match.LastRoundReason = ESSRoundEndReason::TimeExpired;
	FSSObjectiveHudModel End = FSSObjectiveHudModel::Build(Over, nullptr, FText::GetEmpty(), ESSTeamId::TeamTwo);
	End.ApplySectionAssault(Over, Match, ESSTeamId::TeamTwo);
	TestEqual(TEXT("match result from the viewer"), End.PhaseLabel.ToString(), FString(TEXT("Match lost")));
	TestEqual(TEXT("the header is only the reason"), End.Header.ToString(), FString(TEXT("time expired")));
	TestTrue(TEXT("no alive count after the round"), End.Alive.IsEmpty());

	// Every Section Assault string fits the 184 px panel: the longest is kept short by construction.
	for (const FSSObjectiveHudModel* M : { &One, &Two, &Spectator, &End })
	{
		TestTrue(TEXT("round label short"), M->RoundLabel.ToString().Len() <= 9);
		TestTrue(TEXT("phase label short"), M->PhaseLabel.ToString().Len() <= 16);
	}
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
