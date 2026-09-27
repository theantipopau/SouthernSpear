// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSSettingsSyncSubsystem.generated.h"

/**
 * Client: pushes the Southern Spear input and audio preferences
 * (FSSUserPrefs: mouse sensitivity, invert Y, master / music / effects
 * volume) into Lyra's own settings objects, which own the input modifiers
 * and sound mixes. Lyra's setters are reached through reflection (the
 * settings classes are not exported). Re-applies when a preference changes.
 */
UCLASS()
class SSBRIDGE_API USSSettingsSyncSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

private:
	float Accumulator = 1.f;
	FString LastApplied;
};
