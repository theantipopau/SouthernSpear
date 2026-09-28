// Copyright Southern Spear. All Rights Reserved.

#include "SSHandIKMeshComponent.h"

#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/SkeletalMeshSocket.h"
#include "HAL/IConsoleManager.h"

DEFINE_LOG_CATEGORY_STATIC(LogSSHandIK, Log, All);

namespace
{
	TAutoConsoleVariable<int32> CVarHandIK(TEXT("ss.HandIK"), 1,
		TEXT("Left hand on the held weapon's SOCKET_LeftHandGrip (W2): 1 on, 0 off (for comparison)."));

	FVector Perpendicular(const FVector& V, const FVector& Axis)
	{
		return V - Axis * FVector::DotProduct(V, Axis);
	}
}

// --------------------------------------------------------------------------- pure IK

bool FSSHandIK::IsAncestor(TConstArrayView<int32> Parents, int32 Ancestor, int32 Bone)
{
	for (int32 Guard = 0; Bone != INDEX_NONE && Guard <= Parents.Num(); ++Guard)
	{
		if (Bone == Ancestor)
		{
			return true;
		}
		Bone = Parents.IsValidIndex(Bone) ? Parents[Bone] : INDEX_NONE;
	}
	return false;
}

bool FSSHandIK::Apply(TArray<FTransform>& ComponentSpace, TConstArrayView<int32> Parents,
	int32 Upper, int32 Lower, int32 Hand, const FVector& Target, float InAlpha)
{
	const int32 Num = ComponentSpace.Num();
	if (InAlpha <= 0.f || Parents.Num() != Num || !ComponentSpace.IsValidIndex(Upper) || !ComponentSpace.IsValidIndex(Lower)
		|| !ComponentSpace.IsValidIndex(Hand) || Upper == Lower || Lower == Hand
		|| !IsAncestor(Parents, Upper, Lower) || !IsAncestor(Parents, Lower, Hand))
	{
		return false;
	}
	const TArray<FTransform> Old = ComponentSpace;
	const FVector A = Old[Upper].GetLocation();
	const FVector B = Old[Lower].GetLocation();
	const FVector C = Old[Hand].GetLocation();
	const double L1 = FVector::Distance(A, B);
	const double L2 = FVector::Distance(B, C);
	if (L1 < UE_KINDA_SMALL_NUMBER || L2 < UE_KINDA_SMALL_NUMBER)
	{
		return false;
	}

	const FVector Effector = FMath::Lerp(C, Target, FMath::Clamp(InAlpha, 0.f, 1.f));
	const FVector ToEffector = Effector - A;
	const double Reach = ToEffector.Size();
	if (Reach < UE_KINDA_SMALL_NUMBER)
	{
		return false;
	}
	const FVector Dir = ToEffector / Reach;
	// No stretching: the hand stops at full reach, and never folds inside |L1 - L2|.
	const double D = FMath::Clamp(Reach, FMath::Abs(L1 - L2) + 0.01, L1 + L2 - 0.001);

	// Bend in the plane of the animated elbow (its direction off the shoulder-to-target line).
	FVector Bend = Perpendicular(B - A, Dir);
	if (Bend.SizeSquared() < 1e-6)
	{
		Bend = Perpendicular(C - B, Dir);
	}
	if (Bend.SizeSquared() < 1e-6)
	{
		Bend = Perpendicular(FVector::UpVector, Dir);
	}
	Bend.Normalize();

	const double CosA = FMath::Clamp((L1 * L1 + D * D - L2 * L2) / (2.0 * L1 * D), -1.0, 1.0);
	const FVector NewB = A + Dir * (L1 * CosA) + Bend * (L1 * FMath::Sqrt(FMath::Max(0.0, 1.0 - CosA * CosA)));
	const FVector NewC = A + Dir * D;

	// Upper: turn its bone towards the new elbow. Lower: after that turn, towards the new hand.
	const FQuat UpperDelta = FQuat::FindBetweenNormals((B - A).GetSafeNormal(), (NewB - A).GetSafeNormal());
	const FVector CarriedForearm = UpperDelta.RotateVector(C - B).GetSafeNormal();
	const FQuat LowerDelta = FQuat::FindBetweenNormals(CarriedForearm, (NewC - NewB).GetSafeNormal()) * UpperDelta;

	FTransform NewUpper = Old[Upper];
	NewUpper.SetRotation((UpperDelta * Old[Upper].GetRotation()).GetNormalized());
	FTransform NewLower = Old[Lower];
	NewLower.SetRotation((LowerDelta * Old[Lower].GetRotation()).GetNormalized());
	NewLower.SetLocation(NewB);
	FTransform NewHand = Old[Hand]; // the hand keeps its animated rotation
	NewHand.SetLocation(NewC);

	// Carry every descendant of Upper with its (moved) parent; parents precede children.
	TArray<bool> Moved;
	Moved.Init(false, Num);
	Moved[Upper] = true;
	ComponentSpace[Upper] = NewUpper;
	for (int32 Bone = Upper + 1; Bone < Num; ++Bone)
	{
		const int32 Parent = Parents[Bone];
		if (Parent == INDEX_NONE || !Moved[Parent])
		{
			continue;
		}
		Moved[Bone] = true;
		if (Bone == Lower)
		{
			ComponentSpace[Bone] = NewLower;
		}
		else if (Bone == Hand)
		{
			ComponentSpace[Bone] = NewHand;
		}
		else
		{
			ComponentSpace[Bone] = Old[Bone].GetRelativeTransform(Old[Parent]) * ComponentSpace[Parent];
		}
	}
	return true;
}

// --------------------------------------------------------------------------- component

USSHandIKMeshComponent::USSHandIKMeshComponent(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
}

bool USSHandIKMeshComponent::ResolveBones()
{
	const USkeletalMesh* Mesh = GetSkeletalMeshAsset();
	if (!Mesh)
	{
		return false;
	}
	if (ResolvedFor.Get() == Mesh)
	{
		return Upper != INDEX_NONE;
	}
	ResolvedFor = Mesh;
	const FReferenceSkeleton& Ref = Mesh->GetRefSkeleton();
	Parents.SetNum(Ref.GetNum());
	for (int32 Bone = 0; Bone < Ref.GetNum(); ++Bone)
	{
		Parents[Bone] = Ref.GetParentIndex(Bone);
	}
	auto Find = [&Ref](const TArray<FName>& Names)
	{
		for (const FName& Name : Names)
		{
			const int32 Index = Ref.FindBoneIndex(Name);
			if (Index != INDEX_NONE)
			{
				return Index;
			}
		}
		return int32(INDEX_NONE);
	};
	Upper = Find(UpperArmBones);
	Lower = Find(LowerArmBones);
	Hand = Find(HandBones);
	const bool bChain = Upper != INDEX_NONE && Lower != INDEX_NONE && Hand != INDEX_NONE
		&& FSSHandIK::IsAncestor(Parents, Upper, Lower) && FSSHandIK::IsAncestor(Parents, Lower, Hand);
	if (!bChain)
	{
		if (!bWarnedBones)
		{
			bWarnedBones = true;
			UE_LOG(LogSSHandIK, Warning, TEXT("%s (%s): no left-arm chain from the candidate bone names; left-hand IK is off for this mesh."),
				*GetName(), *Mesh->GetName());
		}
		Upper = Lower = Hand = INDEX_NONE;
		return false;
	}
	UE_LOG(LogSSHandIK, Log, TEXT("%s (%s): left-hand IK on %s > %s > %s."), *GetName(), *Mesh->GetName(),
		*Ref.GetBoneName(Upper).ToString(), *Ref.GetBoneName(Lower).ToString(), *Ref.GetBoneName(Hand).ToString());
	return true;
}

bool USSHandIKMeshComponent::IsSuppressingAnimationName(const FString& Name) const
{
	for (const FString& Word : SuppressingAnimationWords)
	{
		if (Name.Contains(Word))
		{
			return true;
		}
	}
	return false;
}

bool USSHandIKMeshComponent::IsSuppressedByAnimation() const
{
	if (bSuppressedExternally)
	{
		return true;
	}
	if (const UAnimInstance* Instance = GetAnimInstance())
	{
		if (!DisableCurve.IsNone() && Instance->GetCurveValue(DisableCurve) > 0.5f)
		{
			return true;
		}
		const UAnimMontage* Montage = Instance->GetCurrentActiveMontage();
		return Montage && IsSuppressingAnimationName(Montage->GetName());
	}
	return false;
}

void USSHandIKMeshComponent::UpdateGrip(float DeltaTime)
{
	// Game thread, before this frame's evaluation: the attached weapon's world transform and this mesh's
	// published pose are from the same (last) frame, so their relative transform is exact.
	bHasGrip = false;
	float Want = 0.f;
	if (CVarHandIK.GetValueOnGameThread() != 0 && ResolveBones() && !IsSimulatingPhysics())
	{
		for (USceneComponent* Child : GetAttachChildren())
		{
			if (!Child)
			{
				continue;
			}
			TArray<USceneComponent*> Candidates;
			Child->GetChildrenComponents(true, Candidates);
			Candidates.Insert(Child, 0);
			for (USceneComponent* Candidate : Candidates)
			{
				const UStaticMeshComponent* Weapon = Cast<UStaticMeshComponent>(Candidate);
				if (Weapon && Weapon->IsVisible() && Weapon->DoesSocketExist(GripSocket))
				{
					AttachSocket = Child->GetAttachSocketName();
					const FTransform AttachWorld = AttachSocket.IsNone() ? GetComponentTransform() : GetSocketTransform(AttachSocket, RTS_World);
					GripInAttach = Weapon->GetSocketTransform(GripSocket, RTS_World).GetRelativeTransform(AttachWorld);
					bHasGrip = true;
					break;
				}
			}
			if (bHasGrip)
			{
				break;
			}
		}
		Want = bHasGrip && !IsSuppressedByAnimation() ? 1.f : 0.f;
	}
	Alpha = FMath::FInterpConstantTo(Alpha, Want, DeltaTime, BlendSpeed);
}

void USSHandIKMeshComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	UpdateGrip(DeltaTime);
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
}

void USSHandIKMeshComponent::FinalizeBoneTransform()
{
	// The new pose is in the editable buffer until Super publishes it; the leader-posed soldier parts
	// and the physics bodies read the published one.
	const USkeletalMesh* Mesh = GetSkeletalMeshAsset();
	if (Alpha > UE_KINDA_SMALL_NUMBER && bHasGrip && Mesh && ResolvedFor.Get() == Mesh && Upper != INDEX_NONE)
	{
		TArray<FTransform>& Pose = GetEditableComponentSpaceTransforms();
		if (Pose.Num() == Parents.Num())
		{
			FTransform AttachCS = FTransform::Identity;
			bool bAttach = AttachSocket.IsNone();
			if (!bAttach)
			{
				if (const USkeletalMeshSocket* Socket = Mesh->FindSocket(AttachSocket))
				{
					const int32 Bone = GetBoneIndex(Socket->BoneName);
					if (Pose.IsValidIndex(Bone))
					{
						AttachCS = Socket->GetSocketLocalTransform() * Pose[Bone];
						bAttach = true;
					}
				}
				else
				{
					const int32 Bone = GetBoneIndex(AttachSocket);
					if (Pose.IsValidIndex(Bone))
					{
						AttachCS = Pose[Bone];
						bAttach = true;
					}
				}
			}
			if (bAttach)
			{
				const FVector Target = (GripInAttach * AttachCS).GetLocation();
				const double ArmLength = FVector::Distance(Pose[Upper].GetLocation(), Pose[Lower].GetLocation())
					+ FVector::Distance(Pose[Lower].GetLocation(), Pose[Hand].GetLocation());
				if (FVector::Distance(Pose[Upper].GetLocation(), Target) <= ArmLength * MaxReachFactor)
				{
					FSSHandIK::Apply(Pose, Parents, Upper, Lower, Hand, Target, Alpha);
				}
			}
		}
	}
	Super::FinalizeBoneTransform();
}
