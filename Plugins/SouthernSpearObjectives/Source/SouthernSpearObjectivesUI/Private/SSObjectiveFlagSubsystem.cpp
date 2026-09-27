// Copyright Southern Spear. All Rights Reserved.

#include "SSObjectiveFlagSubsystem.h"

#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GenericTeamAgentInterface.h"
#include "Materials/MaterialInterface.h"
#include "SSObjectiveActor.h"
#include "SSObjectiveAssaultDirector.h"

namespace
{
	const TCHAR* PoleMeshPath = TEXT("/Game/World_Flags/Meshes/SM_Flag_Holder_00.SM_Flag_Holder_00");
	const TCHAR* ClothMeshPath = TEXT("/Game/World_Flags/Meshes/SM_Flag.SM_Flag");
	const TCHAR* FriendlyPath = TEXT("/SSExp_ObjectiveAssault/Flags/MI_SS_Flag_Friendly.MI_SS_Flag_Friendly");
	const TCHAR* OpposingPath = TEXT("/SSExp_ObjectiveAssault/Flags/MI_SS_Flag_MAF.MI_SS_Flag_MAF");
	constexpr float PoleOffset = 180.f;  // beside the objective centre, cm
	constexpr float FlagBottom = 90.f;   // flag top edge heights on the 476 cm pole
	constexpr float FlagTop = 460.f;
}

bool USSObjectiveFlagSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* World = Cast<UWorld>(Outer);
	return World && World->GetNetMode() != NM_DedicatedServer && Super::ShouldCreateSubsystem(Outer);
}

bool USSObjectiveFlagSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId USSObjectiveFlagSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USSObjectiveFlagSubsystem, STATGROUP_Tickables);
}

void USSObjectiveFlagSubsystem::Tick(float DeltaTime)
{
	UWorld* World = GetWorld();
	TActorIterator<ASSObjectiveAssaultDirector> DirectorIt(World);
	const ASSObjectiveAssaultDirector* Director = DirectorIt ? *DirectorIt : nullptr;
	if (!Director || Director->GetObjectives().Num() == 0)
	{
		return;
	}

	if (!bSpawned)
	{
		bSpawned = true;
		UStaticMesh* PoleMesh = LoadObject<UStaticMesh>(nullptr, PoleMeshPath);
		USkeletalMesh* ClothMesh = LoadObject<USkeletalMesh>(nullptr, ClothMeshPath);
		if (!PoleMesh || !ClothMesh)
		{
			UE_LOG(LogTemp, Warning, TEXT("Objective flags: World Flags pack meshes missing; no flags shown."));
			return;
		}
		for (ASSObjectiveActor* Objective : Director->GetObjectives())
		{
			if (!Objective)
			{
				continue;
			}
			FActorSpawnParameters Params;
			Params.ObjectFlags |= RF_Transient;
			const FVector Base = Objective->GetActorLocation() + FVector(PoleOffset, 0.f, 0.f);
			AActor* Actor = World->SpawnActor<AActor>(AActor::StaticClass(), FTransform(Base), Params);
			if (!Actor)
			{
				continue;
			}
			UStaticMeshComponent* Pole = NewObject<UStaticMeshComponent>(Actor, TEXT("Pole"));
			Pole->SetStaticMesh(PoleMesh);
			Pole->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Actor->SetRootComponent(Pole);
			Pole->RegisterComponent();
			Pole->SetWorldLocation(Base);

			USkeletalMeshComponent* Cloth = NewObject<USkeletalMeshComponent>(Actor, TEXT("Cloth"));
			Cloth->SetSkeletalMesh(ClothMesh);
			Cloth->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Cloth->SetupAttachment(Pole);
			Cloth->SetRelativeLocation(FVector(0.f, 0.f, FlagBottom));
			Cloth->SetVisibility(false);
			Cloth->RegisterComponent();
			Flags.Add({ Objective, Actor, Cloth, FlagBottom });
		}
	}

	ESSTeamId Viewer = ESSTeamId::None;
	if (const IGenericTeamAgentInterface* Agent = Cast<IGenericTeamAgentInterface>(World->GetFirstPlayerController()))
	{
		Viewer = Director->ToTeamId(Agent->GetGenericTeamId());
	}
	static TWeakObjectPtr<UMaterialInterface> Friendly, Opposing;
	if (!Friendly.IsValid()) { Friendly = LoadObject<UMaterialInterface>(nullptr, FriendlyPath); }
	if (!Opposing.IsValid()) { Opposing = LoadObject<UMaterialInterface>(nullptr, OpposingPath); }

	for (FFlag& Flag : Flags)
	{
		const ASSObjectiveActor* Objective = Flag.Objective.Get();
		USkeletalMeshComponent* Cloth = Flag.Cloth.Get();
		if (!Objective || !Cloth)
		{
			continue;
		}
		// Which side's flag is on the pole, and how far up (0..1).
		const FSSObjectiveState& State = Objective->GetObjectiveState();
		ESSTeamId Shown = State.OwnerTeam;
		float Raised = 1.f;
		if (State.CapturingTeam != ESSTeamId::None && State.CapturingTeam != State.OwnerTeam)
		{
			const float Progress = FMath::Clamp(State.Progress, 0.f, 1.f);
			Shown = State.OwnerTeam != ESSTeamId::None ? State.OwnerTeam : State.CapturingTeam;
			Raised = State.OwnerTeam != ESSTeamId::None ? 1.f - Progress : Progress;
		}
		const bool bVisible = Shown != ESSTeamId::None && Viewer != ESSTeamId::None && Raised > 0.02f;
		const int32 ShownCode = bVisible ? (Shown == Viewer ? 1 : 2) : 0;
		if (ShownCode != Flag.LastShown)
		{
			Flag.LastShown = ShownCode;
			UE_LOG(LogTemp, Log, TEXT("Objective flag %s: %s."), *Objective->GetName(),
				ShownCode == 1 ? TEXT("friendly flag") : ShownCode == 2 ? TEXT("MAF flag") : TEXT("bare pole"));
		}
		Cloth->SetVisibility(bVisible);
		if (!bVisible)
		{
			continue;
		}
		UMaterialInterface* Material = (Shown == Viewer ? Friendly : Opposing).Get();
		if (Material && Cloth->GetMaterial(0) != Material)
		{
			Cloth->SetMaterial(0, Material);
		}
		const float Target = FMath::Lerp(FlagBottom, FlagTop - 76.f, Raised);
		Flag.Height = FMath::FInterpTo(Flag.Height, Target, DeltaTime, 3.f);
		Cloth->SetRelativeLocation(FVector(0.f, 0.f, Flag.Height));
	}
}
