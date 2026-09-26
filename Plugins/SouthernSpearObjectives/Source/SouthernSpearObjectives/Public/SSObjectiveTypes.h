// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "SSTeamTypes.h"
#include "SSObjectiveTypes.generated.h"

SSOBJ_API DECLARE_LOG_CATEGORY_EXTERN(LogSSObjectives, Log, All);

/** Tuning for one capturable objective. Identical for both teams by construction. */
USTRUCT(BlueprintType)
struct FSSCaptureRules
{
	GENERATED_BODY()

	/** Seconds of uncontested presence to take a neutral objective from 0 to captured. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Capture", meta = (ClampMin = "1.0"))
	float CaptureSeconds = 20.f;

	/** Seconds for full progress to decay to zero when nobody is present. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Capture", meta = (ClampMin = "1.0"))
	float DecaySeconds = 30.f;
};

/**
 * Replicated state of one objective. Server-authoritative; clients only read it.
 *
 * Teams are ESSTeamId, never ESSLocality: an objective's owner is a fact about
 * the match, not about who is looking at it.
 */
USTRUCT(BlueprintType)
struct FSSObjectiveState
{
	GENERATED_BODY()

	/** Whether this objective is the one currently in play. */
	UPROPERTY(BlueprintReadOnly, Category = "Objective")
	bool bActive = false;

	/** Set once captured. A captured objective is locked for the rest of the round. */
	UPROPERTY(BlueprintReadOnly, Category = "Objective")
	ESSTeamId OwnerTeam = ESSTeamId::None;

	/** The team progress currently belongs to. None when progress is zero. */
	UPROPERTY(BlueprintReadOnly, Category = "Objective")
	ESSTeamId CapturingTeam = ESSTeamId::None;

	/** 0..1 towards CapturingTeam taking the objective. */
	UPROPERTY(BlueprintReadOnly, Category = "Objective")
	float Progress = 0.f;

	/** Both teams present: progress frozen. */
	UPROPERTY(BlueprintReadOnly, Category = "Objective")
	bool bContested = false;

	bool IsCaptured() const { return OwnerTeam != ESSTeamId::None; }
};

UENUM(BlueprintType)
enum class ESSRoundPhase : uint8
{
	/** No round can start: the director has no valid objectives. */
	WaitingToStart,
	/** Short hold before play so both teams deploy on equal terms. */
	PreRound,
	InProgress,
	/** Result shown; the round restarts when this expires. */
	PostRound,
};

UENUM(BlueprintType)
enum class ESSRoundOutcome : uint8
{
	None,
	TeamOneWon,
	TeamTwoWon,
	/** Time expired before the final objective was captured: the round failed. */
	Draw,
};

/** Round timings. Identical for both teams. */
USTRUCT(BlueprintType)
struct FSSRoundRules
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Round", meta = (ClampMin = "0.0"))
	float PreRoundSeconds = 10.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Round", meta = (ClampMin = "1.0"))
	float RoundSeconds = 900.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Round", meta = (ClampMin = "0.0"))
	float PostRoundSeconds = 15.f;
};

/** Replicated round state. Server-authoritative. */
USTRUCT(BlueprintType)
struct FSSRoundState
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Round")
	ESSRoundPhase Phase = ESSRoundPhase::WaitingToStart;

	UPROPERTY(BlueprintReadOnly, Category = "Round")
	ESSRoundOutcome Outcome = ESSRoundOutcome::None;

	/** 1-based. Zero until the first round starts. */
	UPROPERTY(BlueprintReadOnly, Category = "Round")
	int32 RoundNumber = 0;

	/** Index into the objective sequence. INDEX_NONE outside InProgress. */
	UPROPERTY(BlueprintReadOnly, Category = "Round")
	int32 ActiveObjectiveIndex = INDEX_NONE;

	UPROPERTY(BlueprintReadOnly, Category = "Round")
	int32 NumObjectives = 0;

	/** Seconds left in the current phase. */
	UPROPERTY(BlueprintReadOnly, Category = "Round")
	float PhaseTimeRemaining = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Round")
	int32 TeamOneCaptures = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Round")
	int32 TeamTwoCaptures = 0;
};

/** What changed during one round step, so the owner can act on it. */
struct FSSRoundEvents
{
	bool bRoundStarted = false;
	bool bObjectiveAdvanced = false;
	bool bRoundEnded = false;
	bool bRoundReset = false;
};
