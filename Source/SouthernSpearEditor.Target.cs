// Copyright Southern Spear. All Rights Reserved.
//
// Southern Spear editor target.
//
// D-01: Lyra module names are preserved. See Docs/LYRA_ADOPTION.md.

using UnrealBuildTool;

public class SouthernSpearEditorTarget : TargetRules
{
	public SouthernSpearEditorTarget(TargetInfo Target) : base(Target)
	{
		DefaultBuildSettings = BuildSettingsVersion.V7;

		Type = TargetType.Editor;

		ExtraModuleNames.AddRange(new string[] { "LyraGame", "LyraEditor" });

		if (!bBuildAllModules)
		{
			NativePointerMemberBehaviorOverride = PointerMemberBehavior.Disallow;
		}

		LyraGameTarget.ApplySharedLyraTargetSettings(this);

		// Required for on-device development via Unreal Remote 2.
		EnablePlugins.Add("RemoteSession");
	}
}
