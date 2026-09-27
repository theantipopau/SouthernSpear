// Copyright Southern Spear. All Rights Reserved.

#include "SSBallistics.h"

bool FSSPenetrationRules::Penetrates(float ThicknessCm, const FSSPenetrationTuning& Tuning, float& OutDamageLost)
{
	OutDamageLost = 1.f;
	if (!(ThicknessCm >= 0.f) || ThicknessCm > Tuning.MaxThicknessCm || Tuning.MaxThicknessCm <= 0.f)
	{
		return false;
	}
	const float Alpha = ThicknessCm / Tuning.MaxThicknessCm;
	OutDamageLost = FMath::Clamp(FMath::Lerp(Tuning.MinDamageLost, Tuning.MaxDamageLost, Alpha), 0.f, 1.f);
	return true;
}
