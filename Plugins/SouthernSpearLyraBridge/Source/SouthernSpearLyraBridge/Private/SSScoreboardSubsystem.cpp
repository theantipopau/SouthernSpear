// Copyright Southern Spear. All Rights Reserved.

#include "SSScoreboardSubsystem.h"

#include "Engine/World.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerState.h"
#include "GameplayTagContainer.h"
#include "GenericTeamAgentInterface.h"
#include "SSScoreboardState.h"
#include "SSServiceRanks.h"

DEFINE_LOG_CATEGORY_STATIC(LogSSScoreboard, Log, All);

namespace
{
	int32 StatCount(APlayerState* PlayerState, const FGameplayTag& Tag)
	{
		struct FParams { FGameplayTag Tag; int32 ReturnValue = 0; } Params { Tag };
		UFunction* Function = PlayerState ? PlayerState->FindFunction(TEXT("GetStatTagStackCount")) : nullptr;
		if (!Function || Function->ParmsSize != sizeof(FParams) || !Tag.IsValid())
		{
			return 0;
		}
		PlayerState->ProcessEvent(Function, &Params);
		return Params.ReturnValue;
	}

	ESSTeamId ScoreboardTeamOf(const APlayerState* PlayerState)
	{
		const IGenericTeamAgentInterface* Agent = Cast<IGenericTeamAgentInterface>(PlayerState);
		const uint8 Id = Agent ? Agent->GetGenericTeamId().GetId() : FGenericTeamId::NoTeam.GetId();
		return Id == 1 ? ESSTeamId::TeamOne : Id == 2 ? ESSTeamId::TeamTwo : ESSTeamId::None;
	}
}

bool USSScoreboardSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId USSScoreboardSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USSScoreboardSubsystem, STATGROUP_Tickables);
}

void USSScoreboardSubsystem::Tick(float DeltaTime)
{
	Accumulator += DeltaTime;
	if (Accumulator < 0.5f)
	{
		return;
	}
	Accumulator = 0.f;
	UWorld* World = GetWorld();
	USSScoreboardState* State = World->GetSubsystem<USSScoreboardState>();
	const AGameStateBase* GameState = World->GetGameState();
	if (!State || !GameState)
	{
		return;
	}

	static const FGameplayTag Kills = FGameplayTag::RequestGameplayTag(TEXT("ShooterGame.Score.Eliminations"), false);
	static const FGameplayTag Deaths = FGameplayTag::RequestGameplayTag(TEXT("ShooterGame.Score.Deaths"), false);
	static const FGameplayTag Assists = FGameplayTag::RequestGameplayTag(TEXT("ShooterGame.Score.Assists"), false);
	const APlayerController* LocalController = World->GetFirstPlayerController();
	const APlayerState* LocalState = LocalController ? LocalController->PlayerState.Get() : nullptr;

	State->Rows.Reset();
	State->LocalTeam = ScoreboardTeamOf(LocalState);
	for (APlayerState* PlayerState : GameState->PlayerArray)
	{
		if (!PlayerState || PlayerState->IsOnlyASpectator())
		{
			continue;
		}
		FSSScoreRow& Row = State->Rows.AddDefaulted_GetRef();
		Row.Name = PlayerState->GetPlayerName();
		Row.Team = ScoreboardTeamOf(PlayerState);
		Row.Kills = StatCount(PlayerState, Kills);
		Row.Deaths = StatCount(PlayerState, Deaths);
		Row.Assists = StatCount(PlayerState, Assists);
		Row.bBot = PlayerState->IsABot();
		Row.bLocal = PlayerState == LocalState;
		Row.PingMs = Row.bBot ? -1 : FMath::RoundToInt(PlayerState->GetPingInMilliseconds());
		// ADR-033: level and insignia, replicated on the player state by progression.
		const USSServiceRankComponent* Rank = PlayerState->FindComponentByClass<USSServiceRankComponent>();
		Row.ServiceLevel = Rank ? Rank->GetServiceLevel() : 0;
	}
	State->Rows.Sort([](const FSSScoreRow& A, const FSSScoreRow& B)
	{
		return A.Kills != B.Kills ? A.Kills > B.Kills : A.Deaths < B.Deaths;
	});

	// -SSScoreDebug: log the table every 30 s (headless verification).
	DebugAccumulator += 0.5f;
	if (DebugAccumulator >= 30.f && FParse::Param(FCommandLine::Get(), TEXT("SSScoreDebug")))
	{
		DebugAccumulator = 0.f;
		for (const FSSScoreRow& Row : State->Rows)
		{
			UE_LOG(LogSSScoreboard, Log, TEXT("%s team=%d K=%d D=%d A=%d ping=%d%s"), *Row.Name, (int32)Row.Team,
				Row.Kills, Row.Deaths, Row.Assists, Row.PingMs, Row.bLocal ? TEXT(" (local)") : TEXT(""));
		}
	}
}
