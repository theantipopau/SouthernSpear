// Copyright Southern Spear. All Rights Reserved.

#include "SSLoadoutSubsystem.h"

#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "GameFramework/Pawn.h"
#include "Inventory/LyraInventoryItemDefinition.h"
#include "Inventory/LyraInventoryManagerComponent.h"

DEFINE_LOG_CATEGORY_STATIC(LogSSLoadout, Log, All);

namespace
{
	// ULyraQuickBarComponent is not exported from LyraGame; its functions are
	// UFUNCTIONs, so they are called through reflection.
	UActorComponent* FindQuickBar(const AController* Controller)
	{
		static UClass* QuickBarClass = FindObject<UClass>(nullptr, TEXT("/Script/LyraGame.LyraQuickBarComponent"));
		return QuickBarClass ? Controller->GetComponentByClass(QuickBarClass) : nullptr;
	}

	template <typename TParams>
	bool CallQuickBar(UObject* Target, const TCHAR* Name, TParams& Params)
	{
		UFunction* Function = Target ? Target->FindFunction(FName(Name)) : nullptr;
		if (!Function || Function->ParmsSize != sizeof(TParams))
		{
			UE_LOG(LogSSLoadout, Error, TEXT("Quick bar function %s missing or changed signature."), Name);
			return false;
		}
		Target->ProcessEvent(Function, &Params);
		return true;
	}

	struct FSlotsParams { TArray<ULyraInventoryItemInstance*> ReturnValue; };
	struct FNextFreeParams { int32 ReturnValue = INDEX_NONE; };
	struct FAddToSlotParams { int32 SlotIndex; ULyraInventoryItemInstance* Item; };
	struct FSetActiveParams { int32 NewIndex; };
}

bool USSLoadoutSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId USSLoadoutSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USSLoadoutSubsystem, STATGROUP_Tickables);
}

void USSLoadoutSubsystem::Tick(float DeltaTime)
{
	UWorld* World = GetWorld();
	if (!World || World->GetNetMode() == NM_Client)
	{
		return;
	}
	// Lyra grants its own starting items shortly after a pawn spawns; wait a
	// beat so ours land in the next free slots rather than racing it.
	Accumulator += DeltaTime;
	if (Accumulator < 0.5f)
	{
		return;
	}
	Accumulator = 0.f;

	for (FConstControllerIterator It = World->GetControllerIterator(); It; ++It)
	{
		AController* Controller = It->Get();
		APawn* Pawn = Controller ? Controller->GetPawn() : nullptr;
		if (Pawn && !HandledPawns.Contains(Pawn) && Pawn->GetGameTimeSinceCreation() > 0.5f)
		{
			HandledPawns.Add(Pawn);
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

void USSLoadoutSubsystem::Grant(AController* Controller)
{
	const USSLoadoutSettings* Settings = GetDefault<USSLoadoutSettings>();
	ULyraInventoryManagerComponent* Inventory = Controller->FindComponentByClass<ULyraInventoryManagerComponent>();
	UActorComponent* QuickBar = FindQuickBar(Controller);
	if (!Inventory || !QuickBar || Settings->StartingItems.Num() == 0)
	{
		return;
	}

	int32 FirstSlot = INDEX_NONE;
	for (const FSoftClassPath& Path : Settings->StartingItems)
	{
		// ULyraInventoryItemDefinition is not exported, so check the type by name.
		static UClass* ItemDefClass = FindObject<UClass>(nullptr, TEXT("/Script/LyraGame.LyraInventoryItemDefinition"));
		UClass* Loaded = Path.TryLoadClass<UObject>();
		TSubclassOf<ULyraInventoryItemDefinition> ItemDef = (Loaded && ItemDefClass && Loaded->IsChildOf(ItemDefClass)) ? Loaded : nullptr;
		if (!ItemDef)
		{
			UE_LOG(LogSSLoadout, Error, TEXT("Starting item '%s' does not load as a Lyra item definition."), *Path.ToString());
			continue;
		}
		ULyraInventoryItemInstance* Item = Inventory->FindFirstItemStackByDefinition(ItemDef);
		if (!Item)
		{
			Item = Inventory->AddItemDefinition(ItemDef, 1);
		}

		FSlotsParams Slots;
		if (!Item || !CallQuickBar(QuickBar, TEXT("GetSlots"), Slots))
		{
			continue;
		}
		int32 Slot = Slots.ReturnValue.IndexOfByKey(Item);
		if (Slot == INDEX_NONE)
		{
			FNextFreeParams Free;
			CallQuickBar(QuickBar, TEXT("GetNextFreeItemSlot"), Free);
			if (Free.ReturnValue == INDEX_NONE)
			{
				UE_LOG(LogSSLoadout, Warning, TEXT("No free quick-bar slot for '%s'."), *Path.ToString());
				continue;
			}
			FAddToSlotParams Add { Free.ReturnValue, Item };
			CallQuickBar(QuickBar, TEXT("AddItemToSlot"), Add);
			Slot = Free.ReturnValue;
		}
		if (FirstSlot == INDEX_NONE)
		{
			FirstSlot = Slot;
		}
	}
	if (Settings->bActivateFirstItem && FirstSlot != INDEX_NONE)
	{
		FSetActiveParams Active { FirstSlot };
		CallQuickBar(QuickBar, TEXT("SetActiveSlotIndex"), Active);
	}
	UE_LOG(LogSSLoadout, Verbose, TEXT("Loadout granted to %s (active slot %d)."), *Controller->GetName(), FirstSlot);
}
