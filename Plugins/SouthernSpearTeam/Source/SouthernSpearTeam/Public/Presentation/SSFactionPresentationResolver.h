// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Logging/LogMacros.h"
#include "SSTeamTypes.h"
#include "SSViewerContext.h"
#include "Presentation/SSFactionPresentationTypes.h"

SSTEAM_API DECLARE_LOG_CATEGORY_EXTERN(LogSSTeam, Log, All);

/** Why a presentation could not be resolved. */
enum class ESSPresentationFailure : uint8
{
	None,

	/** Locality could not be resolved: bad viewer, bad subject, or spectator without a vantage. */
	LocalityUnresolved,

	/** Locality resolved, but the table entry for it is missing or incomplete. */
	MissingPresentationData,
};

/**
 * Result of a presentation resolution: a presentation, or a reason.
 *
 * There is no fallback presentation. A failure draws nothing faction-specific
 * and is logged, so it is visible instead of silently drawn as one side.
 */
struct FSSPresentationResolution
{
	bool bResolved = false;
	ESSPresentationFailure Failure = ESSPresentationFailure::LocalityUnresolved;

	/** The subject's authoritative team, passed through unchanged. */
	ESSTeamId SubjectTeam = ESSTeamId::None;

	/** Only meaningful when bResolved. */
	ESSLocality Locality = ESSLocality::Friendly;

	/** Copy of the selected entry. Default (None) on failure. */
	FSSFactionPresentation Presentation;
};

/**
 * Stateless faction-presentation resolver.
 *
 * No state, no world access, no gameplay reads: same inputs, same output.
 * The subject's gameplay identity (ESSTeamId) is passed through untouched, so
 * 3 ACR and MAF are always the same underlying team seen from different sides.
 */
class SSTEAM_API FSSFactionPresentationResolver
{
public:
	static FSSPresentationResolution Resolve(
		const FSSViewerContext& Viewer, ESSTeamId SubjectTeam,
		const FSSFactionPresentationTable& Table);

	/**
	 * 3 ACR friendly, MAF opposing, engine placeholder references only.
	 * No final art exists or is implied.
	 */
	static FSSFactionPresentationTable MakePlaceholderTable();
};
