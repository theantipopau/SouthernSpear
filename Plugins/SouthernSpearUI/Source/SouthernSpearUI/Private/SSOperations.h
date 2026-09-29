// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Misc/PackageName.h"

/**
 * The operations the front end offers and the loading screen names: one list, so a map is added in one
 * place. The loading art for an operation is /SouthernSpearUI/Textures/T_SS_Load_<ArtKey>, imported by
 * Tools/Unreal/setup_ui.py from Docs/images/loadingscreens/<ArtKey>.png (any case) when that file exists; without it the
 * loading screen shows the key art.
 */
namespace SSOperations
{
	struct FOperation
	{
		const TCHAR* Map;     // package path, e.g. /Game/Maps/L_RedGum_01
		const TCHAR* ArtKey;  // T_SS_Load_<ArtKey>
		FText Title;
		FText Description;
		FText Meta;
	};

	inline TConstArrayView<FOperation> All()
	{
		static const FOperation Ops[] = {
			{ TEXT("/Game/Maps/L_RedGum_01"), TEXT("RedGum"),
			  NSLOCTEXT("SSMenu", "RedGum", "Red Gum Station"),
			  NSLOCTEXT("SSMenu", "RedGumDesc", "An outback cattle station: the north paddock, the homestead, the south paddock."),
			  NSLOCTEXT("SSMenu", "RedGumMeta", "3 OBJECTIVES  ·  OPEN PADDOCKS") },
			{ TEXT("/Game/Maps/L_DryRiver_01"), TEXT("DryRiver"),
			  NSLOCTEXT("SSMenu", "DryRiver", "Dry River"),
			  NSLOCTEXT("SSMenu", "DryRiverDesc", "A dry creek line between a water point and a farmstead."),
			  NSLOCTEXT("SSMenu", "DryRiverMeta", "2 OBJECTIVES  ·  CREEK BED") },
			{ TEXT("/Game/Maps/L_Saltbush_01"), TEXT("Saltbush"),
			  NSLOCTEXT("SSMenu", "Saltbush", "Saltbush Flats"),
			  NSLOCTEXT("SSMenu", "SaltbushDesc", "Arid scrub and stone country: a windmill, the stock yards, a dry dam."),
			  NSLOCTEXT("SSMenu", "SaltbushMeta", "3 OBJECTIVES  ·  ROCKY COVER") },
			{ TEXT("/Game/Maps/L_SelatCanal_01"), TEXT("SelatCanal"),
			  NSLOCTEXT("SSMenu", "SelatCanal", "Selat Canal"),
			  NSLOCTEXT("SSMenu", "SelatCanalDesc", "A Murasian canal district: the footbridge, market row, the pump house."),
			  NSLOCTEXT("SSMenu", "SelatCanalMeta", "SPECIAL FORCES  ·  CLOSE QUARTERS") },
			{ TEXT("/Game/Maps/L_Bluestone_01"), TEXT("Bluestone"),
			  NSLOCTEXT("SSMenu", "Bluestone", "Bluestone Quarry"),
			  NSLOCTEXT("SSMenu", "BluestoneDesc", "A flooded slate pit: the loading bay, the cutting face, the spoil heaps."),
			  NSLOCTEXT("SSMenu", "BluestoneMeta", "3 OBJECTIVES  ·  CLOSE QUARTERS") },
		};
		return Ops;
	}

	/** The package name of a map reference: "/Game/Maps/L_X.L_X", "/Game/Maps/L_X" and "L_X" all give "L_X". */
	inline FString ShortMapName(const FString& Map)
	{
		FString Name = FPackageName::GetShortName(Map);
		int32 Dot = INDEX_NONE;
		if (Name.FindChar(TEXT('.'), Dot))
		{
			Name.LeftInline(Dot);
		}
		return Name;
	}

	inline const FOperation* Find(const FString& Map)
	{
		const FString Wanted = ShortMapName(Map);
		if (Wanted.IsEmpty())
		{
			return nullptr;
		}
		for (const FOperation& Op : All())
		{
			if (ShortMapName(Op.Map).Equals(Wanted, ESearchCase::IgnoreCase))
			{
				return &Op;
			}
		}
		return nullptr;
	}

	struct FMode
	{
		FText Name;
		FText Summary;
	};

	/** The two rule sets (ADR-018, ADR-031), as the front end names them. Every line must match what the game does. */
	inline FMode Mode(bool bSection)
	{
		if (bSection)
		{
			return { NSLOCTEXT("SSMenu", "RulesSection", "SECTION ASSAULT  ·  ONE LIFE"),
				NSLOCTEXT("SSLoading", "SectionSummary", "One life per round. One side attacks, the other defends, and the sides swap at half time. "
					"Attackers win by taking the last objective or wiping out the defenders; defenders win by wiping out the attackers or holding out until the clock runs down. "
					"First to five rounds.") };
		}
		return { NSLOCTEXT("SSMenu", "RulesObjective", "OBJECTIVE ASSAULT  ·  RESPAWNS"),
			NSLOCTEXT("SSLoading", "ObjectiveSummary", "Both sides fight over the same objectives, one at a time and in order. Stand in the ring to capture; "
				"an enemy inside contests it. Take the last objective to win the round. Respawns are unlimited.") };
	}
}
