// Copyright Southern Spear. All Rights Reserved.
//
// Weapon table (W1): the shipped rows are valid, every loadout weapon has one, and the numbers are the
// source configs' (Docs/WEAPON_SOURCE_DATA.md), not Lyra's shared rifle.

#include "Misc/AutomationTest.h"

#include "SSWeaponStats.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	constexpr EAutomationTestFlags SSWeaponTestFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSWeaponStatsShipped, "SouthernSpear.Core.Weapons.ShippedTable", SSWeaponTestFlags)
bool FSSWeaponStatsShipped::RunTest(const FString& Parameters)
{
	const TArray<FSSWeaponStats>& Table = GetDefault<USSWeaponStatsSettings>()->Weapons;
	TArray<FString> Errors;
	TestTrue(TEXT("table valid"), FSSWeaponStatsRules::Validate(Table, Errors));
	for (const FString& Error : Errors)
	{
		AddError(Error);
	}

	// Every weapon the loadout hands out has a row.
	const TCHAR* Loadout[] = { TEXT("A88"), TEXT("A88G"), TEXT("A89"), TEXT("A4"), TEXT("A416"), TEXT("A25"), TEXT("A9") };
	for (const TCHAR* Name : Loadout)
	{
		TestNotNull(*FString::Printf(TEXT("%s has a row"), Name), FSSWeaponStatsRules::Find(FName(Name), Table));
	}

	// The weapons are no longer one rifle: the source numbers differ, and the table keeps them.
	const FSSWeaponStats* A88 = FSSWeaponStatsRules::Find(TEXT("A88"), Table);
	const FSSWeaponStats* A89 = FSSWeaponStatsRules::Find(TEXT("A89"), Table);
	const FSSWeaponStats* A25 = FSSWeaponStatsRules::Find(TEXT("A25"), Table);
	if (!A88 || !A89 || !A25)
	{
		return false;
	}
	TestEqual(TEXT("A88 682 rpm"), A88->RoundsPerMinute, 682);
	TestEqual(TEXT("A89 belt of 200"), A89->MagazineSize, 200);
	TestTrue(TEXT("A89 wider than the rifle"), A89->SpreadScale > A88->SpreadScale);
	TestTrue(TEXT("A25 tighter than the rifle"), A25->SpreadScale < A88->SpreadScale);
	TestFalse(TEXT("A25 is semi-automatic"), A25->bFullAuto);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSWeaponStatsRulesTest, "SouthernSpear.Core.Weapons.Rules", SSWeaponTestFlags)
bool FSSWeaponStatsRulesTest::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("class name"), FSSWeaponStatsRules::WeaponFromItemDefinition(TEXT("ID_SS_A88_C")), FName(TEXT("A88")));
	TestEqual(TEXT("asset name"), FSSWeaponStatsRules::WeaponFromItemDefinition(TEXT("ID_SS_A416")), FName(TEXT("A416")));
	TestEqual(TEXT("Lyra's own rifle is not ours"), FSSWeaponStatsRules::WeaponFromItemDefinition(TEXT("ID_Rifle_C")), FName(NAME_None));
	TestEqual(TEXT("empty after the prefix"), FSSWeaponStatsRules::WeaponFromItemDefinition(TEXT("ID_SS__C")), FName(NAME_None));

	FSSWeaponStats Row;
	Row.Weapon = TEXT("X");
	Row.RoundsPerMinute = 600;
	Row.MagazineSize = 30;
	Row.SpareMagazines = 4;
	TestEqual(TEXT("600 rpm is 0.1 s"), FSSWeaponStatsRules::FireIntervalSeconds(Row), 0.1f);
	TestEqual(TEXT("spare rounds"), FSSWeaponStatsRules::SpareRounds(Row), 120);

	TArray<FString> E;
	FSSWeaponStats Bad = Row;
	Bad.RoundsPerMinute = 5000;
	TestFalse(TEXT("absurd rate"), FSSWeaponStatsRules::Validate({ Bad }, E));
	E.Reset();
	TestFalse(TEXT("duplicate row"), FSSWeaponStatsRules::Validate({ Row, Row }, E));
	E.Reset();
	TestTrue(TEXT("good row"), FSSWeaponStatsRules::Validate({ Row }, E));
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
