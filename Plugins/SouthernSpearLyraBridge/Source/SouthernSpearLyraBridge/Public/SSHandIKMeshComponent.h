// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/SkeletalMeshComponent.h"
#include "SSHandIKMeshComponent.generated.h"

class UStaticMesh;

/**
 * The hold the left hand takes on a weapon, authored from the weapon's own sockets (Session 073) rather
 * than borrowed from a pose: the FBX round trip mangles a socket's rotation, and a handAnim pose's
 * finger rest joints disagree by ~50 deg, so neither can be the target. Socket positions survive the
 * round trip exactly, so the frame is built from those at run time.
 *
 * Forward runs from the right hand (the trigger) to the muzzle; Up is the weapon component's own up
 * made orthogonal to it; Right is Up x Forward. In UE's axes F x R = U, so R = U x F, and the sign is
 * read off the weapon itself: the ejection port sits on +Right and the left hand grip on -Right.
 *
 * The hand's own frame follows: Thumb along the bore, Palm the weapon's up tilted PalmTiltDeg towards
 * its right (the hand sits under and left of the tube; 0 is the palm flat under it, 90 is a vertical
 * grip with the palm facing across), Finger = Palm x Thumb. That order is the left hand's: a left hand
 * has palm = thumb x finger, while thumb x palm is a RIGHT hand's and renders a mirrored fist. Note the
 * consequence for ToHandRotation: the hand's own (palm, finger, thumb) triple is left-handed - palm x
 * finger = -thumb - so it is not a rotation, and the hand's +Z basis axis is the back-of-hand one.
 * One per-skeleton offset still fits every weapon, because the basis is the same on all of them.
 */
struct SSBRIDGE_API FSSGripHold
{
	/** The weapon's orthonormal basis. */
	FVector Forward, Right, Up;
	/** The hand's orthonormal basis, in the left hand's own order. */
	FVector Thumb, Palm, Finger;

	/** The hold as a rotation: +X palm normal, +Y finger direction, +Z the back-of-hand axis (-Thumb). */
	FQuat ToHandRotation() const;
};

/**
 * Pure two-bone left-hand IK on a component-space pose (W2). Tested without a world
 * (SouthernSpear.Bridge.HandIK).
 */
struct SSBRIDGE_API FSSHandIK
{
	/**
	 * Fills Out from the weapon's sockets: Muzzle and RightHandGrip give the bore, WeaponUp is the
	 * weapon component's own up vector. False when the two points coincide or the up vector lies along
	 * the bore, which leaves no frame to hold; Out is zeroed first either way, so a refused build can
	 * never leave a stale hold behind.
	 */
	static bool BuildGripHold(const FVector& Muzzle, const FVector& RightHandGrip, const FVector& WeaponUp,
		float PalmTiltDeg, FSSGripHold& Out);

	/**
	 * Moves Hand towards Target (component space) by Alpha, bending Upper and Lower in the plane of the
	 * current elbow, then carries every descendant of Upper (twist bones, fingers) with its bone. The
	 * hand keeps its animated rotation. Parents[i] is bone i's parent (INDEX_NONE for the root), and
	 * parents precede children, as in every UE reference skeleton. False (pose untouched) when the
	 * chain is not Upper -> ... -> Lower -> ... -> Hand or Alpha is zero.
	 */
	static bool Apply(TArray<FTransform>& ComponentSpace, TConstArrayView<int32> Parents,
		int32 Upper, int32 Lower, int32 Hand, const FVector& Target, float Alpha);

	/**
	 * Turns Hand to Target (component space) by Alpha (shortest-arc slerp) and carries every descendant
	 * with it: each one keeps the local (parent-relative) transform it has, so fingers and twist bones
	 * follow the hand instead of being left behind. The hand's location is untouched, because the
	 * position solve (Apply) has already put it there. False (pose untouched) for a bad index or Alpha 0.
	 */
	static bool RotateChain(TArray<FTransform>& ComponentSpace, TConstArrayView<int32> Parents, int32 Hand,
		const FQuat& Target, float Alpha);

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
 * The wrist solve places the hand; the hold authored from the weapon's own sockets, then
 * HandRotationOffset, turns the hand itself (a wrist-only solve leaves the palm open and flat,
 * Session 070), and the hand's descendants follow it. The offset is per skeleton, so it lives in config.
 *
 * The IK fades out (BlendSpeed) while a reload, draw, holster or equip plays (the body's active montage
 * name contains one of SuppressingAnimationWords; the first-person arms, which play single clips, are
 * told through SetHandIKSuppressed), while Lyra's
 * DisableLHandIK curve is up, while ragdolled, when the target is out of reach, and when the weapon has
 * no grip socket (pistols, until they get one). Presentation only (ADR-004). ss.HandIK 0 turns it off.
 */
UCLASS(config = Game, ClassGroup = (SouthernSpear), meta = (BlueprintSpawnableComponent))
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

	/** The bore's far end. With RightHandGrip it gives the weapon's forward axis (Session 073). */
	UPROPERTY(EditAnywhere, Category = "Hand IK")
	TArray<FName> MuzzleSockets = { TEXT("Muzzle"), TEXT("SOCKET_Muzzle") };

	/** The trigger hand. With Muzzle it gives the weapon's forward axis. */
	UPROPERTY(EditAnywhere, Category = "Hand IK")
	TArray<FName> RightGripSockets = { TEXT("RightHandGrip"), TEXT("SOCKET_RightHandGrip") };

	/**
	 * How far the palm normal leans off the weapon's up, in degrees, per weapon - the hold, as data
	 * (Session 073). Keyed by the held mesh's name without its SM_ prefix (A88, A416), so a weapon
	 * needs no code change. 0 is the palm flat under the handguard, 90 a vertical grip. Unlisted weapons
	 * take DefaultPalmTiltDeg, which is the plain handguard.
	 */
	UPROPERTY(Config, EditAnywhere, Category = "Hand IK")
	TMap<FName, float> GripPalmTiltDeg;

	/** Palm tilt for a weapon with no row of its own (DefaultPalmTiltDeg, 30: a hand under a handguard). */
	UPROPERTY(Config, EditAnywhere, Category = "Hand IK")
	float DefaultPalmTiltDeg = 30.f;

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

	/**
	 * Turn the hand itself to the grip's hold rotation (hold * HandRotationOffset) once the wrist solve
	 * has put it there, carrying the fingers and wrist-twist bones with it. A wrist-only solve leaves the
	 * palm however the animation had it (flat on the receiver for the first-person arms).
	 *
	 * The hold comes from the sockets (FSSHandIK::BuildGripHold) each time the grip resolves, so one
	 * per-skeleton correction fits every weapon. A weapon without a muzzle or right-hand socket falls
	 * back to the grip socket's own rotation, which is what this did before the hold was authored.
	 *
	 * Off by default: the third-person body's own Lyra hold already gives it a gripping hand, so only the
	 * first-person arms, which have no grip animation, turn it on. The correction is per skeleton, so the
	 * value lives in config: [/Script/SouthernSpearLyraBridge.SSHandIKMeshComponent]
	 * HandRotationOffset=(Pitch=,Yaw=,Roll=). A zero offset takes the hold as authored.
	 */
	UPROPERTY(EditAnywhere, Category = "Hand IK")
	bool bRotateHandToGrip = false;

	/** With bRotateHandToGrip: correction between the grip socket's rotation and this skeleton's hand bone. */
	UPROPERTY(Config, EditAnywhere, Category = "Hand IK")
	FRotator HandRotationOffset = FRotator::ZeroRotator;

	/** For meshes driven by single clips (the first-person arms): true while the clip moves the left hand. */
	void SetHandIKSuppressed(bool bSuppressed) { bSuppressedExternally = bSuppressed; }

	/** True when an animation of this name moves the left hand itself (SuppressingAnimationWords). */
	bool IsSuppressingAnimationName(const FString& Name) const;

	/** The weapon's authored palm tilt: its own row in GripPalmTiltDeg, else DefaultPalmTiltDeg. */
	float PalmTiltDeg(const UStaticMesh& WeaponMesh) const;

	/** Current blend, 0..1 (diagnostics). */
	float GetHandIKAlpha() const { return Alpha; }

private:
	/** Game thread, before this frame's evaluation: find the grip and where it sits on the attach bone. */
	void UpdateGrip(float DeltaTime);
	bool ResolveBones();
	bool IsSuppressedByAnimation() const;

	/** Grip socket relative to the socket (or bone) the weapon hangs from on this mesh. */
	FTransform GripInAttach = FTransform::Identity;
	/** The authored hold, in the attach frame, rebuilt each time the grip resolves. */
	FQuat HoldInAttach = FQuat::Identity;
	FName AttachSocket;
	bool bHasGrip = false;
	bool bHasHold = false;
	float Alpha = 0.f;
	bool bSuppressedExternally = false;

	TWeakObjectPtr<const USkeletalMesh> ResolvedFor;
	TArray<int32> Parents;
	int32 Upper = INDEX_NONE;
	int32 Lower = INDEX_NONE;
	int32 Hand = INDEX_NONE;
	bool bWarnedBones = false;
};
