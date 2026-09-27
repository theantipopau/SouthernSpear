// Copyright Southern Spear. All Rights Reserved.

using UnrealBuildTool;

/**
 * SouthernSpearObjectives - objectives and the Objective Assault round lifecycle.
 *
 * Dependency policy: SouthernSpearCore is the only Southern Spear dependency and
 * no Lyra module is allowed. Team membership is read through the engine's
 * IGenericTeamAgentInterface (AIModule), which Lyra pawns already implement, so
 * this gameplay code stays testable without Lyra. It must never depend on
 * SouthernSpearTeam: gameplay does not read presentation (ADR-004).
 * Tools/validate_architecture.py enforces this.
 */
public class SouthernSpearObjectives : ModuleRules
{
	public SouthernSpearObjectives(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDefinitions.Add("SSOBJ_API=SOUTHERNSPEAROBJECTIVES_API");

		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine",
				"AIModule",
				"SouthernSpearCore",
			}
		);

		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"NetCore",
				"EngineSettings",
			}
		);
	}
}
