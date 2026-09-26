// Copyright Southern Spear. All Rights Reserved.
//
// Faction presentation resolver tests (ADR-004, ADR-017).

#include "Misc/AutomationTest.h"

#include "Presentation/SSFactionPresentationResolver.h"
#include "Presentation/SSFactionPresentationTypes.h"
#include "SSTeamTypes.h"
#include "SSViewerContext.h"
#include "UObject/UnrealType.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	constexpr EAutomationTestFlags SSPresentationTestFlags =
		EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter;

	FSSViewerContext LiveViewer(ESSTeamId Team)
	{
		FSSViewerContext Context;
		Context.ViewerTeam = Team;
		return Context;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FSSPresentationDualPerspective,
	"SouthernSpear.Presentation.DualPerspective",
	SSPresentationTestFlags)

bool FSSPresentationDualPerspective::RunTest(const FString& Parameters)
{
	const FSSFactionPresentationTable Table = FSSFactionPresentationResolver::MakePlaceholderTable();

	struct FCase { ESSTeamId Viewer; ESSTeamId Subject; ESSLocality Locality; ESSFactionPresentationId Id; };
	const FCase Cases[] = {
		{ ESSTeamId::TeamOne, ESSTeamId::TeamOne, ESSLocality::Friendly, ESSFactionPresentationId::ACR3 },
		{ ESSTeamId::TeamOne, ESSTeamId::TeamTwo, ESSLocality::Opposing, ESSFactionPresentationId::MAF },
		{ ESSTeamId::TeamTwo, ESSTeamId::TeamTwo, ESSLocality::Friendly, ESSFactionPresentationId::ACR3 },
		{ ESSTeamId::TeamTwo, ESSTeamId::TeamOne, ESSLocality::Opposing, ESSFactionPresentationId::MAF },
	};

	for (const FCase& Case : Cases)
	{
		const FSSPresentationResolution R =
			FSSFactionPresentationResolver::Resolve(LiveViewer(Case.Viewer), Case.Subject, Table);
		TestTrue(TEXT("resolved"), R.bResolved);
		TestEqual(TEXT("locality"), R.Locality, Case.Locality);
		TestEqual(TEXT("presentation"), R.Presentation.PresentationId, Case.Id);
		TestEqual(TEXT("subject team passed through"), R.SubjectTeam, Case.Subject);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FSSPresentationFailsSafely,
	"SouthernSpear.Presentation.FailsSafely",
	SSPresentationTestFlags)

bool FSSPresentationFailsSafely::RunTest(const FString& Parameters)
{
	AddExpectedError(TEXT("Presentation not resolved"), EAutomationExpectedErrorFlags::Contains, 4);
	AddExpectedError(TEXT("resolution failed"), EAutomationExpectedErrorFlags::Contains, 0);

	const FSSFactionPresentationTable Table = FSSFactionPresentationResolver::MakePlaceholderTable();

	auto ExpectFailure = [&](const TCHAR* What, const FSSViewerContext& Viewer, ESSTeamId Subject)
	{
		const FSSPresentationResolution R = FSSFactionPresentationResolver::Resolve(Viewer, Subject, Table);
		TestFalse(What, R.bResolved);
		TestEqual(What, R.Failure, ESSPresentationFailure::LocalityUnresolved);
		TestEqual(What, R.Presentation.PresentationId, ESSFactionPresentationId::None);
	};

	ExpectFailure(TEXT("invalid viewer"), LiveViewer(ESSTeamId::None), ESSTeamId::TeamOne);
	ExpectFailure(TEXT("invalid subject"), LiveViewer(ESSTeamId::TeamOne), ESSTeamId::None);

	FSSViewerContext Spectator;
	Spectator.bIsSpectator = true;
	ExpectFailure(TEXT("spectator without vantage"), Spectator, ESSTeamId::TeamTwo);

	FSSViewerContext Replay;
	Replay.bIsReplay = true;
	ExpectFailure(TEXT("replay without vantage"), Replay, ESSTeamId::TeamOne);

	// An authorised spectator vantage does resolve.
	Spectator.OverrideViewingTeam = ESSTeamId::TeamTwo;
	const FSSPresentationResolution Authorised =
		FSSFactionPresentationResolver::Resolve(Spectator, ESSTeamId::TeamTwo, Table);
	TestTrue(TEXT("authorised spectator resolves"), Authorised.bResolved);
	TestEqual(TEXT("authorised spectator sees own vantage as 3 ACR"),
		Authorised.Presentation.PresentationId, ESSFactionPresentationId::ACR3);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FSSPresentationMissingDataFailsVisibly,
	"SouthernSpear.Presentation.MissingDataFailsVisibly",
	SSPresentationTestFlags)

bool FSSPresentationMissingDataFailsVisibly::RunTest(const FString& Parameters)
{
	AddExpectedError(TEXT("Presentation data missing or incomplete"), EAutomationExpectedErrorFlags::Contains, 2);

	// Opposing entry wiped: must fail, not borrow the Friendly entry.
	FSSFactionPresentationTable Table = FSSFactionPresentationResolver::MakePlaceholderTable();
	Table.Opposing = FSSFactionPresentation();
	FSSPresentationResolution R =
		FSSFactionPresentationResolver::Resolve(LiveViewer(ESSTeamId::TeamOne), ESSTeamId::TeamTwo, Table);
	TestFalse(TEXT("missing opposing fails"), R.bResolved);
	TestEqual(TEXT("reason"), R.Failure, ESSPresentationFailure::MissingPresentationData);
	TestEqual(TEXT("no substitute presentation"), R.Presentation.PresentationId, ESSFactionPresentationId::None);

	// Friendly entry present but incomplete (no mesh).
	Table = FSSFactionPresentationResolver::MakePlaceholderTable();
	Table.Friendly.CharacterMesh.Reset();
	R = FSSFactionPresentationResolver::Resolve(LiveViewer(ESSTeamId::TeamOne), ESSTeamId::TeamOne, Table);
	TestFalse(TEXT("incomplete friendly fails"), R.bResolved);
	TestEqual(TEXT("reason"), R.Failure, ESSPresentationFailure::MissingPresentationData);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FSSPresentationDeterministic,
	"SouthernSpear.Presentation.Deterministic",
	SSPresentationTestFlags)

bool FSSPresentationDeterministic::RunTest(const FString& Parameters)
{
	const FSSFactionPresentationTable Table = FSSFactionPresentationResolver::MakePlaceholderTable();
	const FSSPresentationResolution First =
		FSSFactionPresentationResolver::Resolve(LiveViewer(ESSTeamId::TeamTwo), ESSTeamId::TeamOne, Table);
	for (int32 Index = 0; Index < 100; ++Index)
	{
		const FSSPresentationResolution Again =
			FSSFactionPresentationResolver::Resolve(LiveViewer(ESSTeamId::TeamTwo), ESSTeamId::TeamOne, Table);
		if (Again.bResolved != First.bResolved || Again.Locality != First.Locality
			|| Again.Presentation.PresentationId != First.Presentation.PresentationId)
		{
			AddError(FString::Printf(TEXT("Resolution changed on iteration %d."), Index));
			return false;
		}
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FSSPresentationSameGameplayIdentity,
	"SouthernSpear.Presentation.SameGameplayIdentity",
	SSPresentationTestFlags)

bool FSSPresentationSameGameplayIdentity::RunTest(const FString& Parameters)
{
	// One subject, seen from both sides: drawn as 3 ACR and as MAF, but the
	// gameplay identity carried through is the same team in both cases.
	const FSSFactionPresentationTable Table = FSSFactionPresentationResolver::MakePlaceholderTable();
	const FSSPresentationResolution AsFriend =
		FSSFactionPresentationResolver::Resolve(LiveViewer(ESSTeamId::TeamOne), ESSTeamId::TeamOne, Table);
	const FSSPresentationResolution AsEnemy =
		FSSFactionPresentationResolver::Resolve(LiveViewer(ESSTeamId::TeamTwo), ESSTeamId::TeamOne, Table);

	TestEqual(TEXT("friendly view is 3 ACR"), AsFriend.Presentation.PresentationId, ESSFactionPresentationId::ACR3);
	TestEqual(TEXT("opposing view is MAF"), AsEnemy.Presentation.PresentationId, ESSFactionPresentationId::MAF);
	TestEqual(TEXT("same gameplay identity"), AsFriend.SubjectTeam, AsEnemy.SubjectTeam);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FSSPresentationReflectionIsCosmeticOnly,
	"SouthernSpear.Presentation.ReflectionIsCosmeticOnly",
	SSPresentationTestFlags)

bool FSSPresentationReflectionIsCosmeticOnly::RunTest(const FString& Parameters)
{
	// Every reflected field of the presentation types must be cosmetic: no
	// replicated property, no team identity, no locality, no object pointer
	// that could reach a gameplay object. Only the allowlisted kinds pass.
	const UScriptStruct* Structs[] = {
		FSSFactionPresentation::StaticStruct(),
		FSSFactionPresentationTable::StaticStruct(),
	};

	const UEnum* LocalityEnum = StaticEnum<ESSLocality>();
	const UEnum* TeamEnum = StaticEnum<ESSTeamId>();
	const UEnum* PresentationEnum = StaticEnum<ESSFactionPresentationId>();

	for (const UScriptStruct* Struct : Structs)
	{
		for (TFieldIterator<FProperty> It(Struct); It; ++It)
		{
			const FProperty* Property = *It;
			const FString Where = FString::Printf(TEXT("%s.%s"), *Struct->GetName(), *Property->GetName());

			TestFalse(*(Where + TEXT(" is not replicated")), Property->HasAnyPropertyFlags(CPF_Net | CPF_RepNotify));

			bool bAllowed = false;
			if (const FEnumProperty* EnumProperty = CastField<FEnumProperty>(Property))
			{
				const UEnum* Enum = EnumProperty->GetEnum();
				TestFalse(*(Where + TEXT(" is not ESSLocality")), Enum == LocalityEnum);
				TestFalse(*(Where + TEXT(" is not ESSTeamId")), Enum == TeamEnum);
				bAllowed = Enum == PresentationEnum;
			}
			else if (Property->IsA<FTextProperty>())
			{
				bAllowed = true;
			}
			else if (const FStructProperty* StructProperty = CastField<FStructProperty>(Property))
			{
				bAllowed = StructProperty->Struct == TBaseStructure<FSoftObjectPath>::Get()
					|| StructProperty->Struct == FSSFactionPresentation::StaticStruct();
			}

			TestTrue(*(Where + TEXT(" is an allowlisted cosmetic kind")), bAllowed);
		}
	}
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
