// Copyright Southern Spear. All Rights Reserved.

#include "SSProgressionSubsystems.h"

#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "HAL/PlatformTime.h"
#include "Misc/Paths.h"
#include "SSLocalProfileState.h"
#include "SSProgressionSettings.h"

#define LOCTEXT_NAMESPACE "SSProgression"

namespace
{
	const USSProgressionSettings& ProgressionSettings()
	{
		return *GetDefault<USSProgressionSettings>();
	}

	/** Log a broken table once per process: awards still run, but the fault is visible. */
	void ValidateSettingsOnce()
	{
		static bool bDone = false;
		if (bDone)
		{
			return;
		}
		bDone = true;
		TArray<FString> Errors;
		FSSProgressionRules::ValidateRanks(ProgressionSettings().Ranks, Errors);
		FSSProgressionRules::ValidateAwards(ProgressionSettings().Awards, Errors);
		for (const FString& Error : Errors)
		{
			UE_LOG(LogSSProgression, Error, TEXT("Progression settings: %s"), *Error);
		}
	}
}

// --- Relay ------------------------------------------------------------------

USSServiceRelay::USSServiceRelay()
{
	SetIsReplicatedByDefault(true);
}

void USSServiceRelay::ClientServiceAward_Implementation(ESSServiceEvent Event, int32 XpDelta)
{
	const UWorld* World = GetWorld();
	UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
	if (USSPlayerProfileSubsystem* Profile = GameInstance ? GameInstance->GetSubsystem<USSPlayerProfileSubsystem>() : nullptr)
	{
		Profile->ApplyServiceAward(Event, XpDelta);
	}
}

// --- Server -----------------------------------------------------------------

void USSProgressionServerSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	USSServiceEventSubsystem* Bus = Collection.InitializeDependency<USSServiceEventSubsystem>();
	if (Bus)
	{
		BusHandle = Bus->OnServiceEvent.AddUObject(this, &ThisClass::HandleServiceEventFromBus);
	}
	ValidateSettingsOnce();
}

void USSProgressionServerSubsystem::Deinitialize()
{
	if (USSServiceEventSubsystem* Bus = GetWorld() ? GetWorld()->GetSubsystem<USSServiceEventSubsystem>() : nullptr)
	{
		Bus->OnServiceEvent.Remove(BusHandle);
	}
	Tallies.Reset();
	Super::Deinitialize();
}

bool USSProgressionServerSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId USSProgressionServerSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USSProgressionServerSubsystem, STATGROUP_Tickables);
}

void USSProgressionServerSubsystem::Tick(float DeltaTime)
{
	UWorld* World = GetWorld();
	if (!World || World->GetNetMode() == NM_Client)
	{
		return;
	}
	Accumulator += DeltaTime;
	if (Accumulator < 0.5f)
	{
		return;
	}
	Accumulator = 0.f;

	// Relays exist before any award, so the component has replicated to its
	// owner by the time the first reliable RPC is sent on it.
	for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
	{
		RelayFor(It->Get());
	}
}

USSServiceRelay* USSProgressionServerSubsystem::RelayFor(APlayerController* Controller)
{
	if (!Controller)
	{
		return nullptr;
	}
	if (USSServiceRelay* Existing = Controller->FindComponentByClass<USSServiceRelay>())
	{
		return Existing;
	}
	USSServiceRelay* Relay = NewObject<USSServiceRelay>(Controller, TEXT("SSServiceRelay"));
	Relay->RegisterComponent();
	return Relay;
}

void USSProgressionServerSubsystem::HandleServiceEventFromBus(AController* Player, ESSServiceEvent Event)
{
	HandleServiceEvent(Player, Event);
}

int32 USSProgressionServerSubsystem::HandleServiceEvent(AController* Player, ESSServiceEvent Event)
{
	APlayerController* Controller = Cast<APlayerController>(Player);
	if (!Controller)
	{
		return 0; // bots have no service record
	}

	FSSMatchTally& Tally = Tallies.FindOrAdd(Controller);
	const int32 Xp = FSSProgressionRules::GrantAward(Tally, Event, ProgressionSettings().Awards);
	if (Event == ESSServiceEvent::MatchCompleted)
	{
		Tallies.Remove(Controller); // the next match starts a fresh tally
	}

	UE_LOG(LogSSProgression, Log, TEXT("Service: %s %s %+d XP."),
		*Controller->GetName(), USSServiceEventSubsystem::LexEvent(Event), Xp);
	if (USSServiceRelay* Relay = RelayFor(Controller))
	{
		Relay->ClientServiceAward(Event, Xp);
	}
	return Xp;
}

// --- Client profile -----------------------------------------------------------

bool USSPlayerProfileSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	// A dedicated server has no local player and no local record.
	return !IsRunningDedicatedServer() && Super::ShouldCreateSubsystem(Outer);
}

void USSPlayerProfileSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	Collection.InitializeDependency<USSLocalProfileState>();
	ValidateSettingsOnce();
	Provider = MakeUnique<FSSLocalDevPersistence>(FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("SouthernSpear"), TEXT("Profiles")));
	LoadOrCreate();
	Publish();
}

void USSPlayerProfileSubsystem::LoadOrCreate()
{
	FString Error;
	const ESSRecordLoad Result = Provider->LoadServiceRecord(LocalPlayerId(), Record, Error);
	switch (Result)
	{
	case ESSRecordLoad::Loaded:
		UE_LOG(LogSSProgression, Log, TEXT("Service record loaded: %d XP, %d match(es) (dev-only local record)."),
			Record.ServiceXp, Record.Statistics.MatchesCompleted);
		return;

	case ESSRecordLoad::FromNewerVersion:
		// Keep the file exactly as it is and play on a blank record that is never written.
		UE_LOG(LogSSProgression, Error, TEXT("%s Progress this session will not be saved."), *Error);
		bWritable = false;
		Record = FSSServiceRecord();
		Record.PlayerId = LocalPlayerId();
		return;

	case ESSRecordLoad::Unreadable:
	{
		const FString Aside = Provider->QuarantineRecord(LocalPlayerId());
		UE_LOG(LogSSProgression, Error, TEXT("%s Kept it as %s and started a new record."), *Error,
			Aside.IsEmpty() ? TEXT("(could not move it)") : *Aside);
		if (Aside.IsEmpty())
		{
			bWritable = false; // never overwrite a record we could not move aside
		}
		break;
	}

	case ESSRecordLoad::NotFound:
	default:
		UE_LOG(LogSSProgression, Log, TEXT("No service record yet; creating one."));
		break;
	}

	Record = FSSServiceRecord();
	Record.PlayerId = LocalPlayerId();
	Record.CreatedUtc = FDateTime::UtcNow().ToIso8601();
	Save();
}

void USSPlayerProfileSubsystem::Save()
{
	if (!bWritable || !Provider)
	{
		return;
	}
	Record.LastSavedUtc = FDateTime::UtcNow().ToIso8601();
	FString Error;
	if (!Provider->SaveServiceRecord(Record, Error))
	{
		UE_LOG(LogSSProgression, Error, TEXT("Service record not saved: %s"), *Error);
	}
}

void USSPlayerProfileSubsystem::ApplyServiceAward(ESSServiceEvent Event, int32 XpDelta)
{
	const int32 RankBefore = FSSProgressionRules::ResolveRankIndex(Record.ServiceXp, ProgressionSettings().Ranks);
	FSSProgressionRules::ApplyAward(Record, Event, XpDelta);
	Save();
	Publish();

	USSLocalProfileState* State = GetGameInstance()->GetSubsystem<USSLocalProfileState>();
	if (State && XpDelta != 0)
	{
		State->LastAward = FText::Format(LOCTEXT("Award", "{0}  {1}{2}"),
			FSSProgressionRules::EventName(Event), FText::FromString(XpDelta > 0 ? TEXT("+") : TEXT("")), FText::AsNumber(XpDelta));
		State->LastAwardTime = FPlatformTime::Seconds();
	}
	const int32 RankAfter = FSSProgressionRules::ResolveRankIndex(Record.ServiceXp, ProgressionSettings().Ranks);
	if (RankAfter != RankBefore && ProgressionSettings().Ranks.IsValidIndex(RankAfter))
	{
		UE_LOG(LogSSProgression, Log, TEXT("Rank changed: %s."), *ProgressionSettings().Ranks[RankAfter].DisplayName.ToString());
	}
}

bool USSPlayerProfileSubsystem::SetCallsign(const FString& NewCallsign)
{
	if (!FSSProgressionRules::IsValidCallsign(NewCallsign))
	{
		return false;
	}
	Record.Callsign = NewCallsign.TrimStartAndEnd();
	Save();
	Publish();
	return true;
}

void USSPlayerProfileSubsystem::Publish()
{
	USSLocalProfileState* State = GetGameInstance() ? GetGameInstance()->GetSubsystem<USSLocalProfileState>() : nullptr;
	if (!State)
	{
		return;
	}
	const TArray<FSSRankDefinition>& Ranks = ProgressionSettings().Ranks;
	const int32 Index = FSSProgressionRules::ResolveRankIndex(Record.ServiceXp, Ranks);

	State->bLoaded = true;
	State->Callsign = Record.Callsign.IsEmpty() ? LOCTEXT("NoCallsign", "Unassigned").ToString() : Record.Callsign;
	State->ServiceXp = Record.ServiceXp;
	State->MatchesCompleted = Record.Statistics.MatchesCompleted;
	State->RoundsWon = Record.Statistics.RoundsWon;
	State->RankIndex = FMath::Max(0, Index);
	if (Ranks.IsValidIndex(Index))
	{
		State->RankName = Ranks[Index].DisplayName;
		State->RankAbbreviation = Ranks[Index].Abbreviation;
		State->RankFloorXp = Ranks[Index].MinServiceXp;
		State->NextRankXp = Ranks.IsValidIndex(Index + 1) ? Ranks[Index + 1].MinServiceXp : -1;
	}
	else
	{
		State->RankName = LOCTEXT("NoRanks", "Unranked");
		State->RankAbbreviation = FText::GetEmpty();
		State->RankFloorXp = 0;
		State->NextRankXp = -1;
	}
}

#undef LOCTEXT_NAMESPACE
