// Copyright Southern Spear. All Rights Reserved.

#include "SSSettingsSyncSubsystem.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/GameUserSettings.h"
#include "GameFramework/PlayerController.h"
#include "Engine/LocalPlayer.h"
#include "SSUserPrefs.h"

namespace
{
	template <typename TValue>
	void CallSetter(UObject* Target, const TCHAR* Name, TValue Value)
	{
		UFunction* Function = Target ? Target->FindFunction(FName(Name)) : nullptr;
		if (Function && Function->ParmsSize == sizeof(TValue))
		{
			Target->ProcessEvent(Function, &Value);
		}
	}
}

bool USSSettingsSyncSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId USSSettingsSyncSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USSSettingsSyncSubsystem, STATGROUP_Tickables);
}

void USSSettingsSyncSubsystem::Tick(float DeltaTime)
{
	Accumulator += DeltaTime;
	if (Accumulator < 0.5f)
	{
		return;
	}
	Accumulator = 0.f;

	const double Sensitivity = FMath::Clamp(FSSUserPrefs::GetFloat(FSSUserPrefs::Sensitivity(), 1.f), 0.2f, 3.f);
	const bool bInvert = FSSUserPrefs::GetInt(FSSUserPrefs::InvertY(), 0) != 0;
	const float Master = FMath::Clamp(FSSUserPrefs::GetFloat(FSSUserPrefs::MasterVolume(), 1.f), 0.f, 1.f);
	const float Music = FMath::Clamp(FSSUserPrefs::GetFloat(FSSUserPrefs::MusicVolume(), 1.f), 0.f, 1.f);
	const float Effects = FMath::Clamp(FSSUserPrefs::GetFloat(FSSUserPrefs::EffectsVolume(), 1.f), 0.f, 1.f);
	const APlayerController* Player = GetWorld()->GetFirstPlayerController();
	ULocalPlayer* Local = Player ? Player->GetLocalPlayer() : nullptr;
	const FString Key = FString::Printf(TEXT("%.3f|%d|%.3f|%.3f|%.3f|%p"), Sensitivity, bInvert, Master, Music, Effects, Local);
	if (Key == LastApplied || !Local)
	{
		return;
	}
	LastApplied = Key;

	// ULyraLocalPlayer::GetSharedSettings (UFUNCTION; Lyra's player headers
	// pull in CommonUI, which the bridge does not link).
	struct FSharedParams { UObject* ReturnValue = nullptr; } Params;
	if (UFunction* Getter = Local->FindFunction(TEXT("GetSharedSettings")); Getter && Getter->ParmsSize == sizeof(FSharedParams))
	{
		Local->ProcessEvent(Getter, &Params);
	}
	if (UObject* Shared = Params.ReturnValue)
	{
		CallSetter(Shared, TEXT("SetMouseSensitivityX"), Sensitivity);
		CallSetter(Shared, TEXT("SetMouseSensitivityY"), Sensitivity);
		CallSetter(Shared, TEXT("SetInvertVerticalAxis"), bInvert);
	}
	if (UObject* LocalSettings = GEngine ? GEngine->GetGameUserSettings() : nullptr)
	{
		CallSetter(LocalSettings, TEXT("SetOverallVolume"), Master);
		CallSetter(LocalSettings, TEXT("SetMusicVolume"), Music);
		CallSetter(LocalSettings, TEXT("SetSoundFXVolume"), Effects);
	}
}
