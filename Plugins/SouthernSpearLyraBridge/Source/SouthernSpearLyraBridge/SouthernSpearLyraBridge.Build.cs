// Copyright Southern Spear. All Rights Reserved.

using UnrealBuildTool;

/**
 * The single, guarded place where Southern Spear code may depend on Lyra
 * (ADR-019). Adapts Lyra to Southern Spear rules; no Southern Spear module may
 * depend on this one (guard SS001/SS007).
 */
public class SouthernSpearLyraBridge : ModuleRules
{
	public SouthernSpearLyraBridge(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDefinitions.Add("SSBRIDGE_API=SOUTHERNSPEARLYRABRIDGE_API");

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
				"LyraGame",
				"GameplayTags",
				"AIModule", // IGenericTeamAgentInterface (scoreboard teams)
				"EnhancedInput", // ASSCharacter tactical inputs (ADR-024)
				"GameplayAbilities", // ALyraCharacter implements IGameplayCueInterface
				"Landscape", // bullet penetration never passes through terrain (ADR-026)
				"ModularGameplayActors", // ALyraCharacter base
				"PhysicsCore", // UPhysicalMaterial (hit zones)
			}
		);
	}
}
