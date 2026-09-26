// Copyright Southern Spear. All Rights Reserved.

#include "Presentation/SSFactionPresentationResolver.h"

#include "Modules/ModuleManager.h"
#include "SSTeamIdentityLibrary.h"

DEFINE_LOG_CATEGORY(LogSSTeam);

IMPLEMENT_MODULE(FDefaultModuleImpl, SouthernSpearTeam)

FSSPresentationResolution FSSFactionPresentationResolver::Resolve(
	const FSSViewerContext& Viewer, ESSTeamId SubjectTeam,
	const FSSFactionPresentationTable& Table)
{
	FSSPresentationResolution Result;
	Result.SubjectTeam = SubjectTeam;

	// SouthernSpearCore logs the specific reason for every locality failure.
	const FSSLocalityResolution Locality = FSSTeamIdentity::ResolveLocality(Viewer, SubjectTeam);
	if (!Locality.IsResolved())
	{
		Result.Failure = ESSPresentationFailure::LocalityUnresolved;
		UE_LOG(LogSSTeam, Error,
			TEXT("Presentation not resolved for subject '%s': locality unresolved. ")
			TEXT("No faction presentation will be drawn."),
			*FSSTeamIdentity::ToDebugString(SubjectTeam));
		return Result;
	}

	Result.Locality = Locality.Locality;
	const bool bFriendly = Locality.Locality == ESSLocality::Friendly;
	const FSSFactionPresentation& Entry = bFriendly ? Table.Friendly : Table.Opposing;

	if (!Entry.IsComplete())
	{
		Result.Failure = ESSPresentationFailure::MissingPresentationData;
		UE_LOG(LogSSTeam, Error,
			TEXT("Presentation data missing or incomplete for %s subject '%s'. ")
			TEXT("Refusing to substitute the other side's presentation."),
			bFriendly ? TEXT("Friendly") : TEXT("Opposing"),
			*FSSTeamIdentity::ToDebugString(SubjectTeam));
		return Result;
	}

	Result.bResolved = true;
	Result.Failure = ESSPresentationFailure::None;
	Result.Presentation = Entry;
	return Result;
}

FSSFactionPresentationTable FSSFactionPresentationResolver::MakePlaceholderTable()
{
	// Engine-shipped placeholders only. Not final art; see ASSET_REGISTER.md.
	const FSoftObjectPath PlaceholderMesh(TEXT("/Engine/EngineMeshes/SkeletalCube.SkeletalCube"));
	const FSoftObjectPath PlaceholderMaterial(TEXT("/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial"));
	const FSoftObjectPath PlaceholderIcon(TEXT("/Engine/EngineResources/DefaultTexture.DefaultTexture"));

	FSSFactionPresentationTable Table;

	Table.Friendly.PresentationId = ESSFactionPresentationId::ACR3;
	Table.Friendly.DisplayName = NSLOCTEXT("SSTeam", "ACR3", "3 ACR");
	Table.Friendly.CharacterMesh = PlaceholderMesh;
	Table.Friendly.UniformMaterial = PlaceholderMaterial;
	Table.Friendly.Icon = PlaceholderIcon;

	Table.Opposing.PresentationId = ESSFactionPresentationId::MAF;
	Table.Opposing.DisplayName = NSLOCTEXT("SSTeam", "MAF", "MAF");
	Table.Opposing.CharacterMesh = PlaceholderMesh;
	Table.Opposing.UniformMaterial = PlaceholderMaterial;
	Table.Opposing.Icon = PlaceholderIcon;

	return Table;
}
