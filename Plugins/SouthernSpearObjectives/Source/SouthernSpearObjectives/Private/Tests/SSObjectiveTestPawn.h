// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "GenericTeamAgentInterface.h"
#include "SSObjectiveTestPawn.generated.h"

class USphereComponent;

/**
 * Test-only pawn with a generic team id, standing in for a Lyra character in
 * the objective integration tests. Not exported, not placeable.
 */
UCLASS(NotPlaceable, Transient, HideDropdown)
class ASSObjectiveTestPawn : public APawn, public IGenericTeamAgentInterface
{
	GENERATED_BODY()

public:
	ASSObjectiveTestPawn();

	virtual FGenericTeamId GetGenericTeamId() const override { return TeamId; }
	virtual void SetGenericTeamId(const FGenericTeamId& InTeamId) override { TeamId = InTeamId; }

	UPROPERTY()
	TObjectPtr<USphereComponent> Body;

	FGenericTeamId TeamId = FGenericTeamId::NoTeam;
};
