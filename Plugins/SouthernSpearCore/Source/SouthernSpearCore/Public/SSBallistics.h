// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

/**
 * Bullet penetration (ADR-026, D-09): a bullet passes through a surface no thicker than
 * MaxThicknessCm (sheet metal, timber, fences, thin walls) and loses damage with the thickness.
 * Landscape and characters are never penetrated (the bridge decides that).
 */
struct FSSPenetrationTuning
{
	float MaxThicknessCm = 20.f;
	/** Damage lost through the thinnest and the thickest penetrable surface (0..1). */
	float MinDamageLost = 0.25f;
	float MaxDamageLost = 0.75f;
};

struct SSCORE_API FSSPenetrationRules
{
	/** True if a surface this thick is penetrated; OutDamageLost is then the fraction of damage lost. */
	static bool Penetrates(float ThicknessCm, const FSSPenetrationTuning& Tuning, float& OutDamageLost);
};
