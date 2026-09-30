// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagAssetInterface.h"
#include "GameplayTagContainer.h"
#include "SSLocalityPresentable.h"
#include "SSCharacterPartActor.generated.h"

class UMaterialInterface;
class UPoseableMeshComponent;
class USkeletalMesh;
class USkeletalMeshComponent;
class USkinnedMeshComponent;
struct FReferenceSkeleton;

/** Cached source-to-target map for one Quantum module, rebuilt only if its mesh changes. */
struct FSSCharacterRetargetMap
{
	TWeakObjectPtr<USkeletalMesh> TargetMesh;
	TArray<FName> TargetNames;
	TArray<int32> TargetParents;
	TArray<int32> SourceForTarget;
	TArray<uint8> DigitMask;
	TArray<FTransform> DigitCurl;
};

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
 * other team as MAF. Manny-rigged parts follow the pawn mesh's pose by bone
 * name (leader pose); parts on an independent skeleton (the Quantum body,
 * ADR-038) are retargeted per tick from the pawn mesh's evaluated pose
 * instead. Hidden until the viewer's client resolves a locality: it never
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
	virtual void Tick(float DeltaSeconds) override;
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

	/** Manny-rigged kit layered over the independent Quantum body when the viewer sees this pawn as friendly. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visual")
	TArray<TObjectPtr<USkeletalMesh>> FriendlyLeaderPoseParts;

	/** True when FriendlyParts use a distinct skeleton that must be locally retargeted from the pawn pose. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visual")
	bool bRetargetFriendlyPose = false;

	/** Curl applied to non-mapped finger chains when retargeting the friendly appearance. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visual", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float FriendlyFingerCurl = 1.0f;

	/** Degrees of curl per finger joint at FriendlyFingerCurl = 1. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visual", meta = (ClampMin = "0.0", ClampMax = "90.0"))
	float FriendlyFingerCurlDegrees = 55.0f;

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
		TArray<TObjectPtr<USkinnedMeshComponent>>& Out, bool bRetarget = false);
	void TickFriendlyRetarget(float DeltaTime);
	void BuildFriendlyBoneMap(const FReferenceSkeleton& Source, USkeletalMesh* TargetMesh,
		FSSCharacterRetargetMap& Out);
	static void ReferenceComponentSpace(const FReferenceSkeleton& Ref, TArray<FTransform>& Out);
	static bool IsDigitBone(const FReferenceSkeleton& Ref, int32 BoneIndex);
	static FTransform CurledDigitTransform(const FReferenceSkeleton& Ref, int32 BoneIndex,
		float Curl, float CurlDegrees);

	/** The pawn mesh the retarget copies the pose from; found once at BeginPlay. */
	TWeakObjectPtr<USkinnedMeshComponent> LeaderMesh;

	UPROPERTY(Transient)
	TArray<TObjectPtr<USkinnedMeshComponent>> FriendlyComponents;

	UPROPERTY(Transient)
	TArray<TObjectPtr<USkinnedMeshComponent>> FriendlyLeaderPoseComponents;

	UPROPERTY(Transient)
	TArray<TObjectPtr<USkinnedMeshComponent>> OpposingComponents;

	/** The Quantum modules (poseable, own skeleton), written from the pawn pose every friendly tick. */
	UPROPERTY(Transient)
	TArray<TObjectPtr<UPoseableMeshComponent>> FriendlyRetargetComponents;

	/** One map per FriendlyRetargetComponents entry; built lazily on the first friendly tick. */
	TArray<FSSCharacterRetargetMap> FriendlyRetargetMaps;
	TArray<FTransform> SourceLocalPose;
	TArray<FTransform> FriendlyRetargetScratch;

	bool bResolved = false;
	ESSLocality Current = ESSLocality::Friendly;
};
