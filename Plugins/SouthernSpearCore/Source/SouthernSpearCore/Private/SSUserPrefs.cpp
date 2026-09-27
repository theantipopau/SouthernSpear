// Copyright Southern Spear. All Rights Reserved.

#include "SSUserPrefs.h"

#include "Engine/Engine.h"
#include "GameFramework/GameUserSettings.h"
#include "HAL/IConsoleManager.h"
#include "UObject/UObjectGlobals.h"

namespace
{
	void SetCVar(const TCHAR* Name, int32 Value)
	{
		if (IConsoleVariable* Var = IConsoleManager::Get().FindConsoleVariable(Name))
		{
			// Game-override priority: project defaults (DefaultEngine.ini) sit above
			// SetByGameSetting and silently won over the player's choice.
			Var->Set(Value, ECVF_SetByGameOverride);
		}
	}
}

void FSSUserPrefs::ApplyRendering()
{
	if (GIsEditor && !IsRunningGame())
	{
		return; // editor viewports and PIE keep the editor's own settings
	}
	// Hardware ray tracing defaults off: with it on, Nanite-converted rocks and the weapons rendered
	// black (Saltbush, producer "textures are horrible", 2026-09-27). Software Lumen is the default.
	SetCVar(TEXT("r.Lumen.HardwareRayTracing"), GetInt(RayTracing(), 0));
	SetCVar(TEXT("r.RayTracing.Shadows"), GetInt(RayTracedShadows(), 0));
	SetCVar(TEXT("r.MotionBlurQuality"), GetInt(MotionBlur(), 1) ? 4 : 0);

	// 0 TSR, 1 TAA, 2 FXAA, 3 off -> r.AntiAliasingMethod 4, 2, 1, 0.
	static const int32 Methods[] = { 4, 2, 1, 0 };
	SetCVar(TEXT("r.AntiAliasingMethod"), Methods[FMath::Clamp(GetInt(AntiAliasing(), 0), 0, 3)]);

	// Engine on-screen developer messages (Blueprint script warnings, editor
	// plugin tracebacks, shadow-map diagnostics) are off for players.
	const bool bDev = GetInt(DevMessages(), 0) != 0;
	GAreScreenMessagesEnabled = bDev;
	SetCVar(TEXT("r.Shadow.Virtual.AllowScreenOverflowMessages"), bDev ? 1 : 0);

	if (GEngine)
	{
		GEngine->DisplayGamma = FMath::Clamp(GetFloat(Brightness(), 2.2f), 1.8f, 2.6f);

		// sg.ResolutionQuality 0 means "project default", which in UE 5.8 renders
		// ~60% of a 1440p display and upscales: every texture looked smeared
		// (producer, 2026-09-27). Unset means native; Settings can lower it.
		// Only once a world exists: during engine start the game's settings
		// class (Lyra's) is not loaded yet and creating it asserts.
		if (UGameUserSettings* Settings = GWorld ? GEngine->GetGameUserSettings() : nullptr)
		{
			float Normalized, Value, Min, Max;
			Settings->GetResolutionScaleInformationEx(Normalized, Value, Min, Max);
			if (Value <= 0.f)
			{
				Settings->SetResolutionScaleValueEx(100.f);
				Settings->ApplyNonResolutionSettings();
				Settings->SaveSettings();
			}
		}
	}
}

void USSUserPrefsSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	FSSUserPrefs::ApplyRendering();
	PostLoadHandle = FCoreUObjectDelegates::PostLoadMapWithWorld.AddLambda([](UWorld*) { FSSUserPrefs::ApplyRendering(); });
}

void USSUserPrefsSubsystem::Deinitialize()
{
	FCoreUObjectDelegates::PostLoadMapWithWorld.Remove(PostLoadHandle);
	Super::Deinitialize();
}
