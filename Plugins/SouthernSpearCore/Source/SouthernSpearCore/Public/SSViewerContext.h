// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "SSTeamTypes.h"

/**
 * The explicit context a resolution is performed from.
 *
 * Why this exists rather than a bare (ViewerTeam, SubjectTeam) pair:
 *
 *   A live player always has a team, so a pair is enough for them. A spectator
 *   does not. A replay does not. If those cases were allowed to pass
 *   ESSTeamId::None through a pair-based API, they would either resolve against
 *   a sentinel and silently render the match from one side's point of view, or
 *   fail deep inside presentation code where nobody is looking.
 *
 *   FSSViewerContext makes the non-live case explicit. A spectator or replay
 *   must state which authorised vantage it is viewing from, or the resolution
 *   fails - visibly, at the boundary, with a reason.
 */
struct FSSViewerContext
{
	/**
	 * The team the viewer fights for, if the viewer is a live participant.
	 * ESSTeamId::None for a spectator or replay, in which case
	 * OverrideViewingTeam decides the vantage.
	 */
	ESSTeamId ViewerTeam = ESSTeamId::None;

	/**
	 * The team to resolve from when ViewerTeam is None.
	 *
	 * Required for spectators and replays, ignored otherwise. A spectator who
	 * has not stated a vantage gets no resolution at all - deliberately, because
	 * guessing which side a free-camera happens to be floating near is how
	 * information leaks between teams.
	 */
	ESSTeamId OverrideViewingTeam = ESSTeamId::None;

	/** True for a free-camera spectator rather than a live player. */
	bool bIsSpectator = false;

	/** True when resolving for a replay rather than a live session. */
	bool bIsReplay = false;

	/**
	 * The team this context resolves from, or ESSTeamId::None if the context
	 * does not authorise one.
	 */
	ESSTeamId GetEffectiveViewingTeam() const
	{
		return ViewerTeam != ESSTeamId::None ? ViewerTeam : OverrideViewingTeam;
	}

	/** True when this context names a team it is allowed to resolve from. */
	bool HasAuthorisedViewingTeam() const
	{
		return GetEffectiveViewingTeam() != ESSTeamId::None;
	}
};
