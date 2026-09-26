// Copyright Southern Spear. All Rights Reserved.

using UnrealBuildTool;

/**
 * Southern Spear player-facing UI: HUD, pause menu, front end, loading screen.
 *
 * Reads USSLocalHudState (SouthernSpearCore), which the Lyra bridge fills, so
 * this module never depends on Lyra (SS002) and gameplay never depends on it
 * (SS005).
 */
public class SouthernSpearUI : ModuleRules
{
	public SouthernSpearUI(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDefinitions.Add("SSUI_API=SOUTHERNSPEARUI_API");

		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine",
				"UMG",
				"SouthernSpearCore",
			}
		);

		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"Slate",
				"SlateCore",
				"InputCore",
			}
		);
	}
}
