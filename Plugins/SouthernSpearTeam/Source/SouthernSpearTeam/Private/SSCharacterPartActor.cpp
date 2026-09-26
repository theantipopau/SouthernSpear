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
	// The part is attached to the pawn's (invisible) body mesh; follow its pose.
	USkinnedMeshComponent* Leader = Cast<USkinnedMeshComponent>(RootComponent->GetAttachParent());
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

void ASSCharacterPartActor::BeginPlay()
{
	Super::BeginPlay();
	BuildSet(FriendlyParts, FriendlyComponents);
	BuildSet(OpposingParts, OpposingComponents);
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
