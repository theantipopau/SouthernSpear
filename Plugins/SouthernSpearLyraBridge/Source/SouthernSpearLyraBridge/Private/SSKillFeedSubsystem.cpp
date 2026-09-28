// Copyright Southern Spear. All Rights Reserved.

#include "SSKillFeedSubsystem.h"

#include "AbilitySystem/Attributes/LyraHealthSet.h"
#include "AbilitySystemComponent.h"
#include "AbilitySystemInterface.h"
#include "Character/LyraHealthComponent.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerState.h"
#include "SSLyraReflection.h"
#include "SSRespawnGate.h"
#include "SSServiceEvents.h"
#include "SSTeamIdentityLibrary.h"

using namespace SSLyraReflection;

namespace
{
	APlayerState* PlayerStateOf(AActor* Actor)
	{
		if (APlayerState* PlayerState = Cast<APlayerState>(Actor))
		{
			return PlayerState;
		}
		if (const APawn* Pawn = Cast<APawn>(Actor))
		{
			return Pawn->GetPlayerState();
		}
		if (const AController* Controller = Cast<AController>(Actor))
		{
			return Controller->PlayerState;
		}
		return nullptr;
	}

	FString WeaponOf(APlayerState* Killer)
	{
		AController* Controller = Killer ? Killer->GetOwningController() : nullptr;
		UObject* Item = ActiveSlotItem(Controller);
		const FText Display = ItemName(Item);
		if (!Display.IsEmpty())
		{
			return Display.ToString();
		}
		const UClass* Def = ItemDefinition(Item);
		return Def ? FSSKillFeedRules::WeaponShortName(Def->GetName()) : FString();
	}
}

USSKillFeedRelay::USSKillFeedRelay()
{
	SetIsReplicatedByDefault(true);
}

void USSKillFeedRelay::ClientAddKill_Implementation(const FSSKillFeedEntry& Entry)
{
	UWorld* World = GetWorld();
	USSKillFeedState* State = World ? World->GetSubsystem<USSKillFeedState>() : nullptr;
	if (!State)
	{
		return;
	}
	FSSKillFeedEntry Local = Entry;
	Local.Time = World->GetTimeSeconds();
	const APlayerController* Owner = Cast<APlayerController>(GetOwner());
	State->LocalTeam = TeamOf(Owner ? Owner->PlayerState : nullptr);
	FSSKillFeedRules::Add(State->Entries, Local);
	UE_LOG(LogTemp, Log, TEXT("Southern Spear kill feed: %s [%s] %s%s"), *Entry.Killer, *Entry.Weapon, *Entry.Victim,
		Entry.bLocalKiller ? TEXT(" (you)") : TEXT(""));
}

void USSKillFeedRelay::ServerRedeploy_Implementation()
{
	const APlayerController* Owner = Cast<APlayerController>(GetOwner());
	// One life per round (ADR-031): re-deploying mid-round would end it for good.
	const USSRespawnGate* Gate = GetWorld() ? GetWorld()->GetSubsystem<USSRespawnGate>() : nullptr;
	if (Gate && Gate->IsLocked())
	{
		UE_LOG(LogTemp, Log, TEXT("Southern Spear re-deploy refused: single-life round in progress."));
		return;
	}
	APawn* Pawn = Owner ? Owner->GetPawn() : nullptr;
	static UClass* HealthClass = FindObject<UClass>(nullptr, TEXT("/Script/LyraGame.LyraHealthComponent"));
	ULyraHealthComponent* Health = Pawn && HealthClass ? static_cast<ULyraHealthComponent*>(Pawn->GetComponentByClass(HealthClass)) : nullptr;
	if (Health && Health->GetHealth() > 0.f)
	{
		UE_LOG(LogTemp, Log, TEXT("Southern Spear re-deploy: %s"), *Pawn->GetName());
		Health->DamageSelfDestruct(/*bFellOutOfWorld=*/ false);
	}
}

bool USSKillFeedSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId USSKillFeedSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USSKillFeedSubsystem, STATGROUP_Tickables);
}

void USSKillFeedSubsystem::Tick(float DeltaTime)
{
	UWorld* World = GetWorld();
	if (!World || World->GetNetMode() == NM_Client)
	{
		return;
	}
	Accumulator += DeltaTime;
	if (Accumulator < 0.5f)
	{
		return;
	}
	Accumulator = 0.f;

	// Every player controller carries a relay (added once; replicated to its owning client).
	for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
	{
		APlayerController* Controller = It->Get();
		if (Controller && !Controller->FindComponentByClass<USSKillFeedRelay>())
		{
			USSKillFeedRelay* Relay = NewObject<USSKillFeedRelay>(Controller, TEXT("SSKillFeedRelay"));
			Relay->RegisterComponent();
		}
	}

	// Bind each pawn's health set once. ULyraHealthSet is not exported: find it by class path.
	static UClass* HealthSetClass = LyraClass(TEXT("/Script/LyraGame.LyraHealthSet"));
	if (!HealthSetClass)
	{
		return;
	}
	for (TActorIterator<APawn> It(World); It; ++It)
	{
		const IAbilitySystemInterface* Asi = Cast<IAbilitySystemInterface>(*It);
		UAbilitySystemComponent* Asc = Asi ? Asi->GetAbilitySystemComponent() : nullptr;
		const UAttributeSet* Set = Asc ? Asc->GetAttributeSet(HealthSetClass) : nullptr;
		if (!Set || Bound.Contains(Set))
		{
			continue;
		}
		Bound.Add(Set);
		TWeakObjectPtr<const UAttributeSet> WeakSet(Set);
		static_cast<const ULyraHealthSet*>(Set)->OnOutOfHealth.AddWeakLambda(this,
			[this, WeakSet](AActor* Instigator, AActor*, const FGameplayEffectSpec*, float, float, float)
			{
				if (const UAttributeSet* Alive = WeakSet.Get())
				{
					HandleOutOfHealth(Alive, Instigator);
				}
			});
	}
}

void USSKillFeedSubsystem::HandleOutOfHealth(const UAttributeSet* Set, AActor* Instigator)
{
	UWorld* World = GetWorld();
	const UAbilitySystemComponent* Asc = Set->GetOwningAbilitySystemComponent();
	APlayerState* Victim = PlayerStateOf(Asc ? Asc->GetOwnerActor() : nullptr);
	if (!Victim && Asc)
	{
		Victim = PlayerStateOf(Asc->GetAvatarActor());
	}
	APlayerState* Killer = PlayerStateOf(Instigator);
	if (!World || !Victim)
	{
		return;
	}

	// Gameplay consequences, server only: the round's roster (ADR-031) and the
	// conduct penalty for a friendly kill (ADR-032). Neither changes damage.
	AController* VictimController = Victim->GetOwningController();
	if (USSRespawnGate* Gate = World->GetSubsystem<USSRespawnGate>())
	{
		Gate->ReportElimination(VictimController);
	}
	const ESSTeamId VictimTeam = TeamOf(Victim);
	const ESSTeamId KillerTeam = TeamOf(Killer);
	if (Killer && Killer != Victim && FSSTeamIdentity::IsPlayableTeam(VictimTeam) && FSSTeamIdentity::IsPlayableTeam(KillerTeam))
	{
		if (USSServiceEventSubsystem* Bus = World->GetSubsystem<USSServiceEventSubsystem>())
		{
			// ADR-034: a kill of the other side earns capped XP; a teammate costs it.
			Bus->Post(Killer->GetOwningController(), KillerTeam == VictimTeam ? ESSServiceEvent::FriendlyKill : ESSServiceEvent::EnemyKill);
		}
	}

	FSSKillFeedEntry Entry;
	Entry.Victim = Victim->GetPlayerName();
	Entry.VictimTeam = TeamOf(Victim);
	Entry.Killer = Killer ? Killer->GetPlayerName() : FString();
	Entry.KillerTeam = TeamOf(Killer);
	Entry.Weapon = Killer && Killer != Victim ? WeaponOf(Killer) : FString();
	for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
	{
		APlayerController* Controller = It->Get();
		USSKillFeedRelay* Relay = Controller ? Controller->FindComponentByClass<USSKillFeedRelay>() : nullptr;
		if (!Relay)
		{
			continue;
		}
		FSSKillFeedEntry ForViewer = Entry;
		ForViewer.bLocalKiller = Killer && Controller->PlayerState == Killer;
		ForViewer.bLocalVictim = Controller->PlayerState == Victim;
		Relay->ClientAddKill(ForViewer);
	}
}
