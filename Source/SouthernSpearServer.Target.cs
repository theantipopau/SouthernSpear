// Copyright Southern Spear. All Rights Reserved.
//
// Southern Spear dedicated server target.
//
// D-05: the dedicated server is a first-class target from Phase 0, not a
// later hardening step. This target excludes client-only modules so there is
// no rendering or UI surface on the server to attack.
// See Docs/LYRA_ADOPTION.md.

using UnrealBuildTool;

[SupportedPlatforms(UnrealPlatformClass.Server)]
public class SouthernSpearServerTarget : TargetRules
{
	public SouthernSpearServerTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Server;

		ExtraModuleNames.AddRange(new string[] { "LyraGame" });

		LyraGameTarget.ApplySharedLyraTargetSettings(this);

		bUseChecksInShipping = true;
	}
}
