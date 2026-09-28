// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "SSProgressionSettings.h"
#include "SSServiceRecord.h"

/** Awards already earned by one player in the current match, per event. Server only. */
struct FSSMatchTally
{
	TMap<ESSServiceEvent, int32> Earned;
};

/**
 * Pure progression rules (ADR-032): award caps, record updates and schema
 * migration. Levels and ranks are Core's (FSSServiceRanks, ADR-034). No world, no files, no clock beyond what the
 * caller passes, so every rule is unit-testable.
 */
struct SSPROG_API FSSProgressionRules
{
	/**
	 * A usable award table: one rule per event at most, no None event, no zero
	 * award, and every positive award capped at 1..100 per match.
	 */
	static bool ValidateAwards(TConstArrayView<FSSXpAwardRule> Awards, TArray<FString>& OutErrors);

	static const FSSXpAwardRule* FindRule(ESSServiceEvent Event, TConstArrayView<FSSXpAwardRule> Awards);

	/**
	 * The XP one more occurrence of Event earns this match, and count it. Zero
	 * without a rule or once a positive award has reached its cap; a penalty
	 * always applies.
	 */
	static int32 GrantAward(FSSMatchTally& Tally, ESSServiceEvent Event, TConstArrayView<FSSXpAwardRule> Awards);

	/** Apply one event to a record: XP (never below zero) and the matching statistic. */
	static void ApplyAward(FSSServiceRecord& Record, ESSServiceEvent Event, int32 XpDelta);

	/**
	 * Bring a loaded record to the current schema. Fails, leaving the record
	 * untouched, for a version below 1 or above FSSServiceRecord::CurrentSchemaVersion.
	 */
	static bool Migrate(FSSServiceRecord& Record, FString& OutError);

	/** A player id safe as a file name: letters, digits, '-' and '_' only, 1..64 characters; empty if nothing usable. */
	static FString SanitisePlayerId(const FString& PlayerId);

	/** A callsign the player may choose: 2..16 characters of letters, digits, space, '-' or '_', trimmed. */
	static bool IsValidCallsign(const FString& Callsign);

	/** Short player-facing name of an event ("Round won"). */
	static FText EventName(ESSServiceEvent Event);
};
