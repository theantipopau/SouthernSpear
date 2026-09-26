// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "GameplayTagContainer.h"
#include "SSProjectSettings.generated.h"

/**
 * Project-level settings for Southern Spear identity.
 *
 * Deliberately thin. This holds *defaults and vocabulary*, never gameplay
 * state: no damage, no health, no weapon tuning, no team assignment for a live
 * match. Anything that would need to differ between a client and a server, or
 * that a cheater could gain from, does not belong here (ADR-004).
 */
UCLASS(config = Game, defaultconfig, meta = (DisplayName = "Southern Spear"))
class SSCORE_API USSProjectSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	USSProjectSettings();

	/**
	 * Presentation unit shown for the player's own conventional team.
	 *
	 * Presentation only. Both teams are mechanically equal; this decides which
	 * insignia a viewer sees on their own side, never how anything behaves.
	 */
	UPROPERTY(config, EditAnywhere, Category = "Identity|Presentation")
	FGameplayTag PlayerFormationUnit;

	/** The canonical opposing force. Presentation only. */
	UPROPERTY(config, EditAnywhere, Category = "Identity|Presentation")
	FGameplayTag OpposingForce;

	/** Every gameplay tag this project registers. Used by data validation. */
	UPROPERTY(config, EditAnywhere, Category = "Identity|Validation")
	FGameplayTagContainer ValidGameplayTags;

	/** The two authoritative team tags, in a stable order. Never contains a None tag. */
	UPROPERTY(config, EditAnywhere, Category = "Identity|Validation")
	FGameplayTagContainer PlayableTeamTags;

	static const USSProjectSettings* Get();

	//~ Begin UDeveloperSettings interface
	virtual FName GetCategoryName() const override { return FName(TEXT("Project")); }
	//~ End UDeveloperSettings interface
};
