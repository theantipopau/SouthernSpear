// Copyright Southern Spear. All Rights Reserved.

#include "SSPlayerHudSubsystem.h"

#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "SSLocalHudState.h"
#include "SSMenuWidget.h"
#include "SSPlayerHudWidget.h"

IMPLEMENT_MODULE(FDefaultModuleImpl, SouthernSpearUI)

bool USSPlayerHudSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* World = Cast<UWorld>(Outer);
	return World && World->GetNetMode() != NM_DedicatedServer && Super::ShouldCreateSubsystem(Outer);
}

bool USSPlayerHudSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId USSPlayerHudSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USSPlayerHudSubsystem, STATGROUP_Tickables);
}

void USSPlayerHudSubsystem::Tick(float DeltaTime)
{
	UWorld* World = GetWorld();
	APlayerController* Player = World ? World->GetFirstPlayerController() : nullptr;
	if (!Player || !Player->IsLocalController())
	{
		return;
	}

	if (!Hud)
	{
		// Only in matches: the HUD appears once the bridge reports a pawn.
		const USSLocalHudState* State = World->GetSubsystem<USSLocalHudState>();
		if (!State || !State->bHasPawn)
		{
			return;
		}
		Hud = CreateWidget<USSPlayerHudWidget>(Player, USSPlayerHudWidget::StaticClass());
		if (Hud)
		{
			Hud->AddToViewport(5);
			UE_LOG(LogTemp, Log, TEXT("Southern Spear player HUD shown for %s."), *Player->GetName());
		}
		return;
	}

	if (Player->WasInputKeyJustPressed(EKeys::Escape))
	{
		if (!PauseMenu)
		{
			PauseMenu = CreateWidget<USSMenuWidget>(Player, USSMenuWidget::StaticClass());
			PauseMenu->Setup(ESSMenuMode::Pause);
			PauseMenu->AddToViewport(60);
			PauseMenu->SetVisibility(ESlateVisibility::Collapsed);
		}
		const bool bOpen = !PauseMenu->IsVisible();
		PauseMenu->SetVisibility(bOpen ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
		if (bOpen)
		{
			FInputModeGameAndUI Input;
			Input.SetWidgetToFocus(PauseMenu->TakeWidget());
			Player->SetInputMode(Input);
		}
		else
		{
			Player->SetInputMode(FInputModeGameOnly());
		}
		Player->SetShowMouseCursor(bOpen);
	}
}
