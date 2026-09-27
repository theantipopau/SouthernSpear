// Copyright Southern Spear. All Rights Reserved.

#include "SSCharacter.h"

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
#include "InputMappingContext.h"
#include "Net/UnrealNetwork.h"
#include "PhysicalMaterials/PhysicalMaterial.h"
#include "PhysicsEngine/BodyInstance.h"
#include "SSCharacterMovementComponent.h"
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
	: Super(ObjectInitializer.SetDefaultSubobjectClass<USSCharacterMovementComponent>(ACharacter::CharacterMovementComponentName))
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
	if (BloodSystem)
	{
		UGameplayStatics::SpawnEmitterAtLocation(GetWorld(), BloodSystem, Where, Shot.Rotation(), FVector(0.6f), /*bAutoDestroy=*/ true);
		UE_LOG(LogTemp, Verbose, TEXT("SSBlood %s at %s (hit result: %d)"), *GetName(), *Where.ToString(), Hit != nullptr);
	}
}
