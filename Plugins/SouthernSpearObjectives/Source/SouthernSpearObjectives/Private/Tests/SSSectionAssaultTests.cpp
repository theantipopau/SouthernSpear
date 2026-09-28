// Copyright Southern Spear. All Rights Reserved.
//
// Section Assault tests (ADR-031): attacker-only capture, round resolution,
// match scoring and side swaps, then a real world with the director, the Core
// respawn gate and the service event bus.

#include "Tests/SSObjectiveTestPawn.h"

#include "AIController.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/WorldSettings.h"
#include "Misc/AutomationTest.h"
#include "SSObjectiveActor.h"
#include "SSObjectiveAssaultDirector.h"
#include "SSObjectiveRules.h"
#include "SSRespawnGate.h"
#include "SSSectionAssaultRules.h"
#include "SSServiceEvents.h"
#include "SSTeamIdentityLibrary.h"
#include "UObject/UnrealType.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	constexpr EAutomationTestFlags SSSectionTestFlags =
		EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter;

	FSSObjectiveState RunAttack(FSSObjectiveState S, ESSTeamId Attacker, int32 Att, int32 Def, float Seconds, const FSSCaptureRules& R)
	{
		for (float T = 0.f; T < Seconds - KINDA_SMALL_NUMBER; T += 0.1f)
		{
			S = FSSSectionAssaultRules::StepAttackCapture(S, Attacker, Att, Def, 0.1f, R);
		}
		return S;
	}

	FSSSectionInputs Full(int32 PerTeam)
	{
		FSSSectionInputs In;
		In.TeamOneRoster = In.TeamOneAlive = PerTeam;
		In.TeamTwoRoster = In.TeamTwoAlive = PerTeam;
		return In;
	}

	struct FSectionSim
	{
		FSSRoundRules RoundRules;
		FSSSectionRules Rules;
		FSSRoundState Round;
		FSSMatchState Match = FSSSectionAssaultRules::NewMatch();
		FSSRoundEvents Seen;

		FSectionSim()
		{
			RoundRules.PreRoundSeconds = 1.f;
			RoundRules.PostRoundSeconds = 1.f;
			Rules.RoundsPerHalf = 2;
			Rules.RoundSeconds = 30.f;
			Rules.PostMatchSeconds = 2.f;
			FSSRoundEvents E;
			Round = FSSObjectiveRules::StartRound(FSSRoundState(), 2, RoundRules, E);
		}

		void Step(float Seconds, const FSSSectionInputs& In)
		{
			Seen = FSSRoundEvents();
			for (float T = 0.f; T < Seconds - KINDA_SMALL_NUMBER; T += 0.1f)
			{
				FSSRoundEvents E;
				FSSRoundState NextRound;
				FSSMatchState NextMatch;
				FSSSectionAssaultRules::StepRound(Round, Match, 0.1f, In, RoundRules, Rules, NextRound, NextMatch, E);
				Round = NextRound;
				Match = NextMatch;
				Seen.bRoundStarted |= E.bRoundStarted;
				Seen.bObjectiveAdvanced |= E.bObjectiveAdvanced;
				Seen.bRoundEnded |= E.bRoundEnded;
				Seen.bRoundReset |= E.bRoundReset;
				Seen.bMatchEnded |= E.bMatchEnded;
				if (E.bRoundEnded)
				{
					return; // the caller decides what the next round looks like
				}
			}
		}

		/** Play pre-round, then end the round with the given inputs. */
		void PlayRound(const FSSSectionInputs& EndInputs)
		{
			if (Round.Phase == ESSRoundPhase::PostRound)
			{
				Step(RoundRules.PostRoundSeconds + 0.05f, Full(3));
			}
			Step(RoundRules.PreRoundSeconds + 0.05f, Full(3));
			Step(Rules.RoundSeconds + 1.f, EndInputs);
		}
	};
}

// --- Capture ----------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSSectionCaptureAttackersOnly, "SouthernSpear.Objectives.Section.CaptureAttackersOnly", SSSectionTestFlags)
bool FSSSectionCaptureAttackersOnly::RunTest(const FString& Parameters)
{
	FSSCaptureRules R;
	R.CaptureSeconds = 10.f;
	R.DecaySeconds = 20.f;
	const FSSObjectiveState Fresh = FSSObjectiveRules::ResetObjective(true);

	const FSSObjectiveState Held = RunAttack(Fresh, ESSTeamId::TeamOne, 0, 3, 30.f, R);
	TestFalse(TEXT("defenders alone never own the objective"), Held.IsCaptured());
	TestEqual(TEXT("defenders build no progress"), Held.Progress, 0.f);

	FSSObjectiveState S = RunAttack(Fresh, ESSTeamId::TeamOne, 1, 0, 5.f, R);
	TestEqual(TEXT("attackers build progress"), S.CapturingTeam, ESSTeamId::TeamOne);
	const float Half = S.Progress;
	S = RunAttack(S, ESSTeamId::TeamOne, 2, 1, 10.f, R);
	TestTrue(TEXT("both present: contested"), S.bContested);
	TestEqual(TEXT("contested: frozen"), S.Progress, Half);

	const FSSObjectiveState Cleared = RunAttack(S, ESSTeamId::TeamOne, 0, 1, 5.f, R);
	TestTrue(TEXT("defenders clear at the capture rate"), Cleared.Progress < 0.02f);
	const FSSObjectiveState Decayed = RunAttack(S, ESSTeamId::TeamOne, 0, 0, 5.f, R);
	TestTrue(TEXT("an empty point decays more slowly than defenders clear it"), Decayed.Progress > Cleared.Progress + 0.2f);

	const FSSObjectiveState Taken = RunAttack(Fresh, ESSTeamId::TeamTwo, 1, 0, 10.1f, R);
	TestEqual(TEXT("the attacking team takes it"), Taken.OwnerTeam, ESSTeamId::TeamTwo);
	TestEqual(TEXT("numbers do not speed capture"),
		RunAttack(Fresh, ESSTeamId::TeamOne, 5, 0, 4.f, R).Progress, RunAttack(Fresh, ESSTeamId::TeamOne, 1, 0, 4.f, R).Progress);
	TestEqual(TEXT("no attacker: nothing happens"),
		FSSSectionAssaultRules::StepAttackCapture(Fresh, ESSTeamId::None, 3, 0, 1.f, R).Progress, 0.f);
	TestEqual(TEXT("NaN step ignored"), FSSSectionAssaultRules::StepAttackCapture(Fresh, ESSTeamId::TeamOne, 1, 0, NAN, R).Progress, 0.f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSSectionCaptureMirrored, "SouthernSpear.Objectives.Section.CaptureMirrored", SSSectionTestFlags)
bool FSSSectionCaptureMirrored::RunTest(const FString& Parameters)
{
	// The same script with the sides swapped gives the mirrored result: the
	// mode is asymmetric within a round, never between the teams.
	FSSCaptureRules R;
	const int32 Script[][2] = { {1, 0}, {2, 1}, {0, 3}, {0, 0}, {1, 0}, {4, 0} };
	FSSObjectiveState A = FSSObjectiveRules::ResetObjective(true);
	FSSObjectiveState B = A;
	for (int32 Pass = 0; Pass < 40; ++Pass)
	{
		const int32* Step = Script[Pass % UE_ARRAY_COUNT(Script)];
		A = FSSSectionAssaultRules::StepAttackCapture(A, ESSTeamId::TeamOne, Step[0], Step[1], 0.7f, R);
		B = FSSSectionAssaultRules::StepAttackCapture(B, ESSTeamId::TeamTwo, Step[0], Step[1], 0.7f, R);
	}
	TestEqual(TEXT("mirrored progress"), A.Progress, B.Progress);
	TestEqual(TEXT("mirrored owner"), A.OwnerTeam, FSSTeamIdentity::GetOpposingTeam(B.OwnerTeam));
	return true;
}

// --- Round resolution -------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSSectionResolveRound, "SouthernSpear.Objectives.Section.ResolveRound", SSSectionTestFlags)
bool FSSSectionResolveRound::RunTest(const FString& Parameters)
{
	const ESSTeamId A = ESSTeamId::TeamOne;
	ESSTeamId W = ESSTeamId::None;

	TestEqual(TEXT("round goes on"), FSSSectionAssaultRules::ResolveRound(false, 4, 2, 4, 1, false, A, W), ESSRoundEndReason::None);
	TestEqual(TEXT("no winner while it goes on"), W, ESSTeamId::None);

	TestEqual(TEXT("final objective"), FSSSectionAssaultRules::ResolveRound(true, 4, 1, 4, 4, false, A, W), ESSRoundEndReason::ObjectiveTaken);
	TestEqual(TEXT("... attackers win"), W, A);

	// A capture on the step the last attacker dies still counts, as in ADR-018.
	TestEqual(TEXT("capture beats elimination"), FSSSectionAssaultRules::ResolveRound(true, 4, 0, 4, 4, true, A, W), ESSRoundEndReason::ObjectiveTaken);

	TestEqual(TEXT("attackers eliminated"), FSSSectionAssaultRules::ResolveRound(false, 4, 0, 4, 3, false, A, W), ESSRoundEndReason::AttackersEliminated);
	TestEqual(TEXT("... defenders win"), W, ESSTeamId::TeamTwo);

	TestEqual(TEXT("defenders eliminated"), FSSSectionAssaultRules::ResolveRound(false, 4, 1, 4, 0, false, A, W), ESSRoundEndReason::DefendersEliminated);
	TestEqual(TEXT("... attackers win"), W, A);

	TestEqual(TEXT("mutual elimination"), FSSSectionAssaultRules::ResolveRound(false, 4, 0, 4, 0, false, A, W), ESSRoundEndReason::MutualElimination);
	TestEqual(TEXT("... no winner"), W, ESSTeamId::None);

	TestEqual(TEXT("time expired"), FSSSectionAssaultRules::ResolveRound(false, 4, 3, 4, 3, true, A, W), ESSRoundEndReason::TimeExpired);
	TestEqual(TEXT("... defenders win on time"), W, ESSTeamId::TeamTwo);

	// An empty side cannot lose by elimination (a solo playtest is not an instant loss).
	TestEqual(TEXT("empty defender roster: attackers play on"), FSSSectionAssaultRules::ResolveRound(false, 1, 1, 0, 0, false, A, W), ESSRoundEndReason::None);
	TestEqual(TEXT("empty attacker roster: defenders hold to time"), FSSSectionAssaultRules::ResolveRound(false, 0, 0, 2, 2, true, A, W), ESSRoundEndReason::TimeExpired);
	return true;
}

// --- Match ------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSSectionMatchScoring, "SouthernSpear.Objectives.Section.MatchScoringAndSwap", SSSectionTestFlags)
bool FSSSectionMatchScoring::RunTest(const FString& Parameters)
{
	FSSSectionRules R;
	R.RoundsPerHalf = 4;

	TestEqual(TEXT("Team One attacks first"), FSSSectionAssaultRules::NewMatch().AttackingTeam, ESSTeamId::TeamOne);
	TestEqual(TEXT("round 4 (0-based 3): still Team One"), FSSSectionAssaultRules::AttackerForRound(3, R), ESSTeamId::TeamOne);
	TestEqual(TEXT("round 5: sides swap"), FSSSectionAssaultRules::AttackerForRound(4, R), ESSTeamId::TeamTwo);

	// Team One wins all four of its attacks, then the first of Team Two's: 5-0, match over.
	FSSMatchState M = FSSSectionAssaultRules::NewMatch();
	for (int32 Round = 0; Round < 4; ++Round)
	{
		M = FSSSectionAssaultRules::ApplyRoundResult(M, ESSTeamId::TeamOne, ESSRoundEndReason::ObjectiveTaken, R);
	}
	TestFalse(TEXT("4-0 is not yet a win"), M.bMatchOver);
	TestEqual(TEXT("half time: Team Two attacks"), M.AttackingTeam, ESSTeamId::TeamTwo);
	TestEqual(TEXT("second half"), M.Half, 2);
	M = FSSSectionAssaultRules::ApplyRoundResult(M, ESSTeamId::TeamOne, ESSRoundEndReason::AttackersEliminated, R);
	TestTrue(TEXT("first to five"), M.bMatchOver);
	TestEqual(TEXT("Team One wins the match"), M.MatchWinner, ESSTeamId::TeamOne);
	TestEqual(TEXT("reason kept"), M.LastRoundReason, ESSRoundEndReason::AttackersEliminated);

	const FSSMatchState After = FSSSectionAssaultRules::ApplyRoundResult(M, ESSTeamId::TeamTwo, ESSRoundEndReason::TimeExpired, R);
	TestEqual(TEXT("a decided match takes no more rounds"), After.TeamTwoRounds, 0);

	// Four each, then level: a drawn match after both halves.
	FSSMatchState Level = FSSSectionAssaultRules::NewMatch();
	for (int32 Round = 0; Round < 8; ++Round)
	{
		Level = FSSSectionAssaultRules::ApplyRoundResult(Level, Round % 2 ? ESSTeamId::TeamTwo : ESSTeamId::TeamOne, ESSRoundEndReason::TimeExpired, R);
	}
	TestTrue(TEXT("both halves played"), Level.bMatchOver);
	TestEqual(TEXT("4-4 is a drawn match"), Level.MatchWinner, ESSTeamId::None);

	// Drawn rounds count towards the halves but score nothing.
	FSSMatchState Draws = FSSSectionAssaultRules::NewMatch();
	Draws = FSSSectionAssaultRules::ApplyRoundResult(Draws, ESSTeamId::None, ESSRoundEndReason::MutualElimination, R);
	TestEqual(TEXT("a drawn round is played"), Draws.RoundsPlayed, 1);
	TestEqual(TEXT("... and scores nothing"), Draws.TeamOneRounds + Draws.TeamTwoRounds, 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSSectionRoundLoop, "SouthernSpear.Objectives.Section.RoundLoop", SSSectionTestFlags)
bool FSSSectionRoundLoop::RunTest(const FString& Parameters)
{
	FSectionSim Sim; // two rounds a half: first to three

	// Round 1: Team One attacks; time runs out with the objective held.
	Sim.PlayRound(Full(3));
	TestTrue(TEXT("round ended"), Sim.Seen.bRoundEnded);
	TestEqual(TEXT("time: defenders (Team Two) win"), Sim.Round.Outcome, ESSRoundOutcome::TeamTwoWon);
	TestEqual(TEXT("reason recorded"), Sim.Match.LastRoundReason, ESSRoundEndReason::TimeExpired);

	// Round 2: Team One eliminates every defender.
	FSSSectionInputs DefendersDown = Full(3);
	DefendersDown.TeamTwoAlive = 0;
	Sim.PlayRound(DefendersDown);
	TestEqual(TEXT("defenders eliminated: Team One wins"), Sim.Round.Outcome, ESSRoundOutcome::TeamOneWon);
	TestEqual(TEXT("1-1"), Sim.Match.TeamOneRounds * 10 + Sim.Match.TeamTwoRounds, 11);
	TestEqual(TEXT("half time: Team Two attacks next"), Sim.Match.AttackingTeam, ESSTeamId::TeamTwo);

	// Round 3: Team Two attacks and takes objective A, then the final objective B.
	Sim.Step(Sim.RoundRules.PostRoundSeconds + 0.05f, Full(3));
	TestTrue(TEXT("reset between rounds"), Sim.Seen.bRoundReset);
	Sim.Step(Sim.RoundRules.PreRoundSeconds + 0.05f, Full(3));
	TestEqual(TEXT("round 3 in progress"), Sim.Round.Phase, ESSRoundPhase::InProgress);
	FSSSectionInputs Took = Full(3);
	Took.ActiveObjectiveCapturedBy = ESSTeamId::TeamOne; // the defenders cannot own it
	Sim.Step(0.1f, Took);
	TestEqual(TEXT("a defender 'capture' is ignored"), Sim.Round.ActiveObjectiveIndex, 0);
	Took.ActiveObjectiveCapturedBy = ESSTeamId::TeamTwo;
	Sim.Step(0.1f, Took);
	TestTrue(TEXT("attackers advance to B"), Sim.Seen.bObjectiveAdvanced);
	Sim.Step(0.1f, Took);
	TestEqual(TEXT("final objective: Team Two wins"), Sim.Round.Outcome, ESSRoundOutcome::TeamTwoWon);
	TestEqual(TEXT("captures counted for the attackers"), Sim.Round.TeamTwoCaptures, 2);

	// Round 4: Team Two attackers wiped out. 2-2 after both halves: a drawn match.
	FSSSectionInputs AttackersDown = Full(3);
	AttackersDown.TeamTwoAlive = 0;
	Sim.PlayRound(AttackersDown);
	TestTrue(TEXT("match decided"), Sim.Seen.bMatchEnded);
	TestTrue(TEXT("match over"), Sim.Match.bMatchOver);
	TestEqual(TEXT("2-2: drawn"), Sim.Match.MatchWinner, ESSTeamId::None);
	TestEqual(TEXT("post-match hold"), Sim.Round.PhaseTimeRemaining, Sim.Rules.PostMatchSeconds);

	// After the post-match hold a new match starts.
	Sim.Step(Sim.Rules.PostMatchSeconds + 0.05f, Full(3));
	TestTrue(TEXT("reset"), Sim.Seen.bRoundReset);
	TestFalse(TEXT("new match"), Sim.Match.bMatchOver);
	TestEqual(TEXT("scores cleared"), Sim.Match.TeamOneRounds + Sim.Match.TeamTwoRounds + Sim.Match.RoundsPlayed, 0);
	TestEqual(TEXT("Team One attacks again"), Sim.Match.AttackingTeam, ESSTeamId::TeamOne);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSSectionReplicationContract, "SouthernSpear.Objectives.Section.ReplicationContract", SSSectionTestFlags)
bool FSSSectionReplicationContract::RunTest(const FString& Parameters)
{
	const FProperty* Match = ASSObjectiveAssaultDirector::StaticClass()->FindPropertyByName(TEXT("MatchState"));
	TestTrue(TEXT("director MatchState replicates"), Match && Match->HasAnyPropertyFlags(CPF_Net));
	const FProperty* Mode = ASSObjectiveAssaultDirector::StaticClass()->FindPropertyByName(TEXT("RulesMode"));
	TestTrue(TEXT("director RulesMode replicates (client HUDs follow the server's choice)"), Mode && Mode->HasAnyPropertyFlags(CPF_Net));
	const UEnum* Locality = StaticEnum<ESSLocality>();
	for (TFieldIterator<FEnumProperty> It(FSSMatchState::StaticStruct()); It; ++It)
	{
		TestFalse(*FString::Printf(TEXT("FSSMatchState.%s is not ESSLocality"), *It->GetName()), It->GetEnum() == Locality);
	}
	return true;
}

// --- Respawn gate -------------------------------------------------------------

namespace
{
	struct FTestWorld
	{
		UWorld* World = nullptr;

		explicit FTestWorld(const TCHAR* Name)
		{
			World = UWorld::CreateWorld(EWorldType::Game, false, Name);
			FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
			Context.SetCurrentWorld(World);
			World->InitializeActorsForPlay(FURL());
		}

		~FTestWorld()
		{
			GEngine->DestroyWorldContext(World);
			World->DestroyWorld(false);
		}

		AAIController* Soldier(const FVector& At, uint8 Team)
		{
			FActorSpawnParameters P;
			P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			ASSObjectiveTestPawn* Pawn = World->SpawnActor<ASSObjectiveTestPawn>(At, FRotator::ZeroRotator, P);
			Pawn->TeamId = FGenericTeamId(Team);
			AAIController* Controller = World->SpawnActor<AAIController>(P);
			Controller->Possess(Pawn);
			return Controller;
		}
	};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSSectionRespawnGate, "SouthernSpear.Objectives.Section.RespawnGate", SSSectionTestFlags)
bool FSSSectionRespawnGate::RunTest(const FString& Parameters)
{
	FTestWorld W(TEXT("SSRespawnGateWorld"));
	USSRespawnGate* Gate = W.World->GetSubsystem<USSRespawnGate>();
	if (!TestNotNull(TEXT("gate exists in a game world"), Gate))
	{
		return false;
	}
	AAIController* A = W.Soldier(FVector::ZeroVector, 1);
	AAIController* B = W.Soldier(FVector(500, 0, 0), 2);
	AAIController* Late = W.Soldier(FVector(900, 0, 0), 1);

	TestFalse(TEXT("unlocked holds nobody"), Gate->MustHoldOut(A));
	Gate->ReportElimination(A);
	TestFalse(TEXT("unlocked ignores eliminations"), Gate->IsEliminated(A));

	Gate->Lock(TArray<AController*>{ A, B });
	TestTrue(TEXT("A alive"), Gate->IsAlive(A));
	TestTrue(TEXT("a mid-round joiner waits"), Gate->MustHoldOut(Late));
	Gate->ReportElimination(A);
	Gate->ReportElimination(A);
	TestTrue(TEXT("eliminated A is held out"), Gate->MustHoldOut(A));
	TestEqual(TEXT("an elimination counts once"), Gate->GetEliminatedCount(), 1);
	Gate->ReportElimination(Late);
	TestEqual(TEXT("off-roster eliminations are ignored"), Gate->GetEliminatedCount(), 1);
	TestFalse(TEXT("B still in"), Gate->MustHoldOut(B));

	Gate->Unlock();
	TestFalse(TEXT("after the reset everyone may spawn"), Gate->MustHoldOut(A) || Gate->MustHoldOut(Late));
	return true;
}

// --- Real world ---------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSSectionWorldRound, "SouthernSpear.Objectives.Section.World.EliminationAndEvents", SSSectionTestFlags)
bool FSSSectionWorldRound::RunTest(const FString& Parameters)
{
	FTestWorld W(TEXT("SSSectionTestWorld"));
	UWorld* World = W.World;

	FActorSpawnParameters P;
	P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ASSObjectiveActor* Obj = World->SpawnActor<ASSObjectiveActor>(FVector::ZeroVector, FRotator::ZeroRotator, P);
	Obj->SequenceIndex = 0;
	Obj->CaptureRules.CaptureSeconds = 5.f;

	ASSObjectiveAssaultDirector* Director = World->SpawnActor<ASSObjectiveAssaultDirector>(P);
	Director->RulesMode = ESSAssaultRules::SectionAssault;
	Director->RoundRules.PreRoundSeconds = 1.f;
	Director->RoundRules.PostRoundSeconds = 1.f;
	Director->SectionRules.RoundSeconds = 60.f;
	Director->SectionRules.RoundsPerHalf = 2;
	Director->bRespawnAllOnRoundReset = false; // no GameMode in a bare world

	TMap<ESSServiceEvent, int32> Posted;
	USSServiceEventSubsystem* Bus = World->GetSubsystem<USSServiceEventSubsystem>();
	Bus->OnServiceEvent.AddLambda([&Posted](AController*, ESSServiceEvent Event) { Posted.FindOrAdd(Event)++; });

	// Two attackers (Team One) away from the point, one defender (Team Two).
	AAIController* Att1 = W.Soldier(FVector(0, 20000, 0), 1);
	AAIController* Att2 = W.Soldier(FVector(0, 21000, 0), 1);
	AAIController* Def = W.Soldier(FVector(0, -20000, 0), 2);

	World->GetWorldSettings()->NotifyBeginPlay();
	auto Step = [Director](float Seconds)
	{
		for (float T = 0.f; T < Seconds - KINDA_SMALL_NUMBER; T += 0.1f)
		{
			Director->ServerStep(0.1f);
		}
	};

	Step(1.1f);
	TestEqual(TEXT("in progress"), Director->GetRoundState().Phase, ESSRoundPhase::InProgress);
	USSRespawnGate* Gate = World->GetSubsystem<USSRespawnGate>();
	TestTrue(TEXT("gate locked for the round"), Gate->IsLocked());
	TestEqual(TEXT("roster is everyone alive"), Gate->GetRosterCount(), 3);

	// The defender stands on the point alone: no capture.
	Def->GetPawn()->SetActorLocation(Obj->GetActorLocation());
	Step(6.f);
	TestFalse(TEXT("defender alone does not capture"), Obj->GetObjectiveState().IsCaptured());

	// The defender is eliminated (as the Lyra bridge would report it): attackers win.
	Def->GetPawn()->SetActorLocation(FVector(0, -20000, 0));
	Gate->ReportElimination(Def);
	Step(0.2f);
	TestEqual(TEXT("defenders eliminated: Team One wins"), Director->GetRoundState().Outcome, ESSRoundOutcome::TeamOneWon);
	TestEqual(TEXT("match score 1-0"), Director->GetMatchState().TeamOneRounds, 1);
	TestEqual(TEXT("both attackers credited"), Posted.FindRef(ESSServiceEvent::RoundWon), 2);
	TestEqual(TEXT("both attackers alive"), Posted.FindRef(ESSServiceEvent::RoundWonAlive), 2);

	// Reset unlocks the gate.
	Step(1.1f);
	TestFalse(TEXT("reset unlocks the gate"), Gate->IsLocked());

	// Round 2: Team One attacks again (two rounds a half); one attacker takes the point.
	Step(1.1f);
	TestEqual(TEXT("round 2 attacker"), Director->GetMatchState().AttackingTeam, ESSTeamId::TeamOne);
	Att1->GetPawn()->SetActorLocation(Obj->GetActorLocation());
	Step(5.2f);
	TestEqual(TEXT("attackers took the final objective"), Director->GetRoundState().Outcome, ESSRoundOutcome::TeamOneWon);
	TestEqual(TEXT("reason"), Director->GetMatchState().LastRoundReason, ESSRoundEndReason::ObjectiveTaken);
	TestEqual(TEXT("capture credited to the one on the point"), Posted.FindRef(ESSServiceEvent::ObjectiveCaptured), 1);
	TestEqual(TEXT("sides swap for round 3"), Director->GetMatchState().AttackingTeam, ESSTeamId::TeamTwo);
	TestNotNull(TEXT("second attacker still present"), Att2);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
