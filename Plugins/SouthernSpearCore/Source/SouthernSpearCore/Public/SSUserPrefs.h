// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Misc/ConfigCacheIni.h"
#include "Subsystems/EngineSubsystem.h"
#include "SSUserPrefs.generated.h"

/**
 * Player preferences that are not UGameUserSettings fields, stored in
 * GameUserSettings.ini [SouthernSpear.Settings]. Written by the settings menu
 * (SouthernSpearUI); rendering ones are applied here (console variables),
 * input and audio ones by the Lyra bridge, field of view by the first-person
 * camera. Local and cosmetic only; never replicated, never read by gameplay
 * (ADR-004).
 */
namespace FSSUserPrefs
{
	inline const TCHAR* Section() { return TEXT("SouthernSpear.Settings"); }

	constexpr float MinFieldOfView = 70.f;
	constexpr float MaxFieldOfView = 110.f;

	// Keys (integers unless noted).
	inline const TCHAR* RayTracing()      { return TEXT("HardwareRayTracing"); } // Lumen GI and reflections, 0/1
	inline const TCHAR* RayTracedShadows(){ return TEXT("RayTracedShadows"); }   // 0/1
	inline const TCHAR* MotionBlur()      { return TEXT("MotionBlur"); }         // 0/1
	inline const TCHAR* AntiAliasing()    { return TEXT("AntiAliasing"); }       // 0 TSR, 1 TAA, 2 FXAA, 3 off
	inline const TCHAR* DevMessages()     { return TEXT("DeveloperMessages"); }  // engine on-screen messages, 0/1
	inline const TCHAR* ShowFps()         { return TEXT("ShowFps"); }            // HUD counter, 0/1
	inline const TCHAR* InvertY()         { return TEXT("InvertY"); }            // 0/1
	inline const TCHAR* Brightness()      { return TEXT("Brightness"); }         // float, display gamma 1.8-2.6
	inline const TCHAR* Sensitivity()     { return TEXT("MouseSensitivity"); }   // float, 0.2-3
	inline const TCHAR* MasterVolume()    { return TEXT("MasterVolume"); }       // float, 0-1
	inline const TCHAR* MusicVolume()     { return TEXT("MusicVolume"); }        // float, 0-1
	inline const TCHAR* EffectsVolume()   { return TEXT("EffectsVolume"); }      // float, 0-1

	inline int32 GetInt(const TCHAR* Key, int32 Default)
	{
		int32 Value = Default;
		if (GConfig) { GConfig->GetInt(Section(), Key, Value, GGameUserSettingsIni); }
		return Value;
	}

	inline float GetFloat(const TCHAR* Key, float Default)
	{
		float Value = Default;
		if (GConfig) { GConfig->GetFloat(Section(), Key, Value, GGameUserSettingsIni); }
		return Value;
	}

	inline void SetInt(const TCHAR* Key, int32 Value)
	{
		if (GConfig) { GConfig->SetInt(Section(), Key, Value, GGameUserSettingsIni); GConfig->Flush(false, GGameUserSettingsIni); }
	}

	inline void SetFloat(const TCHAR* Key, float Value)
	{
		if (GConfig) { GConfig->SetFloat(Section(), Key, Value, GGameUserSettingsIni); GConfig->Flush(false, GGameUserSettingsIni); }
	}

	/** Horizontal field of view, hip fire. Aiming narrows it proportionally. */
	inline float GetFieldOfView() { return FMath::Clamp(GetFloat(TEXT("FieldOfView"), 90.f), MinFieldOfView, MaxFieldOfView); }
	inline void SetFieldOfView(float Value) { SetFloat(TEXT("FieldOfView"), FMath::Clamp(Value, MinFieldOfView, MaxFieldOfView)); }

	/** Pushes the rendering preferences into console variables and the engine. */
	SSCORE_API void ApplyRendering();
}

/** Applies the rendering preferences at startup and after every map load. */
UCLASS()
class SSCORE_API USSUserPrefsSubsystem : public UEngineSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

private:
	FDelegateHandle PostLoadHandle;
};
