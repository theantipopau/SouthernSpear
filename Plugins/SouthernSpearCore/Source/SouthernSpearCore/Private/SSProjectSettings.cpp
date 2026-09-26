// Copyright Southern Spear. All Rights Reserved.

#include "SSProjectSettings.h"

#include "SSNativeGameplayTags.h"

USSProjectSettings::USSProjectSettings()
{
	// 3 ACR is the Phase 1 player formation; MAF is the contextual opposing
	// force. Both are presentation defaults only.
	PlayerFormationUnit = TAG_SS_Unit_ACR_3;
	OpposingForce = TAG_SS_Force_MurasianArmedForces;

	ValidGameplayTags.AddTag(TAG_SS_Team_TeamOne);
	ValidGameplayTags.AddTag(TAG_SS_Team_TeamTwo);
	ValidGameplayTags.AddTag(TAG_SS_Locality_Friendly);
	ValidGameplayTags.AddTag(TAG_SS_Locality_Opposing);
	ValidGameplayTags.AddTag(TAG_SS_Force_CommonwealthDefenceService);
	ValidGameplayTags.AddTag(TAG_SS_Force_MurasianArmedForces);
	ValidGameplayTags.AddTag(TAG_SS_Branch_CommonwealthLandService);
	ValidGameplayTags.AddTag(TAG_SS_Unit_ACR);
	ValidGameplayTags.AddTag(TAG_SS_Unit_ACR_1);
	ValidGameplayTags.AddTag(TAG_SS_Unit_ACR_3);
	ValidGameplayTags.AddTag(TAG_SS_Unit_ACR_5);
	ValidGameplayTags.AddTag(TAG_SS_Unit_ACR_7);
	ValidGameplayTags.AddTag(TAG_SS_Unit_CommandoGroup2);
	ValidGameplayTags.AddTag(TAG_SS_Unit_SpecialOperationsRegiment);
	ValidGameplayTags.AddTag(TAG_SS_Weapon_A88);
	ValidGameplayTags.AddTag(TAG_SS_Weapon_A89);
	ValidGameplayTags.AddTag(TAG_SS_Weapon_A4);
	ValidGameplayTags.AddTag(TAG_SS_Weapon_A416);
	ValidGameplayTags.AddTag(TAG_SS_Weapon_A417);
	ValidGameplayTags.AddTag(TAG_SS_Weapon_A9);
	ValidGameplayTags.AddTag(TAG_SS_Role_Rifleman);
	ValidGameplayTags.AddTag(TAG_SS_Role_Grenadier);
	ValidGameplayTags.AddTag(TAG_SS_Role_AutomaticRifleman);
	ValidGameplayTags.AddTag(TAG_SS_Role_Marksman);
	ValidGameplayTags.AddTag(TAG_SS_Role_Medic);
	ValidGameplayTags.AddTag(TAG_SS_Role_FireteamLeader);
	ValidGameplayTags.AddTag(TAG_SS_Role_SectionCommander);

	PlayableTeamTags.AddTag(TAG_SS_Team_TeamOne);
	PlayableTeamTags.AddTag(TAG_SS_Team_TeamTwo);
}

const USSProjectSettings* USSProjectSettings::Get()
{
	return GetDefault<USSProjectSettings>();
}
