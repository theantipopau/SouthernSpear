// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SSObjectiveTypes.h"
#include "SSObjectiveActor.generated.h"

class USphereComponent;

/**
 * A capturable objective. Placed in the map; driven by ASSObjectiveAssaultDirector.
 *
 * The server counts pawns inside the capture sphere per team and steps the pure
 * capture rules. Clients only receive the replicated State.
 */
UCLASS()
class SSOBJ_API ASSObjectiveActor : public AActor
{
	GENERATED_BODY()

public:
	ASSObjectiveActor();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	/** Position in the sequence, from 0. Must be unique within a map. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Objective")
	int32 SequenceIndex = 0;

	/** Player-facing name ("Water Point"). Identical for both teams. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Objective")
	FText ObjectiveName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Objective")
	FSSCaptureRules CaptureRules;

	UFUNCTION(BlueprintPure, Category = "Objective")
	const FSSObjectiveState& GetObjectiveState() const { return State; }

	/** Server only. Count presence per team and advance capture. */
	void ServerStepCapture(float DeltaSeconds, int32 TeamOneGenericId, int32 TeamTwoGenericId);

	/** Server only. Replace the state (round reset, activation). */
	void ServerSetState(const FSSObjectiveState& NewState);

	/** Presence counts from the last step (server), for diagnostics. */
	int32 GetLastTeamOneCount() const { return LastTeamOneCount; }
	int32 GetLastTeamTwoCount() const { return LastTeamTwoCount; }

	UFUNCTION(BlueprintPure, Category = "Objective")
	float GetCaptureRadius() const;

protected:
	UPROPERTY(VisibleAnywhere, Category = "Objective")
	TObjectPtr<USphereComponent> CaptureVolume;

	UPROPERTY(ReplicatedUsing = OnRep_State, BlueprintReadOnly, Category = "Objective")
	FSSObjectiveState State;

	UFUNCTION()
	void OnRep_State(const FSSObjectiveState& Previous);

private:
	int32 LastTeamOneCount = 0;
	int32 LastTeamTwoCount = 0;
};
