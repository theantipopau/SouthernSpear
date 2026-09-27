// Copyright Southern Spear. All Rights Reserved.

#include "SSCharacter.h"

#include "Components/ChildActorComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "GameFramework/PlayerController.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "Net/UnrealNetwork.h"
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
	if (UClass* PartsClass = SoldierPartsClass.TryLoadClass<AActor>())
	{
		Soldier = NewObject<UChildActorComponent>(this, TEXT("SS_Soldier"));
		Soldier->SetupAttachment(GetMesh());
		Soldier->SetChildActorClass(PartsClass);
		Soldier->RegisterComponent();
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
