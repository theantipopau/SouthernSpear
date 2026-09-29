// Copyright Southern Spear. All Rights Reserved.
//
// TEMPORARY dev probe (Session 070) — not for commit. See SSHandIKProbeSubsystem.h.
// Everything here reads public engine/component API; it changes no pose and no property.

#include "SSHandIKProbeSubsystem.h"

#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Materials/MaterialInterface.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "SSHandIKMeshComponent.h"
#include "UObject/UnrealType.h"

DEFINE_LOG_CATEGORY_STATIC(LogSSHandIKProbe, Log, All);

namespace
{
	constexpr float SampleInterval = 0.5f;
	constexpr int32 SampleCount = 11;   // t = 0, 0.5 ... 5.0 s

	/** Ablation: hide every mesh component whose name or mesh contains this text (empty = off). */
	TAutoConsoleVariable<FString> CVarProbeHide(TEXT("ss.Probe.Hide"), TEXT(""),
		TEXT("TEMP probe: hide mesh components whose component or mesh name contains this text."));

	FString ProbePathOf(const UObject* Object)
	{
		return Object ? Object->GetPathName() : TEXT("none");
	}

	FString ProbeMeshOf(const UMeshComponent& Mesh)
	{
		if (const USkeletalMeshComponent* Skinned = Cast<USkeletalMeshComponent>(&Mesh))
		{
			return ProbePathOf(Skinned->GetSkeletalMeshAsset());
		}
		if (const UStaticMeshComponent* Static = Cast<UStaticMeshComponent>(&Mesh))
		{
			return ProbePathOf(Static->GetStaticMesh());
		}
		return TEXT("none");
	}

	/** First candidate bone name that exists on this mesh, NAME_None if none do. */
	FName ProbeFirstBone(const USkeletalMeshComponent& Mesh, const TArray<FName>& Candidates)
	{
		for (const FName& Name : Candidates)
		{
			if (Mesh.GetBoneIndex(Name) != INDEX_NONE)
			{
				return Name;
			}
		}
		return NAME_None;
	}

	/** The visible weapon whose static mesh carries one of the component's grip sockets. */
	UStaticMeshComponent* ProbeFindWeapon(const USSHandIKMeshComponent& Arms, FName& OutSocket)
	{
		for (USceneComponent* Child : Arms.GetAttachChildren())
		{
			if (!Child)
			{
				continue;
			}
			TArray<USceneComponent*> Candidates;
			Child->GetChildrenComponents(/*bIncludeAllDescendants=*/ true, Candidates);
			Candidates.Insert(Child, 0);
			for (USceneComponent* Candidate : Candidates)
			{
				const UStaticMeshComponent* Weapon = Cast<UStaticMeshComponent>(Candidate);
				if (!Weapon || !Weapon->IsVisible())
				{
					continue;
				}
				for (const FName& Name : Arms.GripSockets)
				{
					if (Weapon->DoesSocketExist(Name))
					{
						OutSocket = Name;
						return const_cast<UStaticMeshComponent*>(Weapon);
					}
				}
			}
		}
		return nullptr;
	}

	FString ProbeVectorText(const FVector& V)
	{
		return FString::Printf(TEXT("(%.1f,%.1f,%.1f)"), V.X, V.Y, V.Z);
	}

	FString ProbeQuatText(const FQuat& Q)
	{
		return FString::Printf(TEXT("(%.4f,%.4f,%.4f,%.4f)"), Q.X, Q.Y, Q.Z, Q.W);
	}

	FString ProbeRotatorText(const FQuat& Q)
	{
		const FRotator R = Q.Rotator();
		return FString::Printf(TEXT("(P=%.2f,Y=%.2f,R=%.2f)"), R.Pitch, R.Yaw, R.Roll);
	}

	/** The angle between two directions, in degrees (0 when either is degenerate). */
	double ProbeAngleDeg(const FVector& A, const FVector& B)
	{
		if (A.IsNearlyZero() || B.IsNearlyZero())
		{
			return -1.0;
		}
		return FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FVector::DotProduct(A.GetSafeNormal(), B.GetSafeNormal()), -1.0, 1.0)));
	}

	/**
	 * The distal bone of the finger whose name contains Key (Thumb, Index, Middle) **under this hand**, found by
	 * walking the hierarchy rather than by trusting the name: which hand a finger belongs to is a fact about the
	 * skeleton, not about its naming, and the two rigs here disagree (SK_FP_Arms_Rifle lists RightHandThumb1
	 * before LeftHandThumb1). The distal bone, not the proximal one, so thumb and fingers are far enough apart
	 * for their cross product (the palm normal) to mean anything.
	 */
	FName ProbeFingerBone(const USkeletalMeshComponent& Mesh, FName Hand, const TCHAR* Key)
	{
		const USkeletalMesh* Skeleton = Mesh.GetSkeletalMeshAsset();
		if (!Skeleton)
		{
			return NAME_None;
		}
		const FReferenceSkeleton& Ref = Skeleton->GetRefSkeleton();
		const int32 HandIndex = Ref.FindBoneIndex(Hand);
		if (HandIndex == INDEX_NONE)
		{
			return NAME_None;
		}
		FName Found = NAME_None;
		for (int32 Bone = 0; Bone < Ref.GetNum(); ++Bone)
		{
			if (!Ref.GetBoneName(Bone).ToString().Contains(Key))
			{
				continue;
			}
			for (int32 Walk = Bone, Guard = 0; Walk != INDEX_NONE && Guard <= Ref.GetNum();
				Walk = Ref.GetParentIndex(Walk), ++Guard)
			{
				if (Walk == HandIndex)
				{
					Found = Ref.GetBoneName(Bone);
					break;
				}
			}
		}
		return Found;
	}

	/**
	 * A hand's own frame, measured from its finger bones and therefore comparable across rigs: where the thumb
	 * points, where the fingers point, and the palm normal. Re-orthogonalised, because three directions read off
	 * bone heads are not a frame.
	 *
	 * The order is the socket's own convention (adfrc_grip.HOLD_PROFILES, Session 072): a left hand obeys
	 * Palm x Finger = Thumb, so the palm normal is Finger x Thumb, NOT Thumb x Finger - that one is the back of
	 * the hand, and reading the palm as its negative put the handguard hold a half turn out.
	 */
	struct FProbeHandFrame
	{
		FVector Thumb = FVector::ZeroVector;
		FVector Finger = FVector::ZeroVector;
		FVector Palm = FVector::ZeroVector;
		bool bValid = false;
	};

	FProbeHandFrame ProbeHandFrame(const USkeletalMeshComponent& Mesh, FName Hand, FName ThumbBone, FName FingerBone)
	{
		FProbeHandFrame Frame;
		if (Hand.IsNone() || ThumbBone.IsNone() || FingerBone.IsNone())
		{
			return Frame;
		}
		const FVector Origin = Mesh.GetBoneLocation(Hand, EBoneSpaces::ComponentSpace);
		const FVector RawThumb = (Mesh.GetBoneLocation(ThumbBone, EBoneSpaces::ComponentSpace) - Origin).GetSafeNormal();
		const FVector RawFinger = (Mesh.GetBoneLocation(FingerBone, EBoneSpaces::ComponentSpace) - Origin).GetSafeNormal();
		Frame.Thumb = RawThumb;
		Frame.Palm = FVector::CrossProduct(RawFinger, RawThumb).GetSafeNormal();
		Frame.Finger = FVector::CrossProduct(Frame.Thumb, Frame.Palm).GetSafeNormal();
		Frame.bValid = !Frame.Thumb.IsNearlyZero() && !Frame.Palm.IsNearlyZero() && !Frame.Finger.IsNearlyZero();
		return Frame;
	}

	/**
	 * The same frame, read off a hold socket: +X is the palm normal, +Y the finger direction, +Z the thumb
	 * direction, on every weapon (adfrc_grip.HOLD_PROFILES). This is the target the arms' own anatomy has to
	 * meet, so the socket - not the other rig - says what the hold is.
	 */
	FProbeHandFrame ProbeSocketFrame(const FQuat& SocketRotation)
	{
		FProbeHandFrame Frame;
		Frame.Palm = SocketRotation.RotateVector(FVector::ForwardVector);
		Frame.Finger = SocketRotation.RotateVector(FVector::RightVector);
		Frame.Thumb = SocketRotation.RotateVector(FVector::UpVector);
		Frame.bValid = true;
		return Frame;
	}

	/**
	 * The rotation that carries the From frame onto the To frame: the shortest arc onto the palm normal, then
	 * the twist about it that brings the thumb across. This is the piece the cross-rig transfer was missing - it
	 * matches the two hands' *measured anatomy*, so neither rig's bone axis convention can leak into the answer.
	 */
	FQuat ProbeAlign(const FProbeHandFrame& From, const FProbeHandFrame& To)
	{
		if (!From.bValid || !To.bValid)
		{
			return FQuat::Identity;
		}
		const FQuat Swing = FQuat::FindBetweenNormals(From.Palm, To.Palm);
		const FVector ThumbAfterSwing = Swing.RotateVector(From.Thumb);
		// Both are perpendicular to the target palm normal, so this arc is exactly the twist about it.
		const FVector Twisted = (ThumbAfterSwing - To.Palm * FVector::DotProduct(ThumbAfterSwing, To.Palm)).GetSafeNormal();
		const FQuat Twist = FQuat::FindBetweenNormals(Twisted, To.Thumb);
		// UE's A * B applies B first and then A (checked against the engine's own logged triples: the arms'
		// weapon_in_cs * hand_in_weapon reproduces its hand rotation exactly), so the swing comes second here.
		return Twist * Swing;
	}

	/** The same frame expressed in another space (or after a rotation), axis by axis. */
	FProbeHandFrame ProbeFrameInFrame(const FProbeHandFrame& Frame, const FQuat& Rotation)
	{
		FProbeHandFrame Out;
		Out.Thumb = Rotation.RotateVector(Frame.Thumb);
		Out.Finger = Rotation.RotateVector(Frame.Finger);
		Out.Palm = Rotation.RotateVector(Frame.Palm);
		Out.bValid = Frame.bValid;
		return Out;
	}

	// The body rig's own grip, measured from its finger bones in the weapon's frame: the reference the arms are
	// aligned to. File scope, because a probe that exists to print two numbers needs no object state for it.
	FProbeHandFrame GBodyFrameInWeapon;
	bool GHaveBodyFrame = false;

	/** The three axis errors of a measured frame against a target one, in degrees. */
	FString ProbeErrorText(const FProbeHandFrame& Measured, const FProbeHandFrame& Target)
	{
		if (!Measured.bValid || !Target.bValid)
		{
			return TEXT("no-frame");
		}
		return FString::Printf(TEXT("palm_err=%.1f thumb_err=%.1f finger_err=%.1f"),
			ProbeAngleDeg(Measured.Palm, Target.Palm), ProbeAngleDeg(Measured.Thumb, Target.Thumb),
			ProbeAngleDeg(Measured.Finger, Target.Finger));
	}

	FString ProbeFrameText(const FProbeHandFrame& Frame)
	{
		if (!Frame.bValid)
		{
			return TEXT("no-frame");
		}
		return FString::Printf(TEXT("palm=%s thumb=%s finger=%s"), *ProbeVectorText(Frame.Palm),
			*ProbeVectorText(Frame.Thumb), *ProbeVectorText(Frame.Finger));
	}

	/** First of Candidates that exists on this static mesh, NAME_None if none do. */
	FName ProbeFirstSocket(const UStaticMeshComponent& Weapon, const TArray<FName>& Candidates)
	{
		for (const FName& Name : Candidates)
		{
			if (Weapon.DoesSocketExist(Name))
			{
				return Name;
			}
		}
		return NAME_None;
	}

	/** Reflection, so the probe compiles whatever the access level of the flag is. */
	bool ProbeBoolProperty(const UObject* Object, const TCHAR* Name)
	{
		if (const FBoolProperty* Property = FindFProperty<FBoolProperty>(Object->GetClass(), FName(Name)))
		{
			return Property->GetPropertyValue_InContainer(Object);
		}
		return false;
	}

	void ProbeCollectArms(AActor& Actor, TArray<USSHandIKMeshComponent*>& Out)
	{
		for (UActorComponent* Component : Actor.GetComponents())
		{
			if (USSHandIKMeshComponent* Arms = Cast<USSHandIKMeshComponent>(Component))
			{
				Out.AddUnique(Arms);
			}
		}
	}
}

void USSHandIKProbeSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	bEnabled = FParse::Param(FCommandLine::Get(), TEXT("SSHandIKProbe"));
	// -SSHandIKProbeNoRotate measures the hand as the clip leaves it, which is the pose the offset has to be
	// solved from: with the rotation step on, the hand bone is already carrying the old offset.
	bNoRotate = bEnabled && FParse::Param(FCommandLine::Get(), TEXT("SSHandIKProbeNoRotate"));
	if (bEnabled)
	{
		UE_LOG(LogSSHandIKProbe, Log, TEXT("Probe armed: %d samples every %.2f s, once the view model exists (%s)."),
			SampleCount, SampleInterval, bNoRotate ? TEXT("hand rotation OFF") : TEXT("hand rotation as configured"));
	}
}

TStatId USSHandIKProbeSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USSHandIKProbeSubsystem, STATGROUP_Tickables);
}

bool USSHandIKProbeSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

void USSHandIKProbeSubsystem::Tick(float DeltaTime)
{
	if (!bEnabled)
	{
		return;
	}
	UWorld* World = GetWorld();
	APlayerController* Player = World ? World->GetFirstPlayerController() : nullptr;
	APawn* Pawn = Player && Player->IsLocalController() ? Player->GetPawn() : nullptr;
	if (!Pawn)
	{
		return;
	}
	// Keep any ablation applied even after the sampling window (the capture comes later).
	HideMatching(*Pawn);
	if (bDone)
	{
		return;
	}

	// The probe follows the local pawn: after death and re-deploy, start again.
	if (ProbePawn.Get() != Pawn)
	{
		ProbePawn = Pawn;
		bStarted = false;
		bListed = false;
		Elapsed = 0.f;
		NextSample = 0.f;
		Samples = 0;
	}

	TArray<USSHandIKMeshComponent*> Arms;
	ProbeCollectArms(*Pawn, Arms);
	if (bNoRotate)
	{
		// Hold the measurement pose: the arms' component is built with the rotation step on.
		for (USSHandIKMeshComponent* ArmsMesh : Arms)
		{
			if (ArmsMesh && ArmsMesh->GetName().Contains(TEXT("FirstPersonArms")))
			{
				ArmsMesh->bRotateHandToGrip = false;
			}
		}
	}
	if (Arms.Num() == 0)
	{
		return; // the view model is built on the first tick after possession
	}

	// Start only once the first-person view model is really there: the body's own mesh is a
	// hand-IK component too, and it appears a few ticks earlier with no weapon on it yet.
	bool bViewReady = false;
	for (const USSHandIKMeshComponent* ArmsMesh : Arms)
	{
		if (ArmsMesh && ArmsMesh->GetName().Contains(TEXT("FirstPersonArms")))
		{
			FName Socket = NAME_None;
			bViewReady = ProbeFindWeapon(*ArmsMesh, Socket) != nullptr;
			if (bViewReady)
			{
				break;
			}
		}
	}
	if (!bViewReady)
	{
		return;
	}

	if (!bStarted)
	{
		bStarted = true;
		Elapsed = 0.f;
		NextSample = 0.f;
		UE_LOG(LogSSHandIKProbe, Log, TEXT("Probe started on pawn %s (%s): %d hand-IK mesh component(s), view model ready."),
			*Pawn->GetName(), *Pawn->GetClass()->GetName(), Arms.Num());
	}

	Elapsed += DeltaTime;
	if (!bListed)
	{
		bListed = true;
		ListMeshes(*Pawn, Arms);
	}
	if (Elapsed >= NextSample)
	{
		NextSample += SampleInterval;
		Sample(Arms, Elapsed);
		if (++Samples >= SampleCount)
		{
			bDone = true; // one weapon per run: the producer runs the A88 and the A89 separately
			UE_LOG(LogSSHandIKProbe, Log, TEXT("Probe complete: %d samples."), Samples);
		}
	}
}

void USSHandIKProbeSubsystem::HideMatching(AActor& Pawn)
{
	const FString Want = CVarProbeHide.GetValueOnGameThread();
	if (Want.IsEmpty())
	{
		return;
	}
	TArray<AActor*> Actors;
	Actors.Add(&Pawn);
	for (int32 Index = 0; Index < Actors.Num() && Index < 64; ++Index)
	{
		for (UActorComponent* Component : Actors[Index]->GetComponents())
		{
			UMeshComponent* Mesh = Cast<UMeshComponent>(Component);
			if (Mesh && (Mesh->GetName().Contains(Want) || ProbeMeshOf(*Mesh).Contains(Want)) && Mesh->IsVisible())
			{
				Mesh->SetVisibility(false, /*bPropagateToChildren=*/ false);
				UE_LOG(LogSSHandIKProbe, Log, TEXT("HID %s (%s)"), *Mesh->GetName(), *ProbeMeshOf(*Mesh));
			}
		}
		TArray<AActor*> Attached;
		Actors[Index]->GetAttachedActors(Attached);
		for (AActor* Child : Attached)
		{
			Actors.AddUnique(Child);
		}
	}
}

void USSHandIKProbeSubsystem::ListMeshes(AActor& Pawn, const TArray<USSHandIKMeshComponent*>& Arms)
{
	TArray<AActor*> Actors;
	Actors.Add(&Pawn);
	for (int32 Index = 0; Index < Actors.Num() && Index < 64; ++Index)
	{
		AActor* Actor = Actors[Index];
		for (UActorComponent* Component : Actor->GetComponents())
		{
			const UMeshComponent* Mesh = Cast<UMeshComponent>(Component);
			if (!Mesh)
			{
				continue;
			}
			const FBoxSphereBounds Bounds = Mesh->Bounds;
			// Every slot, not just slot 0: an unwritten slot is what an untextured part looks like.
			FString Materials;
			for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
			{
				Materials += FString::Printf(TEXT("%s%s"), Slot ? TEXT(" | ") : TEXT(""), *ProbePathOf(Mesh->GetMaterial(Slot)));
			}
			UE_LOG(LogSSHandIKProbe, Log,
				TEXT("MESH actor=%s comp=%s class=%s visible=%d owner_no_see=%d only_owner_see=%d mesh=%s slots=%d mats=[%s] extent=(%.1f,%.1f,%.1f) attach=%s"),
				*Actor->GetName(), *Mesh->GetName(), *Mesh->GetClass()->GetName(),
				Mesh->IsVisible() ? 1 : 0, ProbeBoolProperty(Mesh, TEXT("bOwnerNoSee")) ? 1 : 0,
				ProbeBoolProperty(Mesh, TEXT("bOnlyOwnerSee")) ? 1 : 0, *ProbeMeshOf(*Mesh),
				Mesh->GetNumMaterials(), *Materials,
				Bounds.BoxExtent.X, Bounds.BoxExtent.Y, Bounds.BoxExtent.Z,
				Mesh->GetAttachParent() ? *FString::Printf(TEXT("%s:%s"), *Mesh->GetAttachParent()->GetOwner()->GetName(), *Mesh->GetAttachParent()->GetName()) : TEXT("none"));
		}
		TArray<AActor*> Attached;
		Actor->GetAttachedActors(Attached);
		for (AActor* Child : Attached)
		{
			Actors.AddUnique(Child);
		}
	}
	UE_LOG(LogSSHandIKProbe, Log, TEXT("MESH list complete: %d actor(s) walked, %d hand-IK component(s)."),
		Actors.Num(), Arms.Num());
}

void USSHandIKProbeSubsystem::Sample(const TArray<USSHandIKMeshComponent*>& Arms, float InElapsed)
{
	for (const USSHandIKMeshComponent* ArmsMesh : Arms)
	{
		if (!ArmsMesh)
		{
			continue;
		}
		const FName Upper = ProbeFirstBone(*ArmsMesh, ArmsMesh->UpperArmBones);
		const FName Lower = ProbeFirstBone(*ArmsMesh, ArmsMesh->LowerArmBones);
		const FName Hand = ProbeFirstBone(*ArmsMesh, ArmsMesh->HandBones);
		if (Upper.IsNone() || Lower.IsNone() || Hand.IsNone())
		{
			UE_LOG(LogSSHandIKProbe, Log, TEXT("t=%.2f %s: no left-arm chain on this mesh; skipped."),
				InElapsed, *ArmsMesh->GetName());
			continue;
		}
		FName Socket = NAME_None;
		const UStaticMeshComponent* Weapon = ProbeFindWeapon(*ArmsMesh, Socket);
		if (!Weapon)
		{
			UE_LOG(LogSSHandIKProbe, Log, TEXT("t=%.2f %s: no visible weapon with a grip socket; skipped."),
				InElapsed, *ArmsMesh->GetName());
			continue;
		}

		const FVector HandWorld = ArmsMesh->GetBoneLocation(Hand, EBoneSpaces::WorldSpace);
		const FVector GripWorld = Weapon->GetSocketLocation(Socket);
		// The solver works in this component's space; measure the numbers it decides on.
		const FTransform ToComponent = ArmsMesh->GetComponentTransform().Inverse();
		const FVector HandCS = ToComponent.TransformPosition(HandWorld);
		const FVector GripCS = ToComponent.TransformPosition(GripWorld);
		const FVector UpperCS = ArmsMesh->GetBoneLocation(Upper, EBoneSpaces::ComponentSpace);
		const FVector LowerCS = ArmsMesh->GetBoneLocation(Lower, EBoneSpaces::ComponentSpace);
		const double ArmLength = FVector::Distance(UpperCS, LowerCS) + FVector::Distance(LowerCS, HandCS);
		const double ShoulderToTarget = FVector::Distance(UpperCS, GripCS);
		const double Gate = ArmLength * ArmsMesh->MaxReachFactor;

		UE_LOG(LogSSHandIKProbe, Log,
			TEXT("t=%.2f arms=%s mesh=%s alpha=%.2f chain=%s>%s>%s hand_world=%s grip_world=%s hand_to_grip=%.2fcm "
				 "shoulder_to_grip=%.2fcm arm=%.2fcm gate=%.2fcm reach_limited=%d straight=%d weapon=%s socket=%s"),
			InElapsed, *ArmsMesh->GetName(), *ProbeMeshOf(*ArmsMesh), ArmsMesh->GetHandIKAlpha(),
			*Upper.ToString(), *Lower.ToString(), *Hand.ToString(),
			*ProbeVectorText(HandWorld), *ProbeVectorText(GripWorld), FVector::Distance(HandWorld, GripWorld),
			ShoulderToTarget, ArmLength, Gate,
			ShoulderToTarget > Gate ? 1 : 0,               // the component's own early-out
			ShoulderToTarget > ArmLength ? 1 : 0,          // the solver's full-extension clamp
			*Weapon->GetName(), *Socket.ToString());

		// Each hand's own frame, read off its finger bones and expressed in the WEAPON's frame. That frame is
		// what can be compared between two rigs: the bones' own axes cannot, which is exactly what the
		// cross-rig quaternion transfer assumed and what put the Palm ~90 deg out on the Fab arms.
		const FName Thumb = ProbeFingerBone(*ArmsMesh, Hand, TEXT("Thumb"));
		const FName Index = ProbeFingerBone(*ArmsMesh, Hand, TEXT("Index"));
		const FName Middle = ProbeFingerBone(*ArmsMesh, Hand, TEXT("Middle"));
		const FName MuzzleSocket = ProbeFirstSocket(*Weapon, { TEXT("Muzzle"), TEXT("SOCKET_Muzzle") });
		const FVector MuzzleCS = MuzzleSocket.IsNone()
			? FVector::ZeroVector
			: ToComponent.TransformPosition(Weapon->GetSocketLocation(MuzzleSocket));
		const FQuat SocketRotation = ToComponent.TransformRotation(Weapon->GetSocketQuaternion(Socket));
		const FQuat HandRotation = ArmsMesh->GetBoneQuaternion(Hand, EBoneSpaces::ComponentSpace);
		const FVector Barrel = MuzzleSocket.IsNone()
			? FVector::ZeroVector
			: (MuzzleCS - GripCS).GetSafeNormal();
		const FQuat WeaponRotation = ToComponent.TransformRotation(Weapon->GetComponentQuat());
		// The bore in the weapon's own mesh frame, so "which way is the barrel" can be read against the asset.
		const FVector BarrelLocal = WeaponRotation.Inverse().RotateVector(Barrel);
		const bool bArms = ArmsMesh->GetName().Contains(TEXT("FirstPersonArms"));

		const FProbeHandFrame Measured = ProbeHandFrame(*ArmsMesh, Hand, Thumb, Index);
		FString Grip = TEXT("no-finger-bones");
		if (Measured.bValid)
		{
			const FProbeHandFrame InWeapon = ProbeFrameInFrame(Measured, WeaponRotation.Inverse());
			const FQuat HandInWeapon = WeaponRotation.Inverse() * HandRotation;			if (bArms)
			{
				// The target is the SOCKET's own authored frame (Session 072). The hold is built from the weapon's
				// axes in adfrc_grip and baked into the socket's rotation, so the socket says what the hold is; the
				// arms' own finger-bone anatomy is measured against it. The body's grip is still recorded below,
				// for comparison, but it is no longer the reference.
				const FProbeHandFrame Target = ProbeSocketFrame(SocketRotation);
				const FProbeHandFrame TargetInWeapon = ProbeFrameInFrame(Target, WeaponRotation.Inverse());
				Grip = FString::Printf(
					TEXT("thumb=%s index=%s middle=%s thumb_vs_barrel=%.1fdeg socket_hold=%s %s handrot=%s "
						 "socketrot=%s hand_vs_socket=%.1fdeg realrot=%s weapon_in_cs=%s hand_in_weapon=%s "
						 "handinweaponrot=%s%s"),
					*Thumb.ToString(), *Index.ToString(), *Middle.ToString(), ProbeAngleDeg(Measured.Thumb, Barrel),
					*ProbeFrameText(TargetInWeapon), *ProbeErrorText(InWeapon, TargetInWeapon),
					*ProbeQuatText(HandRotation), *ProbeQuatText(SocketRotation),
					FMath::RadiansToDegrees(HandRotation.AngularDistance(SocketRotation)), *ProbeRotatorText(HandRotation),
					*ProbeQuatText(WeaponRotation), *ProbeQuatText(HandInWeapon), *ProbeRotatorText(HandInWeapon),
					GBodyFrameInWeapon.bValid
						? *FString::Printf(TEXT(" body_vs_socket=%s"), *ProbeErrorText(GBodyFrameInWeapon, TargetInWeapon))
						: TEXT(""));

				// The correction this pose needs, solved from the measured frame directly: the hand rotation that
				// carries the arms' own anatomy onto the socket's, as the config offset (socket rotation * offset).
				// Valid on a run with -SSHandIKProbeNoRotate, where the hand's rotation is still the clip's.
				if (Target.bValid)
				{
					const FQuat Align = ProbeAlign(Measured, Target);
					// A * B applies B first in UE, so the hand's own rotation goes in second: Align(HandRotation(v)).
					const FQuat Required = Align * HandRotation;
					const FQuat Offset = SocketRotation.Inverse() * Required;
					const FQuat HandAfter = SocketRotation * Offset;   // exactly what the component would apply
					const FProbeHandFrame After = ProbeFrameInFrame(ProbeFrameInFrame(Measured, Align), WeaponRotation.Inverse());
					UE_LOG(LogSSHandIKProbe, Log,
						TEXT("OFFSET t=%.2f arms=%s mesh=%s align=%s (%.1fdeg) residual=%s offset_rotator=%s "
							 "HandRotationOffset=(Pitch=%.3f,Yaw=%.3f,Roll=%.3f)"),
						InElapsed, *ArmsMesh->GetName(), *ProbeMeshOf(*ArmsMesh), *ProbeRotatorText(Align),
						FMath::RadiansToDegrees(Align.AngularDistance(FQuat::Identity)),
						*ProbeErrorText(After, TargetInWeapon), *ProbeRotatorText(Offset),
						Offset.Rotator().Pitch, Offset.Rotator().Yaw, Offset.Rotator().Roll);
					UE_LOG(LogSSHandIKProbe, Log,
						TEXT("OFFSETCHECK t=%.2f hand_after=%s realrot=%s socket_hold=%s (the component applies "
							 "socketrot * offset)"),
						InElapsed, *ProbeQuatText(HandAfter), *ProbeRotatorText(HandAfter),
						*ProbeFrameText(TargetInWeapon));
				}
			}
			else
			{
				// The reference rig: record where its own grip puts these axes on this weapon, in the weapon's frame.
				GBodyFrameInWeapon = InWeapon;
				GHaveBodyFrame = true;
				Grip = FString::Printf(
					TEXT("thumb=%s index=%s middle=%s thumb_vs_barrel=%.1fdeg body_in_weapon=%s %s handrot=%s "
						"socketrot=%s hand_vs_socket=%.1fdeg hand_in_weapon=%s"),
					*Thumb.ToString(), *Index.ToString(), *Middle.ToString(), ProbeAngleDeg(Measured.Thumb, Barrel),
					*ProbeFrameText(InWeapon), *ProbeErrorText(InWeapon, GBodyFrameInWeapon),
					*ProbeQuatText(HandRotation), *ProbeQuatText(SocketRotation),
					FMath::RadiansToDegrees(HandRotation.AngularDistance(SocketRotation)), *ProbeQuatText(HandInWeapon));
			}
		}
		UE_LOG(LogSSHandIKProbe, Log,
			TEXT("GRIP t=%.2f arms=%s mesh=%s muzzle_socket=%s barrel=%s barrel_local=%s socket=%s %s"),
			InElapsed, *ArmsMesh->GetName(), *ProbeMeshOf(*ArmsMesh), *MuzzleSocket.ToString(),
			*ProbeVectorText(Barrel), *ProbeVectorText(BarrelLocal), *Socket.ToString(), *Grip);
	}
}
