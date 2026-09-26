// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSObjectiveHudSubsystem.generated.h"

class USSObjectiveStatusWidget;

/**
 * Shows the objective status widget to the local player in any game world
 * that has an Objective Assault director. Lives in the UI module so gameplay
 * never creates UI. Not created on dedicated servers.
 */
UCLASS()
class SSOBJUI_API USSObjectiveHudSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;

	USSObjectiveStatusWidget* GetStatusWidget() const { return StatusWidget; }

private:
	UPROPERTY(Transient)
	TObjectPtr<USSObjectiveStatusWidget> StatusWidget;

	UPROPERTY(Transient)
	TObjectPtr<class USSMinimapWidget> Minimap;

	/** Full map, toggled with M. */
	UPROPERTY(Transient)
	TObjectPtr<class USSMinimapWidget> FullMap;

	float RetryAccumulator = 0.f;
	float ElapsedSeconds = 0.f;
	bool bShotTaken = false;
};
