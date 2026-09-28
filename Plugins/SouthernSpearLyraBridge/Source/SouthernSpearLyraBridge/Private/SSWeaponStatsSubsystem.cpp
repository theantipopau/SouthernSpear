// Copyright Southern Spear. All Rights Reserved.

#include "SSWeaponStatsSubsystem.h"

#include "Curves/CurveFloat.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Equipment/LyraEquipmentInstance.h"
#include "Equipment/LyraEquipmentManagerComponent.h"
#include "GameFramework/Controller.h"
#include "GameFramework/Pawn.h"
#include "GameplayTagContainer.h"
#include "Inventory/LyraInventoryItemInstance.h"
#include "Inventory/LyraInventoryManagerComponent.h"
#include "SSLyraReflection.h"
#include "SSWeaponStats.h"
#include "UObject/UnrealType.h"

DEFINE_LOG_CATEGORY_STATIC(LogSSWeaponStats, Log, All);

using namespace SSLyraReflection;

namespace
{
	/** The A-series row for an item instance (ID_SS_<Weapon>), or nullptr. */
	const FSSWeaponStats* StatsForItem(UObject* Item)
	{
		const UClass* Def = ItemDefinition(Item);
		return Def ? FSSWeaponStatsRules::Find(FSSWeaponStatsRules::WeaponFromItemDefinition(Def->GetName())) : nullptr;
	}

	struct FTagCountParams { FGameplayTag Tag; int32 ReturnValue = 0; };
	struct FTagStackParams { FGameplayTag Tag; int32 StackCount = 0; };

	int32 TagCount(UObject* Item, const FGameplayTag& Tag)
	{
		UFunction* Fn = Item->FindFunction(TEXT("GetStatTagStackCount"));
		if (!Fn || Fn->ParmsSize != sizeof(FTagCountParams))
		{
			return 0;
		}
		FTagCountParams Params{ Tag };
		Item->ProcessEvent(Fn, &Params);
		return Params.ReturnValue;
	}

	/** Server: make the item's stack for Tag exactly Value (Lyra only adds and removes). */
	bool SetTag(UObject* Item, const FGameplayTag& Tag, int32 Value)
	{
		const int32 Current = TagCount(Item, Tag);
		if (!Tag.IsValid() || Current == Value)
		{
			return Tag.IsValid();
		}
		UFunction* Fn = Item->FindFunction(Value > Current ? TEXT("AddStatTagStack") : TEXT("RemoveStatTagStack"));
		if (!Fn || Fn->ParmsSize != sizeof(FTagStackParams))
		{
			return false;
		}
		FTagStackParams Params{ Tag, FMath::Abs(Value - Current) };
		Item->ProcessEvent(Fn, &Params);
		return true;
	}
}

bool USSWeaponStatsSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId USSWeaponStatsSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USSWeaponStatsSubsystem, STATGROUP_Tickables);
}

void USSWeaponStatsSubsystem::Tick(float DeltaTime)
{
	Accumulator += DeltaTime;
	if (Accumulator < 0.25f)
	{
		return;
	}
	Accumulator = 0.f;
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	if (World->GetNetMode() != NM_Client)
	{
		ApplyAmmo(World);
	}
	ApplySpread(World);
}

void USSWeaponStatsSubsystem::ApplyAmmo(UWorld* World)
{
	static const FGameplayTag MagSize = FGameplayTag::RequestGameplayTag(TEXT("Lyra.ShooterGame.Weapon.MagazineSize"), false);
	static const FGameplayTag MagAmmo = FGameplayTag::RequestGameplayTag(TEXT("Lyra.ShooterGame.Weapon.MagazineAmmo"), false);
	static const FGameplayTag Spare = FGameplayTag::RequestGameplayTag(TEXT("Lyra.ShooterGame.Weapon.SpareAmmo"), false);

	for (FConstControllerIterator It = World->GetControllerIterator(); It; ++It)
	{
		AController* Controller = It->Get();
		ULyraInventoryManagerComponent* Inventory = Controller ? Controller->FindComponentByClass<ULyraInventoryManagerComponent>() : nullptr;
		if (!Inventory)
		{
			continue;
		}
		for (ULyraInventoryItemInstance* ItemInstance : Inventory->GetAllItems())
		{
			UObject* Item = ItemInstance;
			if (!Item || DoneItems.Contains(Item))
			{
				continue;
			}
			DoneItems.Add(Item);
			const FSSWeaponStats* Stats = StatsForItem(Item);
			if (!Stats)
			{
				continue; // not an A-series weapon (grenades, Lyra's own items)
			}
			// Lyra's InitialItemStats fragment has already filled the rifle's numbers: replace them.
			const bool bOk = SetTag(Item, MagSize, Stats->MagazineSize) && SetTag(Item, MagAmmo, Stats->MagazineSize)
				&& SetTag(Item, Spare, FSSWeaponStatsRules::SpareRounds(*Stats));
			UE_LOG(LogSSWeaponStats, Log, TEXT("%s: magazine %d, spare %d%s."), *Stats->Weapon.ToString(), Stats->MagazineSize,
				FSSWeaponStatsRules::SpareRounds(*Stats), bOk ? TEXT("") : TEXT(" (a Lyra stat function or tag was missing)"));
		}
	}
}

void USSWeaponStatsSubsystem::ApplySpread(UWorld* World)
{
	static UClass* RangedClass = LyraClass(TEXT("/Script/LyraGame.LyraRangedWeaponInstance"));
	static FStructProperty* SpreadCurveProp = RangedClass
		? FindFProperty<FStructProperty>(RangedClass, TEXT("HeatToSpreadCurve")) : nullptr;
	if (!RangedClass || !SpreadCurveProp || SpreadCurveProp->Struct != FRuntimeFloatCurve::StaticStruct())
	{
		if (!bWarnedSpread)
		{
			bWarnedSpread = true;
			UE_LOG(LogSSWeaponStats, Error, TEXT("LyraRangedWeaponInstance.HeatToSpreadCurve not found; weapon spread is Lyra's."));
		}
		return;
	}

	for (TActorIterator<APawn> It(World); It; ++It)
	{
		ULyraEquipmentManagerComponent* Equipment = It->FindComponentByClass<ULyraEquipmentManagerComponent>();
		if (!Equipment)
		{
			continue;
		}
		for (ULyraEquipmentInstance* Instance : Equipment->GetEquipmentInstancesOfType(TSubclassOf<ULyraEquipmentInstance>(RangedClass)))
		{
			if (!Instance || DoneInstances.Contains(Instance))
			{
				continue;
			}
			// The item may not have replicated yet on a client: try again next pass.
			UObject* Item = Instance->GetInstigator();
			if (!Item)
			{
				continue;
			}
			DoneInstances.Add(Instance);
			const FSSWeaponStats* Stats = StatsForItem(Item);
			if (!Stats || FMath::IsNearlyEqual(Stats->SpreadScale, 1.f))
			{
				continue;
			}
			FRuntimeFloatCurve* Curve = SpreadCurveProp->ContainerPtrToValuePtr<FRuntimeFloatCurve>(Instance);
			FRichCurve* Rich = Curve ? Curve->GetRichCurve() : nullptr;
			if (!Rich)
			{
				continue;
			}
			// This instance's own copy of the curve: spread (degrees) against heat, scaled uniformly.
			for (FRichCurveKey& Key : Rich->Keys)
			{
				Key.Value *= Stats->SpreadScale;
				Key.ArriveTangent *= Stats->SpreadScale;
				Key.LeaveTangent *= Stats->SpreadScale;
			}
			UE_LOG(LogSSWeaponStats, Log, TEXT("%s: spread x%.2f on %s."), *Stats->Weapon.ToString(), Stats->SpreadScale,
				*It->GetName());
		}
	}
}
