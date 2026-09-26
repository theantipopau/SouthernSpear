// Copyright Southern Spear. All Rights Reserved.

using UnrealBuildTool;

/**
 * SouthernSpearTeam - cosmetic faction presentation (ADR-004, ADR-017).
 *
 * Dependency policy: SouthernSpearCore is the only Southern Spear dependency,
 * and no Lyra gameplay module is allowed. Presentation must not be able to
 * reach damage, health, weapons, abilities or any other gameplay state.
 * Tools/validate_architecture.py enforces both rules.
 */
public class SouthernSpearTeam : ModuleRules
{
	public SouthernSpearTeam(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		// Short export prefix, as for SSCORE_API.
		PublicDefinitions.Add("SSTEAM_API=SOUTHERNSPEARTEAM_API");

		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine",
				"SouthernSpearCore",
			}
		);
	}
}
