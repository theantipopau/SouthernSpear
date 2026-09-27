// Copyright Southern Spear. All Rights Reserved.

#include "SSFirstPersonSubsystem.h"

#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "Camera/LyraCameraComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "SSFirstPersonCameraMode.h"
#include "SSLocalHudState.h"

DEFINE_LOG_CATEGORY_STATIC(LogSSFirstPerson, Log, All);

namespace
{
	// Fab "FPS Animation" pack (AKS-74U): first-person arms on the UE5 arms skeleton.
	const TCHAR* ArmsMeshPath = TEXT("/Game/FP_AKS74U_Animation/Demo/FirstPersonArms/Character/Mesh/SK_Mannequin_Arms.SK_Mannequin_Arms");
	const TCHAR* AnimRoot = TEXT("/Game/FP_AKS74U_Animation/AKS74U/Animations/");

	UAnimSequence* Anim(const TCHAR* Name)
	{
		const FString Path = FString(AnimRoot) + Name + TEXT(".") + Name;
		return LoadObject<UAnimSequence>(nullptr, *Path);
	}

	// Live-tunable placement (console): arms relative to the eye, weapon on weapon_r.
	TAutoConsoleVariable<FString> CVarArmsOffset(TEXT("ss.FP.ArmsOffset"), TEXT("0 0 0"),
		TEXT("First-person arms offset from the eye, cm (forward right up)."));
	TAutoConsoleVariable<FString> CVarWeaponOffset(TEXT("ss.FP.WeaponOffset"), TEXT("-1.5 -7.5 -7"),
		TEXT("Held weapon offset on the arms' ik_hand_gun bone, cm."));
	TAutoConsoleVariable<FString> CVarWeaponRotation(TEXT("ss.FP.WeaponRotation"), TEXT("0 90 0"),
		TEXT("Held weapon rotation on ik_hand_gun, degrees (pitch yaw roll); 90 yaw turns our +X meshes to the pack's +Y."));

	FVector ParseVector(const TAutoConsoleVariable<FString>& CVar)
	{
		TArray<FString> Parts;
		CVar.GetValueOnGameThread().ParseIntoArrayWS(Parts);
		return FVector(Parts.IsValidIndex(0) ? FCString::Atof(*Parts[0]) : 0.f,
			Parts.IsValidIndex(1) ? FCString::Atof(*Parts[1]) : 0.f,
			Parts.IsValidIndex(2) ? FCString::Atof(*Parts[2]) : 0.f);
	}
}

bool USSFirstPersonSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* World = Cast<UWorld>(Outer);
	return World && World->GetNetMode() != NM_DedicatedServer && Super::ShouldCreateSubsystem(Outer);
}

bool USSFirstPersonSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId USSFirstPersonSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USSFirstPersonSubsystem, STATGROUP_Tickables);
}

void USSFirstPersonSubsystem::Tick(float DeltaTime)
{
	const APlayerController* Player = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	APawn* Pawn = Player && Player->IsLocalController() ? Player->GetPawn() : nullptr;
	if (!Pawn)
	{
		return;
	}
	if (HandledPawn.Get() == Pawn)
	{
		UpdateViewModel(Pawn, DeltaTime);
		return;
	}

	// ULyraCameraComponent is not exported; find it by class name, then use
	// only its public delegate field (header-inline, no exported symbol).
	static UClass* CameraClass = FindObject<UClass>(nullptr, TEXT("/Script/LyraGame.LyraCameraComponent"));
	ULyraCameraComponent* Camera = CameraClass ? static_cast<ULyraCameraComponent*>(Pawn->GetComponentByClass(CameraClass)) : nullptr;
	if (!Camera || !Camera->DetermineCameraModeDelegate.IsBound())
	{
		return; // hero component binds it during init; try again next tick
	}

	FLyraCameraModeDelegate LyraChoice = Camera->DetermineCameraModeDelegate;
	TSharedRef<bool> AimFlag = bAiming;
	Camera->DetermineCameraModeDelegate.BindLambda([LyraChoice, AimFlag]() -> TSubclassOf<ULyraCameraMode>
	{
		const TSubclassOf<ULyraCameraMode> Chosen = LyraChoice.IsBound() ? LyraChoice.Execute() : nullptr;
		*AimFlag = Chosen && Chosen->GetName().Contains(TEXT("ADS"));
		return *AimFlag ? USSFirstPersonADSCameraMode::StaticClass() : USSFirstPersonCameraMode::StaticClass();
	});

	Arms = nullptr;
	Current = nullptr;
	if (USkeletalMesh* ArmsMesh = LoadObject<USkeletalMesh>(nullptr, ArmsMeshPath))
	{
		Arms = NewObject<USkeletalMeshComponent>(Pawn, TEXT("SS_FirstPersonArms"));
		Arms->SetupAttachment(Camera);
		Arms->SetSkeletalMesh(ArmsMesh);
		Arms->SetOnlyOwnerSee(true);
		Arms->SetCastShadow(false);
		Arms->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Arms->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
		Arms->SetAnimationMode(EAnimationMode::AnimationSingleNode);
		Arms->RegisterComponent();
		Play(Anim(TEXT("A_FP_AKS74U_Equipe")), false);
	}

	ViewModel = NewObject<UStaticMeshComponent>(Pawn, TEXT("SS_ViewModel"));
	if (Arms)
	{
		// The pack holds its rifle at ik_hand_gun, gun along the arms' +Y.
		ViewModel->SetupAttachment(Arms, TEXT("ik_hand_gun"));
	}
	else
	{
		ViewModel->SetupAttachment(Camera);
	}
	ViewModel->SetOnlyOwnerSee(true);
	ViewModel->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	ViewModel->SetCastShadow(false);
	ViewModel->RegisterComponent();

	if (const ACharacter* Character = Cast<ACharacter>(Pawn))
	{
		Character->GetMesh()->HideBoneByName(TEXT("head"), EPhysBodyOp::PBO_None);
	}
	HandledPawn = Pawn;
	LastMagazine = -1;
	UE_LOG(LogSSFirstPerson, Log, TEXT("First-person camera active for %s (arms: %s)."), *Pawn->GetName(), Arms ? TEXT("Fab FPS pack") : TEXT("none"));
}

void USSFirstPersonSubsystem::Play(UAnimSequence* Sequence, bool bLoop)
{
	if (!Arms || !Sequence)
	{
		return;
	}
	if (Sequence == Current && bLoop)
	{
		return; // already looping it
	}
	Current = Sequence;
	Arms->PlayAnimation(Sequence, bLoop);
	OneShotRemaining = bLoop ? 0.f : Sequence->GetPlayLength();
}

void USSFirstPersonSubsystem::UpdateArmsAnimation(APawn* Pawn, float DeltaTime)
{
	const USSLocalHudState* State = GetWorld()->GetSubsystem<USSLocalHudState>();
	const int32 Magazine = State ? State->Magazine : -1;
	const bool bAim = *bAiming;

	// Reload: follow the body's Lyra reload montage (the gameplay authority).
	const ACharacter* Character = Cast<ACharacter>(Pawn);
	const UAnimInstance* Body = Character && Character->GetMesh() ? Character->GetMesh()->GetAnimInstance() : nullptr;
	const UAnimMontage* Montage = Body ? Body->GetCurrentActiveMontage() : nullptr;
	const bool bReloading = Montage && Montage->GetName().Contains(TEXT("Reload"));
	if (bReloading && !bReloadSeen)
	{
		const bool bEmpty = Magazine == 0;
		Play(Anim(bEmpty ? (bAim ? TEXT("A_FP_AKS74U_Reload_Empty_Aimed") : TEXT("A_FP_AKS74U_Reload_Empty"))
			: (bAim ? TEXT("A_FP_AKS74U_Reload_Aimed") : TEXT("A_FP_AKS74U_Reload"))), false);
	}
	bReloadSeen = bReloading;

	// Fire: the magazine count dropped.
	if (Magazine >= 0 && LastMagazine >= 0 && Magazine < LastMagazine && !bReloading)
	{
		Play(Anim(bAim ? TEXT("A_FP_AKS74U_Fire_Aimed") : TEXT("A_FP_AKS74U_Fire")), false);
	}
	LastMagazine = Magazine;

	OneShotRemaining -= DeltaTime;
	if (OneShotRemaining > 0.f)
	{
		return; // let fire / reload / equip finish
	}

	// Loops by movement state.
	const float Speed = Pawn->GetVelocity().Size2D();
	const TCHAR* Loop = bAim
		? (Speed > 30.f ? TEXT("A_FP_AKS74U_Walk_F_Loop_Aimed") : TEXT("A_FP_AKS74U_Aim_Loop"))
		: (Speed > 420.f ? TEXT("A_FP_AKS74U_Run_Loop") : Speed > 30.f ? TEXT("A_FP_AKS74U_Walk_F_Loop") : TEXT("A_FP_AKS74U_Idle_Loop"));
	static TMap<FString, TWeakObjectPtr<UAnimSequence>> Cache;
	TWeakObjectPtr<UAnimSequence>& Cached = Cache.FindOrAdd(Loop);
	if (!Cached.IsValid())
	{
		Cached = Anim(Loop);
	}
	Play(Cached.Get(), true);
}

void USSFirstPersonSubsystem::UpdateViewModel(APawn* Pawn, float DeltaTime)
{
	if (!ViewModel)
	{
		return;
	}
	// The held weapon is a cosmetic actor attached to the pawn's body mesh
	// (Lyra equipment). Show its mesh in first person and hide the body copy
	// from the owner. Soldier body parts are skeletal, so they never match.
	UStaticMesh* Held = nullptr;
	TArray<AActor*> Attached;
	Pawn->GetAttachedActors(Attached, true, true);
	for (AActor* Actor : Attached)
	{
		TInlineComponentArray<UStaticMeshComponent*> Meshes(Actor);
		for (UStaticMeshComponent* Mesh : Meshes)
		{
			if (Mesh->GetStaticMesh() && Mesh != ViewModel)
			{
				Mesh->SetOwnerNoSee(true);
				if (!Held) { Held = Mesh->GetStaticMesh(); }
			}
		}
	}
	if (ViewModel->GetStaticMesh() != Held)
	{
		ViewModel->SetStaticMesh(Held);
		UE_LOG(LogSSFirstPerson, Log, TEXT("View model shows %s."), *GetNameSafe(Held));
	}

	if (USSLocalHudState* HudState = GetWorld()->GetSubsystem<USSLocalHudState>())
	{
		HudState->bAiming = *bAiming;
	}
	AimAlpha = FMath::FInterpConstantTo(AimAlpha, *bAiming ? 1.f : 0.f, DeltaTime, 6.f);

	// Sway: the view model lags look input slightly and settles back.
	const FRotator Control = Pawn->GetControlRotation();
	const FRotator Delta = (Control - LastControlRotation).GetNormalized();
	LastControlRotation = Control;
	const float SwayScale = FMath::Lerp(1.f, 0.25f, AimAlpha);
	SwayOffset += FVector(0.f, -Delta.Yaw * 0.08f, -Delta.Pitch * 0.08f) * SwayScale;
	SwayOffset = FMath::VInterpTo(SwayOffset, FVector::ZeroVector, DeltaTime, 8.f).BoundToCube(3.f);

	if (Arms)
	{
		UpdateArmsAnimation(Pawn, DeltaTime);
		// Arms face +Y in their mesh space (UE mannequin): turn to camera +X, then
		// shift so the animated head bone sits at the eye; the pack's animations
		// frame the weapon for that eye position.
		const FRotator Facing(0.f, -90.f, 0.f);
		const FVector HeadInComponent = Arms->DoesSocketExist(TEXT("head"))
			? Arms->GetBoneLocation(TEXT("head"), EBoneSpaces::ComponentSpace) : FVector(0.f, 0.f, 160.f);
		const FVector Eye = Facing.RotateVector(HeadInComponent);
		Arms->SetRelativeLocationAndRotation(-Eye + ParseVector(CVarArmsOffset) + SwayOffset, Facing);
		const FVector Rot = ParseVector(CVarWeaponRotation);
		ViewModel->SetRelativeLocationAndRotation(ParseVector(CVarWeaponOffset), FRotator(Rot.X, Rot.Y, Rot.Z));
		return;
	}

	// Fallback without the pack: camera-attached weapon with hip/aim placements and bob.
	static const FVector Hip(32.f, 13.f, -15.f);
	static const FVector Aim(24.f, 0.f, -10.5f);
	const float Speed = Pawn->GetVelocity().Size2D();
	const float Time = GetWorld()->GetTimeSeconds();
	const float Bob = FMath::Clamp(Speed / 400.f, 0.f, 1.f) * SwayScale;
	const FVector BobOffset(0.f, FMath::Sin(Time * 6.f) * 0.6f * Bob, FMath::Abs(FMath::Sin(Time * 6.f)) * -0.8f * Bob);
	ViewModel->SetRelativeLocationAndRotation(FMath::Lerp(Hip, Aim, AimAlpha) + SwayOffset + BobOffset, FRotator::ZeroRotator);
}
