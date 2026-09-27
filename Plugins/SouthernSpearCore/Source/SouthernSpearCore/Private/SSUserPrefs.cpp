// Copyright Southern Spear. All Rights Reserved.

#include "SSUserPrefs.h"

#include "Engine/Engine.h"
#include "HAL/IConsoleManager.h"
#include "UObject/UObjectGlobals.h"

namespace
{
	void SetCVar(const TCHAR* Name, int32 Value)
	{
		if (IConsoleVariable* Var = IConsoleManager::Get().FindConsoleVariable(Name))
		{
			Var->Set(Value, ECVF_SetByGameSetting);
		}
	}
}

void FSSUserPrefs::ApplyRendering()
{
	if (GIsEditor && !IsRunningGame())
	{
		return; // editor viewports and PIE keep the editor's own settings
	}
	SetCVar(TEXT("r.Lumen.HardwareRayTracing"), GetInt(RayTracing(), 1));
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
