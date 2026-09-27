// Copyright Southern Spear. All Rights Reserved.

#include "SSCharacterPartActor.h"

#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Materials/MaterialInterface.h"

ASSCharacterPartActor::ASSCharacterPartActor()
{
	PrimaryActorTick.bCanEverTick = false;
	SetReplicates(false);
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	AddDefaultCosmeticTags();
}

void ASSCharacterPartActor::BuildSet(const TArray<TObjectPtr<USkeletalMesh>>& Meshes,
	const TArray<FSSPartMaterialOverride>& Overrides,
	TArray<TObjectPtr<USkeletalMeshComponent>>& Out)
{
	USkinnedMeshComponent* Leader = FindLeader();
	for (int32 Index = 0; Index < Meshes.Num(); ++Index)
	{
		USkeletalMesh* Mesh = Meshes[Index];
		if (!Mesh)
		{
			continue;
		}
		USkeletalMeshComponent* Part = NewObject<USkeletalMeshComponent>(this);
		Part->SetupAttachment(RootComponent);
		Part->SetSkeletalMesh(Mesh);
		if (Overrides.IsValidIndex(Index))
		{
			const TArray<TObjectPtr<UMaterialInterface>>& Slots = Overrides[Index].Slots;
			for (int32 Slot = 0; Slot < Slots.Num(); ++Slot)
			{
				if (Slots[Slot])
				{
					Part->SetMaterial(Slot, Slots[Slot]);
				}
			}
		}
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

void ASSCharacterPartActor::AddDefaultCosmeticTags()
{
	// Tags are declared in the host project's tag config; ErrorIfNotFound=false keeps
	// this module host-agnostic (a missing tag just leaves the container short).
	for (const TCHAR* Name : { TEXT("Cosmetic.AnimationStyle.Masculine"), TEXT("Cosmetic.BodyStyle.Medium") })
	{
		const FGameplayTag Tag = FGameplayTag::RequestGameplayTag(FName(Name), /*ErrorIfNotFound=*/ false);
		if (Tag.IsValid())
		{
			CosmeticTags.AddTag(Tag);
		}
	}
}

void ASSCharacterPartActor::BeginPlay()
{
	// The CDO may be built before the tag config loads; fill in any missing tags now.
	if (CosmeticTags.Num() < 2)
	{
		AddDefaultCosmeticTags();
	}
	Super::BeginPlay();
	BuildSet(FriendlyParts, FriendlyMaterialOverrides, FriendlyComponents);
	BuildSet(OpposingParts, OpposingMaterialOverrides, OpposingComponents);
	UE_LOG(LogTemp, Log, TEXT("SSCharacterPart %s: %d+%d part(s), leader %s."), *GetName(),
		FriendlyComponents.Num(), OpposingComponents.Num(), *GetNameSafe(FindLeader()));
	UE_LOG(LogTemp, Log, TEXT("SSCharacterPart tags: %s"), *CosmeticTags.ToStringSimple());
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
