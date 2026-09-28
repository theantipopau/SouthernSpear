// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "SSServiceRecord.generated.h"

SSPROG_API DECLARE_LOG_CATEGORY_EXTERN(LogSSProgression, Log, All);

/** Counts of what a player has done, for the service record screen. Facts, never XP. */
USTRUCT(BlueprintType)
struct FSSServiceStatistics
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Service") int32 MatchesCompleted = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Service") int32 MatchesWon = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Service") int32 RoundsWon = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Service") int32 RoundsWonAlive = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Service") int32 ObjectivesCaptured = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Service") int32 FriendlyKills = 0;
};

/**
 * A player's persistent service record (TDD §6.4, ADR-032). Schema v1.
 *
 * Versioned from day one: a record carries its SchemaVersion, loading runs the
 * migration chain, and a record from a newer schema is refused rather than
 * mis-read. Add fields only with a version bump and a migration step in
 * FSSProgressionRules::Migrate.
 *
 * Rank is not stored: it is derived from ServiceXp and the rank table, so a
 * change to the thresholds applies to every record without a migration.
 */
USTRUCT(BlueprintType)
struct FSSServiceRecord
{
	GENERATED_BODY()

	static constexpr int32 CurrentSchemaVersion = 1;

	UPROPERTY(BlueprintReadOnly, Category = "Service")
	int32 SchemaVersion = CurrentSchemaVersion;

	/** Stable id of the player this record belongs to. */
	UPROPERTY(BlueprintReadOnly, Category = "Service")
	FString PlayerId;

	/** Chosen display name; empty until the player sets one. */
	UPROPERTY(BlueprintReadOnly, Category = "Service")
	FString Callsign;

	/** Drives the displayed rank. Never negative. */
	UPROPERTY(BlueprintReadOnly, Category = "Service")
	int32 ServiceXp = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Service")
	FSSServiceStatistics Statistics;

	/** Earned in training; permanent, never revoked (GDD §5, TDD §6.4). Empty until training exists. */
	UPROPERTY(BlueprintReadOnly, Category = "Service")
	TArray<FName> Qualifications;

	UPROPERTY(BlueprintReadOnly, Category = "Service")
	TArray<FName> Commendations;

	/** ISO 8601, UTC. */
	UPROPERTY(BlueprintReadOnly, Category = "Service")
	FString CreatedUtc;

	/** ISO 8601, UTC. */
	UPROPERTY(BlueprintReadOnly, Category = "Service")
	FString LastSavedUtc;
};
