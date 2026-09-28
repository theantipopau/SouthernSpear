// Copyright Southern Spear. All Rights Reserved.

#include "SSCharacter.h"

#include "SSHandIKMeshComponent.h"

#include "AbilitySystem/LyraAbilitySystemComponent.h"
#include "Character/LyraPawnExtensionComponent.h"
#include "Components/AudioComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/CollisionProfile.h"
#include "Components/ChildActorComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "GameFramework/PlayerController.h"
#include "GameplayCueInterface.h"
#include "GameplayEffectTypes.h"
#include "InputAction.h"
#include "Kismet/GameplayStatics.h"
#include "Particles/ParticleSystem.h"
#include "Sound/SoundBase.h"
#include "InputMappingContext.h"
#include "Net/UnrealNetwork.h"
#include "PhysicalMaterials/PhysicalMaterial.h"
#include "PhysicsEngine/BodyInstance.h"
#include "SSCharacterMovementComponent.h"
#include "SSLocalHudState.h"
#include "SSLyraReflection.h"
#include "SSFirstPersonSubsystem.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/PlayerState.h"
#include "TimerManager.h"

namespace
{
	const TCHAR* ContextPath = TEXT("/SSExp_ObjectiveAssault/Input/IMC_SS_Tactical.IMC_SS_Tactical");

	const UInputAction* Action(const TCHAR* Name)
	{
		return LoadObject<UInputAction>(nullptr, *FString::Printf(TEXT("/SSExp_ObjectiveAssault/Input/%s.%s"), Name, Name));
	}
}

ASSCharacter::ASSCharacter(const FObjectInitializer& ObjectInitializer)
	// The body mesh puts its left hand on the held weapon's grip socket (W2); the visible soldier parts
	// follow it by leader pose.
	: Super(ObjectInitializer.SetDefaultSubobjectClass<USSCharacterMovementComponent>(ACharacter::CharacterMovementComponentName)
		.SetDefaultSubobjectClass<USSHandIKMeshComponent>(ACharacter::MeshComponentName))
{
}

void ASSCharacter::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ASSCharacter, Lean);
}

void ASSCharacter::BeginPlay()
{
	Super::BeginPlay();
	// Hit zones: head and neck, torso (pelvis, spine, clavicles), limbs (everything else).
	UPhysicalMaterial* Zones[3] = { Cast<UPhysicalMaterial>(HeadZone.TryLoad()), Cast<UPhysicalMaterial>(TorsoZone.TryLoad()),
		Cast<UPhysicalMaterial>(LimbZone.TryLoad()) };
	if (Zones[0] && Zones[1] && Zones[2])
	{
		ZoneMaterials = { Zones[0], Zones[1], Zones[2] };
		for (FBodyInstance* Body : GetMesh()->Bodies)
		{
			const FString Bone = GetMesh()->GetBoneName(Body ? Body->InstanceBoneIndex : INDEX_NONE).ToString().ToLower();
			if (!Body || Bone.IsEmpty() || Bone == TEXT("none"))
			{
				continue;
			}
			const int32 Zone = (Bone.StartsWith(TEXT("head")) || Bone.StartsWith(TEXT("neck"))) ? 0
				: (Bone.StartsWith(TEXT("pelvis")) || Bone.StartsWith(TEXT("spine")) || Bone.StartsWith(TEXT("clavicle"))) ? 1 : 2;
			Body->SetPhysMaterialOverride(Zones[Zone]);
			++ZoneCounts[Zone];
		}
		UE_LOG(LogTemp, Log, TEXT("SSHitZones %s head=%d torso=%d limb=%d"), *GetName(), ZoneCounts[0], ZoneCounts[1], ZoneCounts[2]);
	}
	if (UClass* PartsClass = SoldierPartsClass.TryLoadClass<AActor>())
	{
		Soldier = NewObject<UChildActorComponent>(this, TEXT("SS_Soldier"));
		Soldier->SetupAttachment(GetMesh());
		Soldier->SetChildActorClass(PartsClass);
		Soldier->RegisterComponent();
		// Presentation only, like Lyra's cosmetic parts (CollisionMode=NoCollision): with collision the
		// uniform wrapped the body and blocked the soldier's own sight and weapon traces (bots never fired).
		if (AActor* Parts = Soldier->GetChildActor())
		{
			Parts->SetActorEnableCollision(false);
			TInlineComponentArray<UPrimitiveComponent*> Prims(Parts);
			for (UPrimitiveComponent* Prim : Prims)
			{
				Prim->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			}
		}
	}
	// Lyra's hero component clears and rebuilds the input mappings while the
	// pawn initialises, so keep ours present (cheap check, twice a second).
	if (IsLocallyControlled() || GetNetMode() == NM_Standalone)
	{
		GetWorldTimerManager().SetTimer(InputContextTimer, this, &ASSCharacter::EnsureInputContext, 0.5f, true, 0.1f);
	}
}

void ASSCharacter::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	GetWorldTimerManager().ClearTimer(InputContextTimer);
	Super::EndPlay(EndPlayReason);
}

void ASSCharacter::EnsureInputContext()
{
	const APlayerController* Player = Cast<APlayerController>(GetController());
	const ULocalPlayer* Local = Player ? Player->GetLocalPlayer() : nullptr;
	UEnhancedInputLocalPlayerSubsystem* Input = Local ? Local->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>() : nullptr;
	static TWeakObjectPtr<const UInputMappingContext> Context;
	if (!Context.IsValid())
	{
		Context = LoadObject<UInputMappingContext>(nullptr, ContextPath);
	}
	if (Input && Context.IsValid() && !Input->HasMappingContext(Context.Get()))
	{
		Input->AddMappingContext(Context.Get(), /*Priority=*/ 2); // above Lyra's (0/1): takes Shift, Q, E
	}
}

void ASSCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(PlayerInputComponent);
	if (!Input)
	{
		return;
	}
	struct FBinding { const TCHAR* Name; void (ASSCharacter::*Handler)(const FInputActionValue&); };
	const FBinding Bindings[] = {
		{ TEXT("IA_SS_Sprint"), &ASSCharacter::OnSprint },
		{ TEXT("IA_SS_Walk"), &ASSCharacter::OnWalk },
		{ TEXT("IA_SS_Aim"), &ASSCharacter::OnAim },
		{ TEXT("IA_SS_LeanLeft"), &ASSCharacter::OnLeanLeft },
		{ TEXT("IA_SS_LeanRight"), &ASSCharacter::OnLeanRight },
	};
	for (const FBinding& Binding : Bindings)
	{
		if (const UInputAction* IA = Action(Binding.Name))
		{
			// Started and Completed carry the held state (true / false).
			Input->BindAction(IA, ETriggerEvent::Started, this, Binding.Handler);
			Input->BindAction(IA, ETriggerEvent::Completed, this, Binding.Handler);
		}
	}
}

void ASSCharacter::OnSprint(const FInputActionValue& Value)
{
	if (USSCharacterMovementComponent* Movement = Cast<USSCharacterMovementComponent>(GetCharacterMovement()))
	{
		Movement->SetWantsSprint(Value.Get<bool>());
	}
}

void ASSCharacter::OnWalk(const FInputActionValue& Value)
{
	if (USSCharacterMovementComponent* Movement = Cast<USSCharacterMovementComponent>(GetCharacterMovement()))
	{
		Movement->SetWantsWalk(Value.Get<bool>());
	}
}

void ASSCharacter::OnAim(const FInputActionValue& Value)
{
	if (USSCharacterMovementComponent* Movement = Cast<USSCharacterMovementComponent>(GetCharacterMovement()))
	{
		Movement->SetWantsAim(Value.Get<bool>());
	}
}

void ASSCharacter::OnLeanLeft(const FInputActionValue& Value)
{
	bLeanLeftHeld = Value.Get<bool>();
	UpdateLean();
}

void ASSCharacter::OnLeanRight(const FInputActionValue& Value)
{
	bLeanRightHeld = Value.Get<bool>();
	UpdateLean();
}

void ASSCharacter::UpdateLean()
{
	const int8 Wanted = bLeanLeftHeld == bLeanRightHeld ? 0 : (bLeanLeftHeld ? -1 : 1);
	if (Wanted != Lean)
	{
		Lean = Wanted; // local prediction; the server's value replicates back
		ServerSetLean(Wanted);
	}
}

void ASSCharacter::ServerSetLean_Implementation(int8 NewLean)
{
	Lean = FMath::Clamp<int8>(NewLean, -1, 1);
}

void ASSCharacter::HandleGameplayCue(UObject* Self, FGameplayTag GameplayCueTag, EGameplayCueEvent::Type EventType, const FGameplayCueParameters& Parameters)
{
	Super::HandleGameplayCue(Self, GameplayCueTag, EventType, Parameters);
	static const FGameplayTag RifleFire = FGameplayTag::RequestGameplayTag(TEXT("GameplayCue.Weapon.Rifle.Fire"), false);
	if (EventType == EGameplayCueEvent::Executed && RifleFire.IsValid() && GameplayCueTag.MatchesTagExact(RifleFire)
		&& GetNetMode() != NM_DedicatedServer)
	{
		PlayRifleFire();
		return;
	}
	static const FGameplayTag DamageTaken = FGameplayTag::RequestGameplayTag(TEXT("GameplayCue.Character.DamageTaken"), false);
	if (EventType != EGameplayCueEvent::Executed || !DamageTaken.IsValid() || !GameplayCueTag.MatchesTag(DamageTaken)
		|| GetNetMode() == NM_DedicatedServer)
	{
		return;
	}
	if (!BloodSystem)
	{
		BloodSystem = Cast<UParticleSystem>(BloodEffect.TryLoad());
	}
	const FHitResult* Hit = Parameters.EffectContext.GetHitResult();
	const FVector Where = Hit && !Hit->ImpactPoint.IsZero() ? FVector(Hit->ImpactPoint)
		: (!Parameters.Location.IsZero() ? FVector(Parameters.Location) : GetActorLocation() + FVector(0.f, 0.f, 40.f));
	// Spray away from the shooter, out of the exit side.
	const FVector Shot = Hit && !Hit->TraceStart.Equals(Hit->TraceEnd) ? (FVector(Hit->TraceEnd) - FVector(Hit->TraceStart)).GetSafeNormal()
		: -GetActorForwardVector();
	LastShotDirection = Shot; // the ragdoll push if this hit kills
	// Hit direction for the local player's HUD.
	if (IsLocallyControlled() && IsPlayerControlled())
	{
		if (USSLocalHudState* Hud = GetWorld() ? GetWorld()->GetSubsystem<USSLocalHudState>() : nullptr)
		{
			const AActor* Causer = Parameters.EffectCauser.Get();
			Hud->LastHitTime = GetWorld()->GetTimeSeconds();
			Hud->LastHitFrom = Hit && !Hit->TraceStart.IsZero() ? FVector(Hit->TraceStart) : (Causer ? Causer->GetActorLocation() : Where);
			UE_LOG(LogTemp, Verbose, TEXT("SSHitDir from %s (hit result: %d)"), *Hud->LastHitFrom.ToString(), Hit != nullptr);
		}
	}
	// Not on the local player's own body: the burst would spawn in front of the first-person camera
	// (seen as pale sprites filling the view); the HUD's clay flash and hit arrow cover it.
	if (BloodSystem && !(IsLocallyControlled() && IsPlayerControlled()))
	{
		UGameplayStatics::SpawnEmitterAtLocation(GetWorld(), BloodSystem, Where, Shot.Rotation(), FVector(0.6f), /*bAutoDestroy=*/ true);
		UE_LOG(LogTemp, Verbose, TEXT("SSBlood %s at %s (hit result: %d)"), *GetName(), *Where.ToString(), Hit != nullptr);
	}
}

void ASSCharacter::PlayRifleFire()
{
	auto LoadAll = [](const TArray<FSoftObjectPath>& Paths, TArray<TObjectPtr<USoundBase>>& Out)
	{
		if (Out.Num() == 0)
		{
			for (const FSoftObjectPath& Path : Paths)
			{
				if (USoundBase* Sound = Cast<USoundBase>(Path.TryLoad()))
				{
					Out.Add(Sound);
				}
			}
		}
	};
	LoadAll(RifleCloseShots, LoadedCloseShots);
	LoadAll(RifleDistantShots, LoadedDistantShots);
	if (!LoadedTail)
	{
		LoadedTail = Cast<USoundBase>(RifleTail.TryLoad());
	}
	if (LoadedCloseShots.Num() == 0)
	{
		return; // no recordings: Lyra's sound stays
	}

	// Mute Lyra's rifle MetaSound: Lyra's weapon Blueprint spawns it once, attached to (and owned by) the pawn,
	// and re-triggers it per shot. Matched by sound name so footsteps and other pawn audio are untouched.
	int32 Muted = 0;
	TInlineComponentArray<UAudioComponent*> Audio(this);
	for (UAudioComponent* Component : Audio)
	{
		if (Component->Sound && Component->Sound->GetName().StartsWith(TEXT("MSS_Weapons_Rifle")) && Component->VolumeMultiplier > 0.f)
		{
			Component->SetVolumeMultiplier(0.f);
			++Muted;
		}
	}

	const FVector Muzzle = GetMesh() && GetMesh()->DoesSocketExist(TEXT("weapon_r")) ? GetMesh()->GetSocketLocation(TEXT("weapon_r"))
		: GetPawnViewLocation();
	// Which weapon, for this listener: the other side is MAF (AK recordings), a support weapon is pitched down.
	LoadAll(OpforCloseShots, LoadedOpforShots);
	const APlayerController* Listener = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	const ESSTeamId ListenerTeam = SSLyraReflection::TeamOf(Listener ? Listener->PlayerState.Get() : nullptr);
	const ESSTeamId ShooterTeam = SSLyraReflection::TeamOf(GetPlayerState());
	const bool bOpposing = ListenerTeam != ESSTeamId::None && ShooterTeam != ESSTeamId::None && ListenerTeam != ShooterTeam;
	FString Held;
	TArray<AActor*> Attached;
	GetAttachedActors(Attached, true, true);
	for (const AActor* Actor : Attached)
	{
		TInlineComponentArray<UStaticMeshComponent*> Meshes(Actor);
		for (const UStaticMeshComponent* WeaponMesh : Meshes)
		{
			if (WeaponMesh->GetStaticMesh() && Held.IsEmpty())
			{
				Held = WeaponMesh->GetStaticMesh()->GetName();
			}
		}
	}
	const bool bSupport = Held.Contains(TEXT("A89")) || Held.Contains(TEXT("MAF_S"));
	const TArray<TObjectPtr<USoundBase>>& CloseSet = bOpposing && LoadedOpforShots.Num() > 0 ? LoadedOpforShots : LoadedCloseShots;
	USoundBase* Close = CloseSet[FMath::RandHelper(CloseSet.Num())];
	const float Pitch = FMath::FRandRange(0.97f, 1.03f) * (bSupport ? SupportPitch : 1.f);
	// AI pawns are "locally controlled" on the server; only the human shooter hears the unspatialised close shot.
	const bool bShooterIsListener = IsLocallyControlled() && IsPlayerControlled();
	if (bShooterIsListener)
	{
		UGameplayStatics::PlaySound2D(this, Close, 1.f, Pitch);
	}
	else
	{
		FSoundAttenuationSettings Near;
		Near.FalloffDistance = 6000.f; // 60 m
		Near.AttenuationShapeExtents = FVector(400.f);
		if (UAudioComponent* Shot = UGameplayStatics::SpawnSoundAtLocation(this, Close, Muzzle, FRotator::ZeroRotator, 1.f, Pitch))
		{
			Shot->AdjustAttenuation(Near);
		}
		if (LoadedDistantShots.Num() > 0)
		{
			FSoundAttenuationSettings Far;
			Far.FalloffDistance = 60000.f; // heard across the map (600 m)
			Far.AttenuationShapeExtents = FVector(1500.f);
			if (UAudioComponent* Distant = UGameplayStatics::SpawnSoundAtLocation(this, LoadedDistantShots[FMath::RandHelper(LoadedDistantShots.Num())],
				Muzzle, FRotator::ZeroRotator, 0.7f, Pitch))
			{
				Distant->AdjustAttenuation(Far);
			}
		}
	}
	if (LoadedTail)
	{
		FSoundAttenuationSettings Tail;
		Tail.FalloffDistance = 30000.f;
		Tail.AttenuationShapeExtents = FVector(2000.f);
		if (UAudioComponent* Echo = UGameplayStatics::SpawnSoundAtLocation(this, LoadedTail, Muzzle, FRotator::ZeroRotator, bShooterIsListener ? 0.45f : 0.3f))
		{
			Echo->AdjustAttenuation(Tail);
		}
	}
	UE_LOG(LogTemp, Verbose, TEXT("SSRifleAudio %s local=%d muted=%d opposing=%d weapon=%s support=%d"), *GetName(), bShooterIsListener, Muted,
		bOpposing, *Held, bSupport);
}

bool ASSCharacter::ShouldAcceptGameplayCue(UObject* Self, FGameplayTag GameplayCueTag, EGameplayCueEvent::Type EventType, const FGameplayCueParameters& Parameters)
{
	// Lyra's death cue bursts the body into cubes (NS_DeathCubes); the soldier ragdolls instead.
	static const FGameplayTag DeathCue = FGameplayTag::RequestGameplayTag(TEXT("GameplayCue.Character.Death"), false);
	if (DeathCue.IsValid() && GameplayCueTag.MatchesTagExact(DeathCue))
	{
		return false;
	}
	// A weapon fire cue: its muzzle flash and tracer start at the Muzzle socket of Lyra's hidden weapon mesh.
	// Put that socket on the barrel the viewer actually sees first (called before any cue effect spawns).
	if (EventType == EGameplayCueEvent::Executed && GameplayCueTag.ToString().StartsWith(TEXT("GameplayCue.Weapon."))
		&& GameplayCueTag.ToString().EndsWith(TEXT(".Fire")) && GetNetMode() != NM_DedicatedServer)
	{
		AlignLyraMuzzle();
	}
	// Lyra's spawn-in cue (GCNL_Spawning) materialises the body out of cubes (producer: "the spawn weird
	// cubes needs to go"). Its tag lives in the ShooterCore feature, so match it by name.
	if (GameplayCueTag.ToString().Contains(TEXT("Spawn")))
	{
		UE_LOG(LogTemp, Log, TEXT("SSCue refused %s on %s"), *GameplayCueTag.ToString(), *GetName());
		return false;
	}
	return Super::ShouldAcceptGameplayCue(Self, GameplayCueTag, EventType, Parameters);
}

void ASSCharacter::AlignLyraMuzzle()
{
	// Producer: "where the bullets come out of the weapon, they are coming all over the shop - not out of the
	// barrel". Lyra's weapon actor keeps its own (hidden) skeletal rifle, whose Muzzle socket anchors the fire
	// cue's flash and tracer; our A-series mesh (visible) hangs off it with a different length (A88: ~28 cm
	// shorter), and in first person the whole actor sits in the hidden third-person hands, not in view. Move the
	// hidden mesh so its Muzzle lands on the visible barrel (first person: the view model's), and move its
	// visible children back so they stay where they were. Presentation only: hit traces start at the camera.
	static const FName MuzzleSocket(TEXT("Muzzle"));
	TArray<AActor*> Attached;
	GetAttachedActors(Attached, true, true);
	for (AActor* Actor : Attached)
	{
		TInlineComponentArray<USkeletalMeshComponent*> Skels(Actor);
		for (USkeletalMeshComponent* LyraMesh : Skels)
		{
			if (!LyraMesh->DoesSocketExist(MuzzleSocket))
			{
				continue;
			}
			TInlineComponentArray<UStaticMeshComponent*> Visuals(Actor);
			UStaticMeshComponent* Visual = nullptr;
			for (UStaticMeshComponent* Candidate : Visuals)
			{
				if (Candidate->GetStaticMesh() && Candidate->DoesSocketExist(MuzzleSocket))
				{
					Visual = Candidate;
					break;
				}
			}
			FVector Target;
			const USSFirstPersonSubsystem* FirstPerson = IsLocallyControlled() && IsPlayerControlled() && GetWorld()
				? GetWorld()->GetSubsystem<USSFirstPersonSubsystem>() : nullptr;
			if (FirstPerson && FirstPerson->GetViewModelMuzzle(Target))
			{
				// first person: the barrel in view (or, looking through a scope, just ahead of the eye)
			}
			else if (Visual)
			{
				Target = Visual->GetSocketLocation(MuzzleSocket);
			}
			else
			{
				continue;
			}
			const FVector Delta = Target - LyraMesh->GetSocketLocation(MuzzleSocket);
			if (Delta.SizeSquared() < 0.25f)
			{
				continue;
			}
			LyraMesh->AddWorldOffset(Delta);
			for (UStaticMeshComponent* Child : Visuals)
			{
				if (Child->IsAttachedTo(LyraMesh))
				{
					Child->AddWorldOffset(-Delta);
				}
			}
		}
	}
}

void ASSCharacter::OnDeathStarted(AActor* OwningActor)
{
	Super::OnDeathStarted(OwningActor); // movement and capsule collision off
	if (GetNetMode() != NM_DedicatedServer)
	{
		GetWorldTimerManager().SetTimer(RagdollTimer, this, &ASSCharacter::StartRagdoll, FMath::Max(0.01f, RagdollDelay), false);
	}
}

void ASSCharacter::StartRagdoll()
{
	USkeletalMeshComponent* Body = GetMesh();
	if (!Body || !Body->GetPhysicsAsset() || Body->IsSimulatingPhysics())
	{
		return;
	}
	if (UAnimInstance* Anim = Body->GetAnimInstance())
	{
		Anim->StopAllMontages(0.1f);
	}
	// Presentation only: each machine simulates its own copy; nothing about it replicates.
	Body->SetCollisionProfileName(FName(TEXT("Ragdoll")));
	Body->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	Body->SetAllBodiesSimulatePhysics(true);
	Body->SetSimulatePhysics(true);
	Body->WakeAllRigidBodies();
	Body->bBlendPhysics = true;
	UE_LOG(LogTemp, Log, TEXT("SSRagdoll %s push %s"), *GetName(), *LastShotDirection.ToCompactString());
	const FVector Push = (LastShotDirection.IsNearlyZero() ? -GetActorForwardVector() : LastShotDirection) * RagdollPush;
	static const FName UpperBody(TEXT("spine_03"));
	if (Body->GetBoneIndex(UpperBody) != INDEX_NONE)
	{
		Body->AddImpulseToAllBodiesBelow(Push, UpperBody, /*bVelChange=*/ true);
	}
	else
	{
		Body->AddImpulse(Push, NAME_None, true);
	}
}

void ASSCharacter::OnDeathFinished(AActor* OwningActor)
{
	// Lyra: detach the controller (it respawns now), uninitialise the ability system, then hide and destroy
	// the pawn at once. Here the body stays as a corpse for CorpseSeconds (still visible, still simulated).
	K2_OnDeathFinished();
	if (GetLocalRole() == ROLE_Authority)
	{
		DetachFromControllerPendingDestroy();
		SetLifeSpan(FMath::Max(0.1f, CorpseSeconds));
	}
	if (ULyraPawnExtensionComponent* PawnExt = FindComponentByClass<ULyraPawnExtensionComponent>())
	{
		if (ULyraAbilitySystemComponent* Asc = GetLyraAbilitySystemComponent(); Asc && Asc->GetAvatarActor() == this)
		{
			PawnExt->UninitializeAbilitySystem();
		}
	}
	StartRagdoll(); // in case the death sequence ended before the ragdoll timer (or on late joiners)
}
