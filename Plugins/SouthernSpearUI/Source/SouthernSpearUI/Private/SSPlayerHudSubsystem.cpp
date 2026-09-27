// Copyright Southern Spear. All Rights Reserved.

#include "SSPlayerHudSubsystem.h"

#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "SSLocalHudState.h"
#include "SSClassSelectWidget.h"
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
	// Headless test worlds (e.g. network smoke tests) have no viewport to draw into.
	if (!Player || !Player->IsLocalController() || !World->GetGameViewport())
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
			// The front end leaves input in UI-only mode across the level load;
			// a match always starts with game input and no cursor.
			Player->SetInputMode(FInputModeGameOnly());
			Player->SetShowMouseCursor(false);
			Hud->AddToViewport(5);
			UE_LOG(LogTemp, Log, TEXT("Southern Spear player HUD shown for %s."), *Player->GetName());
		}
		ClassSelect = CreateWidget<USSClassSelectWidget>(Player, USSClassSelectWidget::StaticClass());
		if (ClassSelect)
		{
			ClassSelect->AddToViewport(40);
			if (!FParse::Param(FCommandLine::Get(), TEXT("SSNoClassSelect"))) // dev captures
			{
				ClassSelect->Open(/*bAfterDeath=*/ false);
			}
			else
			{
				ClassSelect->Close();
			}
		}
		bHadPawn = true;
		return;
	}

	// Class selection: after death (applies on respawn) and on L.
	const USSLocalHudState* State = World->GetSubsystem<USSLocalHudState>();
	const bool bHasPawn = State && State->bHasPawn;
	if (ClassSelect)
	{
		if (bHadPawn && !bHasPawn && !ClassSelect->IsVisible())
		{
			ClassSelect->Open(/*bAfterDeath=*/ true);
		}
		else if (Player->WasInputKeyJustPressed(EKeys::L))
		{
			ClassSelect->IsVisible() ? ClassSelect->Close() : ClassSelect->Open(!bHasPawn);
		}
	}
	bHadPawn = bHasPawn;

	if (Player->WasInputKeyJustPressed(EKeys::Escape))
	{
		if (!PauseMenu)
		{
			PauseMenu = CreateWidget<USSMenuWidget>(Player, USSMenuWidget::StaticClass());
			PauseMenu->Setup(ESSMenuMode::Pause);
			PauseMenu->AddToViewport(60);
			PauseMenu->SetVisibility(ESlateVisibility::Collapsed);
		}
		if (PauseMenu->IsVisible())
		{
			PauseMenu->Close();
		}
		else
		{
			PauseMenu->SetVisibility(ESlateVisibility::Visible);
			PauseMenu->Replay();
			FInputModeGameAndUI Input;
			Input.SetWidgetToFocus(PauseMenu->TakeWidget());
			Player->SetInputMode(Input);
			Player->SetShowMouseCursor(true);
		}
	}
}
