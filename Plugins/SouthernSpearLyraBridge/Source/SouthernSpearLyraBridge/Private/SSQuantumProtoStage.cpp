// Copyright Southern Spear. All Rights Reserved.

#include "SSQuantumProtoStage.h"

#include "Camera/CameraComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/PoseableMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/TextureCube.h"
#include "Engine/World.h"
#include "Materials/Material.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "ReferenceSkeleton.h"
#include "UObject/ConstructorHelpers.h"

namespace QuantumProto
{
	// The pose source: the mannequin mesh the current soldier's parts leader-pose to. Note the
	// mesh is SKM_Manny, not SK_Mannequin: in this project SK_Mannequin is the Skeleton, and
	// the two share a name, so a load of "/…/SK_Mannequin" returns a USkeleton and every
	// SkeletalMesh cast silently fails.
	const TCHAR* PoseSourceMesh = TEXT("/Game/Characters/Heroes/Mannequin/Meshes/SKM_Manny.SKM_Manny");

	// The shipping G3 soldier, exactly as setup_soldiers.py assembles it.
	const TCHAR* G3Uniform = TEXT("/SSExp_ObjectiveAssault/Characters/ADF/SK_ADF_Uniform_G3.SK_ADF_Uniform_G3");
	const TCHAR* G3Vest = TEXT("/SSExp_ObjectiveAssault/Characters/ADF/SK_ADF_Vest_TBAS.SK_ADF_Vest_TBAS");
	const TCHAR* G3Helmet = TEXT("/SSExp_ObjectiveAssault/Characters/ADF/SK_ADF_Helmet_OpsCore.SK_ADF_Helmet_OpsCore");
	const TCHAR* G3Head = TEXT("/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Head.SK_Head");

	// The Quantum modules, duplicated onto our side of the project by setup_quantum_proto.py
	// so the camo materials belong to us. The ARMS module is what carries the hands - the
	// shirt is rolled-up sleeves and ends at the forearm - and the hands were the main
	// reason to consider Quantum at all, so a shot without SKM_Arms proves nothing.
	const TCHAR* QuantumShirt = TEXT("/SSExp_ObjectiveAssault/Characters/QuantumProto/SKM_Shirt_RolledUp_Blue.SKM_Shirt_RolledUp_Blue");
	const TCHAR* QuantumJeans = TEXT("/SSExp_ObjectiveAssault/Characters/QuantumProto/SKM_Jeans.SKM_Jeans");
	const TCHAR* QuantumHead = TEXT("/SSExp_ObjectiveAssault/Characters/QuantumProto/SKM_Head.SKM_Head");
	const TCHAR* QuantumArms = TEXT("/SSExp_ObjectiveAssault/Characters/QuantumProto/SKM_Arms.SKM_Arms");

	// The full Quantum body, used only to measure the torso against the plate carrier.
	const TCHAR* QuantumBody = TEXT("/Game/QuantumCharacter/Mesh/SKM_QuantumCharacter.SKM_QuantumCharacter");

	const FVector G3Offset(-45.0, 0.0, 0.0);
	const FVector QuantumOffset(45.0, 0.0, 0.0);
}

static USkeletalMesh* SSLoadMesh(const FString& ObjectPath)
{
	USkeletalMesh* Mesh = LoadObject<USkeletalMesh>(nullptr, *ObjectPath);
	if (!Mesh)
	{
		UE_LOG(LogTemp, Warning, TEXT("SSQuantumProto: could not load %s"), *ObjectPath);
	}
	return Mesh;
}

/**
 * UPoseableMeshComponent derives from USkinnedMeshComponent, not from
 * USkeletalMeshComponent, so GetSkeletalMeshAsset() is not on it in 5.8.
 */
static USkeletalMesh* SSMeshOf(USkinnedMeshComponent* Comp)
{
	return Comp ? Cast<USkeletalMesh>(Comp->GetSkinnedAsset()) : nullptr;
}

ASSQuantumProtoStage::ASSQuantumProtoStage()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PostPhysics;

	StageRoot = CreateDefaultSubobject<USceneComponent>(TEXT("StageRoot"));
	SetRootComponent(StageRoot);

	Platform = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Platform"));
	Platform->SetupAttachment(StageRoot);
	Platform->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	// A 100 cm engine cube scaled into a low plinth: both bodies need something to stand on
	// or they read as floating and the eye compares the wrong thing.
	Platform->SetRelativeScale3D(FVector(4.0, 4.0, 0.1));
	Platform->SetRelativeLocation(FVector(0.0, 0.0, -5.0));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (Cube.Succeeded())
	{
		Platform->SetStaticMesh(Cube.Object);
	}
	// WorldGridMaterial reads as a wet mirror under raking light and ate the lower half of the
	// first capture. BasicShapeMaterial is the engine's matte grey - the comparison is about
	// silhouettes and cloth, not about reflections.
	static ConstructorHelpers::FObjectFinder<UMaterial> Matte(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	if (Matte.Succeeded())
	{
		Platform->SetMaterial(0, Matte.Object);
	}

	// A floor under the plinth: without it the unlit surround reads as a black void and the
	// eye has no horizon to judge the figures against.
	Floor = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Floor"));
	Floor->SetupAttachment(StageRoot);
	Floor->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Floor->SetRelativeScale3D(FVector(40.0, 40.0, 1.0));
	Floor->SetRelativeLocation(FVector(0.0, 0.0, -11.0));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Plane(TEXT("/Engine/BasicShapes/Plane.Plane"));
	if (Plane.Succeeded())
	{
		Floor->SetStaticMesh(Plane.Object);
	}
	if (Matte.Succeeded())
	{
		Floor->SetMaterial(0, Matte.Object);
	}

	Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
	Camera->SetupAttachment(StageRoot);
	// Far enough back that a standing figure fits in frame head to boot: the first capture
	// cut both bodies at the waist and hid exactly the comparison the stage exists to make.
	Camera->SetRelativeLocation(FVector(0.0, -560.0, 100.0));
	// Yaw 90 faces +Y, where both bodies are. A slight downward pitch keeps the eye near
	// chest height, which is where camouflage and carrier fit read.
	Camera->SetRelativeRotation(FRotator(-6.0, 90.0, 0.0));
	Camera->bConstrainAspectRatio = false;

	Sun = CreateDefaultSubobject<UDirectionalLightComponent>(TEXT("Sun"));
	Sun->SetupAttachment(StageRoot);
	// Raking light: flat frontal light hides the silhouette differences this shot exists to show.
	Sun->SetRelativeRotation(FRotator(-38.0, -35.0, 0.0));
	Sun->SetIntensity(4.0f);
	Sun->SetLightColor(FLinearColor(1.0f, 0.96f, 0.90f));

	Fill = CreateDefaultSubobject<USkyLightComponent>(TEXT("Fill"));
	Fill->SetupAttachment(StageRoot);
	Fill->SetIntensity(2.5f);
	Fill->SourceType = ESkyLightSourceType::SLS_SpecifiedCubemap;
	static ConstructorHelpers::FObjectFinder<UTextureCube> DefaultCube(
		TEXT("/Engine/EngineResources/DefaultTextureCube.DefaultTextureCube"));
	if (DefaultCube.Succeeded())
	{
		Fill->Cubemap = DefaultCube.Object;
	}
}

void ASSQuantumProtoStage::BeginPlay()
{
	Super::BeginPlay();

	PoseSource = NewObject<UPoseableMeshComponent>(this);
	PoseSource->SetupAttachment(StageRoot);
	if (USkeletalMesh* Mesh = SSLoadMesh(QuantumProto::PoseSourceMesh))
	{
		// SetSkinnedAsset, not SetSkeletalMesh: the latter is deprecated on
		// USkinnedMeshComponent in 5.8 and warns that it will stop compiling.
		PoseSource->SetSkinnedAsset(Mesh);
	}
	PoseSource->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	PoseSource->SetGenerateOverlapEvents(false);
	// Hidden: the G3 soldier parts stand in for it. Left visible it would poke through the
	// uniform and the shot would be a coin toss.
	PoseSource->SetVisibility(false);
	PoseSource->SetComponentTickEnabled(false);
	PoseSource->RegisterComponent();

	if (USkeletalMesh* SourceMesh = SSMeshOf(PoseSource))
	{
		const FReferenceSkeleton& Ref = SourceMesh->GetRefSkeleton();
		const int32 Num = Ref.GetNum();
		SourceNames.SetNum(Num);
		SourceParent.SetNum(Num);
		SourceByName.Reserve(Num);
		for (int32 Index = 0; Index < Num; ++Index)
		{
			SourceNames[Index] = Ref.GetBoneName(Index);
			SourceParent[Index] = Ref.GetParentIndex(Index);
			SourceByName.Add(SourceNames[Index], Index);
		}
	}

	AddG3Part(QuantumProto::G3Uniform, QuantumProto::G3Offset);
	AddG3Part(QuantumProto::G3Vest, QuantumProto::G3Offset);
	AddG3Part(QuantumProto::G3Helmet, QuantumProto::G3Offset);
	AddG3Part(QuantumProto::G3Head, QuantumProto::G3Offset);

	AddQuantumPart(QuantumProto::QuantumShirt, QuantumProto::QuantumOffset);
	AddQuantumPart(QuantumProto::QuantumJeans, QuantumProto::QuantumOffset);
	AddQuantumPart(QuantumProto::QuantumArms, QuantumProto::QuantumOffset);
	AddQuantumPart(QuantumProto::QuantumHead, QuantumProto::QuantumOffset);

	// The same ADFRC kit as the G3 side, on the Quantum body. These are Manny-authored meshes,
	// so they leader-pose to the Manny pose source exactly as they do on the shipping soldier
	// (ADR-036's mechanism); both bodies are driven from the SAME source pose, so the vest and
	// helmet follow the Quantum body's stance without any new retarget work. The fit numbers
	// (within 1.6 cm on every axis) say they should sit cleanly - this is the eyeball check.
	AddG3Part(QuantumProto::G3Vest, QuantumProto::QuantumOffset);
	AddG3Part(QuantumProto::G3Helmet, QuantumProto::QuantumOffset);

	if (bTakeView)
	{
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
		{
			PC->SetViewTargetWithBlend(this, 0.25f, VTBlend_Cubic);
		}
	}

	LogFitReport();
}

USkeletalMeshComponent* ASSQuantumProtoStage::AddG3Part(const FString& ObjectPath, const FVector& Offset)
{
	USkeletalMesh* Mesh = SSLoadMesh(ObjectPath);
	if (!Mesh)
	{
		return nullptr;
	}
	USkeletalMeshComponent* Part = NewObject<USkeletalMeshComponent>(this);
	Part->SetupAttachment(StageRoot);
	Part->SetSkeletalMesh(Mesh);
	Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Part->SetGenerateOverlapEvents(false);
	Part->SetRelativeLocation(Offset);
	Part->RegisterComponent();
	// Exactly what ASSCharacterPartActor::BuildSet does, so one half of the shot is the
	// soldier that ships rather than a reconstruction of it.
	Part->SetLeaderPoseComponent(PoseSource);
	G3Parts.Add(Part);
	return Part;
}

UPoseableMeshComponent* ASSQuantumProtoStage::AddQuantumPart(const FString& ObjectPath, const FVector& Offset)
{
	USkeletalMesh* Mesh = SSLoadMesh(ObjectPath);
	if (!Mesh)
	{
		return nullptr;
	}
	UPoseableMeshComponent* Part = NewObject<UPoseableMeshComponent>(this);
	Part->SetupAttachment(StageRoot);
	Part->SetSkinnedAsset(Mesh);
	Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Part->SetGenerateOverlapEvents(false);
	Part->SetRelativeLocation(Offset);
	Part->SetComponentTickEnabled(false);
	Part->RegisterComponent();
	QuantumParts.Add(Part);
	return Part;
}

int32 ASSQuantumProtoStage::BuildBoneMap(const FReferenceSkeleton& Source, const FReferenceSkeleton& Ref,
	const TMap<FName, int32>& SourceByName, float Curl, float CurlDegrees, FSSQuantumBoneMap& Out)
{
	const TArray<FTransform>& SourceRefPose = Source.GetRefBonePose();
	const TArray<FTransform>& TargetRefPose = Ref.GetRefBonePose();
	const int32 Num = Ref.GetNum();

	// Rest-pose world positions, which is where the disagreement between these two skeletons
	// actually shows. A shared bone NAME is not the same as a shared joint: Manny and Quantum
	// both name 159 bones, but they stand in different rest poses, so the same name can sit
	// metres apart in space. A local-offset comparison misses this completely - two finger
	// bones can agree on length and orientation and still compound into a hand 2.9 m from where
	// it belongs, because every joint above them drifted.
	//
	// A hand-authored retarget pose is the real fix, and that is an editor operation. This
	// tolerance is the cheap automatic stand-in: keep a name match only if the joint is in
	// roughly the same place in space in both rest poses.
	TArray<FTransform> SourceCS;
	TArray<FTransform> TargetCS;
	ReferenceComponentSpace(Source, SourceCS);
	ReferenceComponentSpace(Ref, TargetCS);

	float SourceHeight = 1.0f;
	for (const FTransform& Transform : SourceCS)
	{
		SourceHeight = FMath::Max(SourceHeight, FMath::Abs(Transform.GetTranslation().Z));
	}
	const float WorldToleranceCm = SourceHeight * 0.06f;  // 6% of standing height
	constexpr float AngleToleranceDeg = 30.0f;

	Out.TargetNames.SetNum(Num);
	Out.SourceForTarget.Init(INDEX_NONE, Num);
	Out.TargetParent.Init(INDEX_NONE, Num);
	Out.DigitMask.Init(0, Num);
	Out.DigitCurl.SetNum(Num);
	Out.RejectedBones.Reset();
	Out.RejectedOffsetDeltaCm.Reset();
	Out.RejectedAngleDeltaDeg.Reset();
	Out.TwistExcluded = 0;

	int32 Mapped = 0;
	int32 Digits = 0;
	int32& TwistExcluded = Out.TwistExcluded;
	for (int32 Index = 0; Index < Num; ++Index)
	{
		Out.TargetNames[Index] = Ref.GetBoneName(Index);
		Out.TargetParent[Index] = Ref.GetParentIndex(Index);
		const FString Name = Out.TargetNames[Index].ToString();

		// Twist and IK helper bones are not articulation, and UE's own IK Retargeter leaves them
		// out of the chain map for the same reason: they carry a deformation weighting rather
		// than a joint, and they are where a small rest-orientation difference between two rigs
		// compounds into centimetres at the far end of an arm. Mapped, the Quantum arm inherits
		// Manny's 2.18-degree twist error; unmapped, it keeps its own.
		const bool bTwistOrHelper = Name.Contains(TEXT("twist")) || Name.Contains(TEXT("tricep"))
			|| Name.Contains(TEXT("bicep")) || Name.StartsWith(TEXT("ik_"));
		if (bTwistOrHelper)
		{
			++TwistExcluded;
		}
		else if (const int32* Found = SourceByName.Find(Out.TargetNames[Index]))
		{
			const int32 SourceIndex = *Found;
			const float WorldDelta = static_cast<float>(
				(SourceCS[SourceIndex].GetTranslation() - TargetCS[Index].GetTranslation()).Size());
			const float AngleDelta = FMath::RadiansToDegrees(
				SourceRefPose[SourceIndex].GetRotation().AngularDistance(TargetRefPose[Index].GetRotation()));
			if (WorldDelta <= WorldToleranceCm && AngleDelta <= AngleToleranceDeg)
			{
				Out.SourceForTarget[Index] = SourceIndex;
				++Mapped;
			}
			else
			{
				Out.RejectedBones.Add(Out.TargetNames[Index]);
				Out.RejectedOffsetDeltaCm.Add(WorldDelta);
				Out.RejectedAngleDeltaDeg.Add(AngleDelta);
			}
		}

		bool bIsHandItself = false;
		if (IsDigitBone(Ref, Index, bIsHandItself))
		{
			Out.DigitMask[Index] = 1;
			Out.DigitCurl[Index] = CurledDigitTransform(Ref, Index, Curl, CurlDegrees);
			++Digits;
		}
	}
	return Mapped;
}

bool ASSQuantumProtoStage::IsDigitBone(const FReferenceSkeleton& Ref, int32 BoneIndex, bool& bOutIsHandItself)
{
	bOutIsHandItself = false;
	if (Ref.GetBoneName(BoneIndex).ToString().StartsWith(TEXT("hand_")))
	{
		bOutIsHandItself = true;
		return false;
	}
	// Walk up until we either hit a hand bone (a finger) or leave the subtree (a toe, a face
	// bone, a vendor extra - all of which keep the reference pose).
	for (int32 Parent = Ref.GetParentIndex(BoneIndex); Parent != INDEX_NONE; Parent = Ref.GetParentIndex(Parent))
	{
		if (Ref.GetBoneName(Parent).ToString().StartsWith(TEXT("hand_")))
		{
			return true;
		}
	}
	return false;
}

FTransform ASSQuantumProtoStage::CurledDigitTransform(const FReferenceSkeleton& Ref, int32 BoneIndex,
	float Curl, float CurlDegrees)
{
	const TArray<FTransform>& RefPose = Ref.GetRefBonePose();
	FTransform Result = RefPose[BoneIndex];
	if (Curl <= 0.0f)
	{
		return Result;
	}

	// The flexion axis is the local axis least aligned with the bone's own direction. Deriving
	// it from the hierarchy cannot be wrong the way a naming-convention guess can: get that
	// wrong and the hand curls sideways.
	FVector Head = RefPose[BoneIndex].GetLocation();
	FVector Direction = FVector::ZeroVector;
	const int32 Num = Ref.GetNum();
	for (int32 Child = 0; Child < Num; ++Child)
	{
		if (Ref.GetParentIndex(Child) == BoneIndex)
		{
			Direction += RefPose[BoneIndex].GetRotation().Inverse().RotateVector(RefPose[Child].GetLocation() - Head);
		}
	}
	if (Direction.IsNearlyZero())
	{
		// Leaf bone: fall back to the bone's own local +X, the UE convention.
		Direction = FVector(1.0, 0.0, 0.0);
	}
	Direction.Normalize();

	int32 Axis = 0;
	float BestAlignment = TNumericLimits<float>::Max();
	for (int32 Candidate = 0; Candidate < 3; ++Candidate)
	{
		const float Alignment = FMath::Abs(Direction[Candidate]);
		if (Alignment < BestAlignment)
		{
			BestAlignment = Alignment;
			Axis = Candidate;
		}
	}

	// The thumb opposes the other fingers; curling it to the same angle puts it through the palm.
	const bool bIsThumb = Ref.GetBoneName(BoneIndex).ToString().StartsWith(TEXT("thumb"));
	const float Scale = bIsThumb ? 0.6f : 1.0f;
	const FQuat CurlRotation(FVector(Axis == 0, Axis == 1, Axis == 2),
		FMath::DegreesToRadians(CurlDegrees) * Curl * Scale);
	// Post-multiply: the curl is applied in the bone's own local frame. The chain composes
	// through the hierarchy on the way to component space, so the joints accumulate.
	Result.SetRotation(Result.GetRotation() * CurlRotation);
	return Result;
}

void ASSQuantumProtoStage::ReferenceComponentSpace(const FReferenceSkeleton& Ref, TArray<FTransform>& Out)
{
	// Unreal composes child component space as  Local * ParentComponentSpace  - see
	// UPoseableMeshComponent::FillComponentSpaceTransforms:
	//   "final component-space transform is relative transform * component-space transform of parent"
	//   FTransform::Multiply(Dest, Local, ParentCS);
	// An earlier version of this function used ParentCS * Local, the other way round. Because
	// every downstream number was built from it, that inversion produced an impossible 144 cm
	// shoulder-to-hand and a rest-drift figure of 0.0001 cm that could not have been true.
	const TArray<FTransform>& RefPose = Ref.GetRefBonePose();
	const int32 Num = Ref.GetNum();
	Out.SetNumUninitialized(Num);
	for (int32 Index = 0; Index < Num; ++Index)
	{
		const int32 Parent = Ref.GetParentIndex(Index);
		Out[Index] = (Parent == INDEX_NONE) ? RefPose[Index] : RefPose[Index] * Out[Parent];
	}
}

void ASSQuantumProtoStage::EvaluateRetarget(const FSSQuantumBoneMap& Map, const TArray<FTransform>& SourceLocalPose,
	const TArray<FTransform>& TargetRefPose, TArray<FTransform>& Out)
{
	// SourceLocalPose is indexed by SOURCE bone index and holds each source bone's LOCAL
	// (parent-relative) transform for this frame. Local rotations compose identically in both
	// rigs, so the source bone's local rotation can be applied straight onto the target's own
	// local transform.
	//
	// An earlier version subtracted the source parent again, on the reasoning that a retarget
	// needs "motion relative to the source's parent". It does not: a local transform IS the
	// motion relative to the parent, and the extra subtraction treated a rest pose as if it were
	// a world transform, which put the hand 2.9 m from the body. Invariant A is what caught it.
	const int32 Num = Map.TargetNames.Num();
	Out.SetNumUninitialized(Num);
	for (int32 Index = 0; Index < Num; ++Index)
	{
		const int32 TargetParent = Map.TargetParent[Index];
		const int32 SourceIndex = Map.SourceForTarget[Index];

		if (SourceIndex == INDEX_NONE)
		{
			// No source bone: the vendor reference pose, with a curl on the digits.
			const FTransform Local = Map.DigitMask[Index] ? Map.DigitCurl[Index] : TargetRefPose[Index];
			Out[Index] = (TargetParent == INDEX_NONE) ? FTransform::Identity : Local * Out[TargetParent];
			continue;
		}

		if (TargetParent == INDEX_NONE)
		{
			// Root: identity, not the source root's transform. The source root carries the
			// character's world movement and copying it would apply that movement twice.
			Out[Index] = FTransform::Identity;
			continue;
		}

		// The source's local ROTATION on the target's own translation. Copying the translation
		// too is the classic retarget bug: it silently replaces the target's bone lengths with
		// the source's, so Quantum's forearm becomes Manny's forearm length. Invariant C in
		// ProveRetarget is the check for exactly that.
		//
		// Order is Local * ParentComponentSpace, matching FillComponentSpaceTransforms.
		Out[Index] = FTransform(
			SourceLocalPose[SourceIndex].GetRotation(),
			TargetRefPose[Index].GetTranslation(),
			TargetRefPose[Index].GetScale3D()) * Out[TargetParent];
	}
}

void ASSQuantumProtoStage::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// Hold the view target. Lyra's pawn takes the view back some frames after BeginPlay (the
	// first capture came out as the spawning player's own first-person view, glove in the
	// middle of the shot), so a one-shot SetViewTargetWithBlend in BeginPlay is not enough.
	// Retaking it every tick until it sticks is cheap and only runs on this capture stage.
	if (bTakeView)
	{
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
		{
			if (PC->GetViewTarget() != this)
			{
				PC->SetViewTargetWithBlend(this, 0.0f);
			}
		}
	}

	if (!PoseSource)
	{
		return;
	}

	PoseSource->RefreshBoneTransforms();
	const TArray<FTransform>& SourceCS = PoseSource->GetComponentSpaceTransforms();
	const int32 NumSource = SourceNames.Num();
	if (SourceCS.Num() < NumSource)
	{
		return;
	}
	// Strip the source's world motion down to per-bone deltas about its own parent. The
	// engine's own definition of a bone's local transform is child * parent^-1, so this is
	// the same arithmetic FCompactPose does.
	SourceLocal.SetNumUninitialized(NumSource);
	for (int32 Index = 0; Index < NumSource; ++Index)
	{
		const int32 Parent = SourceParent[Index];
		SourceLocal[Index] = (Parent == INDEX_NONE)
			? SourceCS[Index]
			: SourceCS[Index] * SourceCS[Parent].Inverse();
	}

	for (UPoseableMeshComponent* Part : QuantumParts)
	{
		RetargetBody(Part);
	}
}

void ASSQuantumProtoStage::RetargetBody(UPoseableMeshComponent* Part)
{
	USkeletalMesh* Mesh = SSMeshOf(Part);
	if (!Mesh)
	{
		return;
	}
	// All Quantum modules share one skeleton, so the map built for the first is the map for
	// all; rebuilding per part is the same work three times.
	if (BoneMap.TargetNames.Num() != Mesh->GetRefSkeleton().GetNum())
	{
		if (USkeletalMesh* SourceMesh = SSLoadMesh(QuantumProto::PoseSourceMesh))
		{
			BuildBoneMap(SourceMesh->GetRefSkeleton(), Mesh->GetRefSkeleton(), SourceByName,
				FingerCurl, CurlDegreesPerJoint, BoneMap);
		}
	}

	// 5.8 dropped the LocalSpace value from EBoneSpaces, so SetBoneTransformByName now always
	// expects a component-space transform and localises it against the parent it finds already
	// written. Bones come parent-before-child in a reference skeleton, so one pass is enough.
	EvaluateRetarget(BoneMap, SourceLocal, Mesh->GetRefSkeleton().GetRefBonePose(), Scratch);

	const int32 Num = Scratch.Num();
	for (int32 Index = 0; Index < Num; ++Index)
	{
		Part->SetBoneTransformByName(BoneMap.TargetNames[Index], Scratch[Index], EBoneSpaces::ComponentSpace);
	}
	Part->RefreshBoneTransforms();
}

FString ASSQuantumProtoStage::ProveRetarget(const FString& PoseSourceMeshPath, const FString& TargetMeshPath,
	float Curl, float CurlDegrees)
{
	USkeletalMesh* SourceMesh = SSLoadMesh(PoseSourceMeshPath);
	USkeletalMesh* TargetMesh = SSLoadMesh(TargetMeshPath);
	if (!SourceMesh || !TargetMesh)
	{
		return TEXT("{\"ok\": false, \"error\": \"mesh did not load\"}");
	}

	const FReferenceSkeleton& SourceRef = SourceMesh->GetRefSkeleton();
	const FReferenceSkeleton& TargetRef = TargetMesh->GetRefSkeleton();
	const TArray<FTransform>& SourceRefPose = SourceRef.GetRefBonePose();
	const TArray<FTransform>& TargetRefPose = TargetRef.GetRefBonePose();

	TMap<FName, int32> SourceByName;
	for (int32 Index = 0; Index < SourceRef.GetNum(); ++Index)
	{
		SourceByName.Add(SourceRef.GetBoneName(Index), Index);
	}

	FSSQuantumBoneMap Map;
	const int32 Mapped = BuildBoneMap(SourceRef, TargetRef, SourceByName, Curl, CurlDegrees, Map);
	int32 Digits = 0;
	for (uint8 Flag : Map.DigitMask)
	{
		Digits += Flag ? 1 : 0;
	}

	// The source "pose" is its own reference pose: a resting skeleton. A reference bone pose is
	// already in local (parent-relative) space, which is exactly what EvaluateRetarget wants.
	TArray<FTransform> SourceLocalPose = SourceRefPose;

	// --- A: rest is a fixed point ---------------------------------------------
	TArray<FTransform> TargetRefCS;
	ReferenceComponentSpace(TargetRef, TargetRefCS);
	TArray<FTransform> AtRest;
	EvaluateRetarget(Map, SourceLocalPose, TargetRefPose, AtRest);

	double WorstRestDrift = 0.0;
	FString WorstRestBone;
	// Tracked separately from the twist and IK helper bones. Those are not anatomy and are not
	// visible, and they are where the two rigs' 2.18-degree rest-orientation difference lands
	// after compounding down a chain. Folding them into the pass criterion would either fail a
	// retarget that looks right or force the tolerance up until it proves nothing.
	double WorstAnatomicalDrift = 0.0;
	FString WorstAnatomicalBone;
	for (int32 Index = 0; Index < Map.TargetNames.Num(); ++Index)
	{
		if (Map.SourceForTarget[Index] == INDEX_NONE || Map.TargetParent[Index] == INDEX_NONE)
		{
			continue;  // the root is deliberately identity
		}
		const double Drift = (AtRest[Index].GetLocation() - TargetRefCS[Index].GetLocation()).Size();
		const double Angle = FMath::RadiansToDegrees(
			AtRest[Index].GetRotation().AngularDistance(TargetRefCS[Index].GetRotation()));
		const double Score = FMath::Max(Drift, Angle * 0.1);
		const FString Name = Map.TargetNames[Index].ToString();
		const bool bHelper = Name.Contains(TEXT("tricep")) || Name.Contains(TEXT("twist"))
			|| Name.StartsWith(TEXT("ik_")) || Name.Contains(TEXT("ik_"));
		if (Score > WorstRestDrift)
		{
			WorstRestDrift = Score;
			WorstRestBone = Name;
		}
		if (!bHelper && Score > WorstAnatomicalDrift)
		{
			WorstAnatomicalDrift = Score;
			WorstAnatomicalBone = Name;
		}
	}

	// --- B and C: move one source bone ----------------------------------------
	// upperarm_l is the probe: it has a parent, a child and a counterpart on both skeletons.
	const int32 ProbeSource = SourceRef.FindBoneIndex(FName(TEXT("upperarm_l")));
	const int32 ProbeTarget = TargetRef.FindBoneIndex(FName(TEXT("upperarm_l")));
	const float ProbeDegrees = 30.0f;

	bool bHasProbe = ProbeSource != INDEX_NONE && ProbeTarget != INDEX_NONE;
	double PropagatedDegrees = 0.0;
	double LengthBefore = 0.0;
	double LengthAfter = 0.0;
	int32 ChildProbe = INDEX_NONE;
	bool bChildFollowed = false;
	double SelfArmToHandCm = 0.0;
	double SourceArmToHandCm = 0.0;
	double TargetLocalLowerarmCm = 0.0;

	if (bHasProbe)
	{
		TArray<FTransform> Moved = SourceLocalPose;
		const FQuat Delta(FVector(0.0, 0.0, 1.0), FMath::DegreesToRadians(ProbeDegrees));
		Moved[ProbeSource].SetRotation(Moved[ProbeSource].GetRotation() * Delta);

		TArray<FTransform> After;
		EvaluateRetarget(Map, Moved, TargetRefPose, After);

		// The rotation the target bone gained, measured about its own parent.
		const FQuat BeforeLocal = AtRest[ProbeTarget].GetRotation()
			* AtRest[Map.TargetParent[ProbeTarget]].GetRotation().Inverse();
		const FQuat AfterLocal = After[ProbeTarget].GetRotation()
			* After[Map.TargetParent[ProbeTarget]].GetRotation().Inverse();
		PropagatedDegrees = FMath::RadiansToDegrees(BeforeLocal.AngularDistance(AfterLocal));

		// The child must follow: a retarget that moves the shoulder but leaves the elbow
		// behind is the classic failure.
		ChildProbe = TargetRef.FindBoneIndex(FName(TEXT("hand_l")));
		if (ChildProbe != INDEX_NONE)
		{
			// C is measured as a BONE LENGTH - bone to its immediate parent - and not as an
			// anatomical span. An earlier version measured upperarm-to-hand, which is 144 cm in
			// this rig's own reference pose and legitimately changes when the arm rotates,
			// because hand_l carries a large offset along the arm. That measured the rig, not
			// the retarget. A bone's own length is the quantity a retarget must not disturb.
			// Tolerance is relative: a 129 cm span measured in float cannot hold 0.01 cm.
			const int32 ChildParent = Map.TargetParent[ChildProbe];
			LengthBefore = (AtRest[ChildProbe].GetLocation()
				- AtRest[ChildParent].GetLocation()).Size();
			LengthAfter = (After[ChildProbe].GetLocation()
				- After[ChildParent].GetLocation()).Size();

			const FVector AtRestOffset = AtRest[ChildProbe].GetLocation() - AtRest[ProbeTarget].GetLocation();
			const FVector AfterOffset = After[ChildProbe].GetLocation() - After[ProbeTarget].GetLocation();
			// "Followed" means the child actually swung, not merely that it kept its length.
			bChildFollowed = AfterOffset.Equals(AtRestOffset, 0.01f) == false;

			TArray<FTransform> SelfCS;
			ReferenceComponentSpace(TargetRef, SelfCS);
			SelfArmToHandCm = (SelfCS[ChildProbe].GetLocation() - SelfCS[ProbeTarget].GetLocation()).Size();
			TArray<FTransform> SourceSelfCS;
			ReferenceComponentSpace(SourceRef, SourceSelfCS);
			SourceArmToHandCm = (SourceSelfCS[SourceRef.FindBoneIndex(FName(TEXT("hand_l")))].GetLocation()
				- SourceSelfCS[SourceRef.FindBoneIndex(FName(TEXT("upperarm_l")))].GetLocation()).Size();
			TargetLocalLowerarmCm = TargetRefPose[TargetRef.FindBoneIndex(FName(TEXT("lowerarm_l")))].GetTranslation().Size();
		}
	}

	// A is allowed 2% of standing height on anatomical bones. Anything larger is a mapping fault
	// rather than accumulated float.
	constexpr float RestToleranceFraction = 0.02f;
	float SourceHeight = 1.0f;
	for (const FTransform& Transform : TargetRefCS)
	{
		SourceHeight = FMath::Max(SourceHeight, FMath::Abs(Transform.GetTranslation().Z));
	}
	const bool bRestOk = WorstAnatomicalDrift <= SourceHeight * RestToleranceFraction;

	// Guard the guard. A/B/C all compare the retarget against reference poses composed by the
	// same function that produced them, so none of them can detect that the COMPOSITION ITSELF
	// is wrong - which is exactly what happened: an inverted multiply order satisfied all three
	// while reporting an impossible 144 cm shoulder-to-hand. So check the composed reference
	// pose against absolute human proportions, which no ordering convention can fake.
	// A forearm is 20-35 cm long and a head sits 55-80 cm above the pelvis. The band is wide on
	// purpose: its job is to catch an inverted multiply order, which lands these numbers in the
	// hundreds, not to police centimetres.
	auto Span = [](const FReferenceSkeleton& Ref, const TArray<FTransform>& CS,
		const TCHAR* A, const TCHAR* B) -> double
	{
		const int32 IA = Ref.FindBoneIndex(FName(A));
		const int32 IB = Ref.FindBoneIndex(FName(B));
		if (IA == INDEX_NONE || IB == INDEX_NONE)
		{
			return -1.0;
		}
		return (CS[IA].GetTranslation() - CS[IB].GetTranslation()).Size();
	};
	const double WristOffsetCm = Span(TargetRef, TargetRefCS, TEXT("hand_l"), TEXT("lowerarm_l"));
	const double HeadOverPelvisCm = Span(TargetRef, TargetRefCS, TEXT("head"), TEXT("pelvis"));
	TArray<FTransform> SourceCSForSanity;
	ReferenceComponentSpace(SourceRef, SourceCSForSanity);
	const double SourceWristOffsetCm = Span(SourceRef, SourceCSForSanity, TEXT("hand_l"), TEXT("lowerarm_l"));
	// lowerarm_l sits at the elbow and hand_l at the wrist, so this span is the FOREARM.
	const bool bSkeletonSane = WristOffsetCm > 15.0 && WristOffsetCm < 40.0
		&& HeadOverPelvisCm > 45.0 && HeadOverPelvisCm < 90.0;
	const bool bMotionOk = !bHasProbe || FMath::Abs(PropagatedDegrees - ProbeDegrees) < 1.0;
	const bool bLengthOk = LengthBefore <= 0.0
		|| FMath::Abs(LengthAfter - LengthBefore) < LengthBefore * 0.005f;

	// Which name matches were thrown out, and by how much. A short list here is the whole
	// argument for not generating a retarget chain map from bone names.
	FString RejectedDetail;
	for (int32 Index = 0; Index < Map.RejectedBones.Num() && Index < 12; ++Index)
	{
		RejectedDetail += FString::Printf(TEXT("%s%s(%.0fcm/%.0fdeg)"),
			Index ? TEXT(" ") : TEXT(""), *Map.RejectedBones[Index].ToString(),
			Map.RejectedOffsetDeltaCm[Index], Map.RejectedAngleDeltaDeg[Index]);
	}

	// The parent chain of the arm in both skeletons. A shared bone NAME is worth nothing if the
	// two rigs hang it off different parents, so this is reported rather than assumed.
	auto Chain = [](const FReferenceSkeleton& Ref, const TCHAR* Bone) -> FString
	{
		FString Result;
		for (int32 Index = Ref.FindBoneIndex(FName(Bone)); Index != INDEX_NONE;
			Index = Ref.GetParentIndex(Index))
		{
			Result += FString::Printf(TEXT("%s%s"), Result.IsEmpty() ? TEXT("") : TEXT("<"),
				*Ref.GetBoneName(Index).ToString());
		}
		return Result;
	};
	const FString ArmSource = Chain(SourceRef, TEXT("upperarm_l"));
	const FString ArmTarget = Chain(TargetRef, TEXT("upperarm_l"));
	const FString HandSource = Chain(SourceRef, TEXT("hand_l"));
	const FString HandTarget = Chain(TargetRef, TEXT("hand_l"));

	// How far apart the two skeletons' REST poses actually are, over the bones they share by
	// name. This is the decisive measurement for the whole prototype: a name match is only
	// useful if the two rigs also agree on where and how the joint sits, and the small
	// per-bone disagreement compounds down a chain until a hand ends up metres from the body.
	TArray<FTransform> SourceCSForStats;
	TArray<FTransform> TargetCSForStats;
	ReferenceComponentSpace(SourceRef, SourceCSForStats);
	ReferenceComponentSpace(TargetRef, TargetCSForStats);
	TArray<float> AngleDeltas;
	TArray<float> WorldDeltas;
	for (int32 Index = 0; Index < Map.TargetNames.Num(); ++Index)
	{
		const int32* Found = SourceByName.Find(Map.TargetNames[Index]);
		if (!Found)
		{
			continue;
		}
		AngleDeltas.Add(FMath::RadiansToDegrees(
			SourceRefPose[*Found].GetRotation().AngularDistance(TargetRefPose[Index].GetRotation())));
		WorldDeltas.Add(static_cast<float>(
			(SourceCSForStats[*Found].GetTranslation() - TargetCSForStats[Index].GetTranslation()).Size()));
	}
	AngleDeltas.Sort();
	WorldDeltas.Sort();
	auto Percentile = [](const TArray<float>& Sorted, float Fraction)
	{
		return Sorted.IsEmpty() ? 0.0f : Sorted[FMath::Clamp(int32(Fraction * Sorted.Num()), 0, Sorted.Num() - 1)];
	};
	const float MedianAngle = Percentile(AngleDeltas, 0.5f);
	const float MedianWorld = Percentile(WorldDeltas, 0.5f);

	// Hand-built rather than via FJsonSerializer: that would pull the Json module into
	// SouthernSpearCore, and the module's dependency policy is engine-modules-only with a
	// validator behind it. The report is flat, so the saving is not worth the policy hit.
	const FString Report = FString::Printf(
		TEXT("{\"ok\": %s, \"source_skeleton\": \"%s\", \"target_skeleton\": \"%s\", ")
		TEXT("\"target_bones\": %d, \"mapped_bones\": %d, \"unmapped_bones\": %d, \"digit_bones\": %d, ")
		TEXT("\"A_rest_is_fixed_point\": %s, \"A_worst_drift_cm\": %.4f, \"A_worst_bone\": \"%s\", ")
		TEXT("\"A_worst_anatomical_drift_cm\": %.4f, \"A_worst_anatomical_bone\": \"%s\", ")
		TEXT("\"B_motion_propagates_relatively\": %s, \"B_applied_degrees\": %.1f, ")
		TEXT("\"B_measured_degrees\": %.3f, \"B_child_followed\": %s, ")
		TEXT("\"C_proportions_survive\": %s, \"C_measured\": \"hand_l bone length (bone to parent)\", ")
		TEXT("\"C_upperarm_to_hand_cm_before\": %.4f, ")
		TEXT("\"C_upperarm_to_hand_cm_after\": %.4f, \"rejected_name_matches\": %d, ")
		TEXT("\"rejected_detail\": \"%s\", \"shared_bones\": %d, \"twist_bones_excluded\": %d, ")
		TEXT("\"rest_angle_deg_median\": %.2f, \"rest_angle_deg_p90\": %.2f, \"rest_angle_deg_max\": %.2f, ")
		TEXT("\"rest_world_cm_median\": %.2f, \"rest_world_cm_p90\": %.2f, ")
		TEXT("\"arm_chain_source\": \"%s\", \"arm_chain_target\": \"%s\", ")
		TEXT("\"hand_chain_source\": \"%s\", \"hand_chain_target\": \"%s\", ")
		TEXT("\"self_arm_to_hand_cm\": %.2f, \"source_arm_to_hand_cm\": %.2f, ")
		TEXT("\"target_local_lowerm_cm\": %.2f, ")
		TEXT("\"skeleton_sane\": %s, \"target_wrist_offset_cm\": %.2f, ")
		TEXT("\"source_wrist_offset_cm\": %.2f, \"target_head_over_pelvis_cm\": %.2f}"),
		(bRestOk && bMotionOk && bLengthOk && bSkeletonSane) ? TEXT("true") : TEXT("false"),
		*SourceMesh->GetName(), *TargetMesh->GetName(),
		Map.TargetNames.Num(), Mapped, Map.TargetNames.Num() - Mapped, Digits,
		bRestOk ? TEXT("true") : TEXT("false"), WorstRestDrift, *WorstRestBone,
		WorstAnatomicalDrift, *WorstAnatomicalBone,
		bMotionOk ? TEXT("true") : TEXT("false"), ProbeDegrees, PropagatedDegrees,
		bChildFollowed ? TEXT("true") : TEXT("false"),
		bLengthOk ? TEXT("true") : TEXT("false"), LengthBefore, LengthAfter,
		Map.RejectedBones.Num(), *RejectedDetail, AngleDeltas.Num(), Map.TwistExcluded,
		MedianAngle, Percentile(AngleDeltas, 0.9f), AngleDeltas.IsEmpty() ? 0.0f : AngleDeltas.Last(),
		MedianWorld, Percentile(WorldDeltas, 0.9f),
		*ArmSource, *ArmTarget, *HandSource, *HandTarget,
		SelfArmToHandCm, SourceArmToHandCm, TargetLocalLowerarmCm,
		bSkeletonSane ? TEXT("true") : TEXT("false"), WristOffsetCm, SourceWristOffsetCm, HeadOverPelvisCm);

	UE_LOG(LogTemp, Log, TEXT("SS_QPROOF %s: %d/%d mapped, %d digits | A=%s (%.3f cm worst) B=%s (%.1f/%.1f deg) C=%s (%.3f->%.3f cm)"),
		*TargetMesh->GetName(), Mapped, Map.TargetNames.Num(), Digits,
		bRestOk ? TEXT("ok") : TEXT("FAIL"), WorstRestDrift,
		bMotionOk ? TEXT("ok") : TEXT("FAIL"), PropagatedDegrees, ProbeDegrees,
		bLengthOk ? TEXT("ok") : TEXT("FAIL"), LengthBefore, LengthAfter);

	if (!bSkeletonSane)
	{
		UE_LOG(LogTemp, Error,
			TEXT("SS_QPROOF %s: COMPOSITION SANITY FAILED - forearm %.1f cm, head %.1f cm above pelvis. ")
			TEXT("The local-to-component-space multiply order is wrong; nothing else in this report means anything."),
			*TargetMesh->GetName(), WristOffsetCm, HeadOverPelvisCm);
	}

	return Report;
}

void ASSQuantumProtoStage::LogFitReport()
{
	// Criterion 3: the ADFRC plate carrier is authored on the mannequin skeleton, so whether
	// it still fits is a measurement of two torsos rather than an opinion.
	// Reference-pose world position, accumulated down the chain from the root.
	auto WorldRef = [](const FReferenceSkeleton& Ref, FName BoneName, FVector& OutLocation) -> bool
	{
		const int32 Index = Ref.FindBoneIndex(BoneName);
		if (Index == INDEX_NONE)
		{
			return false;
		}
		const TArray<FTransform>& RefPose = Ref.GetRefBonePose();
		OutLocation = RefPose[Index].GetLocation();
		for (int32 Parent = Ref.GetParentIndex(Index); Parent != INDEX_NONE; Parent = Ref.GetParentIndex(Parent))
		{
			OutLocation = RefPose[Parent].GetLocation() * OutLocation;
		}
		return true;
	};

	auto Span = [&](const FReferenceSkeleton& Ref, const TCHAR* A, const TCHAR* B) -> float
	{
		FVector Pa, Pb;
		if (!WorldRef(Ref, FName(A), Pa) || !WorldRef(Ref, FName(B), Pb))
		{
			return -1.0f;
		}
		return static_cast<float>((Pa - Pb).Size());
	};

	USkeletalMesh* Body = SSLoadMesh(QuantumProto::QuantumBody);
	USkeletalMesh* Shirt = SSLoadMesh(QuantumProto::QuantumShirt);
	USkeletalMesh* Jeans = SSLoadMesh(QuantumProto::QuantumJeans);
	USkeletalMesh* Vest = SSLoadMesh(QuantumProto::G3Vest);
	USkeletalMesh* Source = SSLoadMesh(QuantumProto::PoseSourceMesh);

	if (Source && Body)
	{
		const FReferenceSkeleton& RefA = Source->GetRefSkeleton();
		const FReferenceSkeleton& RefB = Body->GetRefSkeleton();
		const float ShoulderA = Span(RefA, TEXT("clavicle_l"), TEXT("clavicle_r"));
		const float ShoulderB = Span(RefB, TEXT("clavicle_l"), TEXT("clavicle_r"));
		const float HipA = Span(RefA, TEXT("thigh_l"), TEXT("thigh_r"));
		const float HipB = Span(RefB, TEXT("thigh_l"), TEXT("thigh_r"));
		const float SpineA = Span(RefA, TEXT("pelvis"), TEXT("neck_01"));
		const float SpineB = Span(RefB, TEXT("pelvis"), TEXT("neck_01"));
		UE_LOG(LogTemp, Log,
			TEXT("SS_QFIT shoulders_cm manny=%.1f quantum=%.1f delta=%+.1f | hips_cm manny=%.1f quantum=%.1f delta=%+.1f")
			TEXT(" | spine_cm manny=%.1f quantum=%.1f delta=%+.1f"),
			ShoulderA, ShoulderB, ShoulderB - ShoulderA, HipA, HipB, HipB - HipA, SpineA, SpineB, SpineB - SpineA);
	}

	auto LogBounds = [](const TCHAR* Label, USkeletalMesh* Mesh)
	{
		if (!Mesh)
		{
			UE_LOG(LogTemp, Log, TEXT("SS_QFIT %s missing"), Label);
			return;
		}
		const FBoxSphereBounds Bounds = Mesh->GetBounds();
		UE_LOG(LogTemp, Log, TEXT("SS_QFIT %s %s extent_cm x=%.1f y=%.1f z=%.1f origin_z=%.1f"),
			Label, *Mesh->GetName(), Bounds.BoxExtent.X, Bounds.BoxExtent.Y, Bounds.BoxExtent.Z, Bounds.Origin.Z);
	};
	LogBounds(TEXT("vest"), Vest);
	LogBounds(TEXT("quantum_shirt"), Shirt);
	LogBounds(TEXT("quantum_jeans"), Jeans);
	LogBounds(TEXT("quantum_body"), Body);
	LogBounds(TEXT("mannequin"), Source);
}
