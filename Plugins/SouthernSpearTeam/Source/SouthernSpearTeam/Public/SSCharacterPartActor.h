// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagAssetInterface.h"
#include "GameplayTagContainer.h"
#include "SSLocalityPresentable.h"
#include "SSCharacterPartActor.generated.h"

class UMaterialInterface;
class USkeletalMesh;
class USkeletalMeshComponent;
class USkinnedMeshComponent;

/**
 * Materials for one character part, indexed by that part's material slots.
 * An empty entry keeps the source material. UHT cannot express a nested
 * TArray directly, hence the struct.
 */
USTRUCT(BlueprintType)
struct SSTEAM_API FSSPartMaterialOverride
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Visual")
	TArray<TObjectPtr<UMaterialInterface>> Slots;
};

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
class SSTEAM_API ASSCharacterPartActor : public AActor, public ISSLocalityPresentable, public IGameplayTagAssetInterface
{
	GENERATED_BODY()

public:
	ASSCharacterPartActor();

	virtual void BeginPlay() override;
	virtual void ApplyViewerLocality(ESSLocality Locality) override;
	virtual void GetOwnedGameplayTags(FGameplayTagContainer& TagContainer) const override { TagContainer.AppendTags(CosmeticTags); }

	/**
	 * Cosmetic style tags the host reads from character parts to pick the body
	 * mesh and the weapon animation layers (locomotion, reload). Defaults match
	 * the mannequin these meshes follow; without them no animation set links.
	 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visual")
	FGameplayTagContainer CosmeticTags;

	/** Meshes shown when the viewer is on this pawn's team (3 ACR look). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visual")
	TArray<TObjectPtr<USkeletalMesh>> FriendlyParts;

	/** Meshes shown when the viewer is on the other team (MAF look). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visual")
	TArray<TObjectPtr<USkeletalMesh>> OpposingParts;

	/**
	 * Cosmetic material overrides for FriendlyParts, one inner array per part
	 * and indexed by that part's material slots. Empty entries leave the
	 * source material alone. This is how the original Southern Spear uniforms
	 * (CMECU / MAF) are applied to the licensed third-party bodies without
	 * duplicating or editing the vendor meshes (ADR-004: appearance only).
	 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visual")
	TArray<FSSPartMaterialOverride> FriendlyMaterialOverrides;

	/** Cosmetic material overrides for OpposingParts; same shape as above. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visual")
	TArray<FSSPartMaterialOverride> OpposingMaterialOverrides;

	UFUNCTION(BlueprintPure, Category = "Visual")
	bool HasResolvedLocality() const { return bResolved; }

private:
	USkinnedMeshComponent* FindLeader() const;
	void AddDefaultCosmeticTags();
	void BuildSet(const TArray<TObjectPtr<USkeletalMesh>>& Meshes,
		const TArray<FSSPartMaterialOverride>& Overrides,
		TArray<TObjectPtr<USkeletalMeshComponent>>& Out);

	UPROPERTY(Transient)
	TArray<TObjectPtr<USkeletalMeshComponent>> FriendlyComponents;

	UPROPERTY(Transient)
	TArray<TObjectPtr<USkeletalMeshComponent>> OpposingComponents;

	bool bResolved = false;
	ESSLocality Current = ESSLocality::Friendly;
};
