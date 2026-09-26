// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "SSTeamTypes.h"
#include "SSViewerContext.h"

/** Why a locality resolution could not be performed. */
enum class ESSResolutionFailure : uint8
{
	/** The viewer context names no team and authorises no override. */
	NoAuthorisedViewingTeam,

	/** The subject has no team. */
	SubjectHasNoTeam,

	/** The viewing team is valid but is not one this build knows how to resolve. */
	UnrecognisedViewingTeam,
};

/**
 * Result of a locality resolution.
 *
 * Resolution cannot fail silently. Callers get either a locality and no reason,
 * or no locality and a reason, and a failure is always logged to LogSSCore.
 */
struct FSSLocalityResolution
{
	/** Resolved locality. Only meaningful when bResolved is true. */
	ESSLocality Locality = ESSLocality::Friendly;

	/** Whether a locality was resolved. */
	bool bResolved = false;

	/** Set when bResolved is false. */
	ESSResolutionFailure Failure = ESSResolutionFailure::NoAuthorisedViewingTeam;

	/** The team the resolution was performed from. ESSTeamId::None on failure. */
	ESSTeamId ViewingTeam = ESSTeamId::None;

	/** The team being resolved about. ESSTeamId::None on failure. */
	ESSTeamId SubjectTeam = ESSTeamId::None;

	bool IsResolved() const { return bResolved; }
};

/**
 * Team identity and viewer-relative locality.
 *
 * This is a stateless function library on purpose. It holds no cached team or
 * faction state, so it cannot become a second source of truth that drifts from
 * the server's.
 */
class SSCORE_API FSSTeamIdentity
{
public:
	/** True only for TeamOne and TeamTwo. ESSTeamId::None is not playable. */
	static bool IsPlayableTeam(ESSTeamId Team);

	/** The two playable teams, in a stable order. Never contains None. */
	static void GetPlayableTeams(TArray<ESSTeamId>& OutTeams);

	/** The opposing playable team, or None if Team is not playable. */
	static ESSTeamId GetOpposingTeam(ESSTeamId Team);

	/** Human-readable name. Diagnostic and UI only; never a gameplay key. */
	static FString ToDebugString(ESSTeamId Team);

	/**
	 * Resolve how a subject team relates to a viewing team.
	 *
	 * Pure and deterministic: same inputs, same result, no world access, no
	 * time dependence and no side effects. Fails loudly rather than defaulting.
	 */
	static FSSLocalityResolution ResolveLocality(ESSTeamId ViewingTeam, ESSTeamId SubjectTeam);

	/**
	 * Resolve locality from an explicit viewer context.
	 *
	 * Spectators and replays must supply OverrideViewingTeam; a live player must
	 * not. A context that authorises no team fails.
	 */
	static FSSLocalityResolution ResolveLocality(
		const FSSViewerContext& ViewerContext, ESSTeamId SubjectTeam);
};
