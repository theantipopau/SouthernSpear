// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GenericTeamAgentInterface.h"
#include "SSObjectiveTypes.h"
#include "SSObjectiveAssaultDirector.generated.h"

class ASSObjectiveActor;

/**
 * Runs the Objective Assault round on the server and replicates it.
 *
 * One per map. It collects every ASSObjectiveActor in the level, orders them by
 * SequenceIndex, and drives the pure round rules: pre-round, sequential capture,
 * win on the final objective or draw on time, post-round, reset.
 *
 * Team mapping: Lyra assigns generic team ids (1 and 2 in ShooterCore). This
 * actor maps them to ESSTeamId so gameplay never needs Lyra types.
 */
UCLASS()
class SSOBJ_API ASSObjectiveAssaultDirector : public AActor
{
	GENERATED_BODY()

public:
	ASSObjectiveAssaultDirector();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Round")
	FSSRoundRules RoundRules;

	/** Generic team id that maps to ESSTeamId::TeamOne. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Teams")
	int32 TeamOneGenericId = 1;

	/** Generic team id that maps to ESSTeamId::TeamTwo. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Teams")
	int32 TeamTwoGenericId = 2;

	/**
	 * Server: send idle AI bots to the active objective. A bot counts as busy,
	 * and is left to its own behaviour tree, while BotBusyBlackboardKey holds a
	 * value (Lyra's shooter bot uses TargetEnemy). Player controllers are never
	 * touched. Identical for both teams.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Bots")
	bool bSteerIdleBotsToObjective = true;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Bots", meta = (ClampMin = "0.25"))
	float BotSteerInterval = 2.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Bots")
	FName BotBusyBlackboardKey = TEXT("TargetEnemy");

	/**
	 * Server: when a round resets, send every pawn back to a deployment start
	 * (destroy pawn, GameMode RestartPlayer). Without it the next round starts
	 * wherever the last one ended. Identical for both teams.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Round")
	bool bRespawnAllOnRoundReset = true;

	/** Server: respawn every controlled pawn at a start. Returns the count. Public for tests. */
	int32 RespawnAllPlayers();

	/** Map a generic team id to ESSTeamId using this director's mapping; None if neither. */
	ESSTeamId ToTeamId(FGenericTeamId GenericId) const;

	/** Number of move orders issued on the last steer pass (server, diagnostics/tests). */
	int32 GetLastSteeredBotCount() const { return LastSteeredBotCount; }

	/** Server: one steer pass now. Public for tests. */
	int32 SteerIdleBots();

	UFUNCTION(BlueprintPure, Category = "Round")
	const FSSRoundState& GetRoundState() const { return RoundState; }

	/** Ordered objectives (server and client). */
	const TArray<TObjectPtr<ASSObjectiveActor>>& GetObjectives() const { return Objectives; }

	/**
	 * Collect and order the level's objectives. Returns false, and logs why, if
	 * the sequence is unusable (none, or duplicate SequenceIndex).
	 */
	bool GatherObjectives();

	/** Server: advance round and capture by DeltaSeconds. Public for tests. */
	void ServerStep(float DeltaSeconds);

protected:
	UPROPERTY(ReplicatedUsing = OnRep_RoundState, BlueprintReadOnly, Category = "Round")
	FSSRoundState RoundState;

	UFUNCTION()
	void OnRep_RoundState(const FSSRoundState& Previous);

private:
	void ApplyEvents(const FSSRoundEvents& Events);
	void LogTransition(const FSSRoundState& Previous) const;

	UPROPERTY(Transient)
	TArray<TObjectPtr<ASSObjectiveActor>> Objectives;

	void RestartPawnlessControllers();

	TArray<TWeakObjectPtr<AController>> PendingRespawn;

	float SteerAccumulator = 0.f;
	int32 LastSteeredBotCount = 0;
	int32 LastSteerLogSignature = INDEX_NONE;
};
