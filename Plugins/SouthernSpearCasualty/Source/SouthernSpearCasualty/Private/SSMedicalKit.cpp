// Copyright Southern Spear. All Rights Reserved.

#include "SSMedicalKit.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Net/UnrealNetwork.h"
#include "SSCasualtySettings.h"

ASSMedicalKit::ASSMedicalKit()
{
	bReplicates = true;
	SetNetUpdateFrequency(2.f);
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.25f;

	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->SetCastShadow(false);
	SetRootComponent(Mesh);
}

void ASSMedicalKit::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ASSMedicalKit, Charges);
	DOREPLIFETIME(ASSMedicalKit, Age);
}

void ASSMedicalKit::BeginPlay()
{
	Super::BeginPlay();
	const USSCasualtySettings& Settings = USSCasualtySettings::Get();
	if (HasAuthority())
	{
		Charges = Settings.KitCharges;
		Age = 0.f;
	}
	// The mesh is data. Without one (or on a dedicated server) the kit is still a working invisible point.
	if (GetNetMode() != NM_DedicatedServer)
	{
		if (UStaticMesh* KitMesh = Settings.KitMesh.LoadSynchronous())
		{
			Mesh->SetStaticMesh(KitMesh);
		}
	}
}

ASSMedicalKit* ASSMedicalKit::Drop(UWorld* World, const FVector& Location, AActor* Owner)
{
	if (!World || World->GetNetMode() == NM_Client)
	{
		return nullptr;
	}
	FActorSpawnParameters Params;
	Params.Owner = Owner;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	return World->SpawnActor<ASSMedicalKit>(Location, FRotator::ZeroRotator, Params);
}

ASSMedicalKit* ASSMedicalKit::FindNearest(UWorld* World, const FVector& Location, float RadiusCm)
{
	if (!World)
	{
		return nullptr;
	}
	ASSMedicalKit* Best = nullptr;
	double BestDistance = RadiusCm;
	for (TActorIterator<ASSMedicalKit> It(World); It; ++It)
	{
		ASSMedicalKit* Kit = *It;
		const double Distance = FVector::Distance(Kit->GetActorLocation(), Location);
		if (Kit->IsUsable() && Distance <= BestDistance)
		{
			Best = Kit;
			BestDistance = Distance;
		}
	}
	return Best;
}

float ASSMedicalKit::GetRemainingSeconds() const
{
	return FMath::Max(0.f, USSCasualtySettings::Get().KitLifetimeSeconds - Age);
}

bool ASSMedicalKit::IsUsable() const
{
	return SSCasualty::KitUsable(ToRuleKit(), USSCasualtySettings::Get().ToTuning());
}

SSCasualty::FKit ASSMedicalKit::ToRuleKit() const
{
	SSCasualty::FKit Kit;
	Kit.Charges = Charges;
	Kit.Age = Age;
	return Kit;
}

void ASSMedicalKit::FromRuleKit(const SSCasualty::FKit& Kit)
{
	if (HasAuthority())
	{
		Charges = Kit.Charges;
		Age = Kit.Age;
	}
}

void ASSMedicalKit::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!HasAuthority())
	{
		return;
	}
	SSCasualty::FKit Kit = ToRuleKit();
	const bool bAlive = SSCasualty::TickKit(Kit, USSCasualtySettings::Get().ToTuning(), DeltaSeconds);
	FromRuleKit(Kit);
	if (!bAlive)
	{
		Destroy();
	}
}
