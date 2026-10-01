// Copyright Southern Spear. All Rights Reserved.

#include "SSCharacterPartActor.h"

#include "Components/PoseableMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Materials/MaterialInterface.h"
#include "ReferenceSkeleton.h"

ASSCharacterPartActor::ASSCharacterPartActor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PostPhysics;
	SetReplicates(false);
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	AddDefaultCosmeticTags();
}

void ASSCharacterPartActor::BuildSet(const TArray<TObjectPtr<USkeletalMesh>>& Meshes,
	const TArray<FSSPartMaterialOverride>& Overrides,
	TArray<TObjectPtr<USkinnedMeshComponent>>& Out, bool bRetarget)
{
	USkinnedMeshComponent* Leader = FindLeader();
	if (bRetarget && !Leader)
	{
		UE_LOG(LogTemp, Error, TEXT("SSCharacterPart %s: refusing retarget; no animated leader mesh."), *GetName());
		return;
	}

	for (int32 Index = 0; Index < Meshes.Num(); ++Index)
	{
		USkeletalMesh* Mesh = Meshes[Index];
		if (!Mesh)
		{
			continue;
		}

		USkinnedMeshComponent* Part = nullptr;
		if (bRetarget)
		{
			// The Quantum modules ride their own skeleton (never reparented, ADR-038), so a
			// leader pose cannot drive them. A poseable mesh is written per tick from the
			// pawn mesh's evaluated pose instead; the bone map is built lazily on the first
			// friendly tick, per target mesh, in TickFriendlyRetarget.
			UPoseableMeshComponent* Poseable = NewObject<UPoseableMeshComponent>(this);
			Poseable->SetupAttachment(RootComponent);
			Poseable->SetSkinnedAsset(Mesh);
			Part = Poseable;
			FriendlyRetargetComponents.Add(Poseable);
		}
		else
		{
			USkeletalMeshComponent* Skeletal = NewObject<USkeletalMeshComponent>(this);
			Skeletal->SetupAttachment(RootComponent);
			Skeletal->SetSkeletalMesh(Mesh);
			if (Leader)
			{
				Skeletal->SetLeaderPoseComponent(Leader);
			}
			Part = Skeletal;
		}

		Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Part->SetGenerateOverlapEvents(false);
		Part->SetOwnerNoSee(true); // first person: the local player does not see their own body
		Part->SetVisibility(false);
		Part->RegisterComponent();

		// SetMaterial before the skinned component is registered can trip UE 5.8's
		// KnownSkinnedAsset ensure while its scene proxy is being initialized.
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
		}			Out.Add(Part);

		// One line per part: the class-select preview and the in-game bodies both depend on these
		// meshes being non-null, leader-posed and material-overridden, and a missing helmet is
		// invisible in every report that only counts parts.
		FString Materials;
		const int32 Slots = Part->GetNumMaterials();
		for (int32 Slot = 0; Slot < Slots; ++Slot)
		{
			Materials += FString::Printf(TEXT("%s[%d]=%s "), Slot == 0 ? TEXT("") : TEXT(","), Slot,
				*GetNameSafe(Part->GetMaterial(Slot)));
		}
		UE_LOG(LogTemp, Log, TEXT("SSCharacterPart %s part %d/%d: mesh=%s retarget=%d leader=%s vis=%d mats: %s"),
			*GetName(), Index + 1, Meshes.Num(), *GetNameSafe(Mesh), bRetarget, *GetNameSafe(Leader),
			Part->IsVisible() ? 1 : 0, *Materials);
	}
}

USkinnedMeshComponent* ASSCharacterPartActor::FindLeader() const
{
	// Lyra spawns parts through a ChildActorComponent attached to the pawn's
	// (animated) body mesh: walk up to the first skinned mesh.
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

bool ASSCharacterPartActor::IsDigitBone(const FReferenceSkeleton& Ref, int32 BoneIndex)
{
	for (int32 Parent = Ref.GetParentIndex(BoneIndex); Parent != INDEX_NONE; Parent = Ref.GetParentIndex(Parent))
	{
		if (Ref.GetBoneName(Parent).ToString().StartsWith(TEXT("hand_")))
		{
			return true;
		}
	}
	return false;
}

FTransform ASSCharacterPartActor::CurledDigitTransform(const FReferenceSkeleton& Ref, int32 BoneIndex,
	float Curl, float CurlDegrees)
{
	const TArray<FTransform>& RefPose = Ref.GetRefBonePose();
	FTransform Result = RefPose[BoneIndex];
	if (Curl <= 0.f)
	{
		return Result;
	}

	// The flexion axis is the local axis least aligned with the bone's own direction, derived
	// from the hierarchy (the prototype's approach: a naming guess can curl the hand sideways).
	FVector Direction = FVector::ZeroVector;
	for (int32 Child = 0; Child < Ref.GetNum(); ++Child)
	{
		if (Ref.GetParentIndex(Child) == BoneIndex)
		{
			Direction += RefPose[BoneIndex].GetRotation().Inverse().RotateVector(
				RefPose[Child].GetLocation() - RefPose[BoneIndex].GetLocation());
		}
	}
	if (Direction.IsNearlyZero())
	{
		Direction = FVector(1.f, 0.f, 0.f);
	}
	Direction.Normalize();

	int32 Axis = 0;
	float Alignment = TNumericLimits<float>::Max();
	for (int32 Candidate = 0; Candidate < 3; ++Candidate)
	{
		const float CandidateAlignment = FMath::Abs(Direction[Candidate]);
		if (CandidateAlignment < Alignment)
		{
			Alignment = CandidateAlignment;
			Axis = Candidate;
		}
	}
	const bool bThumb = Ref.GetBoneName(BoneIndex).ToString().StartsWith(TEXT("thumb"));
	const float ThumbScale = bThumb ? 0.6f : 1.f;
	const FQuat CurlRotation(FVector(Axis == 0, Axis == 1, Axis == 2),
		FMath::DegreesToRadians(CurlDegrees) * Curl * ThumbScale);
	Result.SetRotation((Result.GetRotation() * CurlRotation).GetNormalized());
	return Result;
}

void ASSCharacterPartActor::ReferenceComponentSpace(const FReferenceSkeleton& Ref, TArray<FTransform>& Out)
{
	// FillComponentSpaceTransforms order: child component space = local * parent component space.
	const TArray<FTransform>& Local = Ref.GetRefBonePose();
	Out.SetNumUninitialized(Ref.GetNum());
	for (int32 Index = 0; Index < Ref.GetNum(); ++Index)
	{
		const int32 Parent = Ref.GetParentIndex(Index);
		Out[Index] = Parent == INDEX_NONE ? Local[Index] : Local[Index] * Out[Parent];
	}
}

void ASSCharacterPartActor::BuildFriendlyBoneMap(const FReferenceSkeleton& Source, USkeletalMesh* TargetMesh,
	FSSCharacterRetargetMap& Out)
{
	Out.TargetMesh = TargetMesh;
	const FReferenceSkeleton& Target = TargetMesh->GetRefSkeleton();
	const int32 Num = Target.GetNum();
	Out.TargetNames.SetNum(Num);
	Out.TargetParents.SetNum(Num);
	Out.SourceForTarget.Init(INDEX_NONE, Num);
	Out.DigitMask.Init(0, Num);
	Out.DigitCurl.SetNum(Num);

	// A shared bone NAME is not a shared joint: keep a name match only when both rigs agree
	// about the joint in their rest poses (6% of standing height, 30 degrees of rest
	// rotation), the tolerances the prototype's proof passed with.
	TArray<FTransform> SourceCS;
	TArray<FTransform> TargetCS;
	ReferenceComponentSpace(Source, SourceCS);
	ReferenceComponentSpace(Target, TargetCS);
	double StandingHeight = 1.0;
	for (const FTransform& Bone : SourceCS)
	{
		StandingHeight = FMath::Max(StandingHeight, FMath::Abs(Bone.GetTranslation().Z));
	}
	const double PositionTolerance = StandingHeight * 0.06;

	for (int32 Index = 0; Index < Num; ++Index)
	{
		Out.TargetNames[Index] = Target.GetBoneName(Index);
		Out.TargetParents[Index] = Target.GetParentIndex(Index);
		const FString Name = Out.TargetNames[Index].ToString();
		// Twist and IK helper bones are not articulation; UE's own IK Retargeter leaves them
		// out of the chain map for the same reason.
		const bool bHelper = Name.Contains(TEXT("twist")) || Name.Contains(TEXT("tricep"))
			|| Name.Contains(TEXT("bicep")) || Name.StartsWith(TEXT("ik_"));
		if (!bHelper)
		{
			const int32 SourceIndex = Source.FindBoneIndex(Out.TargetNames[Index]);
			if (SourceIndex != INDEX_NONE)
			{
				const double PositionDelta = FVector::Distance(SourceCS[SourceIndex].GetLocation(), TargetCS[Index].GetLocation());
				const double AngleDelta = FMath::RadiansToDegrees(Source.GetRefBonePose()[SourceIndex].GetRotation().AngularDistance(
					Target.GetRefBonePose()[Index].GetRotation()));
				if (PositionDelta <= PositionTolerance && AngleDelta <= 30.f)
				{
					Out.SourceForTarget[Index] = SourceIndex;
				}
			}
		}
		// Finger bones are Quantum-only: the mannequin has no digits, so they get the grip curl.
		Out.DigitMask[Index] = IsDigitBone(Target, Index) ? 1 : 0;
		if (Out.DigitMask[Index])
		{
			Out.DigitCurl[Index] = CurledDigitTransform(Target, Index, FriendlyFingerCurl, FriendlyFingerCurlDegrees);
		}
	}
}

void ASSCharacterPartActor::TickFriendlyRetarget(float DeltaTime)
{
	// The pose source is the pawn's own mesh: its component-space transforms already hold this
	// frame's evaluated pose (locomotion, aim overlay and the hand-IK wrist), because this
	// actor's tick is ordered after the pawn's. Retargeting a second, separately animated copy
	// instead would drive the Quantum body into a pose nobody is in.
	if (!bRetargetFriendlyPose || Current != ESSLocality::Friendly
		|| FriendlyRetargetComponents.Num() == 0 || GetNetMode() == NM_DedicatedServer)
	{
		return;
	}
	USkinnedMeshComponent* Leader = LeaderMesh.Get();
	USkeletalMesh* SourceMesh = Leader ? Cast<USkeletalMesh>(Leader->GetSkinnedAsset()) : nullptr;
	if (!SourceMesh)
	{
		return;
	}
	const FReferenceSkeleton& SourceRef = SourceMesh->GetRefSkeleton();
	const TArray<FTransform>& SourceCS = Leader->GetComponentSpaceTransforms();
	if (SourceCS.Num() != SourceRef.GetNum() || SourceCS.Num() == 0)
	{
		return; // not evaluated yet: keep the reference pose rather than guess
	}
	// Component space -> local (parent-relative), the form the retarget consumes.
	SourceLocalPose.SetNumUninitialized(SourceCS.Num());
	for (int32 Index = 0; Index < SourceCS.Num(); ++Index)
	{
		const int32 Parent = SourceRef.GetParentIndex(Index);
		SourceLocalPose[Index] = Parent == INDEX_NONE ? SourceCS[Index] : SourceCS[Index] * SourceCS[Parent].Inverse();
	}

	for (int32 PartIndex = 0; PartIndex < FriendlyRetargetComponents.Num(); ++PartIndex)
	{
		UPoseableMeshComponent* Part = FriendlyRetargetComponents[PartIndex];
		USkeletalMesh* TargetMesh = Part ? Cast<USkeletalMesh>(Part->GetSkinnedAsset()) : nullptr;
		if (!TargetMesh)
		{
			continue;
		}
		// One map per module, built once per target mesh and cached; rebuilding it would redo
		// 350+ rest-pose comparisons every tick for an unchanged pair of skeletons.
		if (FriendlyRetargetMaps.Num() != FriendlyRetargetComponents.Num())
		{
			FriendlyRetargetMaps.SetNum(FriendlyRetargetComponents.Num());
		}
		FSSCharacterRetargetMap& Map = FriendlyRetargetMaps[PartIndex];
		if (Map.TargetMesh.Get() != TargetMesh || Map.TargetNames.Num() != TargetMesh->GetRefSkeleton().GetNum())
		{
			BuildFriendlyBoneMap(SourceRef, TargetMesh, Map);

			// How far this module's own anchor sits from the mannequin's at rest, before the rigid
			// alignment below closes the gap. This is the number that decides whether a helmet fitted
			// to the mannequin covers this module's head, so it is worth one line per part.
			const int32 Anchor = Map.TargetNames.IndexOfByKey(FriendlyRetargetAnchor);
			const int32 AnchorSource = Map.SourceForTarget.IsValidIndex(Anchor) ? Map.SourceForTarget[Anchor] : INDEX_NONE;
			if (Anchor != INDEX_NONE && AnchorSource != INDEX_NONE)
			{
				TArray<FTransform> TargetRest;
				ReferenceComponentSpace(TargetMesh->GetRefSkeleton(), TargetRest);
				const FVector Gap = TargetRest[Anchor].GetLocation() - SourceCS[AnchorSource].GetLocation();
				UE_LOG(LogTemp, Log, TEXT("SSCharacterPart %s: anchor '%s' rest gap to leader %.1f cm (%s); "
					"rigid alignment applied."), *GetName(), *FriendlyRetargetAnchor.ToString(), Gap.Size(), *Gap.ToCompactString());
			}
			else
			{
				UE_LOG(LogTemp, Warning, TEXT("SSCharacterPart %s: anchor '%s' not mapped on %s; module kept at its own "
					"skeleton's position."), *GetName(), *FriendlyRetargetAnchor.ToString(), *GetNameSafe(TargetMesh));
			}
		}

		const TArray<FTransform>& TargetLocal = TargetMesh->GetRefSkeleton().GetRefBonePose();
		const int32 Count = Map.TargetNames.Num();
		FriendlyRetargetScratch.SetNumUninitialized(Count);
		for (int32 Index = 0; Index < Count; ++Index)
		{
			const int32 Parent = Map.TargetParents[Index];
			const int32 SourceIndex = Map.SourceForTarget[Index];
			FTransform Local;
			if (SourceIndex != INDEX_NONE)
			{
				// The source's local ROTATION over the target's own translation and scale:
				// copying the translation too would silently replace Quantum's proportions
				// with the mannequin's bone lengths.
				Local = FTransform(SourceLocalPose[SourceIndex].GetRotation(),
					TargetLocal[Index].GetTranslation(), TargetLocal[Index].GetScale3D());
			}
			else
			{
				Local = Map.DigitMask[Index] ? Map.DigitCurl[Index] : TargetLocal[Index];
			}
			// Local * parent component space, matching FillComponentSpaceTransforms. The root
			// stays identity: it carries the pawn's world motion, which the component's own
			// transform already provides.
			FriendlyRetargetScratch[Index] = Parent == INDEX_NONE ? FTransform::Identity
				: Local * FriendlyRetargetScratch[Parent];
		}
		// Rigid alignment to the leader's anchor bone (FriendlyRetargetAnchor). The retarget above
		// keeps this skeleton's own rest translations, so a module whose bone orientation or spine
		// length differs from the mannequin's lands away from the mannequin's bone -- the mannequin
		// being what the fitted vest, helmet and uniform follow. Moving the whole module rigidly is
		// exact: the anchor lands on the leader's bone and the module keeps its own proportions.
		const int32 Anchor = Map.TargetNames.IndexOfByKey(FriendlyRetargetAnchor);
		const int32 AnchorSource = Map.SourceForTarget.IsValidIndex(Anchor) ? Map.SourceForTarget[Anchor] : INDEX_NONE;
		if (Anchor != INDEX_NONE && AnchorSource != INDEX_NONE && SourceCS.IsValidIndex(AnchorSource))
		{
			// In UE's convention A * B applies as B then A, so the pose that puts this module's anchor
			// on the leader's is TargetAnchor⁻¹ * SourceAnchor, and it is applied on every bone.
			const FTransform Correction = FriendlyRetargetScratch[Anchor].Inverse() * SourceCS[AnchorSource];
			for (FTransform& Pose : FriendlyRetargetScratch)
			{
				Pose = Pose * Correction;
			}
		}

		// Bones come parent-before-child in a reference skeleton, so writing component-space
		// transforms in order localises each against its already-written parent (5.8 removed
		// the LocalSpace bone space from SetBoneTransformByName).
		for (int32 Index = 0; Index < Count; ++Index)
		{
			Part->SetBoneTransformByName(Map.TargetNames[Index], FriendlyRetargetScratch[Index], EBoneSpaces::ComponentSpace);
		}
		Part->RefreshBoneTransforms();
	}
}

void ASSCharacterPartActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	TickFriendlyRetarget(DeltaSeconds);
}

void ASSCharacterPartActor::BeginPlay()
{
	// The CDO may be built before the tag config loads; fill in any missing tags now.
	if (CosmeticTags.Num() < 2)
	{
		AddDefaultCosmeticTags();
	}
	Super::BeginPlay();

	LeaderMesh = FindLeader();
	BuildSet(FriendlyParts, FriendlyMaterialOverrides, FriendlyComponents, bRetargetFriendlyPose);
	BuildSet(OpposingParts, OpposingMaterialOverrides, OpposingComponents);
	BuildSet(FriendlyLeaderPoseParts, {}, FriendlyLeaderPoseComponents);
	if (USkinnedMeshComponent* Leader = LeaderMesh.Get())
	{
		// Component tick order is not actor order: put this actor's retarget tick after the
		// pawn's so the copied pose is this frame's, not last frame's.
		if (AActor* LeaderOwner = Leader->GetOwner())
		{
			PrimaryActorTick.AddPrerequisite(LeaderOwner, LeaderOwner->PrimaryActorTick);
		}
	}
	UE_LOG(LogTemp, Log, TEXT("SSCharacterPart %s: %d retarget + %d leader + %d opposing part(s), leader %s, retarget=%d."), *GetName(),
		FriendlyRetargetComponents.Num(), FriendlyLeaderPoseComponents.Num(), OpposingComponents.Num(),
		*GetNameSafe(LeaderMesh.Get()), bRetargetFriendlyPose);
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
	for (USkinnedMeshComponent* Part : FriendlyComponents) { Part->SetVisibility(bFriendly); }
	for (USkinnedMeshComponent* Part : FriendlyLeaderPoseComponents) { Part->SetVisibility(bFriendly); }
	for (USkinnedMeshComponent* Part : OpposingComponents) { Part->SetVisibility(!bFriendly); }

	// One line per locality change: which parts are drawn. A helmet or vest that is present in the
	// asset but not in this list is invisible in every report that only counts configured parts.
	TInlineComponentArray<USkinnedMeshComponent*> All;
	GetComponents(All);
	FString Drawn;
	int32 DrawnCount = 0;
	for (USkinnedMeshComponent* Part : All)
	{
		if (Part->IsVisible())
		{
			++DrawnCount;
			Drawn += FString::Printf(TEXT("%s "), *GetNameSafe(Part->GetSkinnedAsset()));
		}
	}
	UE_LOG(LogTemp, Log, TEXT("SSCharacterPart %s locality=%d: %d of %d skinned part(s) drawn: %s"),
		*GetName(), static_cast<int32>(Locality), DrawnCount, All.Num(), *Drawn);
}
