// Copyright Southern Spear. All Rights Reserved.

#include "SSStableId.h"

#include "SSCoreLog.h"

namespace
{
	/** Names that must never be used as stable IDs, because tooling reserves them. */
	const TCHAR* const ReservedIds[] =
	{
		TEXT("None"),
		TEXT("Default"),
		TEXT("Test"),
		TEXT("Debug"),
		TEXT("Self"),
		TEXT("Null"),
	};
}

bool FSSStableId::Validate(ESSStableIdFailure& OutFailure) const
{
	if (Value.IsEmpty() || Value.TrimStartAndEnd().IsEmpty())
	{
		OutFailure = ESSStableIdFailure::Empty;
		return false;
	}

	if (Value.Len() < MinLength || Value.Len() > MaxLength)
	{
		OutFailure = ESSStableIdFailure::LengthOutOfRange;
		return false;
	}

	for (const TCHAR* Reserved : ReservedIds)
	{
		if (Value.Equals(Reserved, ESearchCase::IgnoreCase))
		{
			OutFailure = ESSStableIdFailure::Reserved;
			return false;
		}
	}

	const TCHAR First = Value[0];
	if (!((First >= TEXT('A') && First <= TEXT('Z')) || (First >= TEXT('a') && First <= TEXT('z'))))
	{
		OutFailure = ESSStableIdFailure::BadLeadingCharacter;
		return false;
	}

	for (const TCHAR Char : Value)
	{
		const bool bDigit = (Char >= TEXT('0') && Char <= TEXT('9'));
		const bool bUpper = (Char >= TEXT('A') && Char <= TEXT('Z'));
		const bool bLower = (Char >= TEXT('a') && Char <= TEXT('z'));
		const bool bSeparator = (Char == TEXT('_') || Char == TEXT('.') || Char == TEXT('-'));
		if (!(bDigit || bUpper || bLower || bSeparator))
		{
			OutFailure = ESSStableIdFailure::IllegalCharacter;
			return false;
		}
	}

	return true;
}

bool FSSStableId::ValidateAndLog(const TCHAR* ContextDescription) const
{
	ESSStableIdFailure Failure = ESSStableIdFailure::Empty;
	if (Validate(Failure))
	{
		return true;
	}

	// FString, not const TCHAR*: the formatted branch builds a temporary, and a
	// raw pointer into it would dangle the moment the switch scope ended.
	FString Reason = TEXT("is invalid for an unknown reason");
	switch (Failure)
	{
	case ESSStableIdFailure::Empty:					Reason = TEXT("is empty or whitespace"); break;
	case ESSStableIdFailure::LengthOutOfRange:
		Reason = FString::Printf(TEXT("has length outside [%d, %d]"), MinLength, MaxLength);
		break;
	case ESSStableIdFailure::IllegalCharacter:		Reason = TEXT("contains a character outside [A-Za-z0-9_.-]"); break;
	case ESSStableIdFailure::BadLeadingCharacter:	Reason = TEXT("does not start with a letter"); break;
	case ESSStableIdFailure::Reserved:				Reason = TEXT("is a reserved name"); break;
	default:										break;
	}

	UE_LOG(LogSSCore, Error,
		TEXT("Invalid stable ID '%s' at %s: %s."), *Value, ContextDescription, *Reason);
	return false;
}

bool FindDuplicateStableIds(
	const TArray<FSSStableId>& Ids, FString& OutDuplicateDescription)
{
	TSet<FString> Seen;
	TArray<FString> Duplicates;

	for (const FSSStableId& Id : Ids)
	{
		const FString& Value = Id.GetValue();
		bool bAlreadySeen = false;
		Seen.Add(Value, &bAlreadySeen);
		if (bAlreadySeen && !Duplicates.Contains(Value))
		{
			Duplicates.Add(Value);
		}
	}

	if (Duplicates.Num() == 0)
	{
		OutDuplicateDescription.Reset();
		return false;
	}

	OutDuplicateDescription = FString::Printf(
		TEXT("%d duplicate stable ID(s): %s"),
		Duplicates.Num(), *FString::Join(Duplicates, TEXT(", ")));
	return true;
}
