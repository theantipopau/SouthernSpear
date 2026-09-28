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
 * With RulesMode = SectionAssault (or ?Rules=Section on the map URL) it runs
 * ADR-031 instead: one life per round, attack and defend, sides swapping at
 * half time, first to RoundsPerHalf + 1. Who is alive is kept by the Core
 * respawn gate, which this actor locks for the round and the Lyra bridge
 * feeds with eliminations.
 *
 * Both rule sets post service events (objective captured, round won, ...) to
 * the Core service event bus for progression (ADR-032).
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

	/** Which rule set runs. The map URL option ?Rules=Section (or ?Rules=Objective) overrides it on the server; replicated so client HUDs follow. */
	UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category = "Round")
	ESSAssaultRules RulesMode = ESSAssaultRules::ObjectiveAssault;

	/** Section Assault tuning; unused in Objective Assault. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Round")
	FSSSectionRules SectionRules;

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

	/** Section Assault match score, sides and alive counts. Default-valued in Objective Assault. */
	UFUNCTION(BlueprintPure, Category = "Round")
	const FSSMatchState& GetMatchState() const { return MatchState; }

	UFUNCTION(BlueprintPure, Category = "Round")
	bool IsSectionAssault() const { return RulesMode == ESSAssaultRules::SectionAssault; }

	/** The ESSTeamId of a controller, from the controller, its player state or its pawn. None if unteamed. */
	ESSTeamId TeamOfController(const AController* Controller) const;

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

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Round")
	FSSMatchState MatchState;

	UFUNCTION()
	void OnRep_RoundState(const FSSRoundState& Previous);

private:
	void ServerStepObjectiveAssault(float DeltaSeconds);
	void ServerStepSectionAssault(float DeltaSeconds);
	void SteerIfDue(float DeltaSeconds);

	void ApplyEvents(const FSSRoundEvents& Events);
	void LogTransition(const FSSRoundState& Previous) const;

	/** Section Assault: roster sizes and alive counts from the respawn gate. */
	void GatherSectionInputs(FSSSectionInputs& Inputs) const;
	/** Section Assault: lock the respawn gate with everyone alive and teamed now. */
	void LockRespawnGate();

	/** Service events for a capture this step: everyone of the captor's team on the objective. */
	void PostCaptureEvents(const ASSObjectiveActor* Objective, ESSTeamId Captor);
	/** Service events for the round (and match) that just ended. */
	void PostRoundEndEvents(ESSTeamId Winner, bool bMatchEnded, ESSTeamId MatchWinner);
	int32 GenericIdOf(ESSTeamId Team) const;

	UPROPERTY(Transient)
	TArray<TObjectPtr<ASSObjectiveActor>> Objectives;

	void RestartPawnlessControllers();

	TArray<TWeakObjectPtr<AController>> PendingRespawn;
	/** Section Assault: Lyra's own respawn was held off, so bots are restarted at the reset too. */
	bool bPendingRestartIncludesBots = false;

	float SteerAccumulator = 0.f;
	int32 LastSteeredBotCount = 0;
	int32 LastSteerLogSignature = INDEX_NONE;
};
