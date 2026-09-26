// Copyright Southern Spear. All Rights Reserved.

#include "SSHeldItemVisualActor.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"

ASSHeldItemVisualActor::ASSHeldItemVisualActor()
{
	PrimaryActorTick.bCanEverTick = false;
	SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));

	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	Mesh->SetupAttachment(GetRootComponent());
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->SetGenerateOverlapEvents(false);
	Mesh->SetCanEverAffectNavigation(false);
	Mesh->bCastDynamicShadow = true;
}

void ASSHeldItemVisualActor::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	ApplyMesh();
}

void ASSHeldItemVisualActor::PostInitializeComponents()
{
	Super::PostInitializeComponents();
	ApplyMesh();
}

void ASSHeldItemVisualActor::ApplyMesh()
{
	if (Mesh)
	{
		Mesh->SetStaticMesh(VisualMesh);
		Mesh->SetRelativeTransform(MeshOffset);
	}
}
