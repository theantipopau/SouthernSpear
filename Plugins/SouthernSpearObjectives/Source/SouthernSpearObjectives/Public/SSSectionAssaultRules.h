// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "SSObjectiveTypes.h"

/**
 * Pure Section Assault rules (ADR-031).
 *
 * Like FSSObjectiveRules: no world, no actors, no time source. Every function
 * takes a state and returns the next one, so the mode is deterministic and
 * unit-testable, and the director only applies the result.
 *
 * Mode summary: one team attacks, one defends, and every player has one life
 * per round. Only the attackers capture, in sequence. The attackers win on the
 * final objective or by eliminating the defenders; the defenders win by
 * eliminating the attackers or holding until time. Team One attacks the first
 * half and Team Two the second, so the match, not the round, is symmetric.
 */
struct SSOBJ_API FSSSectionAssaultRules
{
	/** A fresh match: nothing scored, Team One attacking, first half. */
	static FSSMatchState NewMatch();

	/** The team attacking round RoundsPlayed (0-based) of a match. */
	static ESSTeamId AttackerForRound(int32 RoundsPlayed, const FSSSectionRules& Rules);

	/**
	 * Advance one objective when only the attackers may take it.
	 *
	 * Attackers alone build progress at the capture rate. Attackers and defenders
	 * together freeze it (contested). Defenders alone clear it at the capture
	 * rate; nobody present lets it decay at the decay rate. Defenders can never
	 * own an objective. Inactive or captured objectives never change; invalid
	 * steps are ignored. Counts are presence, not strength.
	 */
	static FSSObjectiveState StepAttackCapture(
		const FSSObjectiveState& State, ESSTeamId Attacker, int32 AttackersPresent, int32 DefendersPresent,
		float DeltaSeconds, const FSSCaptureRules& Rules);

	/**
	 * Decide whether a round in progress is over, and who won.
	 *
	 * Order: final objective taken, both sides eliminated, attackers eliminated,
	 * defenders eliminated, time expired. A side with nobody on its roster can
	 * not be eliminated. OutWinner is None for a draw or when the round goes on.
	 */
	static ESSRoundEndReason ResolveRound(
		bool bFinalObjectiveTaken, int32 AttackerRoster, int32 AttackersAlive, int32 DefenderRoster,
		int32 DefendersAlive, bool bTimeExpired, ESSTeamId Attacker, ESSTeamId& OutWinner);

	/** Score a finished round and decide whether the match is over; sets the next round's attacker. */
	static FSSMatchState ApplyRoundResult(
		const FSSMatchState& Match, ESSTeamId Winner, ESSRoundEndReason Reason, const FSSSectionRules& Rules);

	/**
	 * Advance a Section Assault round by DeltaSeconds.
	 *
	 * Pre-round counts down into play; in play, a capture by the attackers
	 * advances the sequence or ends the round, then ResolveRound decides
	 * eliminations and time; post-round counts down into the next round, or a
	 * new match once one has been decided. The caller applies the events, as for
	 * FSSObjectiveRules::StepRound, and locks the respawn gate on bRoundStarted.
	 */
	static void StepRound(
		const FSSRoundState& Round, const FSSMatchState& Match, float DeltaSeconds, const FSSSectionInputs& Inputs,
		const FSSRoundRules& RoundRules, const FSSSectionRules& SectionRules,
		FSSRoundState& OutRound, FSSMatchState& OutMatch, FSSRoundEvents& OutEvents);

	static const TCHAR* LexReason(ESSRoundEndReason Reason);
};
