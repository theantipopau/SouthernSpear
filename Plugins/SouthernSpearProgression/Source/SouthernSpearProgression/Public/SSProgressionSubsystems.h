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
class IConsoleObject;

/**
 * Added by the server to every player controller: delivers each service event
 * and the XP it earned to the owning client, which records it (ADR-032), and
 * carries the client's service level and callsign back to the server for the
 * scoreboard (ADR-034).
 */
UCLASS()
class SSPROG_API USSServiceRelay : public UActorComponent
{
	GENERATED_BODY()

public:
	USSServiceRelay();

	virtual void BeginPlay() override;

	/** XpDelta is the server's decision after caps; zero once an award is capped (the statistic still counts). */
	UFUNCTION(Client, Reliable)
	void ClientServiceAward(ESSServiceEvent Event, int32 XpDelta);

	/**
	 * The owning client's level (from its local record) and callsign. The server
	 * shows them on the scoreboard: the level through USSServiceRankComponent on
	 * the player state, the callsign as the player name. Display only: the record
	 * is not authoritative (R-53), so nothing is gated on it.
	 */
	UFUNCTION(Server, Reliable)
	void ServerReportProfile(int32 ServiceLevel, const FString& Callsign);
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

	virtual void Deinitialize() override;

	/** Record one award from the server and save. */
	void ApplyServiceAward(ESSServiceEvent Event, int32 XpDelta);

	/** Send level and callsign to the server through the local player's relay, if it exists yet. */
	void ReportToServer() const;

	/** The current service level from the record's XP. */
	int32 GetServiceLevel() const;

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

	/** ss.Callsign <name>: set the callsign from the console until the front end has a field for it. */
	IConsoleObject* CallsignCommand = nullptr;

	TUniquePtr<FSSLocalDevPersistence> Provider;
	FSSServiceRecord Record;
	bool bWritable = true;
};
