// Copyright Southern Spear. All Rights Reserved.

#include "SSFirstPersonSubsystem.h"

#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "Camera/CameraActor.h"
#include "Camera/LyraCameraComponent.h"
#include "AIController.h"
#include "EngineUtils.h"
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
	TAutoConsoleVariable<FString> CVarWeaponRotation(TEXT("ss.FP.WeaponRotation"), TEXT("0 -90 0"),
		TEXT("Held weapon rotation on ik_hand_gun, degrees (pitch yaw roll); 90 yaw turns our +X meshes to the pack's +Y."));
	TAutoConsoleVariable<int32> CVarArms(TEXT("ss.FP.Arms"), 0,
		TEXT("1: Fab arms pack holding the weapon (its AKS74U poses do not fit our weapons). 0: camera-held weapon view model."));
	TAutoConsoleVariable<FString> CVarHip(TEXT("ss.FP.Hip"), TEXT("38 13 -16"),
		TEXT("Camera-held weapon: grip position at the hip, cm (forward right up)."));
	TAutoConsoleVariable<int32> CVarBodyView(TEXT("ss.FP.BodyView"), 0,
		TEXT("1: true first person (the body's own hands and weapon, Lyra animations; the eye moves to the optic when aiming). 0: the Fab arms pack view model."));
	TAutoConsoleVariable<float> CVarFollowBot(TEXT("ss.Debug.FollowBot"), 0.f,
		TEXT("Debug: non-zero views the nearest bot from this many cm (behind and to the side), for animation checks."));
	TAutoConsoleVariable<float> CVarDebugPitch(TEXT("ss.FP.DebugPitch"), 0.f,
		TEXT("Debug: non-zero holds the local view at this pitch, degrees (captures)."));
	TAutoConsoleVariable<int32> CVarForceAim(TEXT("ss.FP.ForceAim"), 0,
		TEXT("Debug: 1 holds the first-person view in aim (for sight alignment captures)."));
	TAutoConsoleVariable<float> CVarEyeRelief(TEXT("ss.FP.EyeRelief"), 13.f,
		TEXT("Minimum distance, cm, from the eye to the weapon's Sight socket when aiming."));

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
	if (const float Follow = CVarFollowBot.GetValueOnGameThread())
	{
		// Third-person look at the nearest bot (animation review): a camera
		// actor trails it, and the local view switches to that camera.
		APawn* Bot = nullptr;
		float Best = TNumericLimits<float>::Max();
		for (TActorIterator<APawn> It(GetWorld()); It; ++It)
		{
			if (Cast<AAIController>(It->GetController()) && FVector::DistSquared(It->GetActorLocation(), Pawn->GetActorLocation()) < Best)
			{
				Best = FVector::DistSquared(It->GetActorLocation(), Pawn->GetActorLocation());
				Bot = *It;
			}
		}
		if (Bot)
		{
			if (!FollowCamera.IsValid())
			{
				FActorSpawnParameters Params;
				Params.ObjectFlags |= RF_Transient;
				FollowCamera = GetWorld()->SpawnActor<ACameraActor>(Params);
			}
			const FRotator Facing(0.f, Bot->GetActorRotation().Yaw + 150.f, 0.f);
			const FVector Eye = Bot->GetActorLocation() + Facing.Vector() * -Follow + FVector(0.f, 0.f, 60.f);
			FollowCamera->SetActorLocationAndRotation(Eye, (Bot->GetActorLocation() + FVector(0, 0, 20) - Eye).Rotation());
			APlayerController* Controller = const_cast<APlayerController*>(Player);
			if (Controller->GetViewTarget() != FollowCamera.Get())
			{
				Controller->SetViewTarget(FollowCamera.Get());
			}
		}
	}
	if (const float DebugPitch = CVarDebugPitch.GetValueOnGameThread())
	{
		APlayerController* Controller = const_cast<APlayerController*>(Player);
		FRotator Rotation = Controller->GetControlRotation();
		Rotation.Pitch = DebugPitch;
		Controller->SetControlRotation(Rotation);
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
		*AimFlag = (Chosen && Chosen->GetName().Contains(TEXT("ADS"))) || CVarForceAim.GetValueOnGameThread() != 0;
		return *AimFlag ? USSFirstPersonADSCameraMode::StaticClass() : USSFirstPersonCameraMode::StaticClass();
	});

	Arms = nullptr;
	Current = nullptr;
	ViewModel = nullptr;
	if (CVarBodyView.GetValueOnGameThread() != 0)
	{
		// True first person: Lyra's full rifle set (run, reload, aim) already
		// animates the body holding the real weapon; show both to the owner
		// and hide the head the eye sits in (the soldier parts follow it).
		if (ACharacter* Character = Cast<ACharacter>(Pawn))
		{
			Character->GetMesh()->HideBoneByName(TEXT("head"), EPhysBodyOp::PBO_None);
		}
		HandledPawn = Pawn;
		UE_LOG(LogSSFirstPerson, Log, TEXT("First-person camera active for %s (body view)."), *Pawn->GetName());
		return;
	}
	USkeletalMesh* ArmsMesh = CVarArms.GetValueOnGameThread() != 0 ? LoadObject<USkeletalMesh>(nullptr, ArmsMeshPath) : nullptr;
	if (ArmsMesh)
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
		// First person shows only the arms: the body (and the soldier parts
		// that follow it, below) is hidden from its owner but keeps its shadow.
		Character->GetMesh()->SetOwnerNoSee(true);
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
	static bool bListed = false;
	if (!bListed && Pawn->GetGameTimeSinceCreation() > 8.f && FParse::Param(FCommandLine::Get(), TEXT("SSAnimDebug")))
	{
		bListed = true;
		TArray<AActor*> Actors;
		Pawn->GetAttachedActors(Actors, true, true);
		Actors.Add(Pawn);
		for (const AActor* Actor : Actors)
		{
			TInlineComponentArray<UPrimitiveComponent*> Prims(Actor);
			for (const UPrimitiveComponent* Prim : Prims)
			{
				UE_LOG(LogSSFirstPerson, Log, TEXT("FP component %s.%s (%s) visible=%d ownerNoSee=%d mesh=%s"), *Actor->GetName(), *Prim->GetName(),
					*Prim->GetClass()->GetName(), Prim->IsVisible(), Prim->bOwnerNoSee,
					Cast<USkeletalMeshComponent>(Prim) ? *GetNameSafe(Cast<USkeletalMeshComponent>(Prim)->GetSkeletalMeshAsset()) : TEXT("-"));
			}
		}
	}
	if (USSLocalHudState* HudState = GetWorld()->GetSubsystem<USSLocalHudState>())
	{
		HudState->bAiming = *bAiming;
	}
	if (!ViewModel)
	{
		// Body view: the soldier parts and the held weapon hide themselves
		// from their owner for third-person bodies; undo that here (weapons
		// change, so every tick; a handful of components).
		TArray<AActor*> Attached;
		Pawn->GetAttachedActors(Attached, true, true);
		for (AActor* Actor : Attached)
		{
			TInlineComponentArray<UPrimitiveComponent*> Parts(Actor);
			for (UPrimitiveComponent* Part : Parts)
			{
				if (Part->bOwnerNoSee)
				{
					Part->SetOwnerNoSee(false);
				}
			}
		}
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
		TInlineComponentArray<USkeletalMeshComponent*> Bodies(Actor);
		for (USkeletalMeshComponent* Body : Bodies)
		{
			// Hidden locally (this subsystem only runs for the local player),
			// shadow kept: owner-no-see alone let the beret through from inside.
			Body->SetOwnerNoSee(true);
			Body->bCastHiddenShadow = true;
			Body->SetHiddenInGame(true);
		}
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
		// The pack animates a short AKS74U; its hand bone swings our longer
		// weapons across the view. Keep the grip in the hand but point the
		// weapon along the view (a slight inward cant at the hip).
		if (const USceneComponent* ViewParent = Arms->GetAttachParent())
		{
			const FRotator Cant(0.f, FMath::Lerp(-2.5f, 0.f, AimAlpha), FMath::Lerp(-4.f, 0.f, AimAlpha));
			ViewModel->SetWorldRotation(ViewParent->GetComponentQuat() * Cant.Quaternion());
		}

		// Aiming: the pack frames its own iron sights; our optics sit higher and
		// differ per weapon, so shift the arms until the weapon's Sight socket is
		// on the line of sight (camera X axis) with some eye relief.
		static const FName SightSocket(TEXT("Sight"));
		const USceneComponent* View = Arms->GetAttachParent();
		if (View && AimAlpha > 0.f && ViewModel->DoesSocketExist(SightSocket))
		{
			const FVector Sight = View->GetComponentTransform().InverseTransformPosition(ViewModel->GetSocketLocation(SightSocket));
			const FVector Correction(FMath::Max(0.f, CVarEyeRelief.GetValueOnGameThread() - Sight.X), -Sight.Y, -Sight.Z);
			Arms->AddRelativeLocation(Correction * AimAlpha);
		}
		return;
	}

	// Camera-held view model: the whole weapon in view, placed from its own
	// geometry; motion is procedural (bob, recoil, reload dip) and follows the
	// gameplay state (magazine count, the body's Lyra reload montage).
	const USSLocalHudState* State = GetWorld()->GetSubsystem<USSLocalHudState>();
	const int32 Magazine = State ? State->Magazine : -1;
	const ACharacter* Character = Cast<ACharacter>(Pawn);
	const UAnimInstance* Body = Character && Character->GetMesh() ? Character->GetMesh()->GetAnimInstance() : nullptr;
	const UAnimMontage* Montage = Body ? Body->GetCurrentActiveMontage() : nullptr;
	const bool bReloading = Montage && Montage->GetName().Contains(TEXT("Reload"));
	if (Magazine >= 0 && LastMagazine >= 0 && Magazine < LastMagazine && !bReloading)
	{
		Recoil = 1.f;
	}
	LastMagazine = Magazine;
	Recoil = FMath::FInterpTo(Recoil, 0.f, DeltaTime, 12.f);
	ReloadAlpha = FMath::FInterpTo(ReloadAlpha, bReloading ? 1.f : 0.f, DeltaTime, 6.f);

	// Aim: optics put their Sight socket on the line of sight; iron-sight
	// weapons (no socket) put the top of the mesh just under it.
	static const FName SightSocket(TEXT("Sight"));
	const float EyeRelief = CVarEyeRelief.GetValueOnGameThread();
	FVector Aim(28.f, 0.f, -6.f);
	if (ViewModel->DoesSocketExist(SightSocket))
	{
		const FVector Sight = ViewModel->GetSocketTransform(SightSocket, RTS_Component).GetLocation();
		Aim = FVector(EyeRelief - Sight.X, -Sight.Y, -Sight.Z);
	}
	else if (const UStaticMesh* Mesh = ViewModel->GetStaticMesh())
	{
		const FBox Box = Mesh->GetBoundingBox();
		Aim = FVector(28.f, -Box.GetCenter().Y, -(Box.Max.Z - 1.5f));
	}
	const FVector Hip = ParseVector(CVarHip);
	const float Speed = Pawn->GetVelocity().Size2D();
	const float Time = GetWorld()->GetTimeSeconds();
	const float Bob = FMath::Clamp(Speed / 400.f, 0.f, 1.f) * SwayScale;
	const FVector BobOffset(0.f, FMath::Sin(Time * 7.f) * 0.8f * Bob, FMath::Abs(FMath::Sin(Time * 7.f)) * -1.0f * Bob);
	const FVector Location = FMath::Lerp(Hip, Aim, AimAlpha) + SwayOffset + BobOffset
		+ FVector(-2.5f * Recoil, 0.f, -12.f * ReloadAlpha);
	const FRotator Rotation(3.f * Recoil * SwayScale - 18.f * ReloadAlpha, FMath::Lerp(-2.f, 0.f, AimAlpha),
		FMath::Lerp(-3.f, 0.f, AimAlpha) - 30.f * ReloadAlpha);
	ViewModel->SetRelativeLocationAndRotation(Location, Rotation);
}
