// Copyright Southern Spear. All Rights Reserved.

#include "SSObjectiveHudSubsystem.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "SSObjectiveAssaultDirector.h"
#include "SSObjectiveStatusWidget.h"
#include "SSMinimapWidget.h"
#include "SSCompassWidget.h"
#include "SSRoundBannerWidget.h"
#include "InputCoreTypes.h"
#include "SSObjectiveTypes.h"
#include "SSScoreboardState.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "UnrealClient.h"

IMPLEMENT_MODULE(FDefaultModuleImpl, SouthernSpearObjectivesUI)

bool USSObjectiveHudSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* World = Cast<UWorld>(Outer);
	return World && World->GetNetMode() != NM_DedicatedServer && Super::ShouldCreateSubsystem(Outer);
}

bool USSObjectiveHudSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId USSObjectiveHudSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USSObjectiveHudSubsystem, STATGROUP_Tickables);
}

void USSObjectiveHudSubsystem::Tick(float DeltaTime)
{
	// The scoreboard (SouthernSpearUI, Core-only) names the rule set from here:
	// only this module can see the director. RulesMode replicates.
	if (USSScoreboardState* Scores = GetWorld() ? GetWorld()->GetSubsystem<USSScoreboardState>() : nullptr)
	{
		const ASSObjectiveAssaultDirector* Director = nullptr;
		for (TActorIterator<ASSObjectiveAssaultDirector> It(GetWorld()); It; ++It)
		{
			Director = *It;
			break;
		}
		Scores->ModeTitle = !Director ? FText::GetEmpty() : Director->IsSectionAssault()
			? NSLOCTEXT("SSScore", "SectionAssault", "SECTION ASSAULT  ·  ONE LIFE")
			: NSLOCTEXT("SSScore", "ObjectiveAssault", "OBJECTIVE ASSAULT");
	}

	// Dev capture: -SSShotAt=<seconds> takes one viewport screenshot
	// (Saved/Screenshots) without touching the desktop or window focus.
	ElapsedSeconds += DeltaTime;
	float ShotAt = 0.f;
	if (!bShotTaken && FParse::Value(FCommandLine::Get(), TEXT("SSShotAt="), ShotAt) && ElapsedSeconds >= ShotAt)
	{
		bShotTaken = true;
		FScreenshotRequest::RequestScreenshot(TEXT("SSShot.png"), /*bShowUI=*/ true, /*bAddFilenameSuffix=*/ false);
		UE_LOG(LogSSObjectives, Log, TEXT("Requested viewport screenshot at %.1f s."), ElapsedSeconds);
	}
	// Dev scripting: -SSExecAt=<seconds> -SSExec="cmd1|cmd2" runs console commands as the local player
	// once (after the pawn exists, unlike -ExecCmds, which runs at startup).
	float ExecAt = 0.f;
	FString Exec;
	if (!bExecDone && FParse::Value(FCommandLine::Get(), TEXT("SSExecAt="), ExecAt) && ElapsedSeconds >= ExecAt
		&& FParse::Value(FCommandLine::Get(), TEXT("SSExec="), Exec, /*bShouldStopOnSeparator=*/ false))
	{
		if (APlayerController* Player = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr)
		{
			bExecDone = true;
			TArray<FString> Commands;
			Exec.ParseIntoArray(Commands, TEXT("|"));
			for (const FString& Command : Commands)
			{
				UE_LOG(LogSSObjectives, Log, TEXT("SSExec at %.1f s: %s"), ElapsedSeconds, *Command);
				Player->ConsoleCommand(Command.TrimStartAndEnd());
			}
		}
	}

	if (StatusWidget)
	{
		APlayerController* Owner = StatusWidget->GetOwningPlayer();
		if (FullMap && Owner && Owner->WasInputKeyJustPressed(EKeys::M))
		{
			const bool bOpen = !FullMap->IsVisible();
			FullMap->SetVisibility(bOpen ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
			if (bOpen)
			{
				FullMap->Refresh();
			}
		}
		return;
	}
	// The local player and the (replicated) director can arrive in any order.
	RetryAccumulator += DeltaTime;
	if (RetryAccumulator < 0.5f)
	{
		return;
	}
	RetryAccumulator = 0.f;

	UWorld* World = GetWorld();
	APlayerController* Player = World ? World->GetFirstPlayerController() : nullptr;
	// Headless test worlds (e.g. network smoke tests) have no viewport to draw into.
	if (!Player || !Player->IsLocalController() || !World->GetGameViewport())
	{
		return;
	}
	TActorIterator<ASSObjectiveAssaultDirector> It(World);
	if (!It)
	{
		return;
	}

	StatusWidget = CreateWidget<USSObjectiveStatusWidget>(Player, USSObjectiveStatusWidget::StaticClass());
	if (!StatusWidget)
	{
		UE_LOG(LogSSObjectives, Error, TEXT("Objective status widget could not be created."));
		return;
	}
	StatusWidget->SetDirector(*It);
	StatusWidget->AddToViewport(10);

	Minimap = CreateWidget<USSMinimapWidget>(Player, USSMinimapWidget::StaticClass());
	if (Minimap)
	{
		Minimap->Setup(*It, /*bFullMap=*/ false);
		Minimap->AddToViewport(9);
	}
	Compass = CreateWidget<USSCompassWidget>(Player, USSCompassWidget::StaticClass());
	if (Compass)
	{
		Compass->Setup(*It);
		Compass->AddToViewport(9);
	}
	Banner = CreateWidget<USSRoundBannerWidget>(Player, USSRoundBannerWidget::StaticClass());
	if (Banner)
	{
		Banner->Setup(*It);
		Banner->AddToViewport(12);
	}
	FullMap = CreateWidget<USSMinimapWidget>(Player, USSMinimapWidget::StaticClass());
	if (FullMap)
	{
		FullMap->Setup(*It, /*bFullMap=*/ true);
		FullMap->SetVisibility(ESlateVisibility::Collapsed);
		FullMap->AddToViewport(20);
	}
	UE_LOG(LogSSObjectives, Log, TEXT("Objective status widget shown for %s."), *Player->GetName());
}
