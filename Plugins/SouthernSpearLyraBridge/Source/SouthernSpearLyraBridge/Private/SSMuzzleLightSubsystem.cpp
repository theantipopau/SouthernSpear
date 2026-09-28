// Copyright Southern Spear. All Rights Reserved.

#include "SSMuzzleLightSubsystem.h"

#include "SSShellEjectSubsystem.h"
#include "SSWeaponPresentation.h"

#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "HAL/IConsoleManager.h"

namespace
{
	TAutoConsoleVariable<int32> CVarMuzzleLight(TEXT("ss.MuzzleLight"), 1,
		TEXT("A brief flash of light at the muzzle on every shot (W3): 1 on, 0 off."));
	TAutoConsoleVariable<int32> CVarMuzzleLightShadows(TEXT("ss.MuzzleLightShadows"), 0,
		TEXT("Muzzle lights cast shadows: 1 on (costly with many shooters), 0 off."));

	constexpr int32 MuzzleLightPool = 8;
	const FLinearColor MuzzleColour(1.f, 0.62f, 0.28f); // warm propellant flash
}

// --------------------------------------------------------------------------- pure rules

float FSSMuzzleLightRules::Intensity(float Peak, float Age, float Seconds)
{
	if (Seconds <= 0.f || Age < 0.f || Age >= Seconds)
	{
		return 0.f;
	}
	const float Left = 1.f - Age / Seconds;
	return Peak * Left * Left;
}

FSSMuzzleLightSpec FSSMuzzleLightRules::SpecFor(const FString& WeaponName)
{
	if (WeaponName == TEXT("A9"))
	{
		return { 1200.f, 450.f, 0.035f };
	}
	if (WeaponName == TEXT("A25") || WeaponName == TEXT("A417"))
	{
		return { 3500.f, 900.f, 0.055f };
	}
	return { 2500.f, 700.f, 0.045f };
}

// --------------------------------------------------------------------------- subsystem

bool USSMuzzleLightSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId USSMuzzleLightSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USSMuzzleLightSubsystem, STATGROUP_Tickables);
}

UPointLightComponent* USSMuzzleLightSubsystem::LightComponent(int32 Index)
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return nullptr;
	}
	if (!PoolActor)
	{
		FActorSpawnParameters Params;
		Params.ObjectFlags |= RF_Transient;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		PoolActor = World->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity, Params);
		if (!PoolActor)
		{
			return nullptr;
		}
		USceneComponent* Root = NewObject<USceneComponent>(PoolActor, TEXT("MuzzleLightRoot"));
		PoolActor->SetRootComponent(Root);
		Root->RegisterComponent();
		Lights.SetNum(MuzzleLightPool);
	}
	if (!Lights.IsValidIndex(Index))
	{
		return nullptr;
	}
	if (!Lights[Index])
	{
		UPointLightComponent* Light = NewObject<UPointLightComponent>(PoolActor);
		Light->SetMobility(EComponentMobility::Movable);
		Light->SetIntensityUnits(ELightUnits::Candelas);
		Light->SetLightColor(MuzzleColour);
		Light->SetIntensity(0.f);
		Light->SetCastShadows(false);
		Light->SetupAttachment(PoolActor->GetRootComponent());
		Light->RegisterComponent();
		Light->SetVisibility(false);
		Lights[Index] = Light;
	}
	return Lights[Index];
}

void USSMuzzleLightSubsystem::FlashFrom(APawn* Shooter)
{
	UWorld* World = GetWorld();
	if (CVarMuzzleLight.GetValueOnGameThread() == 0 || !Shooter || !World || World->GetNetMode() == NM_DedicatedServer)
	{
		return;
	}
	UStaticMeshComponent* Weapon = FSSWeaponPresentation::FindViewerWeapon(Shooter, FSSWeaponPresentation::MuzzleSockets());
	if (!Weapon || !Weapon->GetStaticMesh())
	{
		return;
	}
	const FName Muzzle = FSSWeaponPresentation::FirstSocket(Weapon, FSSWeaponPresentation::MuzzleSockets());
	const FVector MuzzleWorld = Weapon->GetSocketLocation(Muzzle);
	const FVector Forward = (MuzzleWorld - Weapon->GetComponentLocation()).GetSafeNormal();

	const int32 Index = NextLight;
	NextLight = (NextLight + 1) % MuzzleLightPool;
	Flashes.RemoveAllSwap([Index](const FLiveFlash& Live) { return Live.Light == Index; });
	UPointLightComponent* Light = LightComponent(Index);
	if (!Light)
	{
		return;
	}
	const FSSMuzzleLightSpec Spec = FSSMuzzleLightRules::SpecFor(FSSCasingMotion::WeaponNameFromMesh(Weapon->GetStaticMesh()->GetName()));
	FLiveFlash Live;
	Live.Light = Index;
	Live.Peak = Spec.Candela * FMath::FRandRange(0.8f, 1.2f); // no two shots alike
	Live.Seconds = Spec.Seconds;
	// A little ahead of the muzzle, where the propellant burns, so the barrel itself is lit from the front.
	Light->SetWorldLocation(MuzzleWorld + Forward * 6.f);
	Light->SetAttenuationRadius(Spec.RadiusCm);
	Light->SetCastShadows(CVarMuzzleLightShadows.GetValueOnGameThread() != 0);
	Light->SetIntensity(Live.Peak);
	Light->SetVisibility(true);
	Flashes.Add(Live);
}

void USSMuzzleLightSubsystem::Tick(float DeltaTime)
{
	for (int32 I = Flashes.Num() - 1; I >= 0; --I)
	{
		FLiveFlash& Live = Flashes[I];
		UPointLightComponent* Light = Lights.IsValidIndex(Live.Light) ? Lights[Live.Light].Get() : nullptr;
		Live.Age += DeltaTime;
		const float Now = FSSMuzzleLightRules::Intensity(Live.Peak, Live.Age, Live.Seconds);
		if (!Light || Now <= 0.f)
		{
			if (Light)
			{
				Light->SetIntensity(0.f);
				Light->SetVisibility(false);
			}
			Flashes.RemoveAtSwap(I);
			continue;
		}
		Light->SetIntensity(Now);
	}
}
