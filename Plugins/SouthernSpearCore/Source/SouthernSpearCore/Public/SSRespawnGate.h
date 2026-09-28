// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSRespawnGate.generated.h"

class AController;

/**
 * Server: who may be given a pawn during a single-life round (ADR-031).
 *
 * The objective director locks the gate with the round roster when play
 * starts and unlocks it at the next reset. The Lyra bridge reports each
 * elimination and, while the gate is locked, holds out any controller that is
 * eliminated or was not on the roster (a mid-round joiner). Unlocked, the gate
 * holds nobody out and ignores eliminations, so modes with respawns are
 * unaffected. Lives in Core because the director and the bridge may not
 * depend on each other (guard SS001).
 */
UCLASS()
class SSCORE_API USSRespawnGate : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	/** A single-life round begins: Roster is everyone alive and playing at this moment. */
	void Lock(const TArray<AController*>& Roster);

	/** The round is over and reset: everyone may spawn again. Clears roster and eliminations. */
	void Unlock();

	bool IsLocked() const { return bLocked; }

	/** A controller's pawn ran out of health. Ignored while unlocked or for controllers not on the roster. */
	void ReportElimination(AController* Victim);

	bool IsOnRoster(const AController* Controller) const;
	bool IsEliminated(const AController* Controller) const;

	/** On the roster and not eliminated. False while unlocked. */
	bool IsAlive(const AController* Controller) const;

	/** True when the controller must not be given a pawn now. */
	bool MustHoldOut(const AController* Controller) const;

	int32 GetRosterCount() const { return Roster.Num(); }
	int32 GetEliminatedCount() const { return Eliminated.Num(); }

private:
	static TWeakObjectPtr<AController> Key(const AController* Controller);

	bool bLocked = false;
	TSet<TWeakObjectPtr<AController>> Roster;
	TSet<TWeakObjectPtr<AController>> Eliminated;
};
