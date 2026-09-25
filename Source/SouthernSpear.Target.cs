// Copyright Southern Spear. All Rights Reserved.
//
// Southern Spear game (client) target.
//
// D-01: Lyra module names are preserved, so this target compiles the
// upstream LyraGame module rather than a renamed one. Only the TARGET
// is ours. See Docs/LYRA_ADOPTION.md.

using UnrealBuildTool;

public class SouthernSpearTarget : TargetRules
{
	public SouthernSpearTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;

		ExtraModuleNames.AddRange(new string[] { "LyraGame" });

		// Reuse Epic's shared client settings (installed plugins, engine
		// directory resolution, launcher iteration behaviour).
		LyraGameTarget.ApplySharedLyraTargetSettings(this);
	}
}
