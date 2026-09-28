// Copyright Southern Spear. All Rights Reserved.

#include "SSServiceEvents.h"

#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "SSCoreLog.h"

void USSServiceEventSubsystem::Post(AController* Player, ESSServiceEvent Event)
{
	const UWorld* World = GetWorld();
	if (!World || World->GetNetMode() == NM_Client || !Player || Event == ESSServiceEvent::None)
	{
		return;
	}
	UE_LOG(LogSSCore, Verbose, TEXT("Service event %s for %s."), LexEvent(Event), *Player->GetName());
	OnServiceEvent.Broadcast(Player, Event);
}

const TCHAR* USSServiceEventSubsystem::LexEvent(ESSServiceEvent Event)
{
	switch (Event)
	{
	case ESSServiceEvent::None:					return TEXT("None");
	case ESSServiceEvent::ObjectiveCaptured:	return TEXT("ObjectiveCaptured");
	case ESSServiceEvent::RoundWon:				return TEXT("RoundWon");
	case ESSServiceEvent::RoundWonAlive:		return TEXT("RoundWonAlive");
	case ESSServiceEvent::MatchCompleted:		return TEXT("MatchCompleted");
	case ESSServiceEvent::MatchWon:				return TEXT("MatchWon");
	case ESSServiceEvent::FriendlyKill:			return TEXT("FriendlyKill");
	case ESSServiceEvent::EnemyKill:			return TEXT("EnemyKill");
	default:									return TEXT("Unknown");
	}
}
