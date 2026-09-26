// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "SSStableId.h"
#include "SSTeamTypes.h"

/**
 * Shared validation helpers.
 *
 * Every content-construction boundary in Southern Spear routes its checks
 * through here rather than writing its own, so that "is this valid?" means the
 * same thing in a data asset, in a test and in a runtime guard. Failures log to
 * LogSSCore with enough context to find the offending row.
 */
class SSCORE_API FSSCoreValidation
{
public:
	/**
	 * Report a failed check.
	 *
	 * Returns false so callers can `return FSSCoreValidation::Fail(...)`, but
	 * the value is not a success signal - it is always a failure.
	 */
	static bool Fail(const TCHAR* CheckName, const FString& Reason);

	/** Validate a stable ID, logging and returning false when invalid. */
	static bool ValidateStableId(
		const FSSStableId& Id, const TCHAR* ContextDescription, FString& OutError);

	/** Validate a set of stable IDs, detecting duplicates as well as bad ones. */
	static bool ValidateStableIdSet(
		const TArray<FSSStableId>& Ids, const TCHAR* ContextDescription, FString& OutError);

	/** Validate that a team is one this build can actually resolve. */
	static bool ValidateTeam(ESSTeamId Team, const TCHAR* ContextDescription, FString& OutError);

	/**
	 * Validate a Gameplay Tag that is required to be present.
	 *
	 * A missing tag is a failure, not a default. Defaulting a tag is how a
	 * weapon ends up with no owner filter and quietly matches everything.
	 */
	static bool ValidateGameplayTag(
		const FGameplayTag& Tag, const TCHAR* ContextDescription, FString& OutError);
};
