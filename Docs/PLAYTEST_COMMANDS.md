# Play-test commands (for agents)

How to launch Southern Spear, put the producer in a playable window, capture screenshots without touching the
desktop, and read the result. All commands are Git Bash, from `E:/SouthernSpear`. Every flag and command
below has been used successfully on this machine (2026-09-28).

## 0. Before anything

```bash
tasklist | grep -i unreal          # nothing may be running: an open editor/game locks .uasset and DLLs
```

- **Never screen-capture the desktop** (it grabs the user's other windows). Use `-SSShotAt` (§3) or ask the
  producer for screenshots.
- **Always pass your own log**: `-abslog=E:/SouthernSpear/Saved/Logs/SS_probe_<name>.log`. The default
  `Saved/Logs/SouthernSpear.log` is overwritten by other agents' commandlets, which has caused misdiagnoses.
- Map paths need `MSYS_NO_PATHCONV=1` in Git Bash, or `/Game/...` is rewritten to a Windows path.
- After C++ changes, build first (the game loads the editor DLLs):
  `"/e/Unreal/UE_5.8/Engine/Build/BatchFiles/Build.bat" SouthernSpearEditor Win64 Development "-Project=E:/SouthernSpear/SouthernSpear.uproject" -WaitMutex`

## 1. A window for the producer to play in (they take the screenshots)

Cheapest way to get eyes on a map. Run it in the background, tell the producer it is loading (~30 s), and wait
for their screenshots. The command returns when they close the window.

```bash
MSYS_NO_PATHCONV=1 "/e/Unreal/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe" \
  "E:/SouthernSpear/SouthernSpear.uproject" "/Game/Maps/L_Ravenshoe_01?NumBots=6" \
  -game -windowed -ResX=1600 -ResY=900 -FORCELOGFLUSH \
  -abslog=E:/SouthernSpear/Saved/Logs/SS_probe_<name>.log
```

- Maps: `L_DryRiver_01`, `L_Ravenshoe_01`, `L_RedGum_01`; front end `L_SS_FrontEnd`.
- URL options: `?NumBots=N`, `?RoundSeconds=60`, `?PreRoundSeconds=`, `?PostRoundSeconds=`.
- In game: class select on spawn (**L** re-opens it), **Esc** match menu (includes Re-deploy).
- Tell the producer what to look for (spawn point, bots moving, surfaces, anything floating or grey).

## 2. Headless live check (no window, log only)

```bash
MSYS_NO_PATHCONV=1 "/e/Unreal/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" \
  "E:/SouthernSpear/SouthernSpear.uproject" "/Game/Maps/L_DryRiver_01?NumBots=8?RoundSeconds=60" \
  -game -nullrhi -unattended -nosplash -FORCELOGFLUSH \
  -abslog=E:/SouthernSpear/Saved/Logs/SS_probe_<name>.log
```

Without `-FORCELOGFLUSH` a timeout kill loses the log tail. `-nosound` makes Lyra print harmless
`WeaponAudioFunctions` Blueprint errors; leave it off when checking audio.

## 3. Self-captured screenshot (no desktop capture)

Add to a **windowed** `-game` run (§1 command, without waiting for a human):

| Flag | Effect |
|---|---|
| `-SSShotAt=45` | at 45 s, writes `Saved/Screenshots/WindowsEditor/SSShot.png`, then keep going |
| `-SSExecAt=14 "-SSExec=cmd1\|cmd2"` | runs console commands once the pawn exists (`-ExecCmds` runs too early) |
| `-SSNoClassSelect` | skips the class-select screen so the capture shows the world |
| `-SSAnimDebug` | logs the held weapon's components and sockets |

Copy the PNG to your scratchpad before the next run overwrites it, then read it. Example (follow the nearest
enemy from 2 m behind, capture at 40 s):

```bash
MSYS_NO_PATHCONV=1 "/e/Unreal/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe" \
  "E:/SouthernSpear/SouthernSpear.uproject" "/Game/Maps/L_DryRiver_01?NumBots=6" \
  -game -windowed -ResX=1600 -ResY=900 -FORCELOGFLUSH -SSNoClassSelect \
  -SSExecAt=14 "-SSExec=ss.Debug.FollowBot -200" -SSShotAt=40 \
  -abslog=E:/SouthernSpear/Saved/Logs/SS_probe_<name>.log
```

The run does not exit by itself; stop it after the shot (`taskkill //IM UnrealEditor.exe //F`, only for a
process you started).

### Useful console variables for captures

| CVar | Use |
|---|---|
| `ss.Debug.FollowBot <cm>` | third-person camera behind a bot; **negative = nearest enemy** (to see OPFOR/MAF) |
| `ss.FP.ForceAim 1` | hold aim-down-sights (scope/iron-sight checks) |
| `ss.FP.DebugPitch <deg>` | fix view pitch |
| `ss.FP.DebugSlot 1` | switch to the pistol |
| `ss.FP.WeaponOffset "x y z"`, `ss.FP.WeaponRotation` | nudge the first-person weapon (tuning only; default `0 0 0`) |
| `ss.FP.IronRelief <cm>` | iron-sight eye relief (default 38) |
| `EnableCheats\|DamageSelf 20` | test damage, death, KIA and re-deploy |

## 4. Reading the log

```bash
L=Saved/Logs/SS_probe_<name>.log
grep "LogSSObjectives" $L | tail                      # round flow, objectives, bot steering
grep -c "SpawnActor failed" $L                        # >0: pawns have no valid start (see §6)
grep -i "warning\|error" $L | grep -iv "LogConfig\|LogPython\|Toolset" | cut -c31-200 | sort | uniq -c | sort -rn | head -25
```

Known noise: Engine Toolset Python import errors, `Lyra.Automation` CS0579 duplicate-attribute errors,
`Failed to load 'nvcuvid.dll'` etc., `LogEditorDataStorageUI` widget-factory warnings.

## 5. Running an editor Python script headless (probes and fixes)

```bash
"/e/Unreal/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" "E:/SouthernSpear/SouthernSpear.uproject" \
  -nullrhi -unattended -nosplash -nosound \
  "-ExecutePythonScript=E:/SouthernSpear/Tools/Unreal/<script>.py" \
  -abslog=E:/SouthernSpear/Saved/Logs/SS_probe_<name>.log
```

- Scripts get no useful stdout: **write a JSON report** to `Build/<name>.json` and read that.
- One-off probes go in your scratchpad, not `Tools/`.
- Skinned-mesh FBX export crashes under `-nullrhi`; use `-RenderOffscreen` for that one case.
- Navigation bake works headless with this extra flag (both Dry River and Ravenshoe):
  `"-ini:Engine:[/Script/NavigationSystem.NavigationSystemV1]:bWaitForAsyncLoadingBeforeBuildingNavigationAutomatically=False"`
  (Ravenshoe also needs `SS_RAVENSHOE_NAV_BUILD=1` in the environment).

## 6. First-launch checklist for a new map

What broke Ravenshoe on its first run (`Docs/HANDOVER_RAVENSHOE.md` §0); check these before asking for eyes:

1. **Player starts are `LyraPlayerStart`**, not plain `PlayerStart`, or everyone spawns at the origin.
2. **Level meshes use complex-as-simple collision** (`CTF_USE_COMPLEX_AS_SIMPLE`, no auto convex hull), or
   pawns walk on an invisible hull.
3. **Navmesh is baked** (bounds volume + `RecastNavMesh`, then the nav build with the ini flag above).
4. **Every level mesh has a real material**: `FBXLegacyPhongSurfaceMaterial` means the import left the
   placeholder in the slot. Set per-actor overrides with `StaticMeshComponent.set_material(i, mat)`.
5. **Experience bound** in World Settings (`B_SS_ObjectiveAssault`) and the objectives/director placed.
6. Terrain continues past the playable edge, or the horizon shows a black band.

## 7. Automated tests (no rendering)

```bash
python Tools/validate_architecture.py
"/e/Unreal/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" "E:/SouthernSpear/SouthernSpear.uproject" \
  -nullrhi -unattended -nosplash -nosound -NoLoadingScreen -stdout \
  "-ExecCmds=Automation RunTests SouthernSpear;Quit" -TestExit="Automation Test Queue Empty"
```

Count `Result={Success}` in the output.
