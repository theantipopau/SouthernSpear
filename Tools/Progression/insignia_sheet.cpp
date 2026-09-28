// Southern Spear - render every rank's insignia and the level/XP table outside Unreal (ADR-034).
//
// Compiles the exact headers the game uses (SSInsigniaRaster.h, SSServiceLevelMath.h).
// Input (stdin), one rank per line, from Tools/Progression/rank_preview.py:
//   <abbrev> <min_level> <chevrons> <pips> <crown 0/1> <crest 0/1> <sword 0/1>
// Output: <out>.raw (8-bit alpha, ranks side by side, Size px each) and the table on stdout.
//
// Built and run by Tools/Progression/rank_preview.py (g++ -std=c++20 -Wall -Wextra -Werror).

#include <cstdio>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

#include "SSInsigniaRaster.h"
#include "SSServiceLevelMath.h"

int main(int argc, char** argv)
{
	if (argc < 5)
	{
		std::fprintf(stderr, "usage: insignia_sheet <out.raw> <size> <xp_scale> <xp_exponent> [max_level]\n");
		return 2;
	}
	const std::string Out = argv[1];
	const int Size = std::stoi(argv[2]);
	const double Scale = std::stod(argv[3]);
	const double Exponent = std::stod(argv[4]);
	const int MaxLevel = argc > 5 ? std::stoi(argv[5]) : 100;

	struct FRank { std::string Abbrev; int MinLevel; SSInsigniaRaster::FSpec Spec; };
	std::vector<FRank> Ranks;
	std::string Abbrev;
	int MinLevel, Chevrons, Pips, Crown, Crest, Sword;
	while (std::cin >> Abbrev >> MinLevel >> Chevrons >> Pips >> Crown >> Crest >> Sword)
	{
		SSInsigniaRaster::FSpec Spec;
		Spec.Chevrons = Chevrons; Spec.Pips = Pips; Spec.bCrown = Crown; Spec.bCrest = Crest; Spec.bSwordAndBaton = Sword;
		Ranks.push_back({ Abbrev, MinLevel, Spec });
	}
	if (Ranks.empty())
	{
		std::fprintf(stderr, "no ranks on stdin\n");
		return 2;
	}

	// Sheet: one row, ranks side by side.
	const int Width = Size * static_cast<int>(Ranks.size());
	std::vector<unsigned char> Sheet(static_cast<size_t>(Width) * Size, 0);
	std::vector<unsigned char> Tile(static_cast<size_t>(Size) * Size);
	int Failures = 0;
	for (size_t R = 0; R < Ranks.size(); ++R)
	{
		SSInsigniaRaster::Rasterize(Ranks[R].Spec, Size, Tile.data());
		long Ink = 0;
		for (int Y = 0; Y < Size; ++Y)
		{
			for (int X = 0; X < Size; ++X)
			{
				Sheet[static_cast<size_t>(Y) * Width + R * Size + X] = Tile[static_cast<size_t>(Y) * Size + X];
				Ink += Tile[static_cast<size_t>(Y) * Size + X] > 127 ? 1 : 0;
			}
		}
		const bool bEmpty = SSInsigniaRaster::IsEmpty(Ranks[R].Spec);
		const double Coverage = 100.0 * Ink / (Size * Size);
		// A rank with devices must draw something visible; a plain rank must draw nothing.
		const bool bOk = bEmpty ? Ink == 0 : Coverage > 3.0;
		Failures += bOk ? 0 : 1;
		const int NextMin = R + 1 < Ranks.size() ? Ranks[R + 1].MinLevel : MaxLevel + 1;
		char Upper[32] = "";	// the top rank has no upper bound
		if (NextMin <= MaxLevel)
		{
			std::snprintf(Upper, sizeof(Upper), "%lld", SSServiceLevelMath::XpForLevel(NextMin, Scale, Exponent) - 1);
		}
		std::printf("%-7s levels %3d-%-3d  XP %8lld-%-8s  ink %5.1f%%  %s\n", Ranks[R].Abbrev.c_str(),
			Ranks[R].MinLevel, NextMin - 1, SSServiceLevelMath::XpForLevel(Ranks[R].MinLevel, Scale, Exponent),
			Upper, Coverage, bOk ? "ok" : "FAIL");
	}

	// Level maths: monotonic, and LevelForXp inverts XpForLevel at every threshold.
	for (int Level = 1; Level <= MaxLevel; ++Level)
	{
		const long long Xp = SSServiceLevelMath::XpForLevel(Level, Scale, Exponent);
		if (SSServiceLevelMath::LevelForXp(Xp, Scale, Exponent, MaxLevel) != Level
			|| (Level > 1 && SSServiceLevelMath::LevelForXp(Xp - 1, Scale, Exponent, MaxLevel) != Level - 1)
			|| (Level > 1 && Xp <= SSServiceLevelMath::XpForLevel(Level - 1, Scale, Exponent)))
		{
			std::printf("level maths FAIL at level %d\n", Level);
			++Failures;
		}
	}
	std::printf("level %d needs %lld XP; LevelForXp(huge) = %d\n", MaxLevel,
		SSServiceLevelMath::XpForLevel(MaxLevel, Scale, Exponent), SSServiceLevelMath::LevelForXp(1LL << 40, Scale, Exponent, MaxLevel));

	std::ofstream File(Out, std::ios::binary);
	File.write(reinterpret_cast<const char*>(Sheet.data()), static_cast<std::streamsize>(Sheet.size()));
	std::printf("%s: %d x %d, %zu ranks, %d failure(s)\n", Out.c_str(), Width, Size, Ranks.size(), Failures);
	return Failures == 0 ? 0 : 1;
}
