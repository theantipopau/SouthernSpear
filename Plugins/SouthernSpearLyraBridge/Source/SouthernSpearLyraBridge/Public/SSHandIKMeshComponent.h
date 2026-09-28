// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/SkeletalMeshComponent.h"
#include "SSHandIKMeshComponent.generated.h"

/**
 * Pure two-bone left-hand IK on a component-space pose (W2). Tested without a world
 * (SouthernSpear.Bridge.HandIK).
 */
struct SSBRIDGE_API FSSHandIK
{
	/**
	 * Moves Hand towards Target (component space) by Alpha, bending Upper and Lower in the plane of the
	 * current elbow, then carries every descendant of Upper (twist bones, fingers) with its bone. The
	 * hand keeps its animated rotation. Parents[i] is bone i's parent (INDEX_NONE for the root), and
	 * parents precede children, as in every UE reference skeleton. False (pose untouched) when the
	 * chain is not Upper -> ... -> Lower -> ... -> Hand or Alpha is zero.
	 */
	static bool Apply(TArray<FTransform>& ComponentSpace, TConstArrayView<int32> Parents,
		int32 Upper, int32 Lower, int32 Hand, const FVector& Target, float Alpha);

	/** True when Ancestor is Bone or one of its ancestors. */
	static bool IsAncestor(TConstArrayView<int32> Parents, int32 Ancestor, int32 Bone);
};

/**
 * A skeletal mesh component that puts its left hand on the held weapon (W2, WEAPONS_ANIMATION_PLAN).
 *
 * The held weapon's static mesh carries the LeftHandGrip socket (exported from Blender as
 * SOCKET_LeftHandGrip; the FBX importer drops the prefix, as it does for Muzzle), where the ADFRC handAnim pose puts the left
 * wrist on that weapon (Tools/Common/adfrc_grip.py). After each animation evaluation, before the pose is
 * published, this component runs a two-bone IK on its left arm to that socket, in C++: no Lyra asset is
 * changed and no Animation Blueprint is needed. Everything that follows this mesh by leader pose (the
 * visible soldier parts) inherits the result, because they read its component-space pose.
 *
 * Used for the third-person body (ASSCharacter's mesh; Manny bones upperarm_l / lowerarm_l / hand_l) and
 * the first-person arms (USSFirstPersonSubsystem; the Fab arms' LeftArm / LeftForeArm / LeftHand). The
 * bones are found by name from a candidate list, so one class serves both skeletons.
 *
 * The IK fades out (BlendSpeed) while a reload, draw, holster or equip plays (the body's active montage
 * name contains one of SuppressingAnimationWords; the first-person arms, which play single clips, are
 * told through SetHandIKSuppressed), while Lyra's
 * DisableLHandIK curve is up, while ragdolled, when the target is out of reach, and when the weapon has
 * no grip socket (pistols, until they get one). Presentation only (ADR-004). ss.HandIK 0 turns it off.
 */
UCLASS(ClassGroup = (SouthernSpear), meta = (BlueprintSpawnableComponent))
class SSBRIDGE_API USSHandIKMeshComponent : public USkeletalMeshComponent
{
	GENERATED_BODY()

public:
	USSHandIKMeshComponent(const FObjectInitializer& ObjectInitializer);

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
	virtual void FinalizeBoneTransform() override;

	/** Socket names on the held weapon's static mesh, first match wins (imported name, then the Blender name). */
	UPROPERTY(EditAnywhere, Category = "Hand IK")
	TArray<FName> GripSockets = { TEXT("LeftHandGrip"), TEXT("SOCKET_LeftHandGrip") };

	/** Candidate bone names, first match wins (Manny, then the Fab first-person arms). */
	UPROPERTY(EditAnywhere, Category = "Hand IK")
	TArray<FName> UpperArmBones = { TEXT("upperarm_l"), TEXT("LeftArm") };
	UPROPERTY(EditAnywhere, Category = "Hand IK")
	TArray<FName> LowerArmBones = { TEXT("lowerarm_l"), TEXT("LeftForeArm") };
	UPROPERTY(EditAnywhere, Category = "Hand IK")
	TArray<FName> HandBones = { TEXT("hand_l"), TEXT("LeftHand") };

	/** An animation whose name contains one of these moves the left hand itself: the IK fades out. */
	UPROPERTY(EditAnywhere, Category = "Hand IK")
	TArray<FString> SuppressingAnimationWords = { TEXT("Reload"), TEXT("Equip"), TEXT("Holster"), TEXT("Draw"), TEXT("Inspect") };

	/** Lyra's curve for the same purpose; 1 turns the IK off. */
	UPROPERTY(EditAnywhere, Category = "Hand IK")
	FName DisableCurve = TEXT("DisableLHandIK");

	/** Alpha change per second when fading in or out. */
	UPROPERTY(EditAnywhere, Category = "Hand IK")
	float BlendSpeed = 8.f;

	/** The target may be at most this factor of the arm's length from the shoulder. */
	UPROPERTY(EditAnywhere, Category = "Hand IK")
	float MaxReachFactor = 1.05f;

	/** For meshes driven by single clips (the first-person arms): true while the clip moves the left hand. */
	void SetHandIKSuppressed(bool bSuppressed) { bSuppressedExternally = bSuppressed; }

	/** True when an animation of this name moves the left hand itself (SuppressingAnimationWords). */
	bool IsSuppressingAnimationName(const FString& Name) const;

	/** Current blend, 0..1 (diagnostics). */
	float GetHandIKAlpha() const { return Alpha; }

private:
	/** Game thread, before this frame's evaluation: find the grip and where it sits on the attach bone. */
	void UpdateGrip(float DeltaTime);
	bool ResolveBones();
	bool IsSuppressedByAnimation() const;

	/** Grip socket relative to the socket (or bone) the weapon hangs from on this mesh. */
	FTransform GripInAttach = FTransform::Identity;
	FName AttachSocket;
	bool bHasGrip = false;
	float Alpha = 0.f;
	bool bSuppressedExternally = false;

	TWeakObjectPtr<const USkeletalMesh> ResolvedFor;
	TArray<int32> Parents;
	int32 Upper = INDEX_NONE;
	int32 Lower = INDEX_NONE;
	int32 Hand = INDEX_NONE;
	bool bWarnedBones = false;
};
