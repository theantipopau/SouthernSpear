// Copyright Southern Spear. All Rights Reserved.

#include "SSKillFeedState.h"

void FSSKillFeedRules::Add(TArray<FSSKillFeedEntry>& Entries, const FSSKillFeedEntry& Entry)
{
	Entries.Add(Entry);
	if (Entries.Num() > MaxEntries)
	{
		Entries.RemoveAt(0, Entries.Num() - MaxEntries);
	}
}

TArray<FSSKillFeedEntry> FSSKillFeedRules::Visible(const TArray<FSSKillFeedEntry>& Entries, double Now)
{
	TArray<FSSKillFeedEntry> Out;
	for (int32 Index = Entries.Num() - 1; Index >= 0; --Index)
	{
		if (Now - Entries[Index].Time <= EntryLifetime)
		{
			Out.Add(Entries[Index]);
		}
	}
	return Out;
}

const FSSKillFeedEntry* FSSKillFeedRules::RecentLocalKill(const TArray<FSSKillFeedEntry>& Entries, double Now)
{
	for (int32 Index = Entries.Num() - 1; Index >= 0; --Index)
	{
		const FSSKillFeedEntry& Entry = Entries[Index];
		if (Entry.bLocalKiller && !Entry.bLocalVictim && Now - Entry.Time <= LocalKillLifetime)
		{
			return &Entry;
		}
	}
	return nullptr;
}

const FSSKillFeedEntry* FSSKillFeedRules::RecentLocalDeath(const TArray<FSSKillFeedEntry>& Entries, double Now)
{
	for (int32 Index = Entries.Num() - 1; Index >= 0; --Index)
	{
		const FSSKillFeedEntry& Entry = Entries[Index];
		if (Entry.bLocalVictim)
		{
			return Now - Entry.Time <= LocalDeathLifetime ? &Entry : nullptr;
		}
	}
	return nullptr;
}

FString FSSKillFeedRules::WeaponShortName(const FString& ItemClassName)
{
	FString Name = ItemClassName;
	Name.RemoveFromEnd(TEXT("_C"));
	Name.RemoveFromStart(TEXT("ID_SS_"));
	return Name;
}
