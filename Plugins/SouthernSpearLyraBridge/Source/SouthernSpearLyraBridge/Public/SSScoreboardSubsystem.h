// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSScoreboardSubsystem.generated.h"

/**
 * Client: fills USSScoreboardState (Core) from the game state's player
 * states twice a second: name, team (Lyra team 1/2 -> TeamOne/TeamTwo), ping,
 * and Lyra's score stat tags (eliminations, deaths, assists) through
 * reflection, since ULyraPlayerState's stat functions are not exported.
 */
UCLASS()
class SSBRIDGE_API USSScoreboardSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

private:
	float Accumulator = 0.f;
	float DebugAccumulator = 0.f;
};
