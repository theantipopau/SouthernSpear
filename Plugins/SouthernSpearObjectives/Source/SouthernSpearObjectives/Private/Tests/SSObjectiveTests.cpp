// Copyright Southern Spear. All Rights Reserved.
//
// Objective Assault tests (ADR-018): pure capture and round rules, then a real
// world with a director, two objectives and team pawns.

#include "Tests/SSObjectiveTestPawn.h"

#include "AIController.h"
#include "Components/SphereComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/WorldSettings.h"
#include "Misc/AutomationTest.h"
#include "SSObjectiveActor.h"
#include "SSObjectiveAssaultDirector.h"
#include "SSObjectiveRules.h"
#include "SSTeamIdentityLibrary.h"
#include "UObject/UnrealType.h"

ASSObjectiveTestPawn::ASSObjectiveTestPawn()
{
	Body = CreateDefaultSubobject<USphereComponent>(TEXT("Body"));
	Body->InitSphereRadius(40.f);
	Body->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	Body->SetGenerateOverlapEvents(true);
	RootComponent = Body;
	AutoPossessAI = EAutoPossessAI::Disabled;
}

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	constexpr EAutomationTestFlags SSObjectiveTestFlags =
		EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter;

	FSSObjectiveState Active()
	{
		return FSSObjectiveRules::ResetObjective(true);
	}

	/** Step in fixed 0.1 s frames, as the director does. */
	FSSObjectiveState Run(FSSObjectiveState S, int32 One, int32 Two, float Seconds, const FSSCaptureRules& R)
	{
		for (float T = 0.f; T < Seconds - KINDA_SMALL_NUMBER; T += 0.1f)
		{
			S = FSSObjectiveRules::StepCapture(S, One, Two, 0.1f, R);
		}
		return S;
	}
}

// --- Capture rules ----------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSObjCaptureUncontested, "SouthernSpear.Objectives.Capture.Uncontested", SSObjectiveTestFlags)
bool FSSObjCaptureUncontested::RunTest(const FString& Parameters)
{
	FSSCaptureRules R;
	R.CaptureSeconds = 10.f;

	FSSObjectiveState S = Run(Active(), 1, 0, 9.5f, R);
	TestFalse(TEXT("not captured before CaptureSeconds"), S.IsCaptured());
	TestEqual(TEXT("progress belongs to TeamOne"), S.CapturingTeam, ESSTeamId::TeamOne);

	S = Run(S, 1, 0, 0.6f, R);
	TestEqual(TEXT("captured by TeamOne at CaptureSeconds"), S.OwnerTeam, ESSTeamId::TeamOne);

	// Presence, not strength: five players capture no faster than one.
	const FSSObjectiveState Five = Run(Active(), 5, 0, 5.f, R);
	const FSSObjectiveState One = Run(Active(), 1, 0, 5.f, R);
	TestEqual(TEXT("numbers do not speed capture"), Five.Progress, One.Progress);

	// Locked once captured.
	const FSSObjectiveState After = Run(S, 0, 3, 30.f, R);
	TestEqual(TEXT("captured objective stays with its owner"), After.OwnerTeam, ESSTeamId::TeamOne);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSObjCaptureContestedAndNeutralise, "SouthernSpear.Objectives.Capture.ContestedAndNeutralise", SSObjectiveTestFlags)
bool FSSObjCaptureContestedAndNeutralise::RunTest(const FString& Parameters)
{
	FSSCaptureRules R;
	R.CaptureSeconds = 10.f;

	FSSObjectiveState S = Run(Active(), 1, 0, 5.f, R);
	const float Half = S.Progress;
	S = Run(S, 2, 2, 20.f, R);
	TestTrue(TEXT("contested flag set"), S.bContested);
	TestEqual(TEXT("contested progress frozen"), S.Progress, Half);

	// TeamTwo must first undo TeamOne's 5 s of progress, then build its own 10 s.
	S = Run(S, 0, 1, 5.f, R);
	TestTrue(TEXT("neutralised to zero"), S.Progress < 0.02f);
	TestFalse(TEXT("not captured while neutralising"), S.IsCaptured());
	S = Run(S, 0, 1, 10.1f, R);
	TestEqual(TEXT("TeamTwo captures after neutralising"), S.OwnerTeam, ESSTeamId::TeamTwo);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSObjCaptureDecayAndInvalid, "SouthernSpear.Objectives.Capture.DecayAndInvalidInput", SSObjectiveTestFlags)
bool FSSObjCaptureDecayAndInvalid::RunTest(const FString& Parameters)
{
	FSSCaptureRules R;
	R.CaptureSeconds = 10.f;
	R.DecaySeconds = 10.f;

	FSSObjectiveState S = Run(Active(), 1, 0, 5.f, R);
	S = Run(S, 0, 0, 6.f, R);
	TestEqual(TEXT("empty objective decays to zero"), S.Progress, 0.f);
	TestEqual(TEXT("decayed progress has no owner"), S.CapturingTeam, ESSTeamId::None);

	const FSSObjectiveState Before = Run(Active(), 1, 0, 2.f, R);
	TestEqual(TEXT("negative dt ignored"), FSSObjectiveRules::StepCapture(Before, 1, 0, -1.f, R).Progress, Before.Progress);
	TestEqual(TEXT("NaN dt ignored"), FSSObjectiveRules::StepCapture(Before, 1, 0, NAN, R).Progress, Before.Progress);
	TestEqual(TEXT("inf dt ignored"), FSSObjectiveRules::StepCapture(Before, 1, 0, INFINITY, R).Progress, Before.Progress);

	const FSSObjectiveState Inactive = FSSObjectiveRules::ResetObjective(false);
	TestEqual(TEXT("inactive objective never changes"), Run(Inactive, 1, 0, 30.f, R).Progress, 0.f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSObjCaptureSymmetric, "SouthernSpear.Objectives.Capture.Symmetric", SSObjectiveTestFlags)
bool FSSObjCaptureSymmetric::RunTest(const FString& Parameters)
{
	// Swapping which team does what must mirror the outcome exactly.
	FSSCaptureRules R;
	const int32 Script[][2] = { {1, 0}, {2, 1}, {0, 3}, {0, 0}, {1, 0}, {4, 0} };
	FSSObjectiveState A = Active();
	FSSObjectiveState B = Active();
	for (int32 Pass = 0; Pass < 40; ++Pass)
	{
		const int32* Step = Script[Pass % UE_ARRAY_COUNT(Script)];
		A = FSSObjectiveRules::StepCapture(A, Step[0], Step[1], 0.7f, R);
		B = FSSObjectiveRules::StepCapture(B, Step[1], Step[0], 0.7f, R);
	}
	TestEqual(TEXT("mirrored progress"), A.Progress, B.Progress);
	// GetOpposingTeam(None) is None, so an uncaptured pair also matches.
	TestEqual(TEXT("mirrored owner"), A.OwnerTeam, FSSTeamIdentity::GetOpposingTeam(B.OwnerTeam));
	TestEqual(TEXT("mirrored capturer"), A.CapturingTeam, FSSTeamIdentity::GetOpposingTeam(B.CapturingTeam));
	return true;
}

// --- Round rules ------------------------------------------------------------

namespace
{
	FSSRoundRules QuickRules()
	{
		FSSRoundRules R;
		R.PreRoundSeconds = 1.f;
		R.RoundSeconds = 60.f;
		R.PostRoundSeconds = 2.f;
		return R;
	}

	FSSRoundState Advance(FSSRoundState S, float Seconds, ESSTeamId Captured, const FSSRoundRules& R, FSSRoundEvents& Events)
	{
		Events = FSSRoundEvents();
		for (float T = 0.f; T < Seconds - KINDA_SMALL_NUMBER; T += 0.1f)
		{
			FSSRoundEvents E;
			S = FSSObjectiveRules::StepRound(S, 0.1f, Captured, R, E);
			Events.bRoundStarted |= E.bRoundStarted;
			Events.bObjectiveAdvanced |= E.bObjectiveAdvanced;
			Events.bRoundEnded |= E.bRoundEnded;
			Events.bRoundReset |= E.bRoundReset;
			if (E.bObjectiveAdvanced || E.bRoundEnded)
			{
				Captured = ESSTeamId::None; // the caller would now be on a fresh objective
			}
		}
		return S;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSRoundCompletes, "SouthernSpear.Objectives.Round.CompletesSequentially", SSObjectiveTestFlags)
bool FSSRoundCompletes::RunTest(const FString& Parameters)
{
	const FSSRoundRules R = QuickRules();
	FSSRoundEvents E;
	FSSRoundState S = FSSObjectiveRules::StartRound(FSSRoundState(), 2, R, E);
	TestEqual(TEXT("pre-round first"), S.Phase, ESSRoundPhase::PreRound);
	TestEqual(TEXT("round 1"), S.RoundNumber, 1);

	S = Advance(S, 1.f, ESSTeamId::None, R, E);
	TestEqual(TEXT("in progress after pre-round"), S.Phase, ESSRoundPhase::InProgress);
	TestEqual(TEXT("objective A active"), S.ActiveObjectiveIndex, 0);

	S = Advance(S, 0.1f, ESSTeamId::TeamTwo, R, E);
	TestTrue(TEXT("advanced"), E.bObjectiveAdvanced);
	TestEqual(TEXT("objective B active"), S.ActiveObjectiveIndex, 1);
	TestEqual(TEXT("round not over after A"), S.Phase, ESSRoundPhase::InProgress);

	S = Advance(S, 0.1f, ESSTeamId::TeamOne, R, E);
	TestTrue(TEXT("round ended"), E.bRoundEnded);
	TestEqual(TEXT("final captor wins"), S.Outcome, ESSRoundOutcome::TeamOneWon);
	TestEqual(TEXT("captures counted"), S.TeamOneCaptures + S.TeamTwoCaptures, 2);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSRoundFailsAndRestarts, "SouthernSpear.Objectives.Round.FailsAndRestarts", SSObjectiveTestFlags)
bool FSSRoundFailsAndRestarts::RunTest(const FString& Parameters)
{
	const FSSRoundRules R = QuickRules();
	FSSRoundEvents E;
	FSSRoundState S = FSSObjectiveRules::StartRound(FSSRoundState(), 2, R, E);
	S = Advance(S, 1.f, ESSTeamId::None, R, E);
	S = Advance(S, 60.f, ESSTeamId::None, R, E);
	TestEqual(TEXT("timeout ends the round"), S.Phase, ESSRoundPhase::PostRound);
	TestEqual(TEXT("timeout is a draw"), S.Outcome, ESSRoundOutcome::Draw);

	S = Advance(S, 2.f, ESSTeamId::None, R, E);
	TestTrue(TEXT("reset requested"), E.bRoundReset);
	TestEqual(TEXT("restarted into pre-round"), S.Phase, ESSRoundPhase::PreRound);
	TestEqual(TEXT("round 2"), S.RoundNumber, 2);
	TestEqual(TEXT("outcome cleared"), S.Outcome, ESSRoundOutcome::None);
	TestEqual(TEXT("captures cleared"), S.TeamOneCaptures + S.TeamTwoCaptures, 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSRoundFailsSafely, "SouthernSpear.Objectives.Round.FailsSafely", SSObjectiveTestFlags)
bool FSSRoundFailsSafely::RunTest(const FString& Parameters)
{
	const FSSRoundRules R = QuickRules();
	FSSRoundEvents E;
	FSSRoundState S = FSSObjectiveRules::StartRound(FSSRoundState(), 0, R, E);
	TestEqual(TEXT("no objectives: cannot start"), S.Phase, ESSRoundPhase::WaitingToStart);
	S = Advance(S, 30.f, ESSTeamId::TeamOne, R, E);
	TestEqual(TEXT("stays waiting"), S.Phase, ESSRoundPhase::WaitingToStart);
	TestEqual(TEXT("no outcome invented"), S.Outcome, ESSRoundOutcome::None);

	// A capture reported outside InProgress is ignored.
	FSSRoundState Pre = FSSObjectiveRules::StartRound(FSSRoundState(), 2, R, E);
	Pre = FSSObjectiveRules::StepRound(Pre, 0.1f, ESSTeamId::TeamOne, R, E);
	TestEqual(TEXT("no capture credit in pre-round"), Pre.TeamOneCaptures, 0);

	// A non-playable captor is not a capture.
	FSSRoundState Live = Advance(FSSObjectiveRules::StartRound(FSSRoundState(), 2, R, E), 1.f, ESSTeamId::None, R, E);
	Live = FSSObjectiveRules::StepRound(Live, 0.1f, static_cast<ESSTeamId>(7), R, E);
	TestEqual(TEXT("corrupt team id ignored"), Live.ActiveObjectiveIndex, 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSRoundDeterministic, "SouthernSpear.Objectives.Round.Deterministic", SSObjectiveTestFlags)
bool FSSRoundDeterministic::RunTest(const FString& Parameters)
{
	const FSSRoundRules R = QuickRules();
	auto Play = [&R]()
	{
		FSSRoundEvents E;
		FSSRoundState S = FSSObjectiveRules::StartRound(FSSRoundState(), 2, R, E);
		S = Advance(S, 3.f, ESSTeamId::None, R, E);
		S = Advance(S, 0.1f, ESSTeamId::TeamOne, R, E);
		S = Advance(S, 7.3f, ESSTeamId::None, R, E);
		return S;
	};
	const FSSRoundState A = Play();
	const FSSRoundState B = Play();
	TestTrue(TEXT("same inputs, same state"),
		A.Phase == B.Phase && A.ActiveObjectiveIndex == B.ActiveObjectiveIndex
		&& A.PhaseTimeRemaining == B.PhaseTimeRemaining && A.TeamOneCaptures == B.TeamOneCaptures);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSObjReplicationContract, "SouthernSpear.Objectives.ReplicationContract", SSObjectiveTestFlags)
bool FSSObjReplicationContract::RunTest(const FString& Parameters)
{
	// Server-authoritative state must replicate, and nothing on these types may
	// carry viewer-relative locality.
	const FProperty* ObjState = ASSObjectiveActor::StaticClass()->FindPropertyByName(TEXT("State"));
	const FProperty* RoundState = ASSObjectiveAssaultDirector::StaticClass()->FindPropertyByName(TEXT("RoundState"));
	TestTrue(TEXT("objective State replicates"), ObjState && ObjState->HasAnyPropertyFlags(CPF_Net));
	TestTrue(TEXT("director RoundState replicates"), RoundState && RoundState->HasAnyPropertyFlags(CPF_Net));

	const UEnum* Locality = StaticEnum<ESSLocality>();
	const UStruct* Types[] = {
		FSSObjectiveState::StaticStruct(), FSSRoundState::StaticStruct(),
		ASSObjectiveActor::StaticClass(), ASSObjectiveAssaultDirector::StaticClass() };
	for (const UStruct* Type : Types)
	{
		for (TFieldIterator<FEnumProperty> It(Type); It; ++It)
		{
			TestFalse(*FString::Printf(TEXT("%s.%s is not ESSLocality"), *Type->GetName(), *It->GetName()),
				It->GetEnum() == Locality);
		}
	}
	return true;
}

// --- Real world -----------------------------------------------------------

namespace
{
	ASSObjectiveTestPawn* SpawnSoldier(UWorld* World, const FVector& At, uint8 Team)
	{
		FActorSpawnParameters P;
		P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		ASSObjectiveTestPawn* Pawn = World->SpawnActor<ASSObjectiveTestPawn>(At, FRotator::ZeroRotator, P);
		Pawn->TeamId = FGenericTeamId(Team);
		AAIController* Controller = World->SpawnActor<AAIController>(P);
		Controller->Possess(Pawn);
		return Pawn;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSObjWorldRound, "SouthernSpear.Objectives.World.FullRound", SSObjectiveTestFlags)
bool FSSObjWorldRound::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("SSObjectiveTestWorld"));
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	World->InitializeActorsForPlay(FURL());

	FActorSpawnParameters P;
	P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ASSObjectiveActor* ObjB = World->SpawnActor<ASSObjectiveActor>(FVector(4000, -5200, 0), FRotator::ZeroRotator, P);
	ObjB->SequenceIndex = 1;
	ASSObjectiveActor* ObjA = World->SpawnActor<ASSObjectiveActor>(FVector(-1500, 0, 0), FRotator::ZeroRotator, P);
	ObjA->SequenceIndex = 0;
	ObjA->CaptureRules.CaptureSeconds = 5.f;
	ObjB->CaptureRules.CaptureSeconds = 5.f;

	ASSObjectiveAssaultDirector* Director = World->SpawnActor<ASSObjectiveAssaultDirector>(P);
	Director->RoundRules.PreRoundSeconds = 1.f;
	Director->RoundRules.RoundSeconds = 120.f;
	Director->RoundRules.PostRoundSeconds = 1.f;

	// No GameMode in a bare world, so dispatch BeginPlay the way it would.
	World->GetWorldSettings()->NotifyBeginPlay();

	TestEqual(TEXT("director ordered objectives by SequenceIndex"),
		Director->GetObjectives().Num() == 2 ? Director->GetObjectives()[0].Get() : nullptr, ObjA);

	auto Step = [Director](float Seconds)
	{
		for (float T = 0.f; T < Seconds - KINDA_SMALL_NUMBER; T += 0.1f)
		{
			Director->ServerStep(0.1f);
		}
	};

	Step(1.1f);
	TestEqual(TEXT("round in progress"), Director->GetRoundState().Phase, ESSRoundPhase::InProgress);
	TestTrue(TEXT("A active"), ObjA->GetObjectiveState().bActive);
	TestFalse(TEXT("B inactive"), ObjB->GetObjectiveState().bActive);

	// Contest A: one of each team inside the sphere.
	ASSObjectiveTestPawn* One = SpawnSoldier(World, ObjA->GetActorLocation(), 1);
	ASSObjectiveTestPawn* Two = SpawnSoldier(World, ObjA->GetActorLocation() + FVector(100, 0, 0), 2);
	Step(3.f);
	TestEqual(TEXT("overlap sees TeamOne pawn"), ObjA->GetLastTeamOneCount(), 1);
	TestEqual(TEXT("overlap sees TeamTwo pawn"), ObjA->GetLastTeamTwoCount(), 1);
	TestTrue(TEXT("A contested"), ObjA->GetObjectiveState().bContested);
	TestFalse(TEXT("contested A not captured"), ObjA->GetObjectiveState().IsCaptured());

	// TeamOne leaves; TeamTwo takes A.
	One->SetActorLocation(FVector(0, 20000, 0));
	Step(5.2f);
	TestEqual(TEXT("TeamTwo captured A"), ObjA->GetObjectiveState().OwnerTeam, ESSTeamId::TeamTwo);
	TestEqual(TEXT("play moved to B"), Director->GetRoundState().ActiveObjectiveIndex, 1);
	TestTrue(TEXT("B active"), ObjB->GetObjectiveState().bActive);

	// TeamOne takes B and wins.
	One->SetActorLocation(ObjB->GetActorLocation());
	Two->SetActorLocation(FVector(0, 20000, 0));
	Step(5.2f);
	TestEqual(TEXT("TeamOne won on the final objective"), Director->GetRoundState().Outcome, ESSRoundOutcome::TeamOneWon);
	TestEqual(TEXT("post-round"), Director->GetRoundState().Phase, ESSRoundPhase::PostRound);

	// Restart resets both objectives.
	Step(1.1f);
	TestEqual(TEXT("round 2"), Director->GetRoundState().RoundNumber, 2);
	TestFalse(TEXT("A reset"), ObjA->GetObjectiveState().IsCaptured());
	TestFalse(TEXT("B reset"), ObjB->GetObjectiveState().IsCaptured());

	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSObjWorldNoObjectives, "SouthernSpear.Objectives.World.NoObjectivesFailsVisibly", SSObjectiveTestFlags)
bool FSSObjWorldNoObjectives::RunTest(const FString& Parameters)
{
	AddExpectedError(TEXT("found no ASSObjectiveActor"), EAutomationExpectedErrorFlags::Contains, 1);

	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("SSObjectiveEmptyWorld"));
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	World->InitializeActorsForPlay(FURL());
	FActorSpawnParameters P;
	ASSObjectiveAssaultDirector* Director = World->SpawnActor<ASSObjectiveAssaultDirector>(P);
	// No GameMode in a bare world, so dispatch BeginPlay the way it would.
	World->GetWorldSettings()->NotifyBeginPlay();
	Director->ServerStep(5.f);
	TestEqual(TEXT("director waits instead of inventing a round"),
		Director->GetRoundState().Phase, ESSRoundPhase::WaitingToStart);

	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
