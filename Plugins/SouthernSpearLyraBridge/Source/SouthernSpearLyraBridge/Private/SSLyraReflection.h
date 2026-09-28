// Copyright Southern Spear. All Rights Reserved.
//
// Lyra's inventory and quick-bar classes are not exported from LyraGame: find them by path and call their
// UFUNCTIONs through reflection. Shared by the bridge's HUD state and kill feed.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Controller.h"
#include "GameFramework/PlayerState.h"
#include "GenericTeamAgentInterface.h"
#include "SSTeamTypes.h"
#include "UObject/UnrealType.h"

namespace SSLyraReflection
{
	inline UClass* LyraClass(const TCHAR* Path) { return FindObject<UClass>(nullptr, Path); }

	/** The item in the controller's active quick-bar slot (the held weapon), or nullptr. */
	inline UObject* ActiveSlotItem(AController* Controller)
	{
		static UClass* QuickBarClass = LyraClass(TEXT("/Script/LyraGame.LyraQuickBarComponent"));
		UActorComponent* QuickBar = QuickBarClass && Controller ? Controller->GetComponentByClass(QuickBarClass) : nullptr;
		UFunction* Fn = QuickBar ? QuickBar->FindFunction(TEXT("GetActiveSlotItem")) : nullptr;
		if (!Fn)
		{
			return nullptr;
		}
		struct { UObject* ReturnValue = nullptr; } Params;
		QuickBar->ProcessEvent(Fn, &Params);
		return Params.ReturnValue;
	}

	/** The item instance's definition class (ID_SS_A88_C...), or nullptr. */
	inline const UClass* ItemDefinition(UObject* Item)
	{
		const FClassProperty* DefProp = Item ? CastField<FClassProperty>(Item->GetClass()->FindPropertyByName(TEXT("ItemDef"))) : nullptr;
		return DefProp ? Cast<UClass>(DefProp->GetObjectPropertyValue_InContainer(Item)) : nullptr;
	}

	/** The item definition's DisplayName, or empty. */
	inline FText ItemName(UObject* Item)
	{
		const UClass* Def = ItemDefinition(Item);
		const UObject* Cdo = Def ? Def->GetDefaultObject() : nullptr;
		const FTextProperty* NameProp = Cdo ? CastField<FTextProperty>(Cdo->GetClass()->FindPropertyByName(TEXT("DisplayName"))) : nullptr;
		return NameProp ? NameProp->GetPropertyValue_InContainer(Cdo) : FText::GetEmpty();
	}

	/** Lyra team 1/2 -> TeamOne/TeamTwo (IGenericTeamAgentInterface on the player state). */
	inline ESSTeamId TeamOf(const APlayerState* PlayerState)
	{
		const IGenericTeamAgentInterface* Agent = Cast<IGenericTeamAgentInterface>(PlayerState);
		const uint8 Id = Agent ? Agent->GetGenericTeamId().GetId() : FGenericTeamId::NoTeam.GetId();
		return Id == 1 ? ESSTeamId::TeamOne : Id == 2 ? ESSTeamId::TeamTwo : ESSTeamId::None;
	}
}
