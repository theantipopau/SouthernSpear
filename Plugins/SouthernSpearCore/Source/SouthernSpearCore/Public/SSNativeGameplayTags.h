// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "NativeGameplayTags.h"

/**
 * Native Gameplay Tags for Southern Spear.
 *
 * These are native rather than data-driven because they are part of the
 * project's shared vocabulary, not content: two data assets that both mean "the
 * Australian Commonwealth Regiment" must mean it by the same tag. A tag that
 * only exists in one asset cannot be validated by this module, and the team and
 * presentation boundaries are exactly where a typo must be caught.
 *
 * All tags use the SS root. Any SS code that accepts a tag from outside this
 * root is a bug.
 */

// --- Stable team identity (authoritative) ------------------------------------
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Team_TeamOne);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Team_TeamTwo);

// --- Viewer-relative locality (derived locally, never replicated) -------------
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Locality_Friendly);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Locality_Opposing);

// --- Forces and branches -----------------------------------------------------
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Force_CommonwealthDefenceService);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Force_MurasianArmedForces);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Branch_CommonwealthLandService);

// --- Units -------------------------------------------------------------------
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Unit_ACR);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Unit_ACR_1);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Unit_ACR_3);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Unit_ACR_5);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Unit_ACR_7);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Unit_CommandoGroup2);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Unit_SpecialOperationsRegiment);

// --- Weapons -----------------------------------------------------------------
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Weapon_A88);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Weapon_A89);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Weapon_A4);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Weapon_A416);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Weapon_A417);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Weapon_A9);

// --- Roles -------------------------------------------------------------------
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Role_Rifleman);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Role_Grenadier);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Role_AutomaticRifleman);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Role_Marksman);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Role_Medic);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Role_FireteamLeader);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Role_SectionCommander);

// --- Hit zones (damage model, Session 032): tags on the soldier's physical materials ----
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Zone_Head);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Zone_Torso);
SSCORE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_SS_Zone_Limb);
