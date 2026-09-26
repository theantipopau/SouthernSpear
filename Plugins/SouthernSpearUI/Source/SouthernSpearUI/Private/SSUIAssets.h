// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "Engine/Texture2D.h"

/** Content the C++ widgets load by path (plugin content, SouthernSpearUI/Content). */
namespace SSUIAssets
{
	/** Key art: loading screen and front-end background (Docs/images/loadingscreen.png). */
	inline UTexture2D* KeyArt()
	{
		return LoadObject<UTexture2D>(nullptr, TEXT("/SouthernSpearUI/Textures/T_SS_KeyArt.T_SS_KeyArt"));
	}
}
