// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SSLocalityPresentable.h"
#include "SSCharacterPartActor.generated.h"

class USkeletalMesh;
class USkeletalMeshComponent;
class USkinnedMeshComponent;

/**
 * Cosmetic soldier body, spawned as a character part on the pawn's mesh.
 * Holds two looks (ADR-003): the viewer's own team is shown as 3 ACR, the
 * other team as MAF. Every mesh follows the pawn mesh's pose by bone name
 * (leader pose), so any UE-mannequin-named skeleton works without a
 * retarget. Hidden until the viewer's client resolves a locality: it never
 * defaults to a side (ADR-017). Hidden from its own player's first-person
 * view. No collision, no gameplay state (ADR-004).
 */
UCLASS(Abstract, Blueprintable)
class SSTEAM_API ASSCharacterPartActor : public AActor, public ISSLocalityPresentable
{
	GENERATED_BODY()

public:
	ASSCharacterPartActor();

	virtual void BeginPlay() override;
	virtual void ApplyViewerLocality(ESSLocality Locality) override;

	/** Meshes shown when the viewer is on this pawn's team (3 ACR look). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visual")
	TArray<TObjectPtr<USkeletalMesh>> FriendlyParts;

	/** Meshes shown when the viewer is on the other team (MAF look). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visual")
	TArray<TObjectPtr<USkeletalMesh>> OpposingParts;

	UFUNCTION(BlueprintPure, Category = "Visual")
	bool HasResolvedLocality() const { return bResolved; }

private:
	USkinnedMeshComponent* FindLeader() const;
	void BuildSet(const TArray<TObjectPtr<USkeletalMesh>>& Meshes, TArray<TObjectPtr<USkeletalMeshComponent>>& Out);

	UPROPERTY(Transient)
	TArray<TObjectPtr<USkeletalMeshComponent>> FriendlyComponents;

	UPROPERTY(Transient)
	TArray<TObjectPtr<USkeletalMeshComponent>> OpposingComponents;

	bool bResolved = false;
	ESSLocality Current = ESSLocality::Friendly;
};
