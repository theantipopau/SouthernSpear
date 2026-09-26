// Copyright Southern Spear. All Rights Reserved.

#include "SSCoreValidation.h"

#include "SSCoreLog.h"
#include "SSNativeGameplayTags.h"
#include "SSTeamIdentityLibrary.h"

#include "GameplayTagContainer.h"

namespace
{
	/** Render a validation failure reason without trailing punctuation doubling. */
	FString Describe(ESSStableIdFailure Failure)
	{
		switch (Failure)
		{
		case ESSStableIdFailure::Empty:					return TEXT("is empty or whitespace");
		case ESSStableIdFailure::LengthOutOfRange:
			return FString::Printf(TEXT("has length outside [%d, %d]"),
				FSSStableId::MinLength, FSSStableId::MaxLength);
		case ESSStableIdFailure::IllegalCharacter:		return TEXT("contains a character outside [A-Za-z0-9_.-]");
		case ESSStableIdFailure::BadLeadingCharacter:	return TEXT("does not start with a letter");
		case ESSStableIdFailure::Reserved:				return TEXT("is a reserved name");
		default:										return TEXT("is invalid for an unknown reason");
		}
	}
}

bool FSSCoreValidation::Fail(const TCHAR* CheckName, const FString& Reason)
{
	UE_LOG(LogSSCore, Error, TEXT("[%s] %s"), CheckName, *Reason);
	return false;
}

bool FSSCoreValidation::ValidateStableId(
	const FSSStableId& Id, const TCHAR* ContextDescription, FString& OutError)
{
	ESSStableIdFailure Failure = ESSStableIdFailure::Empty;
	if (Id.Validate(Failure))
	{
		return true;
	}

	OutError = FString::Printf(TEXT("stable ID '%s' at %s %s"),
		*Id.GetValue(), ContextDescription, *Describe(Failure));
	return Fail(TEXT("ValidateStableId"), OutError);
}

bool FSSCoreValidation::ValidateStableIdSet(
	const TArray<FSSStableId>& Ids, const TCHAR* ContextDescription, FString& OutError)
{
	TArray<FString> Problems;

	for (const FSSStableId& Id : Ids)
	{
		ESSStableIdFailure Failure = ESSStableIdFailure::Empty;
		if (!Id.Validate(Failure))
		{
			Problems.Add(FString::Printf(TEXT("stable ID '%s' %s"),
				*Id.GetValue(), *Describe(Failure)));
		}
	}

	FString DuplicateDescription;
	if (FindDuplicateStableIds(Ids, DuplicateDescription))
	{
		Problems.Add(DuplicateDescription);
	}

	if (Problems.Num() == 0)
	{
		return true;
	}

	OutError = FString::Printf(TEXT("%s: %s"),
		ContextDescription, *FString::Join(Problems, TEXT("; ")));
	return Fail(TEXT("ValidateStableIdSet"), OutError);
}

bool FSSCoreValidation::ValidateTeam(
	ESSTeamId Team, const TCHAR* ContextDescription, FString& OutError)
{
	if (FSSTeamIdentity::IsPlayableTeam(Team))
	{
		return true;
	}

	OutError = FString::Printf(TEXT("team '%s' at %s is not a playable team (expected TeamOne or TeamTwo)"),
		*FSSTeamIdentity::ToDebugString(Team), ContextDescription);
	return Fail(TEXT("ValidateTeam"), OutError);
}

bool FSSCoreValidation::ValidateGameplayTag(
	const FGameplayTag& Tag, const TCHAR* ContextDescription, FString& OutError)
{
	if (!Tag.IsValid())
	{
		OutError = FString::Printf(TEXT("a required Gameplay Tag at %s is missing"), ContextDescription);
		return Fail(TEXT("ValidateGameplayTag"), OutError);
	}

	// Every Southern Spear tag lives under the SS root. A tag that does not is
	// either a typo or a foreign tag leaking in, and both are worth a hard
	// failure rather than a default.
	const FString TagString = Tag.ToString();
	if (!TagString.StartsWith(TEXT("SS."), ESearchCase::CaseSensitive))
	{
		OutError = FString::Printf(
			TEXT("Gameplay Tag '%s' at %s is outside the SS root; all Southern Spear tags must start with 'SS.'"),
			*TagString, ContextDescription);
		return Fail(TEXT("ValidateGameplayTag"), OutError);
	}

	return true;
}
