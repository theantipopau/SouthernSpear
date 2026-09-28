// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "SSTeamTypes.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSScoreboardState.generated.h"

/** One player on the scoreboard, as plain values. */
USTRUCT(BlueprintType)
struct FSSScoreRow
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Scoreboard") FString Name;
	UPROPERTY(BlueprintReadOnly, Category = "Scoreboard") ESSTeamId Team = ESSTeamId::None;
	UPROPERTY(BlueprintReadOnly, Category = "Scoreboard") int32 Kills = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Scoreboard") int32 Deaths = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Scoreboard") int32 Assists = 0;
	/** Round-trip time in ms; -1 for bots (no connection). */
	UPROPERTY(BlueprintReadOnly, Category = "Scoreboard") int32 PingMs = -1;
	UPROPERTY(BlueprintReadOnly, Category = "Scoreboard") bool bLocal = false;
	UPROPERTY(BlueprintReadOnly, Category = "Scoreboard") bool bBot = false;
	/** Service level 1..100 from USSServiceRankComponent (ADR-034); 0 without a record (bots). */
	UPROPERTY(BlueprintReadOnly, Category = "Scoreboard") int32 ServiceLevel = 0;
};

/**
 * Scoreboard rows for the local viewer. The Lyra bridge fills it from the
 * player states twice a second; UI modules only read it (ADR-019, guard
 * SS002/SS005). Client-local, never replicated, never read by gameplay.
 */
UCLASS()
class SSCORE_API USSScoreboardState : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Scoreboard")
	TArray<FSSScoreRow> Rows;

	/** The local viewer's team, for the friendly/opposing split. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Scoreboard")
	ESSTeamId LocalTeam = ESSTeamId::None;

	/** The running rule set's name ("SECTION ASSAULT"), filled by the objective HUD; empty until known. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Scoreboard")
	FText ModeTitle;
};
