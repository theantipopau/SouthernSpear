// Copyright Southern Spear. All Rights Reserved.

#include "SSWeaponStats.h"

FName FSSWeaponStatsRules::WeaponFromItemDefinition(const FString& ClassName)
{
	static const FString Prefix = TEXT("ID_SS_");
	if (!ClassName.StartsWith(Prefix, ESearchCase::CaseSensitive))
	{
		return NAME_None;
	}
	FString Name = ClassName.Mid(Prefix.Len());
	Name.RemoveFromEnd(TEXT("_C"), ESearchCase::CaseSensitive);
	return Name.IsEmpty() ? NAME_None : FName(*Name);
}

const FSSWeaponStats* FSSWeaponStatsRules::Find(FName Weapon, TConstArrayView<FSSWeaponStats> Table)
{
	if (Weapon.IsNone())
	{
		return nullptr;
	}
	for (const FSSWeaponStats& Row : Table)
	{
		if (Row.Weapon == Weapon)
		{
			return &Row;
		}
	}
	return nullptr;
}

const FSSWeaponStats* FSSWeaponStatsRules::Find(FName Weapon)
{
	return Find(Weapon, GetDefault<USSWeaponStatsSettings>()->Weapons);
}

float FSSWeaponStatsRules::FireIntervalSeconds(const FSSWeaponStats& Stats)
{
	return 60.f / float(FMath::Max(1, Stats.RoundsPerMinute));
}

bool FSSWeaponStatsRules::Validate(TConstArrayView<FSSWeaponStats> Table, TArray<FString>& OutErrors)
{
	const int32 Before = OutErrors.Num();
	TSet<FName> Seen;
	for (const FSSWeaponStats& Row : Table)
	{
		const FString Name = Row.Weapon.ToString();
		if (Row.Weapon.IsNone())
		{
			OutErrors.Add(TEXT("A weapon row has no name."));
			continue;
		}
		if (Seen.Contains(Row.Weapon))
		{
			OutErrors.Add(FString::Printf(TEXT("Weapon %s has more than one row."), *Name));
		}
		Seen.Add(Row.Weapon);
		if (Row.RoundsPerMinute < 60 || Row.RoundsPerMinute > 1500)
		{
			OutErrors.Add(FString::Printf(TEXT("Weapon %s fires at %d rpm; expected 60..1500."), *Name, Row.RoundsPerMinute));
		}
		if (Row.MagazineSize < 1 || Row.MagazineSize > 300)
		{
			OutErrors.Add(FString::Printf(TEXT("Weapon %s holds %d rounds; expected 1..300."), *Name, Row.MagazineSize));
		}
		if (Row.SpreadScale < 0.1f || Row.SpreadScale > 10.f)
		{
			OutErrors.Add(FString::Printf(TEXT("Weapon %s spread scale %.2f is outside 0.1..10."), *Name, Row.SpreadScale));
		}
	}
	return OutErrors.Num() == Before;
}
