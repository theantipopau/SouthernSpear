// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSPersistence.h"
#include "SSProgressionRules.h"
#include "SSServiceEvents.h"
#include "SSProgressionSubsystems.generated.h"

class AController;
class APlayerController;

/**
 * Added by the server to every player controller: delivers each service event
 * and the XP it earned to the owning client, which records it (ADR-032).
 */
UCLASS()
class SSPROG_API USSServiceRelay : public UActorComponent
{
	GENERATED_BODY()

public:
	USSServiceRelay();

	/** XpDelta is the server's decision after caps; zero once an award is capped (the statistic still counts). */
	UFUNCTION(Client, Reliable)
	void ClientServiceAward(ESSServiceEvent Event, int32 XpDelta);
};

/**
 * Server: turns service events into awards. Listens to Core's service event
 * bus, keeps a per-player tally for the current match, applies the award
 * table's caps and sends the result to the player through USSServiceRelay.
 * Bots earn nothing. MatchCompleted closes a player's match tally, so it is
 * the last event the director posts for a match.
 */
UCLASS()
class SSPROG_API USSProgressionServerSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

	/** Server: award one event to one player now. Public for tests; normally called from the bus. */
	int32 HandleServiceEvent(AController* Player, ESSServiceEvent Event);

private:
	void HandleServiceEventFromBus(AController* Player, ESSServiceEvent Event);
	USSServiceRelay* RelayFor(APlayerController* Controller);

	TMap<TWeakObjectPtr<APlayerController>, FSSMatchTally> Tallies;
	FDelegateHandle BusHandle;
	float Accumulator = 0.f;
};

/**
 * Client: the local player's service record. Loads it at start (creating it
 * the first time), applies awards the server sends, saves after each one, and
 * publishes the display values to Core's USSLocalProfileState for the UI.
 *
 * DEV ONLY persistence (FSSLocalDevPersistence under Saved/SouthernSpear/Profiles):
 * the record is not authoritative and must not gate anything other players see.
 */
UCLASS()
class SSPROG_API USSPlayerProfileSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** Record one award from the server and save. */
	void ApplyServiceAward(ESSServiceEvent Event, int32 XpDelta);

	/** Set the callsign; false (and unchanged) if it is not a valid callsign. */
	UFUNCTION(BlueprintCallable, Category = "Southern Spear|Profile")
	bool SetCallsign(const FString& NewCallsign);

	const FSSServiceRecord& GetRecord() const { return Record; }

	/** False when the stored record came from a newer build: nothing is written, so it cannot be lost. */
	bool IsWritable() const { return bWritable; }

	/** The single local profile id used by the dev provider. */
	static const TCHAR* LocalPlayerId() { return TEXT("local"); }

private:
	void LoadOrCreate();
	void Save();
	void Publish();

	TUniquePtr<FSSLocalDevPersistence> Provider;
	FSSServiceRecord Record;
	bool bWritable = true;
};
