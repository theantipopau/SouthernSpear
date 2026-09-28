// Copyright Southern Spear. All Rights Reserved.

#include "SSRespawnGate.h"

#include "GameFramework/Controller.h"
#include "SSCoreLog.h"

TWeakObjectPtr<AController> USSRespawnGate::Key(const AController* Controller)
{
	return TWeakObjectPtr<AController>(const_cast<AController*>(Controller));
}

void USSRespawnGate::Lock(const TArray<AController*>& InRoster)
{
	bLocked = true;
	Roster.Reset();
	Eliminated.Reset();
	for (AController* Controller : InRoster)
	{
		if (Controller)
		{
			Roster.Add(Key(Controller));
		}
	}
	UE_LOG(LogSSCore, Log, TEXT("Respawn gate locked: single-life round, %d on the roster."), Roster.Num());
}

void USSRespawnGate::Unlock()
{
	if (bLocked)
	{
		UE_LOG(LogSSCore, Log, TEXT("Respawn gate unlocked: %d of %d eliminated last round."), Eliminated.Num(), Roster.Num());
	}
	bLocked = false;
	Roster.Reset();
	Eliminated.Reset();
}

void USSRespawnGate::ReportElimination(AController* Victim)
{
	if (!bLocked || !Victim || !Roster.Contains(Key(Victim)))
	{
		return;
	}
	if (!Eliminated.Contains(Key(Victim)))
	{
		Eliminated.Add(Key(Victim));
		UE_LOG(LogSSCore, Log, TEXT("Respawn gate: %s eliminated (%d of %d)."), *Victim->GetName(), Eliminated.Num(), Roster.Num());
	}
}

bool USSRespawnGate::IsOnRoster(const AController* Controller) const
{
	return Controller && Roster.Contains(Key(Controller));
}

bool USSRespawnGate::IsEliminated(const AController* Controller) const
{
	return Controller && Eliminated.Contains(Key(Controller));
}

bool USSRespawnGate::IsAlive(const AController* Controller) const
{
	return bLocked && IsOnRoster(Controller) && !IsEliminated(Controller);
}

bool USSRespawnGate::MustHoldOut(const AController* Controller) const
{
	return bLocked && Controller && (!IsOnRoster(Controller) || IsEliminated(Controller));
}
