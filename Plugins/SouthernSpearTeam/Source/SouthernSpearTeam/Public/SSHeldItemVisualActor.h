// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SSHeldItemVisualActor.generated.h"

class UStaticMeshComponent;
class UStaticMesh;

/**
 * Cosmetic actor that shows a held item's static mesh (ADR-020: original
 * Blender art on Lyra's equipment sockets). Spawned by an equipment
 * definition; carries no gameplay state, no collision, and never replicates
 * anything of its own (ADR-004). One Blueprint subclass per item sets
 * VisualMesh and, if needed, MeshOffset.
 */
UCLASS(Abstract, Blueprintable)
class SSTEAM_API ASSHeldItemVisualActor : public AActor
{
	GENERATED_BODY()

public:
	ASSHeldItemVisualActor();

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void PostInitializeComponents() override;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Visual")
	TObjectPtr<UStaticMesh> VisualMesh;

	/** Mesh placement relative to the attach socket. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Visual")
	FTransform MeshOffset;

	UFUNCTION(BlueprintPure, Category = "Visual")
	UStaticMeshComponent* GetMeshComponent() const { return Mesh; }

private:
	void ApplyMesh();

	UPROPERTY(VisibleAnywhere, Category = "Visual")
	TObjectPtr<UStaticMeshComponent> Mesh;
};
