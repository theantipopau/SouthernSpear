// Copyright Southern Spear. All Rights Reserved.

#include "SSObjectiveActor.h"

#include "Components/SphereComponent.h"
#include "GameFramework/Controller.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerState.h"
#include "GenericTeamAgentInterface.h"
#include "Net/UnrealNetwork.h"
#include "SSObjectiveRules.h"
#include "SSSectionAssaultRules.h"
#include "SSTeamIdentityLibrary.h"

namespace
{
	/** The generic team id of a pawn, from the pawn, its controller or its player state. */
	FGenericTeamId GenericTeamOf(const APawn* Pawn)
	{
		if (const IGenericTeamAgentInterface* Agent = Cast<const IGenericTeamAgentInterface>(Pawn))
		{
			if (Agent->GetGenericTeamId() != FGenericTeamId::NoTeam)
			{
				return Agent->GetGenericTeamId();
			}
		}
		if (const IGenericTeamAgentInterface* Agent = Cast<const IGenericTeamAgentInterface>(Pawn->GetController()))
		{
			if (Agent->GetGenericTeamId() != FGenericTeamId::NoTeam)
			{
				return Agent->GetGenericTeamId();
			}
		}
		if (const IGenericTeamAgentInterface* Agent = Cast<const IGenericTeamAgentInterface>(Pawn->GetPlayerState()))
		{
			return Agent->GetGenericTeamId();
		}
		return FGenericTeamId::NoTeam;
	}
}

ASSObjectiveActor::ASSObjectiveActor()
{
	bReplicates = true;
	bAlwaysRelevant = true;
	PrimaryActorTick.bCanEverTick = false;
	SetNetUpdateFrequency(10.f);

	CaptureVolume = CreateDefaultSubobject<USphereComponent>(TEXT("CaptureVolume"));
	CaptureVolume->InitSphereRadius(1000.f);
	CaptureVolume->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	CaptureVolume->SetGenerateOverlapEvents(true);
	CaptureVolume->SetCanEverAffectNavigation(false);
	RootComponent = CaptureVolume;
}

void ASSObjectiveActor::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ASSObjectiveActor, State);
}

float ASSObjectiveActor::GetCaptureRadius() const
{
	return CaptureVolume ? CaptureVolume->GetScaledSphereRadius() : 0.f;
}

void ASSObjectiveActor::CountPresence(int32 TeamOneGenericId, int32 TeamTwoGenericId)
{
	int32 TeamOne = 0;
	int32 TeamTwo = 0;
	TArray<AActor*> Overlapping;
	CaptureVolume->GetOverlappingActors(Overlapping, APawn::StaticClass());
	for (AActor* Actor : Overlapping)
	{
		const APawn* Pawn = CastChecked<APawn>(Actor);
		// A pawn nobody controls (dead, or not yet possessed) does not hold ground.
		if (!Pawn->GetController())
		{
			continue;
		}
		const uint8 Id = GenericTeamOf(Pawn).GetId();
		if (Id == TeamOneGenericId)
		{
			++TeamOne;
		}
		else if (Id == TeamTwoGenericId)
		{
			++TeamTwo;
		}
	}
	LastTeamOneCount = TeamOne;
	LastTeamTwoCount = TeamTwo;
}

void ASSObjectiveActor::ServerStepCapture(float DeltaSeconds, int32 TeamOneGenericId, int32 TeamTwoGenericId)
{
	if (!HasAuthority())
	{
		return;
	}

	CountPresence(TeamOneGenericId, TeamTwoGenericId);

	const FSSObjectiveState Previous = State;
	State = FSSObjectiveRules::StepCapture(State, LastTeamOneCount, LastTeamTwoCount, DeltaSeconds, CaptureRules);

	if (!Previous.IsCaptured() && State.IsCaptured())
	{
		UE_LOG(LogSSObjectives, Log, TEXT("Objective %d '%s' captured by %s."),
			SequenceIndex, *ObjectiveName.ToString(), *FSSTeamIdentity::ToDebugString(State.OwnerTeam));
	}
}

void ASSObjectiveActor::ServerStepAttackCapture(float DeltaSeconds, int32 TeamOneGenericId, int32 TeamTwoGenericId, ESSTeamId Attacker)
{
	if (!HasAuthority())
	{
		return;
	}

	CountPresence(TeamOneGenericId, TeamTwoGenericId);
	const bool bOneAttacks = Attacker == ESSTeamId::TeamOne;
	const int32 Attackers = bOneAttacks ? LastTeamOneCount : LastTeamTwoCount;
	const int32 Defenders = bOneAttacks ? LastTeamTwoCount : LastTeamOneCount;

	const FSSObjectiveState Previous = State;
	State = FSSSectionAssaultRules::StepAttackCapture(State, Attacker, Attackers, Defenders, DeltaSeconds, CaptureRules);

	if (!Previous.IsCaptured() && State.IsCaptured())
	{
		UE_LOG(LogSSObjectives, Log, TEXT("Objective %d '%s' taken by the attackers (%s)."),
			SequenceIndex, *ObjectiveName.ToString(), *FSSTeamIdentity::ToDebugString(State.OwnerTeam));
	}
}

void ASSObjectiveActor::GetPresentControllers(int32 TeamGenericId, TArray<AController*>& OutControllers) const
{
	TArray<AActor*> Overlapping;
	CaptureVolume->GetOverlappingActors(Overlapping, APawn::StaticClass());
	for (AActor* Actor : Overlapping)
	{
		const APawn* Pawn = CastChecked<APawn>(Actor);
		AController* Controller = Pawn->GetController();
		if (Controller && GenericTeamOf(Pawn).GetId() == TeamGenericId)
		{
			OutControllers.AddUnique(Controller);
		}
	}
}

void ASSObjectiveActor::ServerSetState(const FSSObjectiveState& NewState)
{
	if (HasAuthority())
	{
		State = NewState;
	}
}

void ASSObjectiveActor::OnRep_State(const FSSObjectiveState& Previous)
{
	if (!Previous.IsCaptured() && State.IsCaptured())
	{
		UE_LOG(LogSSObjectives, Log, TEXT("[client] Objective %d captured by %s."),
			SequenceIndex, *FSSTeamIdentity::ToDebugString(State.OwnerTeam));
	}
}
