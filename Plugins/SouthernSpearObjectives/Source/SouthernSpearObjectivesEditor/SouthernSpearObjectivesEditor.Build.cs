// Copyright Southern Spear. All Rights Reserved.

using UnrealBuildTool;

/**
 * Editor-only helpers for authoring the Objective Assault Game Feature from
 * Python (Tools/Unreal/setup_objective_assault.py). Never loaded in a game.
 * No Lyra dependency: Lyra classes are passed in as soft class paths.
 */
public class SouthernSpearObjectivesEditor : ModuleRules
{
	public SouthernSpearObjectivesEditor(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine",
				"GameFeatures",
				"SouthernSpearCore",
			}
		);
	}
}
