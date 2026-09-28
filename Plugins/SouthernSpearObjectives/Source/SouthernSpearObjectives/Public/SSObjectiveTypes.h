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
	/** Section Assault: the round that just ended decided the match. */
	bool bMatchEnded = false;
};

/** Which rule set the director runs. Chosen per match; the map is the same. */
UENUM(BlueprintType)
enum class ESSAssaultRules : uint8
{
	/** ADR-018: symmetric, both teams capture, unlimited respawns, draw on time. */
	ObjectiveAssault,
	/** ADR-031: one life per round, attack and defend, sides swap at half time. */
	SectionAssault,
};

/** Why a Section Assault round ended. */
UENUM(BlueprintType)
enum class ESSRoundEndReason : uint8
{
	None,
	/** The attackers took the final objective. */
	ObjectiveTaken,
	/** Every attacker on the roster was eliminated. */
	AttackersEliminated,
	/** Every defender on the roster was eliminated. */
	DefendersEliminated,
	/** Both teams were eliminated in the same step: a drawn round. */
	MutualElimination,
	/** The clock ran out with objectives still held: a defender win. */
	TimeExpired,
};

/** Section Assault match tuning (ADR-031). Identical for both teams: the sides swap. */
USTRUCT(BlueprintType)
struct FSSSectionRules
{
	GENERATED_BODY()

	/** Rounds each team attacks. First to RoundsPerHalf + 1 wins; level after both halves is a draw. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Section", meta = (ClampMin = "1"))
	int32 RoundsPerHalf = 4;

	/** Length of a round's play. Short, because nobody respawns. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Section", meta = (ClampMin = "1.0"))
	float RoundSeconds = 300.f;

	/** Result hold after the deciding round, before a new match starts. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Section", meta = (ClampMin = "0.0"))
	float PostMatchSeconds = 20.f;
};

/** Replicated Section Assault match state. Server-authoritative. */
USTRUCT(BlueprintType)
struct FSSMatchState
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Match")
	int32 TeamOneRounds = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Match")
	int32 TeamTwoRounds = 0;

	/** Rounds finished this match, draws included. */
	UPROPERTY(BlueprintReadOnly, Category = "Match")
	int32 RoundsPlayed = 0;

	/** The team attacking the current (or next) round. */
	UPROPERTY(BlueprintReadOnly, Category = "Match")
	ESSTeamId AttackingTeam = ESSTeamId::TeamOne;

	/** 1 or 2. */
	UPROPERTY(BlueprintReadOnly, Category = "Match")
	int32 Half = 1;

	UPROPERTY(BlueprintReadOnly, Category = "Match")
	bool bMatchOver = false;

	/** Valid once bMatchOver; None for a drawn match. */
	UPROPERTY(BlueprintReadOnly, Category = "Match")
	ESSTeamId MatchWinner = ESSTeamId::None;

	UPROPERTY(BlueprintReadOnly, Category = "Match")
	ESSRoundEndReason LastRoundReason = ESSRoundEndReason::None;

	/** Players still in the round, per team. Public knowledge, as in the scoreboard. */
	UPROPERTY(BlueprintReadOnly, Category = "Match")
	int32 TeamOneAlive = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Match")
	int32 TeamTwoAlive = 0;

	ESSTeamId GetDefendingTeam() const
	{
		return AttackingTeam == ESSTeamId::TeamOne ? ESSTeamId::TeamTwo : ESSTeamId::TeamOne;
	}
};

/** What the Section Assault rules need to know about the world for one step. */
struct FSSSectionInputs
{
	/** Owner of the active objective after this step's capture (None if not captured). */
	ESSTeamId ActiveObjectiveCapturedBy = ESSTeamId::None;
	/** Round roster size and players still alive, per team. */
	int32 TeamOneRoster = 0;
	int32 TeamOneAlive = 0;
	int32 TeamTwoRoster = 0;
	int32 TeamTwoAlive = 0;
};
