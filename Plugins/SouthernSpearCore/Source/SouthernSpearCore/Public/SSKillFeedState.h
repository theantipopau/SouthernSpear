// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "SSTeamTypes.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSKillFeedState.generated.h"

/** One elimination, as plain values: "Killer [weapon] Victim". */
USTRUCT(BlueprintType)
struct FSSKillFeedEntry
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "KillFeed") FString Killer;
	UPROPERTY(BlueprintReadOnly, Category = "KillFeed") FString Victim;
	/** Weapon short name (A88, A9...); empty when unknown. */
	UPROPERTY(BlueprintReadOnly, Category = "KillFeed") FString Weapon;
	UPROPERTY(BlueprintReadOnly, Category = "KillFeed") ESSTeamId KillerTeam = ESSTeamId::None;
	UPROPERTY(BlueprintReadOnly, Category = "KillFeed") ESSTeamId VictimTeam = ESSTeamId::None;
	UPROPERTY(BlueprintReadOnly, Category = "KillFeed") bool bLocalKiller = false;
	UPROPERTY(BlueprintReadOnly, Category = "KillFeed") bool bLocalVictim = false;
	/** World time (s) the entry arrived on this client. */
	UPROPERTY(BlueprintReadOnly, Category = "KillFeed") double Time = 0.0;
};

/** Pure kill-feed rules, testable without a world. */
struct SSCORE_API FSSKillFeedRules
{
	static constexpr int32 MaxEntries = 6;
	static constexpr double EntryLifetime = 8.0;
	static constexpr double LocalKillLifetime = 3.0;

	/** Appends and keeps only the newest MaxEntries. */
	static void Add(TArray<FSSKillFeedEntry>& Entries, const FSSKillFeedEntry& Entry);

	/** Entries still shown at Now, newest first. */
	static TArray<FSSKillFeedEntry> Visible(const TArray<FSSKillFeedEntry>& Entries, double Now);

	/** The local player's most recent kill still inside LocalKillLifetime, or nullptr. */
	static const FSSKillFeedEntry* RecentLocalKill(const TArray<FSSKillFeedEntry>& Entries, double Now);

	/** How long "KILLED IN ACTION" shows before the class selection opens. */
	static constexpr double LocalDeathLifetime = 4.0;

	/** The local player's own death still inside LocalDeathLifetime (the newest), or nullptr. */
	static const FSSKillFeedEntry* RecentLocalDeath(const TArray<FSSKillFeedEntry>& Entries, double Now);

	/** Weapon short name from an item definition class name: "ID_SS_A88_C" -> "A88"; others unchanged. */
	static FString WeaponShortName(const FString& ItemClassName);
};

/**
 * Kill feed for the local viewer. The Lyra bridge fills it from elimination messages
 * (server -> every client); UI modules only read it (ADR-019, guard SS002/SS005).
 * Client-local, never replicated, never read by gameplay.
 */
UCLASS()
class SSCORE_API USSKillFeedState : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	UPROPERTY(Transient, BlueprintReadOnly, Category = "KillFeed")
	TArray<FSSKillFeedEntry> Entries;

	/** The local viewer's team, for friendly/opposing colours. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "KillFeed")
	ESSTeamId LocalTeam = ESSTeamId::None;
};
