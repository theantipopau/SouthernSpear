// Copyright Southern Spear. All Rights Reserved.

#include "SSLoadoutSubsystem.h"

#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Inventory/LyraInventoryItemDefinition.h"
#include "Inventory/LyraInventoryManagerComponent.h"

DEFINE_LOG_CATEGORY_STATIC(LogSSLoadout, Log, All);

namespace
{
	UActorComponent* FindQuickBar(const AController* Controller)
	{
		static UClass* QuickBarClass = FindObject<UClass>(nullptr, TEXT("/Script/LyraGame.LyraQuickBarComponent"));
		return QuickBarClass ? Controller->GetComponentByClass(QuickBarClass) : nullptr;
	}

	template <typename TParams>
	bool CallReflected(UObject* Target, const TCHAR* Name, TParams& Params)
	{
		UFunction* Function = Target ? Target->FindFunction(FName(Name)) : nullptr;
		if (!Function || Function->ParmsSize != sizeof(TParams))
		{
			UE_LOG(LogSSLoadout, Error, TEXT("Function %s missing or changed signature."), Name);
			return false;
		}
		Target->ProcessEvent(Function, &Params);
		return true;
	}

	struct FSlotsParams { TArray<ULyraInventoryItemInstance*> ReturnValue; };
	struct FNextFreeParams { int32 ReturnValue = INDEX_NONE; };
	struct FAddToSlotParams { int32 SlotIndex; ULyraInventoryItemInstance* Item; };
	struct FRemoveFromSlotParams { int32 SlotIndex; ULyraInventoryItemInstance* ReturnValue = nullptr; };
	struct FSetActiveParams { int32 NewIndex; };
	struct FRestartParams { AController* Controller; bool bForceReset; };

	// Bots spread over the roles (weights: mostly riflemen).
	ESSKitRole RandomBotRole()
	{
		static const ESSKitRole Weighted[] = { ESSKitRole::Rifleman, ESSKitRole::Rifleman, ESSKitRole::Rifleman,
			ESSKitRole::Medic, ESSKitRole::MachineGunner, ESSKitRole::Sniper, ESSKitRole::Grenadier };
		return Weighted[FMath::RandRange(0, UE_ARRAY_COUNT(Weighted) - 1)];
	}
}

const FSSKitDefinition* USSLoadoutSettings::FindKit(ESSKitRole Role, bool bSpecialForces) const
{
	for (const FSSKitDefinition& Kit : Kits)
	{
		if (Kit.Role == Role && Kit.bSpecialForces == bSpecialForces)
		{
			return &Kit;
		}
	}
	return nullptr;
}

bool USSLoadoutSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId USSLoadoutSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USSLoadoutSubsystem, STATGROUP_Tickables);
}

void USSLoadoutSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	if (USSKitSelection* Selection = InWorld.GetSubsystem<USSKitSelection>())
	{
		const FString MapName = FPackageName::GetShortName(InWorld.GetOutermost()->GetName()).Replace(TEXT("UEDPIE_0_"), TEXT(""));
		Selection->bSpecialForcesMap = GetDefault<USSLoadoutSettings>()->SpecialForcesMaps.Contains(MapName);
	}
}

void USSLoadoutSubsystem::Tick(float DeltaTime)
{
	UWorld* World = GetWorld();
	if (!World || World->GetNetMode() == NM_Client)
	{
		return;
	}
	Accumulator += DeltaTime;
	if (Accumulator < 0.25f)
	{
		return;
	}
	Accumulator = 0.f;

	USSKitSelection* Selection = World->GetSubsystem<USSKitSelection>();
	for (FConstControllerIterator It = World->GetControllerIterator(); It; ++It)
	{
		AController* Controller = It->Get();
		if (!Controller)
		{
			continue;
		}
		ESSKitRole Role;
		if (Selection && !Controller->IsPlayerController() && !Selection->GetKit(Controller, Role))
		{
			Selection->RequestKit(Controller, RandomBotRole());
			Selection->ConsumeChange(Controller); // bots take it on their next spawn
		}
		APawn* Pawn = Controller->GetPawn();
		if (Selection && Pawn && HandledPawns.Contains(Pawn) && Selection->ConsumeChange(Controller))
		{
			Respawn(Controller); // class changed while alive: apply now at deployment
			continue;
		}
		if (Pawn && !HandledPawns.Contains(Pawn) && Pawn->GetGameTimeSinceCreation() > 0.5f)
		{
			HandledPawns.Add(Pawn);
			if (Selection)
			{
				Selection->ConsumeChange(Controller); // this spawn already uses the latest choice
			}
			Grant(Controller);
		}
	}
	for (auto SetIt = HandledPawns.CreateIterator(); SetIt; ++SetIt)
	{
		if (!SetIt->IsValid())
		{
			SetIt.RemoveCurrent();
		}
	}
}

void USSLoadoutSubsystem::Respawn(AController* Controller)
{
	UWorld* World = GetWorld();
	AGameModeBase* GameMode = World ? World->GetAuthGameMode() : nullptr;
	APawn* Pawn = Controller->GetPawn();
	if (!GameMode || !Pawn)
	{
		return;
	}
	Controller->UnPossess();
	Pawn->Destroy();
	FRestartParams Params { Controller, false };
	CallReflected(GameMode, TEXT("RequestPlayerRestartNextFrame"), Params);
	UE_LOG(LogSSLoadout, Log, TEXT("%s changed class: respawning at deployment."), *Controller->GetName());
}

void USSLoadoutSubsystem::Grant(AController* Controller)
{
	const USSLoadoutSettings* Settings = GetDefault<USSLoadoutSettings>();
	ULyraInventoryManagerComponent* Inventory = Controller->FindComponentByClass<ULyraInventoryManagerComponent>();
	UActorComponent* QuickBar = FindQuickBar(Controller);
	if (!Inventory || !QuickBar)
	{
		return;
	}

	const USSKitSelection* Selection = GetWorld()->GetSubsystem<USSKitSelection>();
	ESSKitRole Role = ESSKitRole::Rifleman;
	if (Selection)
	{
		Selection->GetKit(Controller, Role);
	}
	const bool bSF = Selection && Selection->bSpecialForcesMap;
	const FSSKitDefinition* Kit = Settings->FindKit(Role, bSF);
	if (!Kit && bSF)
	{
		Kit = Settings->FindKit(Role, false);
	}
	const TArray<FSoftClassPath>& Items = Kit ? Kit->Items : Settings->StartingItems;
	if (Items.Num() == 0)
	{
		return;
	}

	// Fresh kit every spawn: empty the quick bar and inventory first (they live
	// on the controller and outlast the pawn), so ammunition resets and a class
	// change swaps weapons.
	FSlotsParams Existing;
	if (CallReflected(QuickBar, TEXT("GetSlots"), Existing))
	{
		for (int32 Slot = 0; Slot < Existing.ReturnValue.Num(); ++Slot)
		{
			FRemoveFromSlotParams Remove { Slot };
			CallReflected(QuickBar, TEXT("RemoveItemFromSlot"), Remove);
		}
	}
	for (ULyraInventoryItemInstance* Old : Inventory->GetAllItems())
	{
		Inventory->RemoveItemInstance(Old);
	}

	static UClass* ItemDefClass = FindObject<UClass>(nullptr, TEXT("/Script/LyraGame.LyraInventoryItemDefinition"));
	int32 FirstSlot = INDEX_NONE;
	for (const FSoftClassPath& Path : Items)
	{
		UClass* Loaded = Path.TryLoadClass<UObject>();
		TSubclassOf<ULyraInventoryItemDefinition> ItemDef = (Loaded && ItemDefClass && Loaded->IsChildOf(ItemDefClass)) ? Loaded : nullptr;
		if (!ItemDef)
		{
			UE_LOG(LogSSLoadout, Error, TEXT("Kit item '%s' does not load as a Lyra item definition."), *Path.ToString());
			continue;
		}
		ULyraInventoryItemInstance* Item = Inventory->AddItemDefinition(ItemDef, 1);
		FNextFreeParams Free;
		if (!Item || !CallReflected(QuickBar, TEXT("GetNextFreeItemSlot"), Free) || Free.ReturnValue == INDEX_NONE)
		{
			UE_LOG(LogSSLoadout, Warning, TEXT("No free quick-bar slot for '%s'."), *Path.ToString());
			continue;
		}
		FAddToSlotParams Add { Free.ReturnValue, Item };
		CallReflected(QuickBar, TEXT("AddItemToSlot"), Add);
		if (FirstSlot == INDEX_NONE)
		{
			FirstSlot = Free.ReturnValue;
		}
	}
	if (Settings->bActivateFirstItem && FirstSlot != INDEX_NONE)
	{
		FSetActiveParams Active { FirstSlot };
		CallReflected(QuickBar, TEXT("SetActiveSlotIndex"), Active);
	}
	UE_LOG(LogSSLoadout, Log, TEXT("Kit %d%s granted to %s (%d item(s))."), (int32)Role, bSF ? TEXT(" SF") : TEXT(""),
		*Controller->GetName(), Items.Num());
}
