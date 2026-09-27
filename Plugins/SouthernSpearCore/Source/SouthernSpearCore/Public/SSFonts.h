// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/FontFace.h"
#include "Fonts/CompositeFont.h"
#include "Fonts/SlateFontInfo.h"
#include "Styling/CoreStyle.h"

/**
 * The website's typefaces in the game UI (header-only; for the *UI modules,
 * which already link SlateCore): Barlow Condensed for display text (headings,
 * labels, buttons, numbers) and Inter for body text, from the font faces in
 * /SouthernSpearUI/Fonts (Tools/Unreal/setup_fonts.py, SIL OFL 1.1). Falls
 * back to the engine font when the faces are missing.
 */
namespace SSFonts
{
	inline TSharedPtr<const FCompositeFont> Build(const TCHAR* RegularPath, const TCHAR* BoldPath)
	{
		const UFontFace* Regular = LoadObject<UFontFace>(nullptr, RegularPath);
		const UFontFace* Bold = LoadObject<UFontFace>(nullptr, BoldPath);
		if (!Regular || !Bold)
		{
			return nullptr;
		}
		// FStandaloneCompositeFont keeps the face assets referenced for the GC.
		TSharedRef<FStandaloneCompositeFont> Font = MakeShared<FStandaloneCompositeFont>();
		FTypefaceEntry& RegularEntry = Font->DefaultTypeface.Fonts.AddDefaulted_GetRef();
		RegularEntry.Name = TEXT("Regular");
		RegularEntry.Font = FFontData(Regular);
		FTypefaceEntry& BoldEntry = Font->DefaultTypeface.Fonts.AddDefaulted_GetRef();
		BoldEntry.Name = TEXT("Bold");
		BoldEntry.Font = FFontData(Bold);
		return Font;
	}

	/** Barlow Condensed Bold. Condensed, so sizes read ~15% larger than Roboto's. */
	inline FSlateFontInfo Display(float Size)
	{
		static TSharedPtr<const FCompositeFont> Font = Build(
			TEXT("/SouthernSpearUI/Fonts/FF_BarlowCondensed.FF_BarlowCondensed"),
			TEXT("/SouthernSpearUI/Fonts/FF_BarlowCondensed.FF_BarlowCondensed"));
		return Font ? FSlateFontInfo(Font, Size * 1.15f, TEXT("Bold")) : FCoreStyle::GetDefaultFontStyle("Bold", Size);
	}

	/** Inter Regular, or SemiBold when bStrong. */
	inline FSlateFontInfo Body(float Size, bool bStrong = false)
	{
		static TSharedPtr<const FCompositeFont> Font = Build(
			TEXT("/SouthernSpearUI/Fonts/FF_Inter_Regular.FF_Inter_Regular"),
			TEXT("/SouthernSpearUI/Fonts/FF_Inter_SemiBold.FF_Inter_SemiBold"));
		return Font ? FSlateFontInfo(Font, Size, bStrong ? TEXT("Bold") : TEXT("Regular"))
			: FCoreStyle::GetDefaultFontStyle(bStrong ? "Bold" : "Regular", Size);
	}
}
