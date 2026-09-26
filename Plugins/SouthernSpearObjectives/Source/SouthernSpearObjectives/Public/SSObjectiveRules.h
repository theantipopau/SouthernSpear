// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "SSObjectiveTypes.h"

/**
 * Pure Objective Assault rules (ADR-018).
 *
 * No world, no actors, no time source: every function takes a state and returns
 * the next one. Actors call these on the server and replicate the result, which
 * keeps the rules deterministic, symmetric and unit-testable.
 *
 * Mode summary: objectives are neutral and taken in sequence. Both teams contest
 * each one. Capturing one locks it and advances play to the next. The team that
 * captures the final objective wins; if time expires first the round is a draw
 * (failed). After a short post-round the round resets and starts again.
 */
struct SSOBJ_API FSSObjectiveRules
{
	/**
	 * Advance one objective by DeltaSeconds given who is standing on it.
	 * Counts are presence, not strength: one player captures at the same rate as
	 * five. Inactive or captured objectives never change. Invalid time steps
	 * (negative, NaN, infinite) are ignored.
	 */
	static FSSObjectiveState StepCapture(
		const FSSObjectiveState& State, int32 TeamOneCount, int32 TeamTwoCount,
		float DeltaSeconds, const FSSCaptureRules& Rules);

	/** Reset an objective for a new round. */
	static FSSObjectiveState ResetObjective(bool bActive);

	/**
	 * Begin the next round. With zero objectives the round cannot start and
	 * stays WaitingToStart; the caller must log that loudly.
	 */
	static FSSRoundState StartRound(
		const FSSRoundState& Previous, int32 NumObjectives, const FSSRoundRules& Rules,
		FSSRoundEvents& OutEvents);

	/**
	 * Advance the round by DeltaSeconds.
	 *
	 * ActiveObjectiveCapturedBy is the owner of the active objective after this
	 * frame's capture step (None if not captured). The caller applies the events:
	 * activate the next objective on bObjectiveAdvanced, reset every objective
	 * on bRoundReset.
	 */
	static FSSRoundState StepRound(
		const FSSRoundState& State, float DeltaSeconds, ESSTeamId ActiveObjectiveCapturedBy,
		const FSSRoundRules& Rules, FSSRoundEvents& OutEvents);

	static const TCHAR* LexPhase(ESSRoundPhase Phase);
	static const TCHAR* LexOutcome(ESSRoundOutcome Outcome);
};
