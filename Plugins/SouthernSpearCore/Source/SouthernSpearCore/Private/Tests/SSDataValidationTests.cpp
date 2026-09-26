// Copyright Southern Spear. All Rights Reserved.
//
// Shared validation and native Gameplay Tag tests.

#include "Misc/AutomationTest.h"

#include "SSCoreValidation.h"
#include "SSNativeGameplayTags.h"
#include "SSProjectSettings.h"
#include "SSStableId.h"
#include "SSTeamIdentityLibrary.h"
#include "SSTeamTypes.h"

#if WITH_DEV_AUTOMATION_TESTS

// --- Stable IDs --------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FSSStableIdValidation,
	"SouthernSpear.Core.Validation.StableId",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)

bool FSSStableIdValidation::RunTest(const FString& Parameters)
{
	ESSStableIdFailure Failure = ESSStableIdFailure::Empty;

	// Valid IDs.
	TestTrue(TEXT("A88 is valid"), FSSStableId(TEXT("A88")).Validate(Failure));
	TestTrue(TEXT("A88_Standard is valid"), FSSStableId(TEXT("A88_Standard")).Validate(Failure));
	TestTrue(TEXT("Murasian_Rifleman is valid"), FSSStableId(TEXT("Murasian_Rifleman")).Validate(Failure));
	TestTrue(TEXT("Dots, dashes and underscores are allowed"),
		FSSStableId(TEXT("a.b-c_d")).Validate(Failure));
	TestTrue(TEXT("Exactly the minimum length is valid"),
		FSSStableId(FString::ChrN(FSSStableId::MinLength, TEXT('a'))).Validate(Failure));
	TestTrue(TEXT("Exactly the maximum length is valid"),
		FSSStableId(FString::ChrN(FSSStableId::MaxLength, TEXT('a'))).Validate(Failure));

	// Invalid IDs, each for its own reason.
	FSSStableId(TEXT("")).Validate(Failure);
	TestEqual(TEXT("Empty is rejected"), Failure, ESSStableIdFailure::Empty);

	FSSStableId(TEXT("   ")).Validate(Failure);
	TestEqual(TEXT("Whitespace-only is rejected"), Failure, ESSStableIdFailure::Empty);

	FSSStableId(TEXT("a")).Validate(Failure);
	TestEqual(TEXT("Too short is rejected"), Failure, ESSStableIdFailure::LengthOutOfRange);

	FSSStableId(FString::ChrN(FSSStableId::MaxLength + 1, TEXT('a'))).Validate(Failure);
	TestEqual(TEXT("Too long is rejected"), Failure, ESSStableIdFailure::LengthOutOfRange);

	FSSStableId(TEXT("A88 Standard")).Validate(Failure);
	TestEqual(TEXT("A space is rejected"), Failure, ESSStableIdFailure::IllegalCharacter);

	FSSStableId(TEXT("A88/Standard")).Validate(Failure);
	TestEqual(TEXT("A slash is rejected"), Failure, ESSStableIdFailure::IllegalCharacter);

	FSSStableId(TEXT("1st_Regiment")).Validate(Failure);
	TestEqual(TEXT("A leading digit is rejected"), Failure, ESSStableIdFailure::BadLeadingCharacter);

	FSSStableId(TEXT("_Leading")).Validate(Failure);
	TestEqual(TEXT("A leading underscore is rejected"), Failure, ESSStableIdFailure::BadLeadingCharacter);

	FSSStableId(TEXT("Default")).Validate(Failure);
	TestEqual(TEXT("A reserved name is rejected"), Failure, ESSStableIdFailure::Reserved);

	// Duplicates.
	{
		TArray<FSSStableId> Ids;
		Ids.Add(FSSStableId(TEXT("A88")));
		Ids.Add(FSSStableId(TEXT("A89")));
		FString Description;
		TestFalse(TEXT("Distinct IDs report no duplicate"),
			FindDuplicateStableIds(Ids, Description));
		TestTrue(TEXT("No duplicate leaves the description empty"), Description.IsEmpty());
	}
	{
		TArray<FSSStableId> Ids;
		Ids.Add(FSSStableId(TEXT("A88")));
		Ids.Add(FSSStableId(TEXT("A89")));
		Ids.Add(FSSStableId(TEXT("A88")));
		FString Description;
		TestTrue(TEXT("A repeated ID is detected"), FindDuplicateStableIds(Ids, Description));
		TestTrue(TEXT("The duplicate is named in the message"),
			Description.Contains(TEXT("A88")));
	}

	// Comparison and hashing, so IDs can key a TMap.
	{
		TestTrue(TEXT("Equal IDs compare equal"), FSSStableId(TEXT("A88")) == FSSStableId(TEXT("A88")));
		TestTrue(TEXT("Different IDs compare unequal"), FSSStableId(TEXT("A88")) != FSSStableId(TEXT("A89")));
		TestTrue(TEXT("Comparison is case sensitive"), FSSStableId(TEXT("A88")) != FSSStableId(TEXT("a88")));

		TSet<FSSStableId> Set;
		Set.Add(FSSStableId(TEXT("A88")));
		Set.Add(FSSStableId(TEXT("A88")));
		TestEqual(TEXT("A TSet deduplicates equal IDs"), Set.Num(), 1);
	}

	return true;
}

// --- Team and tag validation -------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FSSCoreValidationOfTeamsAndTags,
	"SouthernSpear.Core.Validation.TeamsAndTags",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)

bool FSSCoreValidationOfTeamsAndTags::RunTest(const FString& Parameters)
{
	FString Error;

	// Teams.
	TestTrue(TEXT("TeamOne validates"),
		FSSCoreValidation::ValidateTeam(ESSTeamId::TeamOne, TEXT("test"), Error));
	TestTrue(TEXT("TeamTwo validates"),
		FSSCoreValidation::ValidateTeam(ESSTeamId::TeamTwo, TEXT("test"), Error));

	AddExpectedError(TEXT("ValidateTeam"), EAutomationExpectedErrorFlags::Contains, 0);
	Error.Reset();
	TestFalse(TEXT("None does not validate"),
		FSSCoreValidation::ValidateTeam(ESSTeamId::None, TEXT("test"), Error));
	TestTrue(TEXT("The team failure names the offending value"), Error.Contains(TEXT("None")));
	Error.Reset();

	// Gameplay Tags.
	TestTrue(TEXT("A native SS tag validates"),
		FSSCoreValidation::ValidateGameplayTag(TAG_SS_Weapon_A88, TEXT("test"), Error));
	Error.Reset();

	// A missing tag must fail rather than default. Defaulting a tag is how a
	// filter silently matches everything.
	AddExpectedError(TEXT("ValidateGameplayTag"), EAutomationExpectedErrorFlags::Contains, 0);
	TestFalse(TEXT("A missing tag does not validate"),
		FSSCoreValidation::ValidateGameplayTag(FGameplayTag(), TEXT("test"), Error));
	Error.Reset();

	// A tag from outside the SS root must fail.
	const FGameplayTag ForeignTag = FGameplayTag::RequestGameplayTag(FName(TEXT("Gameplay.Damage")));
	if (ForeignTag.IsValid())
	{
		AddExpectedError(TEXT("ValidateGameplayTag"), EAutomationExpectedErrorFlags::Contains, 0);
		TestFalse(TEXT("A non-SS tag does not validate"),
			FSSCoreValidation::ValidateGameplayTag(ForeignTag, TEXT("test"), Error));
		TestTrue(TEXT("The tag failure says it is outside the SS root"),
			Error.Contains(TEXT("SS.")));
	}
	else
	{
		AddInfo(TEXT("Gameplay.Damage was not registered; the non-SS tag check was skipped."));
	}

	return true;
}

// --- Native tags -------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FSSNativeTagsAreRegisteredUnderTheSSRoot,
	"SouthernSpear.Core.Validation.NativeTags",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)

bool FSSNativeTagsAreRegisteredUnderTheSSRoot::RunTest(const FString& Parameters)
{
	struct FTagUnderTest
	{
		const TCHAR* Label;
		const FGameplayTag Tag;
		const TCHAR* Expected;
	};

	const FTagUnderTest Tags[] =
	{
		{ TEXT("TeamOne"),        TAG_SS_Team_TeamOne,                       TEXT("SS.Team.TeamOne") },
		{ TEXT("TeamTwo"),        TAG_SS_Team_TeamTwo,                       TEXT("SS.Team.TeamTwo") },
		{ TEXT("Locality.Friendly"),   TAG_SS_Locality_Friendly,             TEXT("SS.Locality.Friendly") },
		{ TEXT("Locality.Opposing"),   TAG_SS_Locality_Opposing,             TEXT("SS.Locality.Opposing") },
		{ TEXT("Force.CDS"),      TAG_SS_Force_CommonwealthDefenceService,  TEXT("SS.Force.CommonwealthDefenceService") },
		{ TEXT("Force.MAF"),      TAG_SS_Force_MurasianArmedForces,         TEXT("SS.Force.MurasianArmedForces") },
		{ TEXT("Branch.CLS"),     TAG_SS_Branch_CommonwealthLandService,    TEXT("SS.Branch.CommonwealthLandService") },
		{ TEXT("Unit.ACR"),       TAG_SS_Unit_ACR,                           TEXT("SS.Unit.ACR") },
		{ TEXT("Unit.ACR.3"),     TAG_SS_Unit_ACR_3,                         TEXT("SS.Unit.ACR.3") },
		{ TEXT("Unit.2CG"),       TAG_SS_Unit_CommandoGroup2,                TEXT("SS.Unit.CommandoGroup2") },
		{ TEXT("Unit.SOR"),       TAG_SS_Unit_SpecialOperationsRegiment,     TEXT("SS.Unit.SpecialOperationsRegiment") },
		{ TEXT("Weapon.A88"),     TAG_SS_Weapon_A88,                         TEXT("SS.Weapon.A88") },
		{ TEXT("Weapon.A89"),     TAG_SS_Weapon_A89,                         TEXT("SS.Weapon.A89") },
		{ TEXT("Weapon.A4"),      TAG_SS_Weapon_A4,                          TEXT("SS.Weapon.A4") },
		{ TEXT("Weapon.A416"),    TAG_SS_Weapon_A416,                        TEXT("SS.Weapon.A416") },
		{ TEXT("Weapon.A417"),    TAG_SS_Weapon_A417,                        TEXT("SS.Weapon.A417") },
		{ TEXT("Weapon.A9"),      TAG_SS_Weapon_A9,                          TEXT("SS.Weapon.A9") },
		{ TEXT("Role.Rifleman"),  TAG_SS_Role_Rifleman,                      TEXT("SS.Role.Rifleman") },
		{ TEXT("Role.SectionCommander"), TAG_SS_Role_SectionCommander,       TEXT("SS.Role.SectionCommander") },
	};

	for (const FTagUnderTest& Entry : Tags)
	{
		if (!Entry.Tag.IsValid())
		{
			AddError(FString::Printf(TEXT("Native tag %s failed to register."), Entry.Label));
			continue;
		}
		TestEqual(FString::Printf(TEXT("Tag %s has the expected string"), Entry.Label),
			Entry.Tag.ToString(), FString(Entry.Expected));
	}

	// Project settings must agree with the registered vocabulary.
	const USSProjectSettings* Settings = USSProjectSettings::Get();
	if (TestNotNull(TEXT("Project settings are available"), Settings))
	{
		TestTrue(TEXT("Player formation unit is set to 3 ACR"),
			Settings->PlayerFormationUnit == TAG_SS_Unit_ACR_3);
		TestTrue(TEXT("Opposing force is the Murasian Armed Forces"),
			Settings->OpposingForce == TAG_SS_Force_MurasianArmedForces);

		TestEqual(TEXT("Exactly two playable team tags"),
			Settings->PlayableTeamTags.Num(), 2);
		TestTrue(TEXT("Playable teams include TeamOne"),
			Settings->PlayableTeamTags.HasTagExact(TAG_SS_Team_TeamOne));
		TestTrue(TEXT("Playable teams include TeamTwo"),
			Settings->PlayableTeamTags.HasTagExact(TAG_SS_Team_TeamTwo));

		// No team-less tag may appear in the playable set: a None team is not a
		// team, and letting one into this list would put it in a match.
		TestFalse(TEXT("Playable teams contain no locality tag"),
			Settings->PlayableTeamTags.HasTagExact(TAG_SS_Locality_Friendly));
		TestFalse(TEXT("Playable teams contain no locality tag"),
			Settings->PlayableTeamTags.HasTagExact(TAG_SS_Locality_Opposing));
	}

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
