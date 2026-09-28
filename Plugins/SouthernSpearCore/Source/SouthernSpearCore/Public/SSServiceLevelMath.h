// Copyright Southern Spear. All Rights Reserved.

#pragma once

// Engine-free on purpose (ADR-033): only the C++ standard library, so the same
// maths the game runs can be compiled and checked outside Unreal
// (Tools/Progression/level_table_check.cpp).

#include <cmath>

/**
 * Service level from service XP (ADR-033): level 1 at 0 XP, then
 * XpForLevel(n) = round(Scale * (n - 1) ^ Exponent), capped at MaxLevel.
 * An exponent above 1 makes each level cost more than the last, so level 100
 * (General) is rare, as honour 100 was.
 */
namespace SSServiceLevelMath
{
	inline long long XpForLevel(int Level, double Scale, double Exponent)
	{
		if (Level <= 1 || Scale <= 0.0 || Exponent <= 0.0)
		{
			return 0;
		}
		return static_cast<long long>(std::llround(Scale * std::pow(static_cast<double>(Level - 1), Exponent)));
	}

	inline int LevelForXp(long long Xp, double Scale, double Exponent, int MaxLevel)
	{
		if (MaxLevel < 1)
		{
			return 1;
		}
		int Level = 1;
		// At most MaxLevel steps; MaxLevel is small (100).
		while (Level < MaxLevel && Xp >= XpForLevel(Level + 1, Scale, Exponent))
		{
			++Level;
		}
		return Level;
	}
}
