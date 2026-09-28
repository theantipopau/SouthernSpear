// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SSKillFeedState.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSKillFeedSubsystem.generated.h"

class UAttributeSet;
struct FGameplayEffectSpec;

/**
 * Added by the server to every player controller: delivers each elimination to that player with a reliable
 * client RPC, so the kill feed does not depend on the victim's pawn being relevant to the viewer.
 */
UCLASS()
class SSBRIDGE_API USSKillFeedRelay : public UActorComponent
{
	GENERATED_BODY()

public:
	USSKillFeedRelay();

	UFUNCTION(Client, Reliable)
	void ClientAddKill(const FSSKillFeedEntry& Entry);

	/** RE-DEPLOY (match menu): the owning player asks to end this life and respawn with the selected class.
	 * The server applies Lyra's own self-destruct to the pawn; it counts as a death, not a kill. */
	UFUNCTION(Server, Reliable)
	void ServerRedeploy();
};

/**
 * Server: binds Lyra's out-of-health event (ULyraHealthSet::OnOutOfHealth) on every pawn's attribute set and
 * sends "killer, weapon, victim" to every player controller through USSKillFeedRelay. The weapon is the
 * killer's active quick-bar item at the moment of the kill. Clients write the entry into USSKillFeedState
 * (Core) for the UI. Presentation only (ADR-004): reads gameplay state, never changes it.
 */
UCLASS()
class SSBRIDGE_API USSKillFeedSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

private:
	void HandleOutOfHealth(const UAttributeSet* Set, AActor* Instigator);

	TSet<TWeakObjectPtr<const UAttributeSet>> Bound;
	float Accumulator = 0.f;
};
