// Copyright Southern Spear. All Rights Reserved.

#include "SSShellEjectSubsystem.h"

#include "SSWeaponPresentation.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "HAL/IConsoleManager.h"
#include "Materials/MaterialInstanceDynamic.h"

namespace
{
	TAutoConsoleVariable<int32> CVarCasings(TEXT("ss.Casings"), 1,
		TEXT("Spent cases thrown from the weapon's ejection port (W3): 1 on, 0 off."));

	constexpr int32 PoolSize = 48;
	constexpr float FlightTimeout = 6.f;  // s: a case still falling after this (off the map) is dropped
	constexpr float RestLifetime = 30.f;  // s on the ground before it fades out of the pool
}

// --------------------------------------------------------------------------- pure rules

void FSSCasingMotion::Step(FSSCasing& Casing, float DeltaSeconds, float GravityZ)
{
	constexpr float Drag = 0.15f; // per second: a light case slows a little in air
	Casing.Velocity.Z += GravityZ * DeltaSeconds;
	Casing.Velocity *= FMath::Max(0.f, 1.f - Drag * DeltaSeconds);
	Casing.Location += Casing.Velocity * DeltaSeconds;
	const double Spin = Casing.AngularVelocity.Size();
	if (Spin > UE_KINDA_SMALL_NUMBER)
	{
		Casing.Rotation = (FQuat(Casing.AngularVelocity / Spin, Spin * DeltaSeconds) * Casing.Rotation).GetNormalized();
	}
	Casing.Age += DeltaSeconds;
}

void FSSCasingMotion::Bounce(FSSCasing& Casing, const FVector& Normal, float Restitution, float Friction, float RestSpeed)
{
	const FVector N = Normal.GetSafeNormal();
	const double Into = FVector::DotProduct(Casing.Velocity, N);
	const FVector NormalPart = N * Into;
	const FVector Tangent = Casing.Velocity - NormalPart;
	Casing.Velocity = Tangent * (1.f - FMath::Clamp(Friction, 0.f, 1.f)) - NormalPart * FMath::Clamp(Restitution, 0.f, 1.f);
	Casing.AngularVelocity *= 0.6f;
	++Casing.Bounces;
	if (Casing.Velocity.Size() < RestSpeed)
	{
		Casing.Velocity = FVector::ZeroVector;
		Casing.AngularVelocity = FVector::ZeroVector;
		Casing.bResting = true;
	}
}

FString FSSCasingMotion::WeaponNameFromMesh(const FString& MeshName)
{
	return MeshName.StartsWith(TEXT("SM_")) ? MeshName.RightChop(3) : MeshName;
}

FSSCasingSize FSSCasingMotion::SizeFor(const FString& WeaponName)
{
	// 7.62x51 marksman rifles, 9x19 pistols, MAF's 7.62x39; everything else fires 5.56x45.
	if (WeaponName == TEXT("A25") || WeaponName == TEXT("A417"))
	{
		return { 1.20f, 5.1f };
	}
	if (WeaponName == TEXT("A9"))
	{
		return { 0.99f, 1.9f };
	}
	if (WeaponName.StartsWith(TEXT("MAF")))
	{
		return { 1.13f, 3.9f };
	}
	return { 0.96f, 4.5f };
}

// --------------------------------------------------------------------------- subsystem

bool USSShellEjectSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId USSShellEjectSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USSShellEjectSubsystem, STATGROUP_Tickables);
}

UStaticMeshComponent* USSShellEjectSubsystem::CaseComponent(int32 Index)
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return nullptr;
	}
	if (!CaseMesh)
	{
		CaseMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
		if (UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")))
		{
			Brass = UMaterialInstanceDynamic::Create(Base, this);
			Brass->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.72f, 0.52f, 0.18f));
		}
	}
	if (!CaseMesh)
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
		USceneComponent* Root = NewObject<USceneComponent>(PoolActor, TEXT("CasingRoot"));
		PoolActor->SetRootComponent(Root);
		Root->RegisterComponent();
		Pool.SetNum(PoolSize);
	}
	if (!Pool.IsValidIndex(Index))
	{
		return nullptr;
	}
	if (!Pool[Index])
	{
		UStaticMeshComponent* Case = NewObject<UStaticMeshComponent>(PoolActor);
		Case->SetMobility(EComponentMobility::Movable);
		Case->SetStaticMesh(CaseMesh);
		if (Brass)
		{
			Case->SetMaterial(0, Brass);
		}
		Case->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Case->SetGenerateOverlapEvents(false);
		Case->SetCastShadow(false);
		Case->bReceivesDecals = false;
		Case->SetupAttachment(PoolActor->GetRootComponent());
		Case->RegisterComponent();
		Case->SetVisibility(false);
		Pool[Index] = Case;
	}
	return Pool[Index];
}

void USSShellEjectSubsystem::EjectFrom(APawn* Shooter)
{
	UWorld* World = GetWorld();
	if (CVarCasings.GetValueOnGameThread() == 0 || !Shooter || !World || World->GetNetMode() == NM_DedicatedServer)
	{
		return;
	}
	UStaticMeshComponent* Weapon = FSSWeaponPresentation::FindViewerWeapon(Shooter, FSSWeaponPresentation::EjectSockets());
	if (!Weapon || !Weapon->GetStaticMesh())
	{
		return;
	}
	const FName Port = FSSWeaponPresentation::FirstSocket(Weapon, FSSWeaponPresentation::EjectSockets());
	const FName End = FSSWeaponPresentation::FirstSocket(Weapon, FSSWeaponPresentation::EjectEndSockets());
	const FName Muzzle = FSSWeaponPresentation::FirstSocket(Weapon, FSSWeaponPresentation::MuzzleSockets());
	const FVector PortWorld = Weapon->GetSocketLocation(Port);
	// Arma rifles eject to the right: the weapon's right side when the end marker is missing.
	FVector Throw = End.IsNone() ? Weapon->GetRightVector() : (Weapon->GetSocketLocation(End) - PortWorld).GetSafeNormal();
	if (Throw.IsNearlyZero())
	{
		Throw = Weapon->GetRightVector();
	}
	const FVector Forward = Muzzle.IsNone() ? Weapon->GetForwardVector()
		: (Weapon->GetSocketLocation(Muzzle) - Weapon->GetComponentLocation()).GetSafeNormal();

	const int32 Index = NextSlot;
	NextSlot = (NextSlot + 1) % PoolSize;
	Casings.RemoveAllSwap([Index](const FLiveCasing& Live) { return Live.Slot == Index; });
	UStaticMeshComponent* Case = CaseComponent(Index);
	if (!Case)
	{
		return;
	}

	FLiveCasing Live;
	Live.Shooter = Shooter;
	Live.Slot = Index;
	Live.Motion.Location = PortWorld;
	Live.Motion.Velocity = Throw * FMath::FRandRange(250.f, 380.f) + FVector::UpVector * FMath::FRandRange(40.f, 110.f)
		- Forward * FMath::FRandRange(0.f, 60.f) + Shooter->GetVelocity();
	Live.Motion.Rotation = FRotationMatrix::MakeFromZ(Forward.IsNearlyZero() ? FVector::ForwardVector : Forward).ToQuat();
	Live.Motion.AngularVelocity = FMath::VRand() * FMath::FRandRange(10.f, 25.f);

	const FSSCasingSize Size = FSSCasingMotion::SizeFor(FSSCasingMotion::WeaponNameFromMesh(Weapon->GetStaticMesh()->GetName()));
	Live.Diameter = Size.Diameter;
	// The engine cylinder is 100 cm tall and 100 cm across, centred on its pivot, along Z.
	Case->SetWorldScale3D(FVector(Size.Diameter / 100.f, Size.Diameter / 100.f, Size.Length / 100.f));
	Case->SetWorldLocationAndRotation(Live.Motion.Location, Live.Motion.Rotation);
	Case->SetVisibility(true);
	Casings.Add(Live);
}

void USSShellEjectSubsystem::Tick(float DeltaTime)
{
	UWorld* World = GetWorld();
	if (!World || Casings.Num() == 0)
	{
		return;
	}
	const float GravityZ = World->GetGravityZ();
	const float Step = FMath::Min(DeltaTime, 1.f / 30.f); // a long frame must not tunnel a case through the floor
	for (int32 I = Casings.Num() - 1; I >= 0; --I)
	{
		FLiveCasing& Live = Casings[I];
		UStaticMeshComponent* Case = Pool.IsValidIndex(Live.Slot) ? Pool[Live.Slot].Get() : nullptr;
		if (!Case)
		{
			Casings.RemoveAtSwap(I);
			continue;
		}
		FSSCasing& Motion = Live.Motion;
		if (Motion.bResting)
		{
			Motion.Age += DeltaTime;
			if (Motion.Age > RestLifetime)
			{
				Case->SetVisibility(false);
				Casings.RemoveAtSwap(I);
			}
			continue;
		}
		if (Motion.Age > FlightTimeout)
		{
			Case->SetVisibility(false);
			Casings.RemoveAtSwap(I);
			continue;
		}
		const FVector From = Motion.Location;
		FSSCasingMotion::Step(Motion, Step, GravityZ);
		FCollisionQueryParams Params(SCENE_QUERY_STAT(SSCasing), false);
		if (AActor* Shooter = Live.Shooter.Get())
		{
			Params.AddIgnoredActor(Shooter);
		}
		FHitResult Hit;
		if (World->LineTraceSingleByChannel(Hit, From, Motion.Location, ECC_Visibility, Params))
		{
			const FVector Normal = FVector(Hit.ImpactNormal).GetSafeNormal();
			FSSCasingMotion::Bounce(Motion, Normal);
			Motion.Location = FVector(Hit.ImpactPoint) + Normal * (Live.Diameter * 0.5f);
			if (Motion.bResting)
			{
				// Lie on its side: the case's long axis flat on the surface, keeping its heading.
				FVector Along = FVector::VectorPlaneProject(Motion.Rotation.GetAxisZ(), Normal).GetSafeNormal();
				if (Along.IsNearlyZero())
				{
					Along = FVector::VectorPlaneProject(FVector::ForwardVector, Normal).GetSafeNormal();
				}
				Motion.Rotation = FRotationMatrix::MakeFromZX(Along, Normal).ToQuat();
				Motion.Age = 0.f;
			}
		}
		Case->SetWorldLocationAndRotation(Motion.Location, Motion.Rotation);
	}
}
