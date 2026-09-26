// Copyright Southern Spear. All Rights Reserved.

#include "SSCharacterPartActor.h"

#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"

ASSCharacterPartActor::ASSCharacterPartActor()
{
	PrimaryActorTick.bCanEverTick = false;
	SetReplicates(false);
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

void ASSCharacterPartActor::BuildSet(const TArray<TObjectPtr<USkeletalMesh>>& Meshes,
	TArray<TObjectPtr<USkeletalMeshComponent>>& Out)
{
	USkinnedMeshComponent* Leader = FindLeader();
	for (USkeletalMesh* Mesh : Meshes)
	{
		if (!Mesh)
		{
			continue;
		}
		USkeletalMeshComponent* Part = NewObject<USkeletalMeshComponent>(this);
		Part->SetupAttachment(RootComponent);
		Part->SetSkeletalMesh(Mesh);
		Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Part->SetGenerateOverlapEvents(false);
		Part->SetOwnerNoSee(true); // first person: the local player does not see their own body
		Part->SetVisibility(false);
		Part->RegisterComponent();
		if (Leader)
		{
			Part->SetLeaderPoseComponent(Leader);
		}
		Out.Add(Part);
	}
}

USkinnedMeshComponent* ASSCharacterPartActor::FindLeader() const
{
	// Lyra spawns parts through a ChildActorComponent attached to the pawn's
	// (invisible, animated) body mesh: walk up to the first skinned mesh.
	for (USceneComponent* Parent = RootComponent->GetAttachParent(); Parent; Parent = Parent->GetAttachParent())
	{
		if (USkinnedMeshComponent* Skinned = Cast<USkinnedMeshComponent>(Parent))
		{
			return Skinned;
		}
	}
	const AActor* ParentActor = GetParentActor() ? GetParentActor() : GetAttachParentActor();
	return ParentActor ? ParentActor->FindComponentByClass<USkeletalMeshComponent>() : nullptr;
}

void ASSCharacterPartActor::BeginPlay()
{
	Super::BeginPlay();
	BuildSet(FriendlyParts, FriendlyComponents);
	BuildSet(OpposingParts, OpposingComponents);
	UE_LOG(LogTemp, Log, TEXT("SSCharacterPart %s: %d+%d part(s), leader %s."), *GetName(),
		FriendlyComponents.Num(), OpposingComponents.Num(), *GetNameSafe(FindLeader()));
}

void ASSCharacterPartActor::ApplyViewerLocality(ESSLocality Locality)
{
	if (bResolved && Locality == Current)
	{
		return;
	}
	bResolved = true;
	Current = Locality;
	const bool bFriendly = Locality == ESSLocality::Friendly;
	for (USkeletalMeshComponent* Part : FriendlyComponents) { Part->SetVisibility(bFriendly); }
	for (USkeletalMeshComponent* Part : OpposingComponents) { Part->SetVisibility(!bFriendly); }
}
