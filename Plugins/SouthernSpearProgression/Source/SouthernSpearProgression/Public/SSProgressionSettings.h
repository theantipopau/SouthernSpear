// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "SSServiceEvents.h"
#include "SSProgressionSettings.generated.h"

/** One rank in the ladder (GDD §6.2). Insignia are placeholders pending L-0003. */
USTRUCT(BlueprintType)
struct FSSRankDefinition
{
	GENERATED_BODY()

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Rank")
	FName Id;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Rank")
	FText DisplayName;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Rank")
	FText Abbreviation;

	/** Service XP at which this rank is reached. The first rank must be 0; each after it higher. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Rank")
	int32 MinServiceXp = 0;
};

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
 * The rank ladder and the award table (ADR-032). Data, not code:
 * Config/DefaultGame.ini [/Script/SouthernSpearProgression.SSProgressionSettings].
 * Validated on load (FSSProgressionRules::ValidateRanks/ValidateAwards) and by test.
 */
UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Southern Spear Progression"))
class SSPROG_API USSProgressionSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Ranks")
	TArray<FSSRankDefinition> Ranks;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Awards")
	TArray<FSSXpAwardRule> Awards;
};
