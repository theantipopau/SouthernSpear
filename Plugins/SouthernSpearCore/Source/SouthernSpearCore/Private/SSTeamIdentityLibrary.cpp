// Copyright Southern Spear. All Rights Reserved.

#include "SSTeamIdentityLibrary.h"

#include "SSCoreLog.h"

namespace
{
	/** Human-readable name for a resolution failure, for logs and tooling. */
	const TCHAR* LexToString(ESSResolutionFailure Failure)
	{
		switch (Failure)
		{
		case ESSResolutionFailure::NoAuthorisedViewingTeam:	return TEXT("NoAuthorisedViewingTeam");
		case ESSResolutionFailure::SubjectHasNoTeam:			return TEXT("SubjectHasNoTeam");
		case ESSResolutionFailure::UnrecognisedViewingTeam:	return TEXT("UnrecognisedViewingTeam");
		default:												return TEXT("Unknown");
		}
	}
}

bool FSSTeamIdentity::IsPlayableTeam(ESSTeamId Team)
{
	return Team == ESSTeamId::TeamOne || Team == ESSTeamId::TeamTwo;
}

void FSSTeamIdentity::GetPlayableTeams(TArray<ESSTeamId>& OutTeams)
{
	OutTeams.Reset();
	OutTeams.Add(ESSTeamId::TeamOne);
	OutTeams.Add(ESSTeamId::TeamTwo);
}

ESSTeamId FSSTeamIdentity::GetOpposingTeam(ESSTeamId Team)
{
	switch (Team)
	{
	case ESSTeamId::TeamOne:	return ESSTeamId::TeamTwo;
	case ESSTeamId::TeamTwo:	return ESSTeamId::TeamOne;
	default:					return ESSTeamId::None;
	}
}

FString FSSTeamIdentity::ToDebugString(ESSTeamId Team)
{
	switch (Team)
	{
	case ESSTeamId::None:		return TEXT("None");
	case ESSTeamId::TeamOne:	return TEXT("TeamOne");
	case ESSTeamId::TeamTwo:	return TEXT("TeamTwo");
	default:					return FString::Printf(TEXT("Invalid(%d)"), static_cast<uint8>(Team));
	}
}

FSSLocalityResolution FSSTeamIdentity::ResolveLocality(
	ESSTeamId ViewingTeam, ESSTeamId SubjectTeam)
{
	FSSLocalityResolution Result;
	Result.ViewingTeam = ViewingTeam;
	Result.SubjectTeam = SubjectTeam;

	// Order matters for the reported reason. A subject with no team is a
	// different bug from a viewer with no team, and they need different fixes,
	// so the subject is checked first only once we know the viewer is real.
	if (!IsPlayableTeam(ViewingTeam))
	{
		Result.bResolved = false;
		Result.Failure = ViewingTeam == ESSTeamId::None
			? ESSResolutionFailure::NoAuthorisedViewingTeam
			: ESSResolutionFailure::UnrecognisedViewingTeam;

		if (ViewingTeam == ESSTeamId::None)
		{
			UE_LOG(LogSSCore, Error,
				TEXT("Locality resolution failed (%s): the viewing team is None. ")
				TEXT("Presentation must not be resolved without an authorised viewing team; ")
				TEXT("refusing to guess rather than defaulting to one side."),
				LexToString(Result.Failure));
		}
		else
		{
			// A value that is neither None nor a known team means the data is
			// corrupt or out of sync, not that a vantage is missing. Say so,
			// because the two have completely different fixes.
			UE_LOG(LogSSCore, Error,
				TEXT("Locality resolution failed (%s): viewing team '%s' is not a value this ")
				TEXT("build knows. This is corrupt or desynced team data, not a missing vantage."),
				LexToString(Result.Failure), *ToDebugString(ViewingTeam));
		}
		return Result;
	}

	if (!IsPlayableTeam(SubjectTeam))
	{
		Result.bResolved = false;
		Result.Failure = SubjectTeam == ESSTeamId::None
			? ESSResolutionFailure::SubjectHasNoTeam
			: ESSResolutionFailure::UnrecognisedViewingTeam;
		UE_LOG(LogSSCore, Error,
			TEXT("Locality resolution failed (%s): subject team '%s' is not a playable team. ")
			TEXT("A player with no team must not be rendered as part of either side."),
			LexToString(Result.Failure), *ToDebugString(SubjectTeam));
		return Result;
	}

	Result.bResolved = true;
	Result.Locality = (ViewingTeam == SubjectTeam)
		? ESSLocality::Friendly
		: ESSLocality::Opposing;
	return Result;
}

FSSLocalityResolution FSSTeamIdentity::ResolveLocality(
	const FSSViewerContext& ViewerContext, ESSTeamId SubjectTeam)
{
	const ESSTeamId EffectiveViewingTeam = ViewerContext.GetEffectiveViewingTeam();

	// A spectator or replay must state a vantage. A live player must not: if a
	// live context also carries an override, the override is ignored above by
	// GetEffectiveViewingTeam, so reaching here with a mismatch is not an error.
	// What IS an error is a spectator with no stated vantage, because the only
	// alternatives are guessing a side or showing both.
	if (ViewerContext.bIsSpectator || ViewerContext.bIsReplay)
	{
		if (ViewerContext.ViewerTeam != ESSTeamId::None)
		{
			UE_LOG(LogSSCore, Warning,
				TEXT("Viewer context is marked as spectator/replay but carries ViewerTeam '%s'; ")
				TEXT("OverrideViewingTeam is authoritative for those contexts."),
				*ToDebugString(ViewerContext.ViewerTeam));
		}
		if (!ViewerContext.HasAuthorisedViewingTeam())
		{
			FSSLocalityResolution Result;
			Result.SubjectTeam = SubjectTeam;
			Result.bResolved = false;
			Result.Failure = ESSResolutionFailure::NoAuthorisedViewingTeam;
			UE_LOG(LogSSCore, Error,
				TEXT("Locality resolution failed (%s): a %s context declared no viewing team. ")
				TEXT("Spectators and replays must state which authorised vantage they watch from; ")
				TEXT("defaulting here would leak one team's view to the other."),
				LexToString(Result.Failure),
				ViewerContext.bIsReplay ? TEXT("replay") : TEXT("spectator"));
			return Result;
		}
	}

	return ResolveLocality(EffectiveViewingTeam, SubjectTeam);
}
