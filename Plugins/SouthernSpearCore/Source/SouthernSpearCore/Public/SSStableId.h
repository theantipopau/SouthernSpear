// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Containers/UnrealString.h"

/** Why a stable ID was rejected. */
enum class ESSStableIdFailure : uint8
{
	/** The ID was empty or whitespace. */
	Empty,

	/** Shorter or longer than the permitted range. */
	LengthOutOfRange,

	/** Contained a character outside [A-Za-z0-9_.-]. */
	IllegalCharacter,

	/** Started with a character that is not a letter. */
	BadLeadingCharacter,

	/** Matched a reserved name that must not be used as an ID. */
	Reserved,
};

/**
 * A validated, stable identifier for content data.
 *
 * "Stable" means it survives content iteration: it is the key a save, a
 * progression record or a presentation set is looked up by, so it must not be
 * derived from a display name or an asset path that may be renamed.
 *
 * This is a value type with no world access. It is deliberately the ONLY way
 * content is keyed in this module, so that an invalid key is caught where it is
 * constructed rather than as a silent lookup miss much later.
 */
struct SSCORE_API FSSStableId
{
	/** Minimum permitted identifier length. */
	static constexpr int32 MinLength = 2;

	/** Maximum permitted identifier length. */
	static constexpr int32 MaxLength = 64;

	FSSStableId() = default;

	/** Construct from a candidate. Does not validate; call IsValid or Validate. */
	explicit FSSStableId(const FString& InValue) : Value(InValue) {}

	const FString& GetValue() const { return Value; }

	/** True when this ID passes every rule in Validate. */
	bool IsValid() const
	{
		ESSStableIdFailure Unused = ESSStableIdFailure::Empty;
		return Validate(Unused);
	}

	/**
	 * Validate this ID, reporting why it failed.
	 *
	 * @param OutFailure Receives the reason. Left untouched when valid.
	 * @return True when the ID is valid.
	 */
	bool Validate(ESSStableIdFailure& OutFailure) const;

	/**
	 * Validate and, on failure, log to LogSSCore.
	 *
	 * Use this at data-construction boundaries where a bad ID should be loud.
	 */
	bool ValidateAndLog(const TCHAR* ContextDescription) const;

	/** Whether the ID is valid. Logs to LogSSCore when it is not. */
	bool IsValidOrLog(const TCHAR* ContextDescription) const
	{
		return ValidateAndLog(ContextDescription);
	}

	/** Whether the ID is valid. Logs to LogSSCore when it is not. */
	explicit operator bool() const { return IsValid(); }

	friend bool operator==(const FSSStableId& A, const FSSStableId& B)
	{
		return A.Value.Equals(B.Value, ESearchCase::CaseSensitive);
	}

	friend bool operator!=(const FSSStableId& A, const FSSStableId& B) { return !(A == B); }

	/** Ordering, so IDs can live in sorted sets. */
	friend bool operator<(const FSSStableId& A, const FSSStableId& B)
	{
		return A.Value < B.Value;
	}

	/** Hash for TSet and TMap. */
	friend uint32 GetTypeHash(const FSSStableId& Id)
	{
		return GetTypeHash(Id.Value);
	}

private:
	FString Value;
};

/**
 * Checks that no ID in a set repeats.
 *
 * Duplicates are reported with both offenders named, because "duplicate ID" with
 * no detail is the least actionable validation message there is.
 */
SSCORE_API bool FindDuplicateStableIds(
	const TArray<FSSStableId>& Ids, FString& OutDuplicateDescription);
