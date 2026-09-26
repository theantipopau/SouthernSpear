// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSPlayerHudSubsystem.generated.h"

class USSMenuWidget;
class USSPlayerHudWidget;

/**
 * Client: adds the Southern Spear player HUD once the local player has a pawn,
 * and toggles the match menu with Escape. Not created on the front end.
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
};
