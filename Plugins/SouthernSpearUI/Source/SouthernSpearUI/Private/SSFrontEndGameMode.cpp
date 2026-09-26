// Copyright Southern Spear. All Rights Reserved.

#include "SSFrontEndGameMode.h"

#include "GameFramework/PlayerController.h"
#include "GameFramework/SpectatorPawn.h"
#include "SSMenuWidget.h"

ASSFrontEndGameMode::ASSFrontEndGameMode()
{
	DefaultPawnClass = nullptr;
	bStartPlayersAsSpectators = true;
}

void ASSFrontEndGameMode::PostLogin(APlayerController* NewPlayer)
{
	Super::PostLogin(NewPlayer);
	if (!NewPlayer || !NewPlayer->IsLocalController() || Menu)
	{
		return;
	}
	Menu = CreateWidget<USSMenuWidget>(NewPlayer, USSMenuWidget::StaticClass());
	if (!Menu)
	{
		return;
	}
	Menu->Setup(ESSMenuMode::FrontEnd);
	Menu->AddToViewport(50);
	FInputModeUIOnly Input;
	Input.SetWidgetToFocus(Menu->TakeWidget());
	NewPlayer->SetInputMode(Input);
	NewPlayer->SetShowMouseCursor(true);
	UE_LOG(LogTemp, Log, TEXT("Southern Spear front end shown."));
}
