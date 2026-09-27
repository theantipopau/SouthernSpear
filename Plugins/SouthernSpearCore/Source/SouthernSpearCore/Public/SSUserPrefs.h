// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Misc/ConfigCacheIni.h"

/**
 * Player preferences that are not engine settings, stored in
 * GameUserSettings.ini [SouthernSpear.Settings]. Written by the settings menu
 * (SouthernSpearUI), read by presentation (the first-person camera). Local and
 * cosmetic only; never replicated, never read by gameplay (ADR-004).
 */
namespace FSSUserPrefs
{
	inline const TCHAR* Section() { return TEXT("SouthernSpear.Settings"); }

	constexpr float MinFieldOfView = 70.f;
	constexpr float MaxFieldOfView = 110.f;

	/** Horizontal field of view, hip fire. Aiming narrows it proportionally. */
	inline float GetFieldOfView()
	{
		float Value = 90.f;
		if (GConfig)
		{
			GConfig->GetFloat(Section(), TEXT("FieldOfView"), Value, GGameUserSettingsIni);
		}
		return FMath::Clamp(Value, MinFieldOfView, MaxFieldOfView);
	}

	inline void SetFieldOfView(float Value)
	{
		if (GConfig)
		{
			GConfig->SetFloat(Section(), TEXT("FieldOfView"), FMath::Clamp(Value, MinFieldOfView, MaxFieldOfView), GGameUserSettingsIni);
			GConfig->Flush(false, GGameUserSettingsIni);
		}
	}
}
