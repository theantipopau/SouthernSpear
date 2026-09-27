// Copyright Southern Spear. All Rights Reserved.

#include "SSDeploymentSpawningComponent.h"

#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "Player/LyraPlayerStart.h"
#include "Teams/LyraTeamSubsystem.h"

USSDeploymentSpawningComponent::USSDeploymentSpawningComponent(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
}

AActor* USSDeploymentSpawningComponent::OnChoosePlayerStart(AController* Player, TArray<ALyraPlayerStart*>& PlayerStarts)
{
	const ULyraTeamSubsystem* Teams = GetWorld() ? GetWorld()->GetSubsystem<ULyraTeamSubsystem>() : nullptr;
	const int32 TeamId = Teams && Player ? Teams->FindTeamFromObject(Player) : INDEX_NONE;
	// Lyra's shooter teams use generic ids 1 and 2 (TeamOne / TeamTwo).
	const FName Wanted = TeamId == 1 ? FName(TEXT("TeamOne")) : TeamId == 2 ? FName(TEXT("TeamTwo")) : NAME_None;
	if (Wanted.IsNone())
	{
		return nullptr; // no team yet: Lyra's default choice
	}

	TArray<ALyraPlayerStart*> Ours;
	for (ALyraPlayerStart* Start : PlayerStarts)
	{
		if (Start && Start->PlayerStartTag == Wanted)
		{
			Ours.Add(Start);
		}
	}
	if (Ours.Num() == 0)
	{
		return nullptr; // map has no tagged deployments
	}
	return GetFirstRandomUnoccupiedPlayerStart(Player, Ours);
}
