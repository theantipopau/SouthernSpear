// Copyright Southern Spear. All Rights Reserved.

using UnrealBuildTool;

/**
 * Objective Assault UI: the HUD model and status widget.
 *
 * UI depends on gameplay, never the reverse (guard rule SS005), so this is a
 * separate module from SouthernSpearObjectives. Reads replicated state only.
 * No Lyra dependency (SS002).
 */
public class SouthernSpearObjectivesUI : ModuleRules
{
	public SouthernSpearObjectivesUI(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDefinitions.Add("SSOBJUI_API=SOUTHERNSPEAROBJECTIVESUI_API");

		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine",
				"UMG",
				"SouthernSpearCore",
				"SouthernSpearObjectives",
			}
		);

		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"AIModule",
				"Slate",
				"SlateCore",
			}
		);
	}
}
