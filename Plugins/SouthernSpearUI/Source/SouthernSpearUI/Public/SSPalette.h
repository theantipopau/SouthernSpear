// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

/**
 * Southern Spear UI palette, mirrored from the website design tokens
 * (Site/styles.css). Same values as SouthernSpearObjectivesUI's SSUIStyle.
 */
namespace SSPalette
{
	inline FLinearColor Hex(const TCHAR* Code, float Alpha = 1.f)
	{
		FLinearColor C = FLinearColor::FromSRGBColor(FColor::FromHex(Code));
		C.A = Alpha;
		return C;
	}

	inline FLinearColor Ink950(float A = 1.f)   { return Hex(TEXT("07100B"), A); }
	inline FLinearColor Ink900(float A = 1.f)   { return Hex(TEXT("0C130E"), A); }
	inline FLinearColor Field800(float A = 1.f) { return Hex(TEXT("182219"), A); }
	inline FLinearColor Field700(float A = 1.f) { return Hex(TEXT("263026"), A); }
	inline FLinearColor Line(float A = 1.f)     { return Hex(TEXT("43503D"), A); }
	inline FLinearColor Brass500(float A = 1.f) { return Hex(TEXT("C3A66D"), A); }
	inline FLinearColor Brass300()              { return Hex(TEXT("D6C49D")); }
	inline FLinearColor Sand100(float A = 1.f)  { return Hex(TEXT("F0E9D9"), A); }
	inline FLinearColor Sage200()               { return Hex(TEXT("B9C1B4")); }
	inline FLinearColor Sage400()               { return Hex(TEXT("A5AEA0")); }
	inline FLinearColor Opfor500(float A = 1.f) { return Hex(TEXT("8C493D"), A); }
	inline FLinearColor Opfor300()              { return Hex(TEXT("C98A7C")); }
}
