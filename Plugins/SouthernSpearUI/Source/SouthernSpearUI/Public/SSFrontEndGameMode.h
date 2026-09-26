// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "SSFrontEndGameMode.generated.h"

class USSMenuWidget;

/**
 * Title-screen game mode for L_SS_FrontEnd: no pawn, shows the Southern Spear
 * front-end menu for the local player. Replaces Lyra's front end
 * (Config/DefaultEngine.ini GameDefaultMap).
 */
UCLASS()
class SSUI_API ASSFrontEndGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ASSFrontEndGameMode();

	virtual void PostLogin(APlayerController* NewPlayer) override;

private:
	UPROPERTY(Transient)
	TObjectPtr<USSMenuWidget> Menu;
};
