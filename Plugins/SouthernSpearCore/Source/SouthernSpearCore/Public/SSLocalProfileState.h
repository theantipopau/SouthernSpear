// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "SSLocalProfileState.generated.h"

/**
 * The local player's service profile, as plain values for the UI (ADR-032).
 * SouthernSpearProgression fills it from the service record whenever the
 * record loads or changes; UI modules only read it, because they may depend
 * on Core alone (guard SS001). Client-local, never replicated, never read by
 * gameplay (ADR-004).
 */
UCLASS()
class SSCORE_API USSLocalProfileState : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	/** False until a record has been loaded or created. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Profile")
	bool bLoaded = false;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Profile")
	FString Callsign;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Profile")
	FText RankName;

	/** Short form for tight spaces ("CPL"). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Profile")
	FText RankAbbreviation;

	/** 0-based position in the rank list. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Profile")
	int32 RankIndex = 0;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Profile")
	int32 ServiceXp = 0;

	/** Service XP at which the current rank starts. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Profile")
	int32 RankFloorXp = 0;

	/** Service XP for the next rank; -1 at the highest rank. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Profile")
	int32 NextRankXp = -1;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Profile")
	int32 MatchesCompleted = 0;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Profile")
	int32 RoundsWon = 0;

	/** The most recent award ("ROUND WON +50"), for a HUD toast; empty when none yet. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Profile")
	FText LastAward;

	/** Real seconds (FPlatformTime) of LastAward; -1 never. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Profile")
	double LastAwardTime = -1.0;

	/** 0..1 through the current rank; 1 at the highest rank. */
	float GetRankProgress() const
	{
		if (NextRankXp < 0 || NextRankXp <= RankFloorXp)
		{
			return 1.f;
		}
		return FMath::Clamp(float(ServiceXp - RankFloorXp) / float(NextRankXp - RankFloorXp), 0.f, 1.f);
	}
};
