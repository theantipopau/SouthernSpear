// Copyright Southern Spear. All Rights Reserved.

#include "SSObjectiveAssaultDirector.h"

#include "EngineUtils.h"
#include "Net/UnrealNetwork.h"
#include "SSObjectiveActor.h"
#include "SSObjectiveRules.h"
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
	ESSTeamId CapturedBy = ESSTeamId::None;
	if (RoundState.Phase == ESSRoundPhase::InProgress && Objectives.IsValidIndex(RoundState.ActiveObjectiveIndex))
	{
		ASSObjectiveActor* Active = Objectives[RoundState.ActiveObjectiveIndex];
		Active->ServerStepCapture(DeltaSeconds, TeamOneGenericId, TeamTwoGenericId);
		CapturedBy = Active->GetObjectiveState().OwnerTeam;
	}

	FSSRoundEvents Events;
	const FSSRoundState Previous = RoundState;
	RoundState = FSSObjectiveRules::StepRound(RoundState, DeltaSeconds, CapturedBy, RoundRules, Events);
	LogTransition(Previous);
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
