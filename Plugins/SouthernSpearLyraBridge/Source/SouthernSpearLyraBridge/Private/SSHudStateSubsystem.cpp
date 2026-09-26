// Copyright Southern Spear. All Rights Reserved.

#include "SSHudStateSubsystem.h"

#include "Character/LyraHealthComponent.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "GameplayTagContainer.h"
#include "SSLocalHudState.h"
#include "UObject/UnrealType.h"

namespace
{
	// Lyra's inventory and quick-bar classes are not exported from LyraGame:
	// find them by path and call their UFUNCTIONs through reflection.
	UClass* LyraClass(const TCHAR* Path) { return FindObject<UClass>(nullptr, Path); }

	UObject* ActiveSlotItem(AController* Controller)
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

	int32 StatCount(UObject* Item, const FGameplayTag& Tag)
	{
		UFunction* Fn = Item && Tag.IsValid() ? Item->FindFunction(TEXT("GetStatTagStackCount")) : nullptr;
		if (!Fn)
		{
			return -1;
		}
		struct { FGameplayTag Tag; int32 ReturnValue = 0; } Params { Tag };
		Item->ProcessEvent(Fn, &Params);
		return Params.ReturnValue;
	}

	FText ItemName(UObject* Item)
	{
		const FClassProperty* DefProp = Item ? CastField<FClassProperty>(Item->GetClass()->FindPropertyByName(TEXT("ItemDef"))) : nullptr;
		const UClass* Def = DefProp ? Cast<UClass>(DefProp->GetObjectPropertyValue_InContainer(Item)) : nullptr;
		const UObject* Cdo = Def ? Def->GetDefaultObject() : nullptr;
		const FTextProperty* NameProp = Cdo ? CastField<FTextProperty>(Cdo->GetClass()->FindPropertyByName(TEXT("DisplayName"))) : nullptr;
		return NameProp ? NameProp->GetPropertyValue_InContainer(Cdo) : FText::GetEmpty();
	}
}

bool USSHudStateSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* World = Cast<UWorld>(Outer);
	return World && World->GetNetMode() != NM_DedicatedServer && Super::ShouldCreateSubsystem(Outer);
}

bool USSHudStateSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId USSHudStateSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USSHudStateSubsystem, STATGROUP_Tickables);
}

void USSHudStateSubsystem::Tick(float DeltaTime)
{
	UWorld* World = GetWorld();
	USSLocalHudState* State = World ? World->GetSubsystem<USSLocalHudState>() : nullptr;
	APlayerController* Player = World ? World->GetFirstPlayerController() : nullptr;
	if (!State)
	{
		return;
	}
	APawn* Pawn = Player && Player->IsLocalController() ? Player->GetPawn() : nullptr;

	static UClass* HealthClass = LyraClass(TEXT("/Script/LyraGame.LyraHealthComponent"));
	const ULyraHealthComponent* Health = Pawn && HealthClass
		? static_cast<const ULyraHealthComponent*>(Pawn->GetComponentByClass(HealthClass)) : nullptr;
	State->bHasPawn = Health != nullptr;
	State->Health = Health ? Health->GetHealth() : 0.f;
	State->MaxHealth = Health ? Health->GetMaxHealth() : 0.f;

	static const FGameplayTag MagazineTag = FGameplayTag::RequestGameplayTag(TEXT("Lyra.ShooterGame.Weapon.MagazineAmmo"), false);
	static const FGameplayTag SpareTag = FGameplayTag::RequestGameplayTag(TEXT("Lyra.ShooterGame.Weapon.SpareAmmo"), false);
	UObject* Item = Pawn ? ActiveSlotItem(Player) : nullptr;
	State->Magazine = StatCount(Item, MagazineTag);
	State->Reserve = StatCount(Item, SpareTag);
	State->WeaponName = ItemName(Item);
}
