// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "SSServiceEvents.h"
#include "SSProgressionSettings.generated.h"

/**
 * Service XP for one service event (TDD §6.2). A positive award must carry a
 * per-match cap, which is how "no reward for idling or farming" is enforced
 * rather than intended. A negative award is a penalty and is never capped.
 */
USTRUCT(BlueprintType)
struct FSSXpAwardRule
{
	GENERATED_BODY()

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Award")
	ESSServiceEvent Event = ESSServiceEvent::None;

	/** XP per occurrence. Negative for a penalty. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Award")
	int32 Award = 0;

	/** Occurrences per match that earn the award; later ones are recorded but earn nothing. Ignored for penalties. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Award")
	int32 MaxPerMatch = 0;
};

/**
 * The award table (ADR-032, ADR-033). Data, not code: Config/DefaultGame.ini
 * [/Script/SouthernSpearProgression.SSProgressionSettings]. The rank ladder and
 * level curve live in Core (USSRankSettings), because the scoreboard reads them.
 * Validated on load (FSSProgressionRules::ValidateAwards) and by test.
 */
UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Southern Spear Progression"))
class SSPROG_API USSProgressionSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Awards")
	TArray<FSSXpAwardRule> Awards;
};
