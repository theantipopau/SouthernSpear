// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSServiceEvents.generated.h"

class AController;

/**
 * Things a player did in a match that progression may reward (ADR-032).
 *
 * The list is the GDD §6.3 "what progression rewards", as far as the game can
 * observe it today, plus kills of the other side (ADR-034, producer override
 * of GDD §6.4). Every positive award is capped per match, and a captured
 * objective is worth ten kills in the shipped table. Append new members at the
 * end: award rules name them in config.
 */
UENUM(BlueprintType)
enum class ESSServiceEvent : uint8
{
	None,
	/** The player was inside the objective when their team captured it. */
	ObjectiveCaptured,
	/** The player's team won the round (the player was on the round roster). */
	RoundWon,
	/** Section Assault: the player's team won the round and the player was still alive. */
	RoundWonAlive,
	/** The player finished a match (was on the roster when it ended). */
	MatchCompleted,
	/** The player's team won the match. */
	MatchWon,
	/** The player killed a teammate. A penalty. */
	FriendlyKill,
	/** The player killed a player of the other team (ADR-034). */
	EnemyKill,
};

DECLARE_MULTICAST_DELEGATE_TwoParams(FSSOnServiceEvent, AController* /*Player*/, ESSServiceEvent /*Event*/);

/**
 * Server: the bus between the systems that see service events (the objective
 * director, the Lyra bridge) and progression, which rewards them. It lives in
 * Core because those modules may not depend on each other (guard SS001).
 * Posting on a client does nothing: awards are the server's decision.
 */
UCLASS()
class SSCORE_API USSServiceEventSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	/** Server: record that Player earned Event. Ignored on clients, for None, and without a controller. */
	void Post(AController* Player, ESSServiceEvent Event);

	/** Fires on the server for every accepted Post. */
	FSSOnServiceEvent OnServiceEvent;

	static const TCHAR* LexEvent(ESSServiceEvent Event);
};
