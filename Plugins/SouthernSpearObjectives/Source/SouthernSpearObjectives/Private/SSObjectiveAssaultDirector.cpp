// Copyright Southern Spear. All Rights Reserved.

#include "SSObjectiveAssaultDirector.h"

#include "AIController.h"
#include "Navigation/PathFollowingComponent.h"
#include "BehaviorTree/BlackboardComponent.h"
#include "EngineUtils.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerState.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"
#include "Net/UnrealNetwork.h"
#include "SSObjectiveActor.h"
#include "SSObjectiveRules.h"
#include "SSRespawnGate.h"
#include "SSSectionAssaultRules.h"
#include "SSServiceEvents.h"
#include "SSTeamIdentityLibrary.h"

ASSObjectiveAssaultDirector::ASSObjectiveAssaultDirector()
{
	bReplicates = true;
	bAlwaysRelevant = true;
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.1f;
	SetNetUpdateFrequency(5.f);
}

void ASSObjectiveAssaultDirector::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ASSObjectiveAssaultDirector, RoundState);
	DOREPLIFETIME(ASSObjectiveAssaultDirector, MatchState);
	DOREPLIFETIME(ASSObjectiveAssaultDirector, RulesMode);
}

bool ASSObjectiveAssaultDirector::GatherObjectives()
{
	Objectives.Reset();
	UWorld* World = GetWorld();
	if (!World)
	{
		return false;
	}
	for (TActorIterator<ASSObjectiveActor> It(World); It; ++It)
	{
		Objectives.Add(*It);
	}
	Objectives.Sort([](const ASSObjectiveActor& A, const ASSObjectiveActor& B)
	{
		return A.SequenceIndex < B.SequenceIndex;
	});

	if (Objectives.Num() == 0)
	{
		UE_LOG(LogSSObjectives, Error,
			TEXT("Objective Assault director '%s' found no ASSObjectiveActor in the level. ")
			TEXT("The round cannot start."), *GetName());
		return false;
	}
	for (int32 Index = 1; Index < Objectives.Num(); ++Index)
	{
		if (Objectives[Index]->SequenceIndex == Objectives[Index - 1]->SequenceIndex)
		{
			UE_LOG(LogSSObjectives, Error,
				TEXT("Objectives '%s' and '%s' share SequenceIndex %d. The sequence is ambiguous; ")
				TEXT("refusing to start rather than picking one."),
				*Objectives[Index - 1]->GetName(), *Objectives[Index]->GetName(), Objectives[Index]->SequenceIndex);
			Objectives.Reset();
			return false;
		}
	}
	UE_LOG(LogSSObjectives, Log, TEXT("Objective Assault: %d objective(s) in sequence."), Objectives.Num());
	return true;
}

void ASSObjectiveAssaultDirector::BeginPlay()
{
	Super::BeginPlay();

	const bool bOk = GatherObjectives();
	if (!HasAuthority())
	{
		return;
	}
	if (TeamOneGenericId == TeamTwoGenericId)
	{
		UE_LOG(LogSSObjectives, Error,
			TEXT("Director '%s': TeamOneGenericId and TeamTwoGenericId are both %d. ")
			TEXT("Both teams would count as one; refusing to start."), *GetName(), TeamOneGenericId);
		return;
	}

	// Playtest overrides from the map URL, e.g. ?Rules=Section?RoundSeconds=60
	if (const AGameModeBase* GameMode = GetWorld()->GetAuthGameMode())
	{
		const FString& Options = GameMode->OptionsString;
		const FString Rules = UGameplayStatics::ParseOption(Options, TEXT("Rules"));
		if (Rules.Equals(TEXT("Section"), ESearchCase::IgnoreCase))
		{
			RulesMode = ESSAssaultRules::SectionAssault;
		}
		else if (Rules.Equals(TEXT("Objective"), ESearchCase::IgnoreCase))
		{
			RulesMode = ESSAssaultRules::ObjectiveAssault;
		}
		else if (!Rules.IsEmpty())
		{
			UE_LOG(LogSSObjectives, Error, TEXT("Unknown ?Rules=%s (expected Section or Objective); keeping %s."),
				*Rules, IsSectionAssault() ? TEXT("Section Assault") : TEXT("Objective Assault"));
		}
		float& PlaySeconds = IsSectionAssault() ? SectionRules.RoundSeconds : RoundRules.RoundSeconds;
		PlaySeconds = UGameplayStatics::GetIntOption(Options, TEXT("RoundSeconds"), FMath::RoundToInt(PlaySeconds));
		RoundRules.PreRoundSeconds = UGameplayStatics::GetIntOption(Options, TEXT("PreRoundSeconds"), FMath::RoundToInt(RoundRules.PreRoundSeconds));
		RoundRules.PostRoundSeconds = UGameplayStatics::GetIntOption(Options, TEXT("PostRoundSeconds"), FMath::RoundToInt(RoundRules.PostRoundSeconds));
		SectionRules.RoundsPerHalf = FMath::Max(1, UGameplayStatics::GetIntOption(Options, TEXT("RoundsPerHalf"), SectionRules.RoundsPerHalf));
	}

	if (IsSectionAssault())
	{
		MatchState = FSSSectionAssaultRules::NewMatch();
		UE_LOG(LogSSObjectives, Log, TEXT("Section Assault (ADR-031): one life per round, %d round(s) per half, %.0f s rounds."),
			SectionRules.RoundsPerHalf, SectionRules.RoundSeconds);
	}

	FSSRoundEvents Events;
	const FSSRoundState Previous = RoundState;
	RoundState = FSSObjectiveRules::StartRound(RoundState, bOk ? Objectives.Num() : 0, RoundRules, Events);
	LogTransition(Previous);
	ApplyEvents(Events);
}

void ASSObjectiveAssaultDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (HasAuthority())
	{
		ServerStep(DeltaSeconds);
	}
}

void ASSObjectiveAssaultDirector::ServerStep(float DeltaSeconds)
{
	if (IsSectionAssault())
	{
		ServerStepSectionAssault(DeltaSeconds);
	}
	else
	{
		ServerStepObjectiveAssault(DeltaSeconds);
	}
}

void ASSObjectiveAssaultDirector::SteerIfDue(float DeltaSeconds)
{
	if (bSteerIdleBotsToObjective && RoundState.Phase == ESSRoundPhase::InProgress)
	{
		SteerAccumulator += DeltaSeconds;
		if (SteerAccumulator >= BotSteerInterval)
		{
			SteerAccumulator = 0.f;
			SteerIdleBots();
		}
	}
}

void ASSObjectiveAssaultDirector::ServerStepObjectiveAssault(float DeltaSeconds)
{
	ESSTeamId CapturedBy = ESSTeamId::None;
	if (RoundState.Phase == ESSRoundPhase::InProgress && Objectives.IsValidIndex(RoundState.ActiveObjectiveIndex))
	{
		ASSObjectiveActor* Active = Objectives[RoundState.ActiveObjectiveIndex];
		Active->ServerStepCapture(DeltaSeconds, TeamOneGenericId, TeamTwoGenericId);
		CapturedBy = Active->GetObjectiveState().OwnerTeam;
		if (FSSTeamIdentity::IsPlayableTeam(CapturedBy))
		{
			PostCaptureEvents(Active, CapturedBy);
		}
	}

	SteerIfDue(DeltaSeconds);

	FSSRoundEvents Events;
	const FSSRoundState Previous = RoundState;
	RoundState = FSSObjectiveRules::StepRound(RoundState, DeltaSeconds, CapturedBy, RoundRules, Events);
	LogTransition(Previous);
	if (Events.bRoundEnded)
	{
		const ESSTeamId Winner = RoundState.Outcome == ESSRoundOutcome::TeamOneWon ? ESSTeamId::TeamOne
			: RoundState.Outcome == ESSRoundOutcome::TeamTwoWon ? ESSTeamId::TeamTwo : ESSTeamId::None;
		PostRoundEndEvents(Winner, false, ESSTeamId::None);
	}
	ApplyEvents(Events);
}

void ASSObjectiveAssaultDirector::ServerStepSectionAssault(float DeltaSeconds)
{
	const ESSTeamId Attacker = MatchState.AttackingTeam;
	ESSTeamId CapturedBy = ESSTeamId::None;
	if (RoundState.Phase == ESSRoundPhase::InProgress && Objectives.IsValidIndex(RoundState.ActiveObjectiveIndex))
	{
		ASSObjectiveActor* Active = Objectives[RoundState.ActiveObjectiveIndex];
		Active->ServerStepAttackCapture(DeltaSeconds, TeamOneGenericId, TeamTwoGenericId, Attacker);
		CapturedBy = Active->GetObjectiveState().OwnerTeam;
		if (FSSTeamIdentity::IsPlayableTeam(CapturedBy))
		{
			PostCaptureEvents(Active, CapturedBy);
		}
	}

	SteerIfDue(DeltaSeconds);

	FSSSectionInputs Inputs;
	Inputs.ActiveObjectiveCapturedBy = CapturedBy;
	GatherSectionInputs(Inputs);

	FSSRoundEvents Events;
	const FSSRoundState Previous = RoundState;
	FSSRoundState NextRound;
	FSSMatchState NextMatch;
	FSSSectionAssaultRules::StepRound(RoundState, MatchState, DeltaSeconds, Inputs, RoundRules, SectionRules,
		NextRound, NextMatch, Events);
	RoundState = NextRound;
	MatchState = NextMatch;
	LogTransition(Previous);

	if (Events.bRoundStarted)
	{
		LockRespawnGate();
	}
	if (Events.bRoundEnded)
	{
		const ESSTeamId Winner = RoundState.Outcome == ESSRoundOutcome::TeamOneWon ? ESSTeamId::TeamOne
			: RoundState.Outcome == ESSRoundOutcome::TeamTwoWon ? ESSTeamId::TeamTwo : ESSTeamId::None;
		const FString MatchNote = Events.bMatchEnded
			? FString::Printf(TEXT(" Match over: %s."), *FSSTeamIdentity::ToDebugString(MatchState.MatchWinner)) : FString();
		UE_LOG(LogSSObjectives, Log, TEXT("Section Assault round %d: %s attacked, %s (%s). Score T1=%d T2=%d.%s"),
			RoundState.RoundNumber, *FSSTeamIdentity::ToDebugString(Attacker),
			FSSObjectiveRules::LexOutcome(RoundState.Outcome), FSSSectionAssaultRules::LexReason(MatchState.LastRoundReason),
			MatchState.TeamOneRounds, MatchState.TeamTwoRounds, *MatchNote);
		// Before the reset unlocks the gate: RoundWonAlive reads who is still alive.
		PostRoundEndEvents(Winner, Events.bMatchEnded, MatchState.MatchWinner);
	}
	ApplyEvents(Events);
}

void ASSObjectiveAssaultDirector::ApplyEvents(const FSSRoundEvents& Events)
{
	if (Events.bRoundReset)
	{
		for (ASSObjectiveActor* Objective : Objectives)
		{
			Objective->ServerSetState(FSSObjectiveRules::ResetObjective(false));
		}
		// Everyone may spawn again before the respawn below asks for pawns.
		if (USSRespawnGate* Gate = GetWorld() ? GetWorld()->GetSubsystem<USSRespawnGate>() : nullptr)
		{
			Gate->Unlock();
		}
		// Round 1 players are freshly spawned already; later rounds need it.
		if (bRespawnAllOnRoundReset && RoundState.RoundNumber > 1)
		{
			RespawnAllPlayers();
		}
	}
	if (Events.bRoundStarted || Events.bObjectiveAdvanced)
	{
		// Steer on the next step rather than waiting a full interval.
		SteerAccumulator = BotSteerInterval;
	}
	if ((Events.bRoundStarted || Events.bObjectiveAdvanced) && Objectives.IsValidIndex(RoundState.ActiveObjectiveIndex))
	{
		for (int32 Index = 0; Index < Objectives.Num(); ++Index)
		{
			FSSObjectiveState State = Objectives[Index]->GetObjectiveState();
			State.bActive = Index == RoundState.ActiveObjectiveIndex;
			Objectives[Index]->ServerSetState(State);
		}
	}
	if (Events.bRoundEnded)
	{
		for (ASSObjectiveActor* Objective : Objectives)
		{
			FSSObjectiveState State = Objective->GetObjectiveState();
			State.bActive = false;
			Objective->ServerSetState(State);
		}
	}
}

void ASSObjectiveAssaultDirector::LogTransition(const FSSRoundState& Previous) const
{
	if (Previous.Phase == RoundState.Phase && Previous.ActiveObjectiveIndex == RoundState.ActiveObjectiveIndex
		&& Previous.RoundNumber == RoundState.RoundNumber)
	{
		return;
	}
	UE_LOG(LogSSObjectives, Log,
		TEXT("Round %d: %s -> %s, objective %d/%d, outcome %s, captures T1=%d T2=%d."),
		RoundState.RoundNumber, FSSObjectiveRules::LexPhase(Previous.Phase), FSSObjectiveRules::LexPhase(RoundState.Phase),
		RoundState.ActiveObjectiveIndex, RoundState.NumObjectives, FSSObjectiveRules::LexOutcome(RoundState.Outcome),
		RoundState.TeamOneCaptures, RoundState.TeamTwoCaptures);
}

void ASSObjectiveAssaultDirector::OnRep_RoundState(const FSSRoundState& Previous)
{
	LogTransition(Previous);
}

int32 ASSObjectiveAssaultDirector::SteerIdleBots()
{
	LastSteeredBotCount = 0;
	UWorld* World = GetWorld();
	if (!HasAuthority() || !World || RoundState.Phase != ESSRoundPhase::InProgress
		|| !Objectives.IsValidIndex(RoundState.ActiveObjectiveIndex))
	{
		return 0;
	}

	const ASSObjectiveActor* Target = Objectives[RoundState.ActiveObjectiveIndex];
	const FVector Centre = Target->GetActorLocation();
	const float Radius = Target->GetCaptureRadius();

	for (FConstControllerIterator It = World->GetControllerIterator(); It; ++It)
	{
		AAIController* Bot = Cast<AAIController>(It->Get());
		APawn* Pawn = Bot ? Bot->GetPawn() : nullptr;
		if (!Pawn)
		{
			continue;
		}
		if (const UBlackboardComponent* Blackboard = Bot->GetBlackboardComponent())
		{
			const FBlackboard::FKey Key = Blackboard->GetKeyID(BotBusyBlackboardKey);
			if (Key != FBlackboard::InvalidKey && Blackboard->GetValueAsObject(BotBusyBlackboardKey) != nullptr)
			{
				continue; // fighting; its behaviour tree owns movement
			}
		}
		if (FVector::Dist2D(Pawn->GetActorLocation(), Centre) <= Radius * 0.6f)
		{
			continue; // already holding the objective
		}

		// Spread bots around the objective deterministically, so they do not
		// all queue for the same point.
		const float Angle = static_cast<float>(GetTypeHash(Bot->GetFName()) % 360) * (PI / 180.f);
		const FVector Goal = Centre + FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.f) * (Radius * 0.4f);
		if (Bot->MoveToLocation(Goal, 100.f) != EPathFollowingRequestResult::Failed)
		{
			++LastSteeredBotCount;
		}
	}
	// Log only on change, so a long match does not flood the log.
	const int32 Signature = LastSteeredBotCount * 100 + RoundState.ActiveObjectiveIndex;
	if (Signature != LastSteerLogSignature)
	{
		LastSteerLogSignature = Signature;
		UE_LOG(LogSSObjectives, Log, TEXT("Steered %d idle bot(s) to objective %d."),
			LastSteeredBotCount, RoundState.ActiveObjectiveIndex);
	}
	return LastSteeredBotCount;
}

int32 ASSObjectiveAssaultDirector::RespawnAllPlayers()
{
	UWorld* World = GetWorld();
	if (!HasAuthority() || !World || !World->GetAuthGameMode())
	{
		return 0;
	}
	PendingRespawn.Reset();
	// Section Assault held Lyra's own respawn off all round, so the dead (bots
	// included) have nothing pending and are restarted here too.
	bPendingRestartIncludesBots = IsSectionAssault();
	for (FConstControllerIterator It = World->GetControllerIterator(); It; ++It)
	{
		AController* Controller = It->Get();
		if (!Controller)
		{
			continue;
		}
		if (Controller->GetPawn())
		{
			PendingRespawn.Add(Controller);
			Controller->GetPawn()->Destroy();
		}
		else if (bPendingRestartIncludesBots && FSSTeamIdentity::IsPlayableTeam(TeamOfController(Controller)))
		{
			PendingRespawn.Add(Controller);
		}
	}
	// The game mode normally restarts a controller whose pawn is destroyed.
	// After a second, restart any player controller it did not.
	FTimerHandle Handle;
	World->GetTimerManager().SetTimer(Handle, this, &ThisClass::RestartPawnlessControllers, 1.f, false);
	UE_LOG(LogSSObjectives, Log, TEXT("Round reset: sending %d player(s) back to deployment."), PendingRespawn.Num());
	return PendingRespawn.Num();
}

void ASSObjectiveAssaultDirector::RestartPawnlessControllers()
{
	AGameModeBase* GameMode = GetWorld() ? GetWorld()->GetAuthGameMode() : nullptr;
	int32 Restarted = 0;
	for (const TWeakObjectPtr<AController>& Weak : PendingRespawn)
	{
		AController* Controller = Weak.Get();
		// In Objective Assault AI controllers are left to their own respawn path
		// (Lyra bots may already have one pending from a death), so only players
		// get this. Section Assault suppressed that path, so bots get it too.
		if (GameMode && Controller && (Controller->IsPlayerController() || bPendingRestartIncludesBots) && !Controller->GetPawn())
		{
			GameMode->RestartPlayer(Controller);
			++Restarted;
		}
	}
	PendingRespawn.Reset();
	UE_LOG(LogSSObjectives, Log, TEXT("Round reset: restarted %d controller(s) directly."), Restarted);
}

ESSTeamId ASSObjectiveAssaultDirector::ToTeamId(FGenericTeamId GenericId) const
{
	if (GenericId == FGenericTeamId(static_cast<uint8>(TeamOneGenericId)))
	{
		return ESSTeamId::TeamOne;
	}
	if (GenericId == FGenericTeamId(static_cast<uint8>(TeamTwoGenericId)))
	{
		return ESSTeamId::TeamTwo;
	}
	return ESSTeamId::None;
}

ESSTeamId ASSObjectiveAssaultDirector::TeamOfController(const AController* Controller) const
{
	if (!Controller)
	{
		return ESSTeamId::None;
	}
	const UObject* Sources[] = { Controller, Controller->PlayerState.Get(), Controller->GetPawn() };
	for (const UObject* Source : Sources)
	{
		if (const IGenericTeamAgentInterface* Agent = Cast<const IGenericTeamAgentInterface>(Source))
		{
			if (Agent->GetGenericTeamId() != FGenericTeamId::NoTeam)
			{
				return ToTeamId(Agent->GetGenericTeamId());
			}
		}
	}
	return ESSTeamId::None;
}

int32 ASSObjectiveAssaultDirector::GenericIdOf(ESSTeamId Team) const
{
	return Team == ESSTeamId::TeamOne ? TeamOneGenericId : Team == ESSTeamId::TeamTwo ? TeamTwoGenericId : INDEX_NONE;
}

void ASSObjectiveAssaultDirector::GatherSectionInputs(FSSSectionInputs& Inputs) const
{
	const UWorld* World = GetWorld();
	const USSRespawnGate* Gate = World ? World->GetSubsystem<USSRespawnGate>() : nullptr;
	if (!World || !Gate || !Gate->IsLocked())
	{
		return;
	}
	for (FConstControllerIterator It = World->GetControllerIterator(); It; ++It)
	{
		const AController* Controller = It->Get();
		if (!Controller || !Gate->IsOnRoster(Controller))
		{
			continue;
		}
		const ESSTeamId Team = TeamOfController(Controller);
		const bool bAlive = Gate->IsAlive(Controller);
		if (Team == ESSTeamId::TeamOne)
		{
			++Inputs.TeamOneRoster;
			Inputs.TeamOneAlive += bAlive ? 1 : 0;
		}
		else if (Team == ESSTeamId::TeamTwo)
		{
			++Inputs.TeamTwoRoster;
			Inputs.TeamTwoAlive += bAlive ? 1 : 0;
		}
	}
}

void ASSObjectiveAssaultDirector::LockRespawnGate()
{
	UWorld* World = GetWorld();
	USSRespawnGate* Gate = World ? World->GetSubsystem<USSRespawnGate>() : nullptr;
	if (!Gate)
	{
		UE_LOG(LogSSObjectives, Error, TEXT("Section Assault: no respawn gate in this world; the round has no roster."));
		return;
	}
	TArray<AController*> Roster;
	for (FConstControllerIterator It = World->GetControllerIterator(); It; ++It)
	{
		AController* Controller = It->Get();
		if (Controller && Controller->GetPawn() && FSSTeamIdentity::IsPlayableTeam(TeamOfController(Controller)))
		{
			Roster.Add(Controller);
		}
	}
	Gate->Lock(Roster);
}

void ASSObjectiveAssaultDirector::PostCaptureEvents(const ASSObjectiveActor* Objective, ESSTeamId Captor)
{
	USSServiceEventSubsystem* Bus = GetWorld() ? GetWorld()->GetSubsystem<USSServiceEventSubsystem>() : nullptr;
	if (!Bus || !Objective)
	{
		return;
	}
	TArray<AController*> Present;
	Objective->GetPresentControllers(GenericIdOf(Captor), Present);
	for (AController* Controller : Present)
	{
		Bus->Post(Controller, ESSServiceEvent::ObjectiveCaptured);
	}
}

void ASSObjectiveAssaultDirector::PostRoundEndEvents(ESSTeamId Winner, bool bMatchEnded, ESSTeamId MatchWinner)
{
	UWorld* World = GetWorld();
	USSServiceEventSubsystem* Bus = World ? World->GetSubsystem<USSServiceEventSubsystem>() : nullptr;
	if (!Bus)
	{
		return;
	}
	const USSRespawnGate* Gate = World->GetSubsystem<USSRespawnGate>();
	const bool bRoster = IsSectionAssault() && Gate && Gate->IsLocked();
	for (FConstControllerIterator It = World->GetControllerIterator(); It; ++It)
	{
		AController* Controller = It->Get();
		const ESSTeamId Team = TeamOfController(Controller);
		if (!Controller || !FSSTeamIdentity::IsPlayableTeam(Team))
		{
			continue;
		}
		// Section Assault credits the round to the players who started it; a
		// mid-round joiner earns from the next one.
		const bool bPlayedRound = !bRoster || Gate->IsOnRoster(Controller);
		if (bPlayedRound && Team == Winner)
		{
			Bus->Post(Controller, ESSServiceEvent::RoundWon);
			if (bRoster && Gate->IsAlive(Controller))
			{
				Bus->Post(Controller, ESSServiceEvent::RoundWonAlive);
			}
		}
		if (bMatchEnded)
		{
			// MatchCompleted goes last: progression closes the player's match tally on it.
			if (Team == MatchWinner)
			{
				Bus->Post(Controller, ESSServiceEvent::MatchWon);
			}
			Bus->Post(Controller, ESSServiceEvent::MatchCompleted);
		}
	}
}
