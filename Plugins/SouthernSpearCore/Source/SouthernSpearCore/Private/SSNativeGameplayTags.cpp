// Copyright Southern Spear. All Rights Reserved.

#include "SSNativeGameplayTags.h"

// --- Stable team identity (authoritative) ------------------------------------
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Team_TeamOne, "SS.Team.TeamOne");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Team_TeamTwo, "SS.Team.TeamTwo");

// --- Viewer-relative locality (derived locally, never replicated) -------------
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Locality_Friendly, "SS.Locality.Friendly");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Locality_Opposing, "SS.Locality.Opposing");

// --- Forces and branches -----------------------------------------------------
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Force_CommonwealthDefenceService, "SS.Force.CommonwealthDefenceService");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Force_MurasianArmedForces, "SS.Force.MurasianArmedForces");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Branch_CommonwealthLandService, "SS.Branch.CommonwealthLandService");

// --- Units -------------------------------------------------------------------
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Unit_ACR, "SS.Unit.ACR");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Unit_ACR_1, "SS.Unit.ACR.1");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Unit_ACR_3, "SS.Unit.ACR.3");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Unit_ACR_5, "SS.Unit.ACR.5");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Unit_ACR_7, "SS.Unit.ACR.7");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Unit_CommandoGroup2, "SS.Unit.CommandoGroup2");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Unit_SpecialOperationsRegiment, "SS.Unit.SpecialOperationsRegiment");

// --- Weapons -----------------------------------------------------------------
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Weapon_A88, "SS.Weapon.A88");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Weapon_A89, "SS.Weapon.A89");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Weapon_A4, "SS.Weapon.A4");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Weapon_A416, "SS.Weapon.A416");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Weapon_A417, "SS.Weapon.A417");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Weapon_A9, "SS.Weapon.A9");

// --- Roles -------------------------------------------------------------------
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Role_Rifleman, "SS.Role.Rifleman");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Role_Grenadier, "SS.Role.Grenadier");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Role_AutomaticRifleman, "SS.Role.AutomaticRifleman");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Role_Marksman, "SS.Role.Marksman");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Role_Medic, "SS.Role.Medic");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Role_FireteamLeader, "SS.Role.FireteamLeader");
UE_DEFINE_GAMEPLAY_TAG(TAG_SS_Role_SectionCommander, "SS.Role.SectionCommander");
