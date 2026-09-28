// Copyright Southern Spear. All Rights Reserved.

#include "SSHudStateSubsystem.h"

#include "GameFramework/CharacterMovementComponent.h"

#include "Character/LyraHealthComponent.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "GameplayTagContainer.h"
#include "SSKillFeedSubsystem.h"
#include "SSLocalHudState.h"
#include "UObject/UnrealType.h"
#include "Animation/AnimInstance.h"
#include "Components/SkeletalMeshComponent.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

#include "SSLyraReflection.h"

using namespace SSLyraReflection;

namespace
{
	int32 ItemStatCount(UObject* Item, const FGameplayTag& Tag)
	{
		UFunction* Fn = Item && Tag.IsValid() ? Item->FindFunction(TEXT("GetStatTagStackCount")) : nullptr;
		if (!Fn)
		{
			return -1;
		}
		struct { FGameplayTag Tag; int32 ReturnValue = 0; } Params { Tag };
		Item->ProcessEvent(Fn, &Params);
		return Params.ReturnValue;
	}

	// Lyra presentation Southern Spear replaces (producer, Session 041): the damage-number pops, which drew as
	// blocks over hit players, and the nameplate health bars above other players. Lyra's standard component
	// action set adds them; they are removed on the client by class name so vendored content stays unmodified.
	bool IsReplacedLyraPresentation(const UActorComponent* Component)
	{
		const FString Name = Component->GetClass()->GetName();
		return Name.Contains(TEXT("NumberPop")) || Name.Contains(TEXT("Nameplate"));
	}

	int32 RemoveLyraPresentation(UWorld* World, APlayerController* Player)
	{
		TArray<UActorComponent*> Doomed;
		auto Collect = [&Doomed](AActor* Actor)
		{
			TInlineComponentArray<UActorComponent*> Components(Actor);
			for (UActorComponent* Component : Components)
			{
				if (Component && IsReplacedLyraPresentation(Component))
				{
					Doomed.Add(Component);
				}
			}
		};
		Collect(Player);
		for (TActorIterator<APawn> It(World); It; ++It)
		{
			Collect(*It);
		}
		for (UActorComponent* Component : Doomed)
		{
			Component->DestroyComponent();
		}
		return Doomed.Num();
	}
}

bool USSHudStateSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* World = Cast<UWorld>(Outer);
	return World && World->GetNetMode() != NM_DedicatedServer && Super::ShouldCreateSubsystem(Outer);
}

bool USSHudStateSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId USSHudStateSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USSHudStateSubsystem, STATGROUP_Tickables);
}

void USSHudStateSubsystem::Tick(float DeltaTime)
{
	UWorld* World = GetWorld();
	USSLocalHudState* State = World ? World->GetSubsystem<USSLocalHudState>() : nullptr;
	APlayerController* Player = World ? World->GetFirstPlayerController() : nullptr;
	if (!State)
	{
		return;
	}
	APawn* Pawn = Player && Player->IsLocalController() ? Player->GetPawn() : nullptr;

	static UClass* HealthClass = LyraClass(TEXT("/Script/LyraGame.LyraHealthComponent"));
	const ULyraHealthComponent* Health = Pawn && HealthClass
		? static_cast<const ULyraHealthComponent*>(Pawn->GetComponentByClass(HealthClass)) : nullptr;
	State->bHasPawn = Health != nullptr;
	if (State->bRedeployRequested)
	{
		State->bRedeployRequested = false;
		if (USSKillFeedRelay* Relay = Player ? Player->FindComponentByClass<USSKillFeedRelay>() : nullptr)
		{
			Relay->ServerRedeploy();
		}
	}
	State->Health = Health ? Health->GetHealth() : 0.f;
	State->MaxHealth = Health ? Health->GetMaxHealth() : 0.f;

	static const FGameplayTag MagazineTag = FGameplayTag::RequestGameplayTag(TEXT("Lyra.ShooterGame.Weapon.MagazineAmmo"), false);
	static const FGameplayTag SizeTag = FGameplayTag::RequestGameplayTag(TEXT("Lyra.ShooterGame.Weapon.MagazineSize"), false);
	static const FGameplayTag SpareTag = FGameplayTag::RequestGameplayTag(TEXT("Lyra.ShooterGame.Weapon.SpareAmmo"), false);
	UObject* Item = Pawn ? ActiveSlotItem(Player) : nullptr;
	State->Magazine = ItemStatCount(Item, MagazineTag);
	State->Reserve = ItemStatCount(Item, SpareTag);
	State->MagazineSize = ItemStatCount(Item, SizeTag);
	State->WeaponName = ItemName(Item);
	State->OpticMagnification = USSLocalHudState::OpticMagnificationFor(State->WeaponName.ToString());

	CleanupAccumulator += DeltaTime;
	if (Player && CleanupAccumulator >= 0.5f)
	{
		CleanupAccumulator = 0.f;
		if (const int32 Removed = RemoveLyraPresentation(World, Player))
		{
			UE_LOG(LogTemp, Log, TEXT("Southern Spear: removed %d Lyra number-pop / nameplate component(s)."), Removed);
		}
	}

	// Dev diagnostic (-SSAnimDebug): every 3 s, each pawn's speed, running anim
	// classes (main + linked layers), montage, and ammunition.
	static const bool bAnimDebug = FParse::Param(FCommandLine::Get(), TEXT("SSAnimDebug"));
	DebugAccumulator += DeltaTime;
	if (bAnimDebug && DebugAccumulator >= 3.f)
	{
		DebugAccumulator = 0.f;
		int32 Count = 0;
		for (TActorIterator<ACharacter> It(World); It && Count < 16; ++It, ++Count)
		{
			USkeletalMeshComponent* Mesh = It->GetMesh();
			UAnimInstance* Anim = Mesh ? Mesh->GetAnimInstance() : nullptr;
			FString Linked;
			if (Mesh)
			{
				Mesh->ForEachAnimInstance([&Linked](UAnimInstance* Layer)
				{
					Linked += GetNameSafe(Layer ? Layer->GetClass() : nullptr) + TEXT(" ");
				});
			}
			UObject* PawnItem = ActiveSlotItem(It->GetController());
			TArray<AActor*> Parts;
			It->GetAttachedActors(Parts, true, true);
			FString PartInfo;
			for (const AActor* Part : Parts)
			{
				TInlineComponentArray<USkeletalMeshComponent*> Skels(Part);
				for (const USkeletalMeshComponent* Skel : Skels)
				{
					PartInfo += FString::Printf(TEXT("%s:%s:v%d:h%d "), *GetNameSafe(Part->GetClass()), *GetNameSafe(Skel->GetSkeletalMeshAsset()),
						Skel->IsVisible(), Skel->bHiddenInGame);
				}
			}
			UE_LOG(LogTemp, Log, TEXT("SSPartDebug %s parts=[%s]"), *It->GetName(), *PartInfo);
			const UCharacterMovementComponent* Move = It->GetCharacterMovement();
			UE_LOG(LogTemp, Log, TEXT("SSAnimDebug %s class=%s move=%s max=%.0f speed=%.0f mesh=%s anim=%s linked=[%s] montage=%s tick=%d mag=%d spare=%d size=%d"),
				*It->GetName(), *It->GetClass()->GetSuperClass()->GetName(), *GetNameSafe(Move ? Move->GetClass() : nullptr),
				Move ? Move->GetMaxSpeed() : -1.f, It->GetVelocity().Size2D(), *GetNameSafe(Mesh ? Mesh->GetSkeletalMeshAsset() : nullptr),
				*GetNameSafe(Anim ? Anim->GetClass() : nullptr), *Linked,
				*GetNameSafe(Anim ? Anim->GetCurrentActiveMontage() : nullptr), Mesh ? (int32)Mesh->VisibilityBasedAnimTickOption : -1,
				ItemStatCount(PawnItem, MagazineTag), ItemStatCount(PawnItem, SpareTag), ItemStatCount(PawnItem, SizeTag));
		}
	}
}
