// Copyright Southern Spear. All Rights Reserved.

using UnrealBuildTool;

/**
 * SouthernSpearCore - the foundation layer.
 *
 * Dependency policy (ADR-017, ADR-004):
 *
 *   This module depends on NO other Southern Spear plugin. It is the root of the
 *   SS dependency graph, so anything that depends on it is guaranteed to be at
 *   least one layer above gameplay-neutral foundation code.
 *
 *   It also deliberately does not depend on LyraGame. Lyra owns weapons, damage,
 *   health, abilities, roles, objectives and UI; depending on any of them here
 *   would make it possible for a presentation or identity type to reach gameplay
 *   state, which is exactly what ADR-004 forbids. Lyra is a *consumer* of this
 *   module, never a dependency of it.
 *
 *   Tools/validate_architecture.py enforces both rules statically. If you add a
 *   dependency here, expect CI to fail.
 */
public class SouthernSpearCore : ModuleRules
{
	public SouthernSpearCore(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		// UBT auto-generates SOUTHERNSPEARCORE_API for this module. The project
		// naming standard calls for the short SSCORE_ prefix on Southern Spear
		// symbols, so alias the export macro rather than spelling the long form
		// in every public header.
		PublicDefinitions.Add("SSCORE_API=SOUTHERNSPEARCORE_API");

		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine",
				"GameplayTags",
				"DeveloperSettings",
			}
		);

		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				// Engine modules only. See the dependency policy comment above
				// before adding anything.
				"NetCore", // DOREPLIFETIME for USSServiceRankComponent (ADR-033)
			}
		);
	}
}
