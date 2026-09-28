// Copyright Southern Spear. All Rights Reserved.

using UnrealBuildTool;

/**
 * SouthernSpearProgression - service record, ranks and capped service XP (ADR-032).
 *
 * Dependency policy: SouthernSpearCore is the only Southern Spear dependency and
 * no Lyra module is allowed (guard SS001/SS002). Service events arrive through
 * Core's USSServiceEventSubsystem; the profile reaches the UI through Core's
 * USSLocalProfileState. Nothing here may depend on UI (SS005).
 */
public class SouthernSpearProgression : ModuleRules
{
	public SouthernSpearProgression(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDefinitions.Add("SSPROG_API=SOUTHERNSPEARPROGRESSION_API");

		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine",
				"DeveloperSettings",
				"SouthernSpearCore",
			}
		);

		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"Json",
				"JsonUtilities",
				"NetCore",
			}
		);
	}
}
