// Copyright Southern Spear. All Rights Reserved.

using UnrealBuildTool;

/**
 * SouthernSpearCasualty - wounds, bleeding, the downed state and treatment (ADR-040).
 *
 * Dependency policy: SouthernSpearCore is the only Southern Spear dependency and
 * no Lyra module is allowed (guard SS001/SS002). Damage and interaction reach this
 * module through the Lyra bridge; the HUD reads its state through Core. Nothing
 * here may depend on UI (SS005).
 */
public class SouthernSpearCasualty : ModuleRules
{
	public SouthernSpearCasualty(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDefinitions.Add("SSCASUALTY_API=SOUTHERNSPEARCASUALTY_API");

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
