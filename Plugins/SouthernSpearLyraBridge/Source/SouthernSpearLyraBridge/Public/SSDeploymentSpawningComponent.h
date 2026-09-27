// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Player/LyraPlayerSpawningManagerComponent.h"
#include "SSDeploymentSpawningComponent.generated.h"

/**
 * Server: team-side deployments for Objective Assault. Each team spawns only at
 * player starts tagged for it (PlayerStartTag "TeamOne" / "TeamTwo", written by
 * Tools/Unreal/tag_deployments.py), at a random unoccupied one. Maps without
 * tagged starts fall back to Lyra's default choice. Granted to the game state
 * by the Objective Assault Game Feature in place of Lyra's B_TeamSpawningRules
 * (which picks any start far from enemies, mixing the teams).
 */
UCLASS()
class SSBRIDGE_API USSDeploymentSpawningComponent : public ULyraPlayerSpawningManagerComponent
{
	GENERATED_BODY()

public:
	USSDeploymentSpawningComponent(const FObjectInitializer& ObjectInitializer);

protected:
	virtual AActor* OnChoosePlayerStart(AController* Player, TArray<ALyraPlayerStart*>& PlayerStarts) override;
};
