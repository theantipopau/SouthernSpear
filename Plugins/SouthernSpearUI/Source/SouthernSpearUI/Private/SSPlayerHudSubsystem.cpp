// Copyright Southern Spear. All Rights Reserved.

#include "SSPlayerHudSubsystem.h"

#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "SSLocalHudState.h"
#include "SSClassSelectWidget.h"
#include "SSMenuWidget.h"
#include "SSPlayerHudWidget.h"
#include "SSScoreboardWidget.h"
#include "SSKillFeedState.h"
#include "SSKillFeedWidget.h"
#include "UObject/UObjectIterator.h"

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
			KillFeed = CreateWidget<USSKillFeedWidget>(Player, USSKillFeedWidget::StaticClass());
			if (KillFeed)
			{
				KillFeed->AddToViewport(6);
			}
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
		if (bHadPawn && !bHasPawn)
		{
			bClassSelectPending = true;
		}
		// After a death, "KILLED IN ACTION" shows first (the kill feed widget); then the class selection.
		const USSKillFeedState* Feed = World->GetSubsystem<USSKillFeedState>();
		const bool bKiaShowing = Feed && FSSKillFeedRules::RecentLocalDeath(Feed->Entries, World->GetTimeSeconds()) != nullptr;
		if (bClassSelectPending && (bHasPawn || !bKiaShowing))
		{
			bClassSelectPending = false;
			if (!bHasPawn && !ClassSelect->IsVisible())
			{
				ClassSelect->Open(/*bAfterDeath=*/ true);
			}
		}
		else if (Player->WasInputKeyJustPressed(EKeys::L))
		{
			ClassSelect->IsVisible() ? ClassSelect->Close() : ClassSelect->Open(!bHasPawn);
		}
	}
	bHadPawn = bHasPawn;

	// Scoreboard while Tab is held (-SSShowScoreboard keeps it up for captures).
	if (!Scoreboard)
	{
		Scoreboard = CreateWidget<USSScoreboardWidget>(Player, USSScoreboardWidget::StaticClass());
		if (Scoreboard)
		{
			Scoreboard->AddToViewport(30);
		}
	}
	if (Scoreboard)
	{
		static const bool bForce = FParse::Param(FCommandLine::Get(), TEXT("SSShowScoreboard"));
		const bool bShow = bForce || Player->IsInputKeyDown(EKeys::Tab);
		Scoreboard->SetVisibility(bShow ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
		if (bShow)
		{
			// ShooterCore's input pushes Lyra's own red/blue scoreboard on the same key, drawn under ours.
			// Matched by class name so this module keeps no Lyra dependency; vendored content stays unmodified.
			for (TObjectIterator<UUserWidget> It; It; ++It)
			{
				UUserWidget* Widget = *It;
				if (Widget && Widget != Scoreboard && Widget->GetWorld() == World && Widget->GetClass()->GetName().Contains(TEXT("ScoreBoard"))
					&& Widget->GetVisibility() != ESlateVisibility::Collapsed)
				{
					Widget->SetVisibility(ESlateVisibility::Collapsed);
				}
			}
		}
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
