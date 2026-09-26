// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "SSTeamTypes.generated.h"

/**
 * The authoritative, replicated identity of a team in the world.
 *
 * This is what the server assigns and what replicates. It carries no opinion
 * about who is good or bad, and it must never be used as a presentation
 * decision on its own - see ESSLocality for that.
 *
 * Supersedes the match-relative `Friendly`/`Opposing` values proposed by
 * ADR-003. See ADR-017.
 */
UENUM(BlueprintType)
enum class ESSTeamId : uint8
{
	/** No team. Never a valid gameplay state; resolution against it fails loudly. */
	None		UMETA(DisplayName = "None"),

	/** First authoritative team in the match. Carries no inherent alignment. */
	TeamOne		UMETA(DisplayName = "Team One"),

	/** Second authoritative team in the match. Carries no inherent alignment. */
	TeamTwo		UMETA(DisplayName = "Team Two"),
};

/**
 * A viewer's relationship to a subject team. Derived locally, never replicated.
 *
 * CRITICAL: this is NOT a team identifier and must never be replicated as one.
 * Every client computes its own values from (ViewerTeam, SubjectTeam), so two
 * clients looking at the same pair of players hold opposite values here for the
 * same actors. Anything that treats ESSLocality as authoritative is a bug.
 *
 * Note the default-value hazard: an uninitialised ESSLocality is `Friendly`,
 * not `Invalid`. Callers must therefore never construct one by default and
 * branch on it - always go through
 * FSSViewerContext::ResolveLocality, which returns an explicit optional and
 * fails rather than guessing. This is why the enum has no `None` member: adding
 * one would be a safer default, but the published architecture fixes the value
 * set, so the safety lives in the resolution API instead.
 */
UENUM(BlueprintType)
enum class ESSLocality : uint8
{
	/** The subject is on the viewer's own team. */
	Friendly	UMETA(DisplayName = "Friendly"),

	/** The subject is on the other team. */
	Opposing	UMETA(DisplayName = "Opposing"),
};
