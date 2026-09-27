// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "Engine/Texture2D.h"

/** Content the C++ widgets load by path (plugin content, SouthernSpearUI/Content). */
namespace SSUIAssets
{
	/** Front-end background (Docs/images/mainmenu.png); falls back to the key art. */
	inline UTexture2D* MainMenuArt()
	{
		UTexture2D* Art = LoadObject<UTexture2D>(nullptr, TEXT("/SouthernSpearUI/Textures/T_SS_MainMenu.T_SS_MainMenu"));
		return Art ? Art : LoadObject<UTexture2D>(nullptr, TEXT("/SouthernSpearUI/Textures/T_SS_KeyArt.T_SS_KeyArt"));
	}

	/** Key art: loading screen (Docs/images/loadingscreen.png). */
	inline UTexture2D* KeyArt()
	{
		return LoadObject<UTexture2D>(nullptr, TEXT("/SouthernSpearUI/Textures/T_SS_KeyArt.T_SS_KeyArt"));
	}
}
