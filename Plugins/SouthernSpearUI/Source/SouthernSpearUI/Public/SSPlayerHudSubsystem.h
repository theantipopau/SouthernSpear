// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSPlayerHudSubsystem.generated.h"

class USSClassSelectWidget;
class USSMenuWidget;
class USSPlayerHudWidget;
class USSScoreboardWidget;
class USSKillFeedWidget;

/**
 * Client: adds the Southern Spear player HUD once the local player has a pawn,
 * toggles the match menu with Escape, shows the scoreboard while Tab is held,
 * and shows class selection on first
 * deployment, after death and on L. Not created on the front end.
 */
UCLASS()
class SSUI_API USSPlayerHudSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

private:
	UPROPERTY(Transient) TObjectPtr<USSPlayerHudWidget> Hud;
	UPROPERTY(Transient) TObjectPtr<USSMenuWidget> PauseMenu;
	UPROPERTY(Transient) TObjectPtr<USSClassSelectWidget> ClassSelect;
	UPROPERTY(Transient) TObjectPtr<USSScoreboardWidget> Scoreboard;
	UPROPERTY(Transient) TObjectPtr<USSKillFeedWidget> KillFeed;
	bool bHadPawn = false;
	bool bClassSelectPending = false;
};
