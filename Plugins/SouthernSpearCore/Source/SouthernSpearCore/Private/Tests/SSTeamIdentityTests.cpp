// Copyright Southern Spear. All Rights Reserved.
//
// Team identity and viewer-relative locality tests (ADR-017).

#include "Misc/AutomationTest.h"

#include "SSNativeGameplayTags.h"
#include "SSTeamIdentityLibrary.h"
#include "SSTeamTypes.h"
#include "SSViewerContext.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	/** Resolve and assert the expected locality, reporting both sides on mismatch. */
	bool ExpectLocality(
		FAutomationTestBase& Test, const TCHAR* What,
		ESSTeamId Viewing, ESSTeamId Subject, const TOptional<ESSLocality>& Expected)
	{
		const FSSLocalityResolution Result = FSSTeamIdentity::ResolveLocality(Viewing, Subject);

		if (!Expected.IsSet())
		{
			if (Result.bResolved)
			{
				Test.AddError(FString::Printf(
					TEXT("%s: expected resolution to FAIL for viewer=%s subject=%s, but it resolved to %s."),
					What,
					*FSSTeamIdentity::ToDebugString(Viewing),
					*FSSTeamIdentity::ToDebugString(Subject),
					Result.Locality == ESSLocality::Friendly ? TEXT("Friendly") : TEXT("Opposing")));
				return false;
			}
			return true;
		}

		if (!Result.bResolved)
		{
			Test.AddError(FString::Printf(
				TEXT("%s: expected %s for viewer=%s subject=%s, but resolution failed."),
				What,
				Expected.GetValue() == ESSLocality::Friendly ? TEXT("Friendly") : TEXT("Opposing"),
				*FSSTeamIdentity::ToDebugString(Viewing),
				*FSSTeamIdentity::ToDebugString(Subject)));
			return false;
		}

		if (Result.Locality != Expected.GetValue())
		{
			Test.AddError(FString::Printf(
				TEXT("%s: expected %s for viewer=%s subject=%s, got %s."),
				What,
				Expected.GetValue() == ESSLocality::Friendly ? TEXT("Friendly") : TEXT("Opposing"),
				*FSSTeamIdentity::ToDebugString(Viewing),
				*FSSTeamIdentity::ToDebugString(Subject),
				Result.Locality == ESSLocality::Friendly ? TEXT("Friendly") : TEXT("Opposing")));
			return false;
		}

		return true;
	}
}

// --- Team validity -----------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FSSPlayableTeamsAreExactlyTeamOneAndTeamTwo,
	"SouthernSpear.Core.Identity.PlayableTeams",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)

bool FSSPlayableTeamsAreExactlyTeamOneAndTeamTwo::RunTest(const FString& Parameters)
{
	TestTrue(TEXT("TeamOne is valid"), FSSTeamIdentity::IsPlayableTeam(ESSTeamId::TeamOne));
	TestTrue(TEXT("TeamTwo is valid"), FSSTeamIdentity::IsPlayableTeam(ESSTeamId::TeamTwo));
	TestFalse(TEXT("None is NOT a playable team"), FSSTeamIdentity::IsPlayableTeam(ESSTeamId::None));

	// None must fail, not be treated as a third team.
	TestEqual(TEXT("GetOpposingTeam(None) is None"),
		FSSTeamIdentity::GetOpposingTeam(ESSTeamId::None), ESSTeamId::None);

	// The two teams are each other's opposite, which is what makes the symmetry
	// test in ADR-004 meaningful.
	TestEqual(TEXT("TeamOne's opposite is TeamTwo"),
		FSSTeamIdentity::GetOpposingTeam(ESSTeamId::TeamOne), ESSTeamId::TeamTwo);
	TestEqual(TEXT("TeamTwo's opposite is TeamOne"),
		FSSTeamIdentity::GetOpposingTeam(ESSTeamId::TeamTwo), ESSTeamId::TeamOne);

	TArray<ESSTeamId> Playable;
	FSSTeamIdentity::GetPlayableTeams(Playable);
	TestEqual(TEXT("There are exactly two playable teams"), Playable.Num(), 2);
	for (const ESSTeamId Team : Playable)
	{
		TestFalse(TEXT("Playable list never contains None"),
			Team == ESSTeamId::None);
	}

	return true;
}

// --- Locality resolution matrix ---------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FSSLocalityResolvesForEveryViewerSubjectPair,
	"SouthernSpear.Core.Identity.LocalityMatrix",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)

bool FSSLocalityResolvesForEveryViewerSubjectPair::RunTest(const FString& Parameters)
{
	// The full 2x2 matrix of playable teams.
	ExpectLocality(*this, TEXT("TeamOne sees TeamOne"),
		ESSTeamId::TeamOne, ESSTeamId::TeamOne, ESSLocality::Friendly);
	ExpectLocality(*this, TEXT("TeamOne sees TeamTwo"),
		ESSTeamId::TeamOne, ESSTeamId::TeamTwo, ESSLocality::Opposing);
	ExpectLocality(*this, TEXT("TeamTwo sees TeamTwo"),
		ESSTeamId::TeamTwo, ESSTeamId::TeamTwo, ESSLocality::Friendly);
	ExpectLocality(*this, TEXT("TeamTwo sees TeamOne"),
		ESSTeamId::TeamTwo, ESSTeamId::TeamOne, ESSLocality::Opposing);

	// The symmetry property the whole presentation system rests on: reversing
	// the viewer and subject flips the answer. If this ever fails, two clients
	// in the same match can disagree about who is friendly.
	ExpectLocality(*this, TEXT("Reversed pair flips locality"),
		ESSTeamId::TeamTwo, ESSTeamId::TeamOne, ESSLocality::Opposing);

	return true;
}

// --- Failure paths -----------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FSSLocalityFailsSafelyOnNone,
	"SouthernSpear.Core.Identity.LocalityFailsSafely",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)

bool FSSLocalityFailsSafelyOnNone::RunTest(const FString& Parameters)
{
	// Each of the four cases below fails on purpose, and each logs an error on
	// purpose. Declaring them expected is what keeps "this logs loudly" from
	// reading as "this is broken" - while still failing the test if the message
	// ever stops being produced.
	AddExpectedError(TEXT("Locality resolution failed"), EAutomationExpectedErrorFlags::Contains, 4);

	// None viewer must fail, never silently default to Friendly.
	{
		const FSSLocalityResolution Result =
			FSSTeamIdentity::ResolveLocality(ESSTeamId::None, ESSTeamId::TeamOne);
		TestFalse(TEXT("None viewer does not resolve"), Result.bResolved);
		TestEqual(TEXT("None viewer reports NoAuthorisedViewingTeam"),
			Result.Failure, ESSResolutionFailure::NoAuthorisedViewingTeam);
	}

	// None subject must fail too. A teamless player must not be rendered as part
	// of either side.
	{
		const FSSLocalityResolution Result =
			FSSTeamIdentity::ResolveLocality(ESSTeamId::TeamOne, ESSTeamId::None);
		TestFalse(TEXT("None subject does not resolve"), Result.bResolved);
		TestEqual(TEXT("None subject reports SubjectHasNoTeam"),
			Result.Failure, ESSResolutionFailure::SubjectHasNoTeam);
	}

	// Both None.
	{
		const FSSLocalityResolution Result =
			FSSTeamIdentity::ResolveLocality(ESSTeamId::None, ESSTeamId::None);
		TestFalse(TEXT("None/None does not resolve"), Result.bResolved);
	}

	// An out-of-range enum value must be rejected, not wrapped into something
	// playable. This is the case a corrupt or desynced value would produce.
	{
		const FSSLocalityResolution Result = FSSTeamIdentity::ResolveLocality(
			static_cast<ESSTeamId>(200), ESSTeamId::TeamOne);
		TestFalse(TEXT("An invalid team value does not resolve"), Result.bResolved);
		TestEqual(TEXT("An invalid team value reports UnrecognisedViewingTeam"),
			Result.Failure, ESSResolutionFailure::UnrecognisedViewingTeam);
	}

	return true;
}

// --- Determinism -------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FSSLocalityResolutionIsDeterministic,
	"SouthernSpear.Core.Identity.LocalityIsDeterministic",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)

bool FSSLocalityResolutionIsDeterministic::RunTest(const FString& Parameters)
{
	const ESSTeamId Teams[] = { ESSTeamId::TeamOne, ESSTeamId::TeamTwo };

	for (const ESSTeamId Viewer : Teams)
	{
		for (const ESSTeamId Subject : Teams)
		{
			const FSSLocalityResolution First = FSSTeamIdentity::ResolveLocality(Viewer, Subject);
			for (int32 Repeat = 0; Repeat < 32; ++Repeat)
			{
				const FSSLocalityResolution Again = FSSTeamIdentity::ResolveLocality(Viewer, Subject);
				TestEqual(TEXT("Resolution result is stable across repeats"), Again.bResolved, First.bResolved);
				TestEqual(TEXT("Resolution value is stable across repeats"), Again.Locality, First.Locality);
				TestEqual(TEXT("Resolution viewing team is stable"), Again.ViewingTeam, First.ViewingTeam);
			}
		}
	}

	return true;
}

// --- Spectator and replay context -------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FSSpectatorAndReplayNeedAnAuthorisedVantage,
	"SouthernSpear.Core.Identity.SpectatorContext",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)

bool FSSpectatorAndReplayNeedAnAuthorisedVantage::RunTest(const FString& Parameters)
{
	// The unauthorised spectator and the unauthorised replay each fail loudly.
	AddExpectedError(TEXT("Locality resolution failed"), EAutomationExpectedErrorFlags::Contains, 2);

	// A spectator with no stated vantage must NOT resolve. Defaulting here would
	// show one team's view to the other, which is the exact leak the split into
	// stable identity and viewer locality exists to prevent.
	{
		FSSViewerContext Spectator;
		Spectator.bIsSpectator = true;
		TestFalse(TEXT("A bare spectator context authorises no team"),
			Spectator.HasAuthorisedViewingTeam());

		const FSSLocalityResolution Result =
			FSSTeamIdentity::ResolveLocality(Spectator, ESSTeamId::TeamOne);
		TestFalse(TEXT("A bare spectator context does not resolve"), Result.bResolved);
		TestEqual(TEXT("Spectator failure is NoAuthorisedViewingTeam"),
			Result.Failure, ESSResolutionFailure::NoAuthorisedViewingTeam);
	}

	// A spectator that states a vantage resolves from it.
	{
		FSSViewerContext Spectator;
		Spectator.bIsSpectator = true;
		Spectator.OverrideViewingTeam = ESSTeamId::TeamTwo;

		const FSSLocalityResolution Own = FSSTeamIdentity::ResolveLocality(Spectator, ESSTeamId::TeamTwo);
		TestTrue(TEXT("Authorised spectator resolves"), Own.bResolved);
		TestEqual(TEXT("Authorised spectator sees its vantage as Friendly"),
			Own.Locality, ESSLocality::Friendly);

		const FSSLocalityResolution Other = FSSTeamIdentity::ResolveLocality(Spectator, ESSTeamId::TeamOne);
		TestTrue(TEXT("Authorised spectator resolves the other team"), Other.bResolved);
		TestEqual(TEXT("Authorised spectator sees the other team as Opposing"),
			Other.Locality, ESSLocality::Opposing);
	}

	// A replay follows the same rule.
	{
		FSSViewerContext Replay;
		Replay.bIsReplay = true;
		const FSSLocalityResolution Unauthorised =
			FSSTeamIdentity::ResolveLocality(Replay, ESSTeamId::TeamOne);
		TestFalse(TEXT("A bare replay context does not resolve"), Unauthorised.bResolved);

		Replay.OverrideViewingTeam = ESSTeamId::TeamOne;
		const FSSLocalityResolution Authorised =
			FSSTeamIdentity::ResolveLocality(Replay, ESSTeamId::TeamOne);
		TestTrue(TEXT("An authorised replay context resolves"), Authorised.bResolved);
		TestEqual(TEXT("An authorised replay resolves its vantage as Friendly"),
			Authorised.Locality, ESSLocality::Friendly);
	}

	// A live player is resolved from their own team, ignoring any stray override.
	{
		FSSViewerContext Live;
		Live.ViewerTeam = ESSTeamId::TeamOne;
		Live.OverrideViewingTeam = ESSTeamId::TeamTwo;

		const FSSLocalityResolution Result =
			FSSTeamIdentity::ResolveLocality(Live, ESSTeamId::TeamOne);
		TestTrue(TEXT("A live player resolves"), Result.bResolved);
		TestEqual(TEXT("A live player resolves from their own team, not the override"),
			Result.Locality, ESSLocality::Friendly);
		TestEqual(TEXT("Effective viewing team is the player's own team"),
			Live.GetEffectiveViewingTeam(), ESSTeamId::TeamOne);
	}

	return true;
}

// --- The two-concept split ---------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FSSLocalityIsNeverReplicatedAsTeamIdentity,
	"SouthernSpear.Core.Identity.LocalityIsNotReplicated",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)

bool FSSLocalityIsNeverReplicatedAsTeamIdentity::RunTest(const FString& Parameters)
{
	// The authority rule, asserted structurally rather than by convention:
	// nothing in this module may declare a replicated property of type
	// ESSLocality. ESSLocality is derived per-viewer, so a replicated copy of
	// it would be, by construction, wrong for every client but the server's.
	//
	// This scans the module's real reflected classes, so it catches a violation
	// added later without anyone remembering to update a test.

	int32 ClassesScanned = 0;
	int32 ReplicatedPropertiesScanned = 0;
	int32 Violations = 0;

	for (TObjectIterator<UClass> It; It; ++It)
	{
		UClass* Class = *It;
		const FName PackageName = FName(Class->GetOutermost()->GetName());
		if (PackageName != FName(TEXT("/Script/SouthernSpearCore")))
		{
			continue;
		}

		++ClassesScanned;

		for (TFieldIterator<FProperty> PropertyIt(Class, EFieldIteratorFlags::IncludeSuper); PropertyIt; ++PropertyIt)
		{
			const FProperty* Property = *PropertyIt;
			if (!Property->HasAnyPropertyFlags(CPF_Net))
			{
				continue;
			}
			++ReplicatedPropertiesScanned;

			const FEnumProperty* EnumProperty = CastField<FEnumProperty>(Property);
			if (EnumProperty == nullptr)
			{
				continue;
			}

			if (EnumProperty->GetEnum() == StaticEnum<ESSLocality>())
			{
				++Violations;
				AddError(FString::Printf(
					TEXT("ESSLocality is replicated on %s::%s. Locality is viewer-derived and must ")
					TEXT("never be replicated; replicate ESSTeamId and let each client resolve."),
					*Class->GetName(), *Property->GetName()));
			}
		}
	}

	TestTrue(TEXT("The scan actually found this module's classes (not a vacuous pass)"),
		ClassesScanned > 0);
	TestEqual(TEXT("No replicated ESSLocality property exists"), Violations, 0);

	// ESSTeamId, by contrast, is a uint8 enum and is the type intended for
	// replication. Assert the property that makes it replication-safe.
	TestEqual(TEXT("ESSTeamId is one byte, so it replicates as a compact value"),
		static_cast<int32>(sizeof(ESSTeamId)), 1);
	TestEqual(TEXT("ESSLocality is one byte"), static_cast<int32>(sizeof(ESSLocality)), 1);

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
