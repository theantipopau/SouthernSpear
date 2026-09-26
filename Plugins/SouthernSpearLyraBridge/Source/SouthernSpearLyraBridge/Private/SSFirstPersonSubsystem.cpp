// Copyright Southern Spear. All Rights Reserved.

#include "SSFirstPersonSubsystem.h"

#include "Camera/LyraCameraComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "SSFirstPersonCameraMode.h"
#include "SSLocalHudState.h"

DEFINE_LOG_CATEGORY_STATIC(LogSSFirstPerson, Log, All);

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

	ViewModel = NewObject<UStaticMeshComponent>(Pawn, TEXT("SS_ViewModel"));
	ViewModel->SetupAttachment(Camera);
	ViewModel->SetOnlyOwnerSee(true);
	ViewModel->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	ViewModel->SetCastShadow(false);
	ViewModel->RegisterComponent();

	if (const ACharacter* Character = Cast<ACharacter>(Pawn))
	{
		Character->GetMesh()->HideBoneByName(TEXT("head"), EPhysBodyOp::PBO_None);
	}
	HandledPawn = Pawn;
	UE_LOG(LogSSFirstPerson, Log, TEXT("First-person camera active for %s."), *Pawn->GetName());
}

void USSFirstPersonSubsystem::UpdateViewModel(APawn* Pawn, float DeltaTime)
{
	if (!ViewModel)
	{
		return;
	}
	// The held weapon is a cosmetic actor attached to the pawn's body mesh
	// (Lyra equipment). Show its mesh on the camera and hide the body copy
	// from the owner. Soldier body parts are skeletal, so they never match.
	UStaticMesh* Held = nullptr;
	TArray<AActor*> Attached;
	Pawn->GetAttachedActors(Attached, true, true);
	for (AActor* Actor : Attached)
	{
		TInlineComponentArray<UStaticMeshComponent*> Meshes(Actor);
		for (UStaticMeshComponent* Mesh : Meshes)
		{
			if (Mesh->GetStaticMesh() && Mesh->IsVisible())
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

	// Hip and aimed placements relative to the camera (cm; +X forward, +Y
	// right, +Z up; weapon origin is the top of the grip).
	static const FVector Hip(32.f, 13.f, -15.f);
	static const FVector Aim(24.f, 0.f, -10.5f);
	if (USSLocalHudState* HudState = GetWorld()->GetSubsystem<USSLocalHudState>())
	{
		HudState->bAiming = *bAiming;
	}
	AimAlpha = FMath::FInterpConstantTo(AimAlpha, *bAiming ? 1.f : 0.f, DeltaTime, 6.f);

	// Sway: the weapon lags look input slightly and settles back.
	const FRotator Control = Pawn->GetControlRotation();
	const FRotator Delta = (Control - LastControlRotation).GetNormalized();
	LastControlRotation = Control;
	const float SwayScale = FMath::Lerp(1.f, 0.25f, AimAlpha);
	SwayOffset += FVector(0.f, -Delta.Yaw * 0.08f, -Delta.Pitch * 0.08f) * SwayScale;
	SwayOffset = FMath::VInterpTo(SwayOffset, FVector::ZeroVector, DeltaTime, 8.f).BoundToCube(3.f);

	// Walk bob from ground speed.
	const float Speed = Pawn->GetVelocity().Size2D();
	const float Time = GetWorld()->GetTimeSeconds();
	const float Bob = FMath::Clamp(Speed / 400.f, 0.f, 1.f) * SwayScale;
	const FVector BobOffset(0.f, FMath::Sin(Time * 6.f) * 0.6f * Bob, FMath::Abs(FMath::Sin(Time * 6.f)) * -0.8f * Bob);

	ViewModel->SetRelativeLocationAndRotation(FMath::Lerp(Hip, Aim, AimAlpha) + SwayOffset + BobOffset, FRotator::ZeroRotator);
}
