// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "SSCasualtyRules.h"
#include "SSCasualtySettings.generated.h"

class UStaticMesh;

/**
 * Every number in ADR-040, as data: Config/DefaultGame.ini
 * [/Script/SouthernSpearCasualty.SSCasualtySettings]. Field for field the same as SSCasualty::FTuning, so
 * the pure rules and the game can never disagree about what a number means (a test compares the ini's
 * values with the struct's defaults, which is also how a silently failed ini import shows up).
 * Bone lists are plain strings on purpose: an array of structs imports as empty on a syntax slip.
 */
UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Southern Spear Casualty"))
class SSCASUALTY_API USSCasualtySettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UPROPERTY(Config, EditAnywhere, Category = "Health") float MaxHealth = 100.f;

	UPROPERTY(Config, EditAnywhere, Category = "Zones") float HeadMultiplier = 4.0f;
	UPROPERTY(Config, EditAnywhere, Category = "Zones") float TorsoMultiplier = 1.0f;
	UPROPERTY(Config, EditAnywhere, Category = "Zones") float ArmMultiplier = 0.6f;
	UPROPERTY(Config, EditAnywhere, Category = "Zones") float LegMultiplier = 0.7f;

	UPROPERTY(Config, EditAnywhere, Category = "Bleeding") float HeadBleedPerDamage = 0.0f;
	UPROPERTY(Config, EditAnywhere, Category = "Bleeding") float TorsoBleedPerDamage = 0.02f;
	UPROPERTY(Config, EditAnywhere, Category = "Bleeding") float ArmBleedPerDamage = 0.04f;
	UPROPERTY(Config, EditAnywhere, Category = "Bleeding") float LegBleedPerDamage = 0.04f;
	UPROPERTY(Config, EditAnywhere, Category = "Bleeding") float MaxBleed = 4.0f;
	UPROPERTY(Config, EditAnywhere, Category = "Bleeding") float BleedOutSeconds = 45.f;

	UPROPERTY(Config, EditAnywhere, Category = "Treatment") float DressingSelfSeconds = 6.f;
	UPROPERTY(Config, EditAnywhere, Category = "Treatment") float DressingTeammateSeconds = 4.f;
	UPROPERTY(Config, EditAnywhere, Category = "Treatment") float StabiliseTeammateSeconds = 8.f;
	UPROPERTY(Config, EditAnywhere, Category = "Treatment") float StabiliseMedicSeconds = 5.f;
	UPROPERTY(Config, EditAnywhere, Category = "Treatment") float TreatMedicSeconds = 5.f;
	UPROPERTY(Config, EditAnywhere, Category = "Treatment") float KitSelfTreatSeconds = 8.f;
	UPROPERTY(Config, EditAnywhere, Category = "Treatment") float StabiliseTeammateHealth = 25.f;
	UPROPERTY(Config, EditAnywhere, Category = "Treatment") float StabiliseTeammateBleed = 0.3f;
	UPROPERTY(Config, EditAnywhere, Category = "Treatment") float StabiliseMedicHealth = 50.f;
	UPROPERTY(Config, EditAnywhere, Category = "Treatment") float TreatMedicHealth = 75.f;
	UPROPERTY(Config, EditAnywhere, Category = "Treatment") float KitSelfTreatHealth = 60.f;
	UPROPERTY(Config, EditAnywhere, Category = "Treatment") int32 DressingsCarried = 2;
	UPROPERTY(Config, EditAnywhere, Category = "Treatment") int32 MedicDressingsCarried = 6;

	/** How close the treater must stay to the patient for a treatment to continue. */
	UPROPERTY(Config, EditAnywhere, Category = "Treatment") float TreatRangeCm = 250.f;

	UPROPERTY(Config, EditAnywhere, Category = "Kit") int32 KitCharges = 8;
	UPROPERTY(Config, EditAnywhere, Category = "Kit") float KitLifetimeSeconds = 180.f;
	UPROPERTY(Config, EditAnywhere, Category = "Kit") float KitRadiusCm = 200.f;
	/** The kit's mesh (the Fab IFAK once imported; the engine cube until then). */
	UPROPERTY(Config, EditAnywhere, Category = "Kit") TSoftObjectPtr<UStaticMesh> KitMesh;

	/** Test switch until roles exist (GDD §4.5): everyone treats as a medic. */
	UPROPERTY(Config, EditAnywhere, Category = "Roles") bool bEveryoneIsMedic = false;

	/** Hit-bone name fragments (case-insensitive) per zone; anything else is Torso. Used by the bridge. */
	UPROPERTY(Config, EditAnywhere, Category = "Zones") TArray<FString> HeadBones;
	UPROPERTY(Config, EditAnywhere, Category = "Zones") TArray<FString> ArmBones;
	UPROPERTY(Config, EditAnywhere, Category = "Zones") TArray<FString> LegBones;

	SSCasualty::FTuning ToTuning() const;

	/** The zone a hit on BoneName falls in. Pure: no world needed. */
	SSCasualty::EZone ZoneForBone(FName BoneName) const;

	static const USSCasualtySettings& Get() { return *GetDefault<USSCasualtySettings>(); }
};
