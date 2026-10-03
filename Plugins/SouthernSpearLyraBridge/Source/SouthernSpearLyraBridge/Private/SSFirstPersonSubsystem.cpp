// Copyright Southern Spear. All Rights Reserved.

#include "SSFirstPersonSubsystem.h"

#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "Camera/CameraActor.h"
#include "Camera/LyraCameraComponent.h"
#include "AIController.h"
#include "EngineUtils.h"
#include "GenericTeamAgentInterface.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "SSFirstPersonCameraMode.h"
#include "SSHandIKMeshComponent.h"
#include "SSLocalHudState.h"

DEFINE_LOG_CATEGORY_STATIC(LogSSFirstPerson, Log, All);

namespace
{
	// Fab "M4" (rifle) and "G17" (pistol) FPS animation packs: gloved arms and clips, their real-weapon
	// models removed (Tools/Blender/fp_arms.py, Tools/Unreal/setup_fp_arms.py). Bones: FPS_Camera_j (the
	// eye), Main_j (the weapon), RightHand* / LeftHand* (fingers). Assets: FirstPerson/<Set>/SK_FP_Arms_<Set>
	// and A_FP_<Set>_<Clip> (Draw, Fire, Holster, Idle, Reload, Reload_Empty).
	const TCHAR* const ArmsSets[] = { TEXT("Rifle"), TEXT("Pistol") };
	constexpr float PistolMaxLength = 35.f; // cm: shorter held weapons use the pistol arms

	FString ArmsMeshPath(int32 Set)
	{
		return FString::Printf(TEXT("/SSExp_ObjectiveAssault/FirstPerson/%s/SK_FP_Arms_%s.SK_FP_Arms_%s"), ArmsSets[Set], ArmsSets[Set], ArmsSets[Set]);
	}

	UAnimSequence* Clip(int32 Set, const TCHAR* Name)
	{
		static TMap<FString, TWeakObjectPtr<UAnimSequence>> Cache;
		const FString Asset = FString::Printf(TEXT("A_FP_%s_%s"), ArmsSets[Set], Name);
		TWeakObjectPtr<UAnimSequence>& Cached = Cache.FindOrAdd(Asset);
		if (!Cached.IsValid())
		{
			Cached = LoadObject<UAnimSequence>(nullptr, *FString::Printf(TEXT("/SSExp_ObjectiveAssault/FirstPerson/%s/%s.%s"), ArmsSets[Set], *Asset, *Asset));
		}
		return Cached.Get();
	}
	const FName CameraBone(TEXT("FPS_Camera_j"));
	const FName WeaponBone(TEXT("Main_j"));
	const FName RightGripBone(TEXT("RightHandMiddle1"));
	const FName LeftGripBone(TEXT("LeftHandMiddle1"));
	const FName TriggerBone(TEXT("Trigger_j")); // the pack weapon's trigger: our meshes have their origin there

	// Live-tunable placement (console): arms relative to the eye, weapon on weapon_r.
	TAutoConsoleVariable<FString> CVarArmsOffset(TEXT("ss.FP.ArmsOffset"), TEXT("13 3 -8"),
		TEXT("First-person rifle arms offset from the eye, cm (forward right up). Session 094: was 17 0 -2, which put a fat forearm across the lower left of the view."));
	TAutoConsoleVariable<FString> CVarPistolArmsOffset(TEXT("ss.FP.PistolArmsOffset"), TEXT("11 0 -8"),
		TEXT("First-person pistol arms offset from the eye, cm (forward right up)."));
	TAutoConsoleVariable<FString> CVarWeaponOffset(TEXT("ss.FP.WeaponOffset"), TEXT("0 0 0"),
		TEXT("Held rifle: offset from the pack weapon trigger bone (Trigger_j), in the weapon frame, cm (forward right up)."));
	TAutoConsoleVariable<FString> CVarPistolOffset(TEXT("ss.FP.PistolOffset"), TEXT("0 0 -1"),
		TEXT("Held pistol: grip offset from the pack's weapon bone (where its pistol sat), in the weapon's frame, cm (forward right up)."));
	TAutoConsoleVariable<FString> CVarWeaponRotation(TEXT("ss.FP.WeaponRotation"), TEXT("0 0 0"),
		TEXT("Held weapon: extra rotation on the measured grip, degrees (pitch yaw roll)."));
	TAutoConsoleVariable<int32> CVarArms(TEXT("ss.FP.Arms"), 1,
		TEXT("1: gloved arms view model (Fab M4 FPS pack) holding the weapon. 0: camera-held weapon view model."));
	TAutoConsoleVariable<FString> CVarHip(TEXT("ss.FP.Hip"), TEXT("48 16 -20"),
		TEXT("Camera-held weapon: grip position at the hip, cm (forward right up)."));
	TAutoConsoleVariable<int32> CVarBodyView(TEXT("ss.FP.BodyView"), 0,
		TEXT("1: true first person (the body's own hands and weapon, Lyra animations; the eye moves to the optic when aiming). 0: the Fab arms pack view model."));
	TAutoConsoleVariable<int32> CVarShowLyraWeapon(TEXT("ss.Debug.ShowLyraWeapon"), 0,
		TEXT("Debug: 1 also draws Lyra's original weapon meshes (hidden under ours) to check alignment."));
	TAutoConsoleVariable<float> CVarFollowBot(TEXT("ss.Debug.FollowBot"), 0.f,
		TEXT("Debug: non-zero views the nearest bot from this many cm (behind and to the side); negative: the nearest enemy bot."));
	TAutoConsoleVariable<float> CVarDebugPitch(TEXT("ss.FP.DebugPitch"), 0.f,
		TEXT("Debug: non-zero holds the local view at this pitch, degrees (captures)."));
	TAutoConsoleVariable<float> CVarDebugYawTurn(TEXT("ss.FP.DebugYawTurn"), 0.f,
		TEXT("Debug: non-zero turns the local view by this many degrees once (captures, e.g. to face the own shadow)."));
	TAutoConsoleVariable<int32> CVarDebugSlot(TEXT("ss.FP.DebugSlot"), -1,
		TEXT("Debug: >= 0 selects that quickbar slot once (captures; e.g. 1 = sidearm)."));
	TAutoConsoleVariable<int32> CVarForceAim(TEXT("ss.FP.ForceAim"), 0,
		TEXT("Debug: 1 holds the first-person view in aim (for sight alignment captures)."));
	TAutoConsoleVariable<float> CVarEyeRelief(TEXT("ss.FP.EyeRelief"), 20.f,
		TEXT("Minimum distance, cm, from the eye to the weapon's Sight socket when aiming."));

	TAutoConsoleVariable<float> CVarIronRelief(TEXT("ss.FP.IronRelief"), 38.f,
		TEXT("Iron sights (no Sight socket, e.g. pistols): distance, cm, from the eye to the rear sight when aiming."));

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
			// Negative distance: follow the nearest bot of the OTHER team (MAF presentation checks).
			const IGenericTeamAgentInterface* Mine = Cast<IGenericTeamAgentInterface>(Pawn);
			const IGenericTeamAgentInterface* Theirs = Cast<IGenericTeamAgentInterface>(*It);
			const bool bEnemy = Mine && Theirs && Mine->GetGenericTeamId() != Theirs->GetGenericTeamId();
			if (Follow < 0.f && !bEnemy)
			{
				continue;
			}
			if (Cast<AAIController>(It->GetController()) && FVector::DistSquared(It->GetActorLocation(), Pawn->GetActorLocation()) < Best)
			{
				Best = FVector::DistSquared(It->GetActorLocation(), Pawn->GetActorLocation());
				Bot = *It;
			}
		}
		if (CVarShowLyraWeapon.GetValueOnGameThread() != 0)
		{
			for (TActorIterator<AActor> It(GetWorld()); It; ++It)
			{
				if (It->GetClass()->GetName().StartsWith(TEXT("B_SS_")) && It->GetClass()->GetName().Contains(TEXT("_Weapon")))
				{
					TInlineComponentArray<USkeletalMeshComponent*> Skels(*It);
					for (USkeletalMeshComponent* Skel : Skels)
					{
						Skel->SetVisibility(true);
						Skel->SetHiddenInGame(false);
					}
				}
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
			const FVector Eye = Bot->GetActorLocation() + Facing.Vector() * -FMath::Abs(Follow) + FVector(0.f, 0.f, 60.f);
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
	if (const int32 Slot = CVarDebugSlot.GetValueOnGameThread(); Slot >= 0)
	{
		// ULyraQuickBarComponent is not exported: call its SetActiveSlotIndex UFUNCTION by reflection.
		CVarDebugSlot->Set(-1);
		static UClass* QuickBarClass = FindObject<UClass>(nullptr, TEXT("/Script/LyraGame.LyraQuickBarComponent"));
		UActorComponent* QuickBar = QuickBarClass ? Player->GetComponentByClass(QuickBarClass) : nullptr;
		if (UFunction* Fn = QuickBar ? QuickBar->FindFunction(TEXT("SetActiveSlotIndex")) : nullptr)
		{
			struct { int32 NewIndex; } Params{ Slot };
			QuickBar->ProcessEvent(Fn, &Params);
			UE_LOG(LogSSFirstPerson, Log, TEXT("Debug: quickbar slot %d selected."), Slot);
		}
	}
	if (const float Turn = CVarDebugYawTurn.GetValueOnGameThread())
	{
		APlayerController* Controller = const_cast<APlayerController*>(Player);
		FRotator Rotation = Controller->GetControlRotation();
		Rotation.Yaw += Turn;
		Controller->SetControlRotation(Rotation);
		CVarDebugYawTurn->Set(0.f);
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
		// The Quantum body's head is a separate skinned component on its own skeleton
		// (ADR-042), so the pawn mesh's hidden head bone says nothing about it. Hide the
		// head bone on every attached skinned part that has one (HideBoneByName is a
		// guarded no-op where the bone does not exist).
		TArray<AActor*> Parts;
		Pawn->GetAttachedActors(Parts, true, true);
		for (AActor* Part : Parts)
		{
			TInlineComponentArray<USkinnedMeshComponent*> Skins(Part);
			for (USkinnedMeshComponent* Skin : Skins)
			{
				Skin->HideBoneByName(TEXT("head"), EPhysBodyOp::PBO_None);
			}
		}
		HandledPawn = Pawn;
		UE_LOG(LogSSFirstPerson, Log, TEXT("First-person camera active for %s (body view)."), *Pawn->GetName());
		return;
	}
	USkeletalMesh* ArmsMesh = CVarArms.GetValueOnGameThread() != 0 ? LoadObject<USkeletalMesh>(nullptr, *ArmsMeshPath(0)) : nullptr;
	if (ArmsMesh)
	{
		// The arms put their left hand on the held weapon's grip socket (W2): the Fab pack's own left hand
		// sits where its M4 handguard was.
		USSHandIKMeshComponent* HandIKArms = NewObject<USSHandIKMeshComponent>(Pawn, TEXT("SS_FirstPersonArms"));
		// These arms have no grip animation of their own: the wrist solve puts the hand on the weapon, and
		// the hand itself is then turned to the grip socket (W2, Session 070) so the palm is not left open.
		HandIKArms->bRotateHandToGrip = true;
		Arms = HandIKArms;
		Arms->SetupAttachment(Camera);
		Arms->SetSkeletalMesh(ArmsMesh);
		Arms->SetOnlyOwnerSee(true);
		Arms->SetCastShadow(false);
		Arms->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Arms->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
		Arms->SetAnimationMode(EAnimationMode::AnimationSingleNode);
		// The packs' rest poses sit away from the animated arms: without larger bounds the arms were culled
		// in view (pistol set). Standard for first-person arms.
		Arms->SetBoundsScale(20.f);
		Arms->RegisterComponent();
		ArmsSet = 0;
		Play(Clip(ArmsSet, TEXT("Idle")), true); // the grip is measured from this pose next tick
		bGripMeasured = false;
	}

	ViewModel = NewObject<UStaticMeshComponent>(Pawn, TEXT("SS_ViewModel"));
	if (Arms)
	{
		ViewModel->SetupAttachment(Arms, WeaponBone);
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
		// Hidden meshes stop refreshing bones by default, so the body's shadow froze in the bind pose (the
		// producer's "da Vinci shadow"). Keep the local body posing so its shadow (and the gear and weapon
		// that follow it) matches the soldier.
		Character->GetMesh()->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
	}
	HandledPawn = Pawn;
	LastMagazine = -1;
	UE_LOG(LogSSFirstPerson, Log, TEXT("First-person camera active for %s (arms: %s)."), *Pawn->GetName(), Arms ? TEXT("Fab FPS pack") : TEXT("none"));
}

bool USSFirstPersonSubsystem::GetViewModelMuzzle(FVector& OutLocation) const
{
	static const FName MuzzleSocket(TEXT("Muzzle"));
	if (!ViewModel || !ViewModel->GetStaticMesh())
	{
		return false;
	}
	if (ViewModel->IsVisible() && ViewModel->DoesSocketExist(MuzzleSocket))
	{
		OutLocation = ViewModel->GetSocketLocation(MuzzleSocket);
		return true;
	}
	if (const USceneComponent* View = ViewModel->GetAttachParent() ? ViewModel->GetAttachmentRoot() : nullptr)
	{
		// Scoped (view model hidden) or no socket: from just ahead of and below the eye, along the view.
		const APlayerController* Player = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
		if (Player && Player->PlayerCameraManager)
		{
			const FRotator Rotation = Player->PlayerCameraManager->GetCameraRotation();
			OutLocation = Player->PlayerCameraManager->GetCameraLocation() + Rotation.Vector() * 60.f - FRotationMatrix(Rotation).GetUnitAxis(EAxis::Z) * 6.f;
			return true;
		}
	}
	return false;
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
	if (USSHandIKMeshComponent* HandIK = Cast<USSHandIKMeshComponent>(Arms))
	{
		// Draw, holster and reload move the left hand themselves.
		HandIK->SetHandIKSuppressed(HandIK->IsSuppressingAnimationName(Sequence->GetName()));
	}
	OneShotRemaining = bLoop ? 0.f : Sequence->GetPlayLength();
}

void USSFirstPersonSubsystem::UpdateArmsAnimation(APawn* Pawn, float DeltaTime)
{
	const USSLocalHudState* State = GetWorld()->GetSubsystem<USSLocalHudState>();
	const int32 Magazine = State ? State->Magazine : -1;

	// Reload: follow the body's Lyra reload montage (the gameplay authority), scaled to its length.
	const ACharacter* Character = Cast<ACharacter>(Pawn);
	const UAnimInstance* Body = Character && Character->GetMesh() ? Character->GetMesh()->GetAnimInstance() : nullptr;
	const UAnimMontage* Montage = Body ? Body->GetCurrentActiveMontage() : nullptr;
	const bool bReloading = Montage && Montage->GetName().Contains(TEXT("Reload"));
	if (bReloading && !bReloadSeen)
	{
		if (UAnimSequence* Reload = Clip(ArmsSet, Magazine == 0 ? TEXT("Reload_Empty") : TEXT("Reload")))
		{
			Play(Reload, false);
			const float Rate = Reload->GetPlayLength() / FMath::Max(0.3f, Montage->GetPlayLength());
			Arms->SetPlayRate(Rate);
			OneShotRemaining = Reload->GetPlayLength() / Rate;
		}
	}
	bReloadSeen = bReloading;

	// Fire: the magazine count dropped.
	if (Magazine >= 0 && LastMagazine >= 0 && Magazine < LastMagazine && !bReloading)
	{
		Play(Clip(ArmsSet, TEXT("Fire")), false);
		Recoil = 1.f;
	}
	LastMagazine = Magazine;

	OneShotRemaining -= DeltaTime;
	if (OneShotRemaining > 0.f)
	{
		return; // let draw / fire / reload finish
	}
	Arms->SetPlayRate(1.f);
	Play(Clip(ArmsSet, TEXT("Idle")), true); // a held pose; walk, sway and sprint are procedural (UpdateViewModel)
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
				if (const USkeletalMeshComponent* Skel = Cast<USkeletalMeshComponent>(Prim))
				{
					for (const FName& Socket : Skel->GetAllSocketNames())
					{
						const FTransform T = Skel->GetSocketTransform(Socket, RTS_Component);
						UE_LOG(LogSSFirstPerson, Log, TEXT("  socket %s.%s loc=%s rot=%s"), *Prim->GetName(), *Socket.ToString(),
							*T.GetLocation().ToString(), *T.Rotator().ToString());
					}
				}
				if (const UStaticMeshComponent* Static = Cast<UStaticMeshComponent>(Prim); Static && Static->DoesSocketExist(TEXT("Muzzle")))
				{
					UE_LOG(LogSSFirstPerson, Log, TEXT("  static %s muzzle(component)=%s relrot=%s parent=%s"), *Prim->GetName(),
						*Static->GetSocketTransform(TEXT("Muzzle"), RTS_Component).GetLocation().ToString(),
						*Static->GetRelativeRotation().ToString(), *GetNameSafe(Static->GetAttachParent()));
				}
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
	if (const ACharacter* Character = Cast<ACharacter>(Pawn); Character && Character->GetMesh()->IsSimulatingPhysics())
	{
		// Dead (ASSCharacter ragdolls the body): the arms and weapon leave the view.
		if (Arms) { Arms->SetVisibility(false, true); }
		if (ViewModel) { ViewModel->SetVisibility(false); }
		return;
	}
	// Looking through a magnified scope: the eyepiece view replaces the weapon (HUD overlay, narrowed FOV).
	const USSLocalHudState* Optics = GetWorld()->GetSubsystem<USSLocalHudState>();
	const bool bScoped = *bAiming && Optics && Optics->OpticMagnification > 1.f;
	if (Arms && Arms->IsVisible() == bScoped) { Arms->SetVisibility(!bScoped, true); }
	if (ViewModel && ViewModel->IsVisible() == bScoped) { ViewModel->SetVisibility(!bScoped); }
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
					// Undo the arms-view hiding if this session switched view models:
					// body view shows the soldier parts and the held weapon.
					Part->SetHiddenInGame(false);
				}
			}
		}
		return;
	}
	// The held weapon is a cosmetic actor attached to the pawn's body mesh
	// (Lyra equipment). Show its mesh in first person and hide the body copy
	// from the owner. Soldier body parts are skeletal, so they never match.
	UStaticMesh* Held = nullptr;		TArray<AActor*> Attached;
		Pawn->GetAttachedActors(Attached, true, true);
		for (AActor* Actor : Attached)
		{
			// Skinned, not skeletal: the Quantum body parts are UPoseableMeshComponents
			// (ADR-042) and a USkeletalMeshComponent cast misses them, which put the local
			// player's own body inside the first-person camera.
			TInlineComponentArray<USkinnedMeshComponent*> Bodies(Actor);
			for (USkinnedMeshComponent* Body : Bodies)
			{
				// Hidden locally (this subsystem only runs for the local player),
				// shadow kept: owner-no-see alone let the beret through from inside.
				Body->SetOwnerNoSee(true);
				Body->bCastHiddenShadow = true;
				Body->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
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
		// Pistols use the G17 arms: swap the arms mesh when the held weapon's class changes, and measure
		// the grip again in the new idle pose.
		if (Held != LastHeld.Get())
		{
			const int32 WantSet = Held && Held->GetBoundingBox().GetSize().X < PistolMaxLength ? 1 : 0;
			if (WantSet != ArmsSet)
			{
				if (USkeletalMesh* SetMesh = LoadObject<USkeletalMesh>(nullptr, *ArmsMeshPath(WantSet)))
				{
					ArmsSet = WantSet;
					Arms->SetSkeletalMesh(SetMesh);
					Current = nullptr;
					OneShotRemaining = 0.f;
					Play(Clip(ArmsSet, TEXT("Idle")), true);
					bGripMeasured = false;
					LastHeld = Held; // the draw plays once the grip is measured
					return;
				}
			}
		}

		// Measure the grip once per arms set, in the idle pose. Our meshes have their origin at the pistol
		// grip, +X to the muzzle. A rifle: grip at the right hand's knuckles, barrel toward the left hand. A
		// pistol (small, and the support hand wraps the grip): on the pack's own weapon bone, where its
		// pistol sat, pointing along the view. Upright; the transform is then kept on the weapon bone so
		// the pack's reloads carry the weapon.
		if (!bGripMeasured && Arms->GetBoneIndex(WeaponBone) != INDEX_NONE && Arms->GetBoneIndex(RightGripBone) != INDEX_NONE)
		{
			const FVector Right = Arms->GetBoneLocation(RightGripBone, EBoneSpaces::ComponentSpace);
			const FVector Left = Arms->GetBoneLocation(LeftGripBone, EBoneSpaces::ComponentSpace);
			// Rifle orientation: the pack's weapon bone, as its own M4 sat on it - its axis nearest the view's
			// forward (the arms face +Y) and the one nearest up. The line between the knuckles (used before) runs
			// up and across the body, and pointed the rifle's muzzle up and to the left (producer: "weapons
			// sitting properly in the hands - still not right").
			const FTransform BoneCS = Arms->GetBoneTransform(Arms->GetBoneIndex(WeaponBone), FTransform::Identity);
			auto Nearest = [&BoneCS](const FVector& Want, const FVector& Exclude)
			{
				FVector Best = FVector::ZeroVector;
				float BestDot = 0.f;
				for (const EAxis::Type Axis : { EAxis::X, EAxis::Y, EAxis::Z })
				{
					const FVector V = BoneCS.GetUnitAxis(Axis);
					if (FMath::Abs(FVector::DotProduct(V, Exclude)) > 0.9f)
					{
						continue;
					}
					const float D = FVector::DotProduct(V, Want);
					if (FMath::Abs(D) > FMath::Abs(BestDot))
					{
						BestDot = D;
						Best = V * FMath::Sign(D);
					}
				}
				return Best;
			};
			const FVector BoneForward = Nearest(FVector(0.f, 1.f, 0.f), FVector::ZeroVector);
			const FVector BoneUp = Nearest(FVector::UpVector, BoneForward);
			const FVector Forward = ArmsSet == 1 ? FVector(0.f, 1.f, 0.f) : BoneForward;
			const FVector Up = ArmsSet == 1 || BoneUp.IsNearlyZero() ? FVector::UpVector : BoneUp;
			if (!Forward.IsNearlyZero())
			{
				const FMatrix Frame = FRotationMatrix::MakeFromXZ(Forward, Up);
				// Rifles: our trigger on the pack weapon's trigger bone, so the grip sits in the right hand exactly as
				// the pack's own rifle did (the knuckle estimate needed hand-tuned offsets and still missed).
				const bool bTriggerBone = ArmsSet == 0 && Arms->GetBoneIndex(TriggerBone) != INDEX_NONE;
				const FVector Anchor = ArmsSet == 1 ? Arms->GetBoneLocation(WeaponBone, EBoneSpaces::ComponentSpace)
					: bTriggerBone ? Arms->GetBoneLocation(TriggerBone, EBoneSpaces::ComponentSpace) : Right;
				const FTransform Grip(Frame.Rotator(), Anchor);
				const FTransform Bone = Arms->GetBoneTransform(Arms->GetBoneIndex(WeaponBone), FTransform::Identity);
				GripOnWeaponBone = Grip.GetRelativeTransform(Bone);
				bGripMeasured = true;
				Play(Clip(ArmsSet, TEXT("Draw")), false);
				UE_LOG(LogSSFirstPerson, Log, TEXT("Arms (%s) grip measured: right %s left %s -> on %s %s"), ArmsSets[ArmsSet],
					*Right.ToString(), *Left.ToString(), *WeaponBone.ToString(), *GripOnWeaponBone.ToString());
			}
		}
		if (Held != LastHeld.Get())
		{
			LastHeld = Held;
			if (bGripMeasured)
			{
				Play(Clip(ArmsSet, TEXT("Draw")), false); // weapon switch
			}
		}
		UpdateArmsAnimation(Pawn, DeltaTime);

		// The arms face +Y in their mesh (UE convention): turn to camera +X and put the animated
		// camera bone on the eye.
		const FRotator Facing(0.f, -90.f, 0.f);
		const FVector CameraInComponent = Arms->GetBoneIndex(CameraBone) != INDEX_NONE
			? Arms->GetBoneLocation(CameraBone, EBoneSpaces::ComponentSpace) : FVector(0.f, 0.f, 160.f);
		const FVector Eye = Facing.RotateVector(CameraInComponent);

		// Procedural layer: walk bob, sprint lower, fire kick (the pack's fire clip adds its own).
		const float Speed = Pawn->GetVelocity().Size2D();
		SprintAlpha = FMath::FInterpTo(SprintAlpha, (Speed > 450.f && !*bAiming) ? 1.f : 0.f, DeltaTime, 6.f);
		BobPhase += DeltaTime * FMath::Lerp(6.f, 9.f, SprintAlpha) * FMath::Clamp(Speed / 350.f, 0.f, 1.f);
		const float Bob = FMath::Clamp(Speed / 400.f, 0.f, 1.f) * SwayScale;
		const FVector BobOffset(0.f, FMath::Sin(BobPhase) * 0.9f * Bob, -FMath::Abs(FMath::Sin(BobPhase)) * 1.1f * Bob);
		Recoil = FMath::FInterpTo(Recoil, 0.f, DeltaTime, 14.f);
		const FVector Kick(-1.2f * Recoil * SwayScale, 0.f, 0.f);
		const FVector SprintOffset(-4.f, 3.f, -6.f);
		const FRotator SprintTilt(-22.f * SprintAlpha, 18.f * SprintAlpha, -12.f * SprintAlpha);
		Arms->SetRelativeLocationAndRotation(-Eye + ParseVector(ArmsSet == 1 ? CVarPistolArmsOffset : CVarArmsOffset) + SwayOffset + BobOffset + Kick + SprintOffset * SprintAlpha,
			(SprintTilt.Quaternion() * Facing.Quaternion()).Rotator());

		const FVector Rot = ParseVector(CVarWeaponRotation);
		const FTransform Tune(FRotator(Rot.X, Rot.Y, Rot.Z), ParseVector(ArmsSet == 1 ? CVarPistolOffset : CVarWeaponOffset));
		ViewModel->SetRelativeTransform(Tune * GripOnWeaponBone);

		// Aiming: put the weapon's sight on the line of sight (camera X axis) with eye relief. An optic has a
		// Sight socket. Iron sights (the pistols: producer, "pistol ... has no iron sights") have none: their
		// sight line runs along the top of the mesh, so the rear sight (the top, a fifth of the way from the
		// back) goes on the eye line, held at arm's length.
		static const FName SightSocket(TEXT("Sight"));
		const USceneComponent* View = Arms->GetAttachParent();
		const UStaticMesh* HeldMesh = ViewModel->GetStaticMesh();
		if (View && AimAlpha > 0.f && HeldMesh)
		{
			const bool bOptic = ViewModel->DoesSocketExist(SightSocket);
			FVector SightWorld;
			if (bOptic)
			{
				SightWorld = ViewModel->GetSocketLocation(SightSocket);
			}
			else
			{
				const FBox Box = HeldMesh->GetBoundingBox();
				SightWorld = ViewModel->GetComponentTransform().TransformPosition(
					FVector(Box.Min.X + Box.GetSize().X * 0.2f, Box.GetCenter().Y, Box.Max.Z - 0.2f));
			}
			const FVector Sight = View->GetComponentTransform().InverseTransformPosition(SightWorld);
			const float Relief = bOptic ? CVarEyeRelief.GetValueOnGameThread() : CVarIronRelief.GetValueOnGameThread();
			const FVector Correction(bOptic ? FMath::Max(0.f, Relief - Sight.X) : Relief - Sight.X, -Sight.Y, -Sight.Z);
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
