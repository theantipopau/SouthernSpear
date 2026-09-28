// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Engine/DeveloperSettings.h"
#include "SSInsigniaRaster.h"
#include "SSServiceRanks.generated.h"

class APlayerState;
class UTexture2D;

/** A rank's insignia, as the devices on the rank slide (ADR-033). Drawn by SSInsigniaRaster. */
USTRUCT(BlueprintType)
struct FSSInsignia
{
	GENERATED_BODY()

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Insignia", meta = (ClampMin = "0", ClampMax = "3"))
	int32 Chevrons = 0;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Insignia", meta = (ClampMin = "0", ClampMax = "3"))
	int32 Pips = 0;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Insignia")
	bool bCrown = false;

	/** The Coat of Arms (WO1). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Insignia")
	bool bCrest = false;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Insignia")
	bool bSwordAndBaton = false;

	SSInsigniaRaster::FSpec ToSpec() const
	{
		SSInsigniaRaster::FSpec Spec;
		Spec.Chevrons = Chevrons;
		Spec.Pips = Pips;
		Spec.bCrown = bCrown;
		Spec.bCrest = bCrest;
		Spec.bSwordAndBaton = bSwordAndBaton;
		return Spec;
	}
};

/** One rank: reached at MinLevel, held until the next rank's MinLevel. */
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

	/** Service level at which this rank is reached. The first rank must start at 1; each after it higher. */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Rank")
	int32 MinLevel = 1;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Rank")
	FSSInsignia Insignia;
};

/**
 * The rank ladder and the level curve (ADR-033): Australian Army ranks,
 * Private to General, as service levels 1..MaxLevel, the way honour worked in
 * America's Army. Data, not code: Config/DefaultGame.ini
 * [/Script/SouthernSpearCore.SSRankSettings]. In Core because the scoreboard,
 * the front end and progression all read it.
 */
UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Southern Spear Ranks"))
class SSCORE_API USSRankSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Ranks")
	TArray<FSSRankDefinition> Ranks;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Levels", meta = (ClampMin = "1"))
	int32 MaxLevel = 100;

	/** XpForLevel(n) = round(LevelXpScale * (n - 1) ^ LevelXpExponent). */
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Levels", meta = (ClampMin = "1.0"))
	float LevelXpScale = 60.f;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Levels", meta = (ClampMin = "1.0"))
	float LevelXpExponent = 1.9f;
};

/** Pure rank and level rules, and the insignia textures. */
struct SSCORE_API FSSServiceRanks
{
	/** Service XP needed to reach Level with the configured curve (0 for level 1). */
	static int64 XpForLevel(int32 Level);

	/** Service level for Xp with the configured curve, 1..MaxLevel. */
	static int32 LevelForXp(int64 Xp);

	/** Index of the highest rank whose MinLevel <= Level; INDEX_NONE for level 0 (no record, e.g. a bot) or an empty ladder. */
	static int32 RankIndexForLevel(int32 Level, TConstArrayView<FSSRankDefinition> Ranks);

	/** The configured rank for Level, or nullptr. */
	static const FSSRankDefinition* RankForLevel(int32 Level);

	/** A usable ladder: not empty, first rank at level 1, levels strictly rising and within MaxLevel, ids unique and set. */
	static bool Validate(TConstArrayView<FSSRankDefinition> Ranks, int32 MaxLevel, TArray<FString>& OutErrors);

	/** A 64 px white insignia texture for the UI to tint; nullptr for a rank with no insignia (Private). Cached. */
	static UTexture2D* InsigniaTexture(const FSSInsignia& Insignia);
};

/**
 * Server-set, replicated to everyone: a player's service level, shown with
 * their rank insignia on the scoreboard (ADR-033). Added to the player state
 * by progression. Zero means no service record (bots).
 *
 * The level comes from the player's own local record, which is dev-only and
 * not authoritative (ADR-032, R-46): it is display, and gates nothing.
 */
UCLASS()
class SSCORE_API USSServiceRankComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USSServiceRankComponent();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	int32 GetServiceLevel() const { return ServiceLevel; }

	/** Server only. Clamped to 0..MaxLevel. */
	void SetServiceLevel(int32 Level);

	/** Server: the component on PlayerState, created if missing. */
	static USSServiceRankComponent* FindOrAdd(APlayerState* PlayerState);

private:
	UPROPERTY(Replicated)
	int32 ServiceLevel = 0;
};
