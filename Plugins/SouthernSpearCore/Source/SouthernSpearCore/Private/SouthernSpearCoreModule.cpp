// Copyright Southern Spear. All Rights Reserved.

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

#include "SSCoreLog.h"
#include "SSNativeGameplayTags.h"
#include "SSProjectSettings.h"
#include "SSTeamIdentityLibrary.h"

DEFINE_LOG_CATEGORY(LogSSCore);

/**
 * SouthernSpearCore - the foundation layer.
 *
 * Startup validation is deliberately noisy: the two team tags and the
 * presentation tags are checked against the project settings container so that a
 * tag renamed in C++ but not in data is caught at load rather than the first
 * time a player is rendered.
 */
class FSouthernSpearCoreModule : public IModuleInterface
{
public:
	virtual void StartupModule() override
	{
		UE_LOG(LogSSCore, Log, TEXT("SouthernSpearCore module started."));

		// Force the native tags to register before anything asks for them.
		(void)TAG_SS_Team_TeamOne;
		(void)TAG_SS_Team_TeamTwo;

		const USSProjectSettings* Settings = USSProjectSettings::Get();
		if (Settings == nullptr)
		{
			UE_LOG(LogSSCore, Error, TEXT("USSProjectSettings could not be loaded."));
			return;
		}

		// Team tags must be exactly the two playable teams.
		const FGameplayTagContainer& TeamTags = Settings->PlayableTeamTags;
		if (TeamTags.Num() != 2)
		{
			UE_LOG(LogSSCore, Error,
				TEXT("PlayableTeamTags must contain exactly 2 tags (TeamOne, TeamTwo); found %d."),
				TeamTags.Num());
		}
		else if (!TeamTags.HasTagExact(TAG_SS_Team_TeamOne) || !TeamTags.HasTagExact(TAG_SS_Team_TeamTwo))
		{
			UE_LOG(LogSSCore, Error,
				TEXT("PlayableTeamTags must contain SS.Team.TeamOne and SS.Team.TeamTwo."));
		}

		// Sanity check on team identity: two teams, each other's opposite.
		TArray<ESSTeamId> PlayableTeams;
		FSSTeamIdentity::GetPlayableTeams(PlayableTeams);
		if (PlayableTeams.Num() != 2)
		{
			UE_LOG(LogSSCore, Error, TEXT("Expected exactly 2 playable teams."));
		}
		else
		{
			for (const ESSTeamId Team : PlayableTeams)
			{
				const ESSTeamId Opposing = FSSTeamIdentity::GetOpposingTeam(Team);
				if (Opposing == Team || !FSSTeamIdentity::IsPlayableTeam(Opposing))
				{
					UE_LOG(LogSSCore, Error,
						TEXT("Team '%s' does not resolve to a distinct opposing team."),
						*FSSTeamIdentity::ToDebugString(Team));
				}
			}
		}
	}

	virtual void ShutdownModule() override
	{
		UE_LOG(LogSSCore, Log, TEXT("SouthernSpearCore module shut down."));
	}
};

IMPLEMENT_MODULE(FSouthernSpearCoreModule, SouthernSpearCore)
