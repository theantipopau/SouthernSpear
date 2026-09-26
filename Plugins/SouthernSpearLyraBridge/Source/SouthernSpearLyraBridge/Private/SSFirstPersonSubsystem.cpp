// Copyright Southern Spear. All Rights Reserved.

#include "SSFirstPersonSubsystem.h"

#include "Camera/LyraCameraComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "SSFirstPersonCameraMode.h"

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
	if (!Pawn || HandledPawn.Get() == Pawn)
	{
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
	Camera->DetermineCameraModeDelegate.BindLambda([LyraChoice]() -> TSubclassOf<ULyraCameraMode>
	{
		const TSubclassOf<ULyraCameraMode> Chosen = LyraChoice.IsBound() ? LyraChoice.Execute() : nullptr;
		const bool bAiming = Chosen && Chosen->GetName().Contains(TEXT("ADS"));
		return bAiming ? USSFirstPersonADSCameraMode::StaticClass() : USSFirstPersonCameraMode::StaticClass();
	});

	if (const ACharacter* Character = Cast<ACharacter>(Pawn))
	{
		Character->GetMesh()->HideBoneByName(TEXT("head"), EPhysBodyOp::PBO_None);
	}
	HandledPawn = Pawn;
	UE_LOG(LogSSFirstPerson, Log, TEXT("First-person camera active for %s."), *Pawn->GetName());
}
