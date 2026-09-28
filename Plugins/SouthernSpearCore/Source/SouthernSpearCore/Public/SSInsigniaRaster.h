// Copyright Southern Spear. All Rights Reserved.

#pragma once

// Engine-free on purpose (ADR-034): only the C++ standard library, so the
// insignia the game draws can be rendered and inspected outside Unreal
// (Tools/Progression/rank_preview.py).

#include <algorithm>
#include <cmath>

/**
 * Australian Army rank insignia, drawn from a description rather than art
 * files (ADR-034). The devices follow the Army's own:
 *
 *   LCPL/CPL/SGT   one, two or three chevrons, point down
 *   WO2            crown (St Edward's pattern)
 *   WO1            Coat of Arms (shield, kangaroo and emu, star)
 *   2LT/LT/CAPT    one, two or three pips (Order of the Bath star), in a column
 *   MAJ            crown
 *   LTCOL/COL      crown above one or two pips
 *   BRIG           crown above three pips in a triangle
 *   MAJGEN         pip above crossed sword and baton
 *   LTGEN          crown above crossed sword and baton
 *   GEN            crown and pip above crossed sword and baton
 *
 * They are silhouettes sized for a scoreboard row, not heraldic reproductions.
 * The crown and the Coat of Arms are Crown and Commonwealth emblems: their use
 * is a release gate recorded in ADR-034 (R-55), as ADR-025 did for uniforms.
 *
 * Output is white coverage (0..255) on transparent, so the UI tints it.
 */
namespace SSInsigniaRaster
{
	struct FSpec
	{
		int Chevrons = 0;	// 0..3
		int Pips = 0;		// 0..3
		bool bCrown = false;
		bool bCrest = false;	// the Coat of Arms (WO1)
		bool bSwordAndBaton = false;
	};

	inline bool IsEmpty(const FSpec& Spec)
	{
		return Spec.Chevrons <= 0 && Spec.Pips <= 0 && !Spec.bCrown && !Spec.bCrest && !Spec.bSwordAndBaton;
	}

	namespace Detail
	{
		constexpr float Pi = 3.14159265f;

		inline float Length(float X, float Y) { return std::sqrt(X * X + Y * Y); }

		/** Distance from P to the segment AB. */
		inline float SegmentDistance(float Px, float Py, float Ax, float Ay, float Bx, float By)
		{
			const float Dx = Bx - Ax, Dy = By - Ay;
			const float LenSq = Dx * Dx + Dy * Dy;
			const float T = LenSq > 0.f ? std::clamp(((Px - Ax) * Dx + (Py - Ay) * Dy) / LenSq, 0.f, 1.f) : 0.f;
			return Length(Ax + T * Dx - Px, Ay + T * Dy - Py);
		}

		inline bool InEllipse(float X, float Y, float Cx, float Cy, float Rx, float Ry)
		{
			const float Dx = (X - Cx) / Rx, Dy = (Y - Cy) / Ry;
			return Dx * Dx + Dy * Dy <= 1.f;
		}

		inline bool InRect(float X, float Y, float X0, float Y0, float X1, float Y1)
		{
			return X >= X0 && X <= X1 && Y >= Y0 && Y <= Y1;
		}

		/** A star with Points points, outer radius R, inner radius R * Inner, one point straight up. */
		inline bool InStarPolygon(float X, float Y, float Cx, float Cy, float R, int Points, float Inner)
		{
			const float Dx = X - Cx, Dy = Y - Cy;
			const float Rho = Length(Dx, Dy);
			if (Rho > R)
			{
				return false;
			}
			const float Sector = 2.f * Pi / Points;
			float Theta = std::atan2(Dx, -Dy);	// 0 at the top, clockwise
			Theta = std::fmod(Theta + 2.f * Pi, Sector);
			const float T = std::abs(Theta / Sector - 0.5f) * 2.f;	// 1 on a point, 0 between points
			// Straight edges between tip and notch: interpolate the radius along the angle.
			const float Edge = R * Inner + (R - R * Inner) * T;
			return Rho <= Edge;
		}

		/**
		 * The officer's pip, after the Order of the Bath star: eight points
		 * around a round centre, with the ring of the centre cut as a thin line.
		 * Unit square.
		 */
		inline bool InPip(float X, float Y)
		{
			const float Rho = Length(X - 0.5f, Y - 0.5f);
			if (Rho >= 0.18f && Rho <= 0.215f)
			{
				return false;	// the ring around the roundel
			}
			return Rho <= 0.2f || InStarPolygon(X, Y, 0.5f, 0.5f, 0.48f, 8, 0.52f);
		}

		/**
		 * The crown, after St Edward's pattern: band on a rim, cap under two
		 * arches that dip where they meet, orb and cross on top. Unit square.
		 */
		inline bool InCrown(float X, float Y)
		{
			// Band, with three jewels cut out, and the rim below it.
			if (InRect(X, Y, 0.16f, 0.7f, 0.84f, 0.84f))
			{
				const float Jewels[] = { 0.3f, 0.5f, 0.7f };
				for (const float J : Jewels)
				{
					if (InEllipse(X, Y, J, 0.77f, 0.035f, 0.035f))
					{
						return false;
					}
				}
				return true;
			}
			if (InRect(X, Y, 0.12f, 0.84f, 0.88f, 0.92f))
			{
				return true;
			}
			// Arches: two lobes, so the outline dips in the middle, each drawn as a
			// band with the cap showing lower down inside it.
			if (Y < 0.72f)
			{
				const bool bOuter = InEllipse(X, Y, 0.33f, 0.72f, 0.19f, 0.4f) || InEllipse(X, Y, 0.67f, 0.72f, 0.19f, 0.4f);
				const bool bInner = InEllipse(X, Y, 0.33f, 0.72f, 0.12f, 0.31f) || InEllipse(X, Y, 0.67f, 0.72f, 0.12f, 0.31f);
				const bool bCap = Y > 0.54f && InEllipse(X, Y, 0.5f, 0.72f, 0.3f, 0.22f);
				if (bOuter && (!bInner || bCap))
				{
					return true;
				}
			}
			// Orb and cross.
			if (InEllipse(X, Y, 0.5f, 0.3f, 0.075f, 0.075f))
			{
				return true;
			}
			return InRect(X, Y, 0.465f, 0.05f, 0.535f, 0.25f) || InRect(X, Y, 0.41f, 0.1f, 0.59f, 0.165f);
		}

		/**
		 * The Coat of Arms as a silhouette: the shield, the kangaroo to its left
		 * and the emu to its right, the seven-point star above, the scroll below.
		 * Unit square.
		 */
		inline bool InCoatOfArms(float X, float Y)
		{
			// Star above the shield.
			if (InStarPolygon(X, Y, 0.5f, 0.13f, 0.11f, 7, 0.5f))
			{
				return true;
			}
			// Shield: square top, rounded base.
			if (InRect(X, Y, 0.34f, 0.27f, 0.66f, 0.55f) || (Y > 0.55f && InEllipse(X, Y, 0.5f, 0.55f, 0.16f, 0.2f)))
			{
				return true;
			}
			// Kangaroo (left, facing the shield): body, head, ears, tail to the ground.
			if (InEllipse(X, Y, 0.22f, 0.55f, 0.09f, 0.17f) || InEllipse(X, Y, 0.25f, 0.33f, 0.055f, 0.05f)
				|| SegmentDistance(X, Y, 0.23f, 0.29f, 0.21f, 0.23f) <= 0.015f
				|| SegmentDistance(X, Y, 0.17f, 0.66f, 0.07f, 0.86f) <= 0.03f)
			{
				return true;
			}
			// Emu (right): body, long neck, small head, legs.
			if (InEllipse(X, Y, 0.8f, 0.58f, 0.1f, 0.12f) || SegmentDistance(X, Y, 0.76f, 0.5f, 0.74f, 0.3f) <= 0.025f
				|| InEllipse(X, Y, 0.745f, 0.28f, 0.035f, 0.03f)
				|| SegmentDistance(X, Y, 0.78f, 0.68f, 0.78f, 0.84f) <= 0.015f
				|| SegmentDistance(X, Y, 0.84f, 0.68f, 0.86f, 0.84f) <= 0.015f)
			{
				return true;
			}
			// Scroll the supporters stand on.
			return InRect(X, Y, 0.1f, 0.84f, 0.9f, 0.9f);
		}

		/** Crossed sword (hilt bottom left) and baton (bottom right to top left). Unit square. */
		inline bool InSwordAndBaton(float X, float Y)
		{
			const bool bBlade = SegmentDistance(X, Y, 0.3f, 0.7f, 0.9f, 0.1f) <= 0.028f;
			const bool bGrip = SegmentDistance(X, Y, 0.14f, 0.86f, 0.3f, 0.7f) <= 0.036f;
			const bool bGuard = SegmentDistance(X, Y, 0.2f, 0.6f, 0.4f, 0.8f) <= 0.03f;
			const bool bPommel = InEllipse(X, Y, 0.12f, 0.88f, 0.045f, 0.045f);
			const bool bBaton = SegmentDistance(X, Y, 0.86f, 0.86f, 0.14f, 0.14f) <= 0.05f;
			const bool bBatonEnds = InEllipse(X, Y, 0.86f, 0.86f, 0.065f, 0.065f) || InEllipse(X, Y, 0.14f, 0.14f, 0.065f, 0.065f);
			return bBlade || bGrip || bGuard || bPommel || bBaton || bBatonEnds;
		}

		/** A chevron, point down, in a slot W wide and H high (tile units). */
		inline bool InChevron(float X, float Y, float W, float H)
		{
			const float Half = H * 0.2f;
			return std::min(SegmentDistance(X, Y, Half, Half, W * 0.5f, H - Half),
				SegmentDistance(X, Y, W * 0.5f, H - Half, W - Half, Half)) <= Half;
		}

		enum class EDevice { Crown, CoatOfArms, PipColumn, PipTriangle, Chevron, SwordAndBaton };
	}

	/**
	 * Draw Spec into OutAlpha (Size * Size bytes, row-major, top row first).
	 * Devices stack top to bottom as on a rank slide: crown or Coat of Arms,
	 * pips, chevrons, sword and baton. The stack is scaled to fill the tile.
	 */
	inline void Rasterize(const FSpec& Spec, int Size, unsigned char* OutAlpha)
	{
		using namespace Detail;
		struct FSlot { EDevice Device; int Count; float Width; float Height; };
		FSlot Slots[8];
		int NumSlots = 0;
		const int Pips = std::clamp(Spec.Pips, 0, 3);
		const float Pip = 0.22f;
		if (Spec.bCrest)		{ Slots[NumSlots++] = { EDevice::CoatOfArms, 1, 0.56f, 0.56f }; }
		else if (Spec.bCrown)	{ Slots[NumSlots++] = { EDevice::Crown, 1, 0.36f, 0.36f }; }
		if (Pips == 3 && Spec.bCrown)	{ Slots[NumSlots++] = { EDevice::PipTriangle, 3, 0.4f, 0.36f }; }	// Brigadier
		else if (Pips > 0)				{ Slots[NumSlots++] = { EDevice::PipColumn, Pips, Pip, Pip * Pips }; }
		for (int Index = 0; Index < std::clamp(Spec.Chevrons, 0, 3); ++Index)
		{
			Slots[NumSlots++] = { EDevice::Chevron, 1, 0.72f, 0.19f };
		}
		if (Spec.bSwordAndBaton) { Slots[NumSlots++] = { EDevice::SwordAndBaton, 1, 0.42f, 0.42f }; }

		float Total = 0.f;
		float Widest = 0.f;
		for (int Index = 0; Index < NumSlots; ++Index)
		{
			Total += Slots[Index].Height;
			Widest = std::max(Widest, Slots[Index].Width);
		}
		// Fill the tile inside a small margin: grow a lone device, shrink a tall stack, never overflow the width.
		const float Scale = Total > 0.f ? std::min({ 0.88f / Total, 0.92f / Widest, 2.4f }) : 1.f;
		float Cursor = 0.5f - Total * Scale * 0.5f;
		float Tops[8];
		for (int Index = 0; Index < NumSlots; ++Index)
		{
			Tops[Index] = Cursor;
			Cursor += Slots[Index].Height * Scale;
		}

		auto InSlot = [](const FSlot& Slot, float X, float Y) -> bool	// X, Y in tile units from the slot's top left, unscaled
		{
			switch (Slot.Device)
			{
			case EDevice::Crown:		return InCrown(X / Slot.Width, Y / Slot.Height);
			case EDevice::CoatOfArms:	return InCoatOfArms(X / Slot.Width, Y / Slot.Height);
			case EDevice::SwordAndBaton: return InSwordAndBaton(X / Slot.Width, Y / Slot.Height);
			case EDevice::Chevron:		return InChevron(X, Y, Slot.Width, Slot.Height);
			case EDevice::PipColumn:
			{
				const float Cell = Slot.Width;
				const float Row = std::floor(Y / Cell);
				return InPip(X / Cell, (Y - Row * Cell) / Cell);
			}
			case EDevice::PipTriangle:
			{
				// One above, two below, touching.
				const float Cell = Slot.Height * 0.5f;
				const float U = X / Slot.Width;
				if (Y < Cell)
				{
					const float Left = (Slot.Width - Cell) * 0.5f;
					return X >= Left && X <= Left + Cell && InPip((X - Left) / Cell, Y / Cell);
				}
				const float Gap = (Slot.Width - 2.f * Cell) / 3.f;
				const float Col = U < 0.5f ? Gap : 2.f * Gap + Cell;
				return X >= Col && X <= Col + Cell && InPip((X - Col) / Cell, (Y - Cell) / Cell);
			}
			}
			return false;
		};

		constexpr int Samples = 4;	// 4x4 supersampling for clean edges
		for (int Py = 0; Py < Size; ++Py)
		{
			for (int Px = 0; Px < Size; ++Px)
			{
				int Hit = 0;
				for (int S = 0; S < Samples * Samples; ++S)
				{
					const float X = (Px + (S % Samples + 0.5f) / Samples) / Size;
					const float Y = (Py + (S / Samples + 0.5f) / Samples) / Size;
					for (int Index = 0; Index < NumSlots; ++Index)
					{
						const FSlot& Slot = Slots[Index];
						const float Left = 0.5f - Slot.Width * Scale * 0.5f;
						const float Lx = (X - Left) / Scale, Ly = (Y - Tops[Index]) / Scale;
						if (Lx >= 0.f && Lx <= Slot.Width && Ly >= 0.f && Ly <= Slot.Height && InSlot(Slot, Lx, Ly))
						{
							++Hit;
							break;
						}
					}
				}
				OutAlpha[Py * Size + Px] = static_cast<unsigned char>(Hit * 255 / (Samples * Samples));
			}
		}
	}
}
