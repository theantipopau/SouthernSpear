// Copyright Southern Spear. All Rights Reserved.

#include "SSObjectiveHudSubsystem.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "SSObjectiveAssaultDirector.h"
#include "SSObjectiveStatusWidget.h"
#include "SSObjectiveTypes.h"

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
	if (StatusWidget)
	{
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
	if (!Player || !Player->IsLocalController())
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
	UE_LOG(LogSSObjectives, Log, TEXT("Objective status widget shown for %s."), *Player->GetName());
}
