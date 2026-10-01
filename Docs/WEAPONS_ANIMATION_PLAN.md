# Weapons and Animation — What the ADF Re-Cut Registry Unlocks

**Status:** historical proposal, 2026-09-28 (Session 049); current weapon stats and implementation are summarized in `Docs/NEXT_PRIORITIES.md` §5. The measured source-config values are in `Docs/WEAPON_SOURCE_DATA.md` (generated; `python Tools/Weapons/adfrc_weapon_data.py`). Stages below preserve their planning history; do not treat their pre-build claims as current state.

## Where we are

| Area | State | Producer verdict |
|---|---|---|
| Meshes | ADFRC MLOD rebuilds with their real optics (`Tools/build_adfrc_weapons.py`); `SOCKET_Muzzle`, sight sockets on the optical axis; SMDI mapped | "much better, still not amazing" |
| First person | Fab M4/G17 gloved arms carry every A-series weapon on the arms' weapon bone, with their draw, fire, reload and holster; sway, bob and kick are procedural | — |
| Third person | Historical producer verdict and animation snapshot. Current friendly visible body is Quantum on its own skeleton, retargeted from Manny; the bridge IK changes the rendered pose, but per-weapon contact and broader fit acceptance remain open under R-65. | "animations are still terrible" |
| Gameplay tuning | Historical Session 049 baseline: shared Lyra rifle/pistol defaults. Superseded by project-owned `SSWeaponStatsSettings` rows and `USSWeaponStatsSubsystem`, which apply configured magazine/spare ammo, spread scale and RPM; `bFullAuto=false` is still not enforced | — |
| Audio | A88 family uses the ADFRC AUG recordings (Session 035); reload and dry-fire not wired | — |

## Historical proposal: what the registry adds as source-config evidence

1. **Real per-weapon numbers**: rate of fire, dispersion, magazine, fire modes and handling for every
   source weapon. For example, A88 682 rpm at 2.0 MOA; A416 and A4 857 rpm; A89 750 rpm from a 200-round belt
   with a deployed (bipod) mode; A25 semi-only at 1.5 MOA; A9 8.6 MOA.
2. **A hand-grip pose per weapon** (`handAnim`): `EF88_Vg_static`, `Minimi_Standard`, `ar15_8in_cgrip`,
   `hk416_cgrip`, `hk417_static`, `ar15_10in_cgrip`, plus vertical-grip and angled-grip variants of each, and
   **AK grips for the MAF counterparts**. Each one is exactly where Arma puts both hands on that weapon.
3. **The muzzle and ejection memory points** (`konec hlavne`, `nabojnicestart`/`nabojniceend`) on every
   rifle: a muzzle flash and a shell ejection port with a direction, per weapon.
4. **Real reload animation for the bullpup**: `GestureReloadAUG` and its prone version (165 frames each),
   plus fast and slow pistol reloads. Every other `reloadAction` names a vanilla Arma state the pack does
   not ship.
5. **LMG holds**: F89 standard, para and bipod poses, and MAG58 standing and prone.

## Historical plan, in order of payoff for effort

Each step was originally proposed as one commit with evidence; the sequencing below is historical, not a current work order.

### W1. Per-weapon gameplay stats from data (biggest feel change, no animation needed)

**Current implementation (source/config review, 2026-10-01):** `Config/DefaultGame.ini` supplies A88/A88G/A89/A4/A416/A417/A25/A9 rows. `USSWeaponStatsSubsystem` applies magazine size, full magazine and spare rounds server-side, scales each instance's spread curve and applies RPM as `FireDelayTimeSecs`. `bFullAuto=false` is not enforced, and the A89 bipod/deployed mode and ADS/sway values in the old W1 proposal are not implemented by this table. See `NEXT_PRIORITIES.md` §5.2–§5.6 for exact boundaries.

### W2. Left-hand grip sockets from the `handAnim` poses (historical implementation record; fit acceptance open)

> **Current correction (R-65; Sessions 065–070):** the original Session 059 conclusion that the hook never ran was superseded by later UE 5.8 source tracing and Session 067 rendered A/B evidence that `ss.HandIK 0/1` changes the left-hand pose; Session 070 measured the A88 wrist at the grip target. This does not prove correct foregrip contact across weapons or complete third-person acceptance. The implementation notes below are historical; use current R-65 in `PROJECT_AUDIT.md` for outstanding fit/acceptance work.

**Session 058: left-hand IK written (uncompiled)** — the recorded `USSHandIKMeshComponent` design was a two-bone IK to `SOCKET_LeftHandGrip` after each animation evaluation, on the third-person body (the soldier parts follow by leader pose) and the first-person arms; no Lyra asset or Animation Blueprint changed. `ss.HandIK 0` was intended to compare. **Session 057: 6 of 6 fit on the committed real clips** (`adfrc_grip.py` rewritten: the clips store each bone as a rotation about its rest joint, with the quaternion handedness flipped, and `weapon` hangs off Spine1; see CHANGELOG 057). Awaiting the producer's build at that historical point. **Session 054: the first real run fitted 0 of 7. Session 055: two causes fixed** (case-sensitive bone names; the decoder parents `weapon` to the right hand, where Arma's skeleton has `Spine1`). Both hierarchies are now tried, and a refusal reports its numbers. Awaiting the next run. **Session 052: sockets built.** `Tools/Common/adfrc_grip.py` + `test_adfrc_grip.py`
(synthetic-rig tests pass here); `adfrc_weapon.py` writes `SOCKET_LeftHandGrip` / `SOCKET_RightHandGrip` when
`build_adfrc_weapons.py` passes `SS_GRIP_CLIP`. The Arma-to-MLOD axis map is calibrated per weapon (right hand on
`trigger_axis`, left hand forward on the barrel), and a pose that doesn't fit is refused and reported. The original next step was to run the build on the producer's machine and check `manifest.json → grip`. Later source tracing and Session 067–070 captures established that the bridge hook changes the rendered pose and measured the A88 wrist at the grip target; per-weapon fit and broader visual acceptance remain open under current R-65.
- A stdlib tool (`Tools/Weapons/grip_sockets_from_handanim.py`) reads each weapon's grip clip from
  `Art/ADFRC/Animations/Rig/…` and rebuilds world transforms with the rig hierarchy (`rtm_rigs.world_from_local`).
  It expresses `lefthand` and `righthand` in the `weapon` bone's space and writes `SOCKET_LeftHandGrip` /
  `SOCKET_RightHandGrip` per weapon into the manifest that `setup_weapons.py` already reads.
- **This doesn't need the Arma rest pose (R-32).** It uses only the relative transform of two bones in the
  same frame, so the missing `SkeletonPivots.p3d` doesn't block it.
- The original proposal was to drive **left-hand IK** to that socket in third person (LOCOMOTION_AUDIT stage S0) and on the first-person arms, then verify the MAF counterparts with AK grip clips. Later evidence confirms a rendered pose change and A88 target measurement; it does not establish the proposed per-weapon contact result.
- **Historical acceptance proposal:** report hand-to-socket distances and capture each weapon to show both hands on it. Broader per-weapon fit acceptance remains open under R-65/R-85.

### W3. Muzzle flash and shell ejection from the memory points (historical implementation record; see current VFX status in NEXT_PRIORITIES §4)

**Session 059: shell ejection built (uncompiled).** `adfrc_weapon.py` writes `SOCKET_Eject` / `SOCKET_EjectEnd`
from `nabojnicestart` / `nabojniceend` (imported as `Eject` / `EjectEnd`); `USSShellEjectSubsystem` (bridge,
clients only) throws a pooled brass case per rifle or pistol fire cue from the viewer's weapon, flies it
ballistically, bounces it off the world and leaves it lying. **Session 060: muzzle light** — `USSMuzzleLightSubsystem` flashes a warm point light at the visible muzzle for 35–55 ms per shot (Lyra's flash sprite already sits on our barrel via `AlignLyraMuzzle`). Still open: a realistic flash sprite in place of Lyra's.
- **Historical next steps, superseded in part:** socket work is recorded in the source tooling; code-driven casing ejection and muzzle light exist. A visible player-facing flash and current-build confirmation remain open (see `NEXT_PRIORITIES.md` §4 and `ASSET_REGISTER.md` §4.7).

### W4. Reload and handling audio
- The pack's resolved WAVs for the A88 family (closure, magazine) are already imported. Wire them to the
  reload montage notifies and dry fire.
- **MetaSound instead of SoundCue:** SoundCues can't be authored headlessly in UE 5.8 (Session 032b).
  UE 5.x exposes `MetaSoundBuilderSubsystem` to scripting, which may allow building a MetaSound source from
  Python: random shot layers and distance tails without editor work. **Unverified.** One headless probe
  decides it.

### W5. Bullpup reload for the A88 family, as IK trajectories
- R-32 blocks a full-body retarget of `GestureReloadAUG`. Its **end-effector paths** don't need one: for
  each frame, take the left hand, right hand and magazine proxy relative to the weapon, and play them as IK
  targets over the first-person arms and the third-person upper body. The error is measurable (hand-to-target
  distance), which is exactly what R-32 asked for. The fallback stays the Fab M4 reload, time-scaled.

### W6. Support weapon and stances (needs locomotion work)
- F89 bipod deploy (`fullautodeployed`, the `f89`/`f89_para` holds), prone MAG58/F89 holds. These depend on
  prone (LOCOMOTION_AUDIT S5).

### W7. Third-person body animation (the "animations are still terrible" item)
- Still LOCOMOTION_AUDIT S3–S5: motion matching from the Game Animation Sample, weapon overlays and ready
  poses. The registry doesn't change this, but W2's grip sockets are the hand targets those overlays need.

## Model quality ("still not amazing")

The registry doesn't hold mesh data. It points at the next three mesh fixes:
- **LOD chain:** the ADFRC FBX merges the model and its LODs as separate objects. Build real UE LOD groups
  (or Nanite for third person) instead of shipping LOD0 everywhere.
- **Texture resolution and channels:** check each weapon's `_co`/`_nohq`/`_smdi` against
  `texheaders_report.json`. Where the `Workshop/` variant of a texture is larger than the `Source/` one (the
  two trees differ, registry §6.2), take the larger. Not yet measured.
- **Attachments as parts, not baked:** `linked_items` and `weapon_slots` name each weapon's optic, muzzle,
  pointer and grip. Building those as separate sockets and meshes lets the grip variant match its `handAnim`
  variant (vertical grip or angled foregrip).

## Licence note

The pack's README carries APL-SA's "no model reuse" wording. For this project that is superseded by the
producer's blanket permission (L-0021) and ADR-035: everything is cleared for the free game, including real
weapon and optic names. R-27 is producer-accepted; the residual trademark exposure is R-57.

## Historical recommendation

The original proposal recommended W1 then W2. W1 is now implemented at the source/config layer as described above; do not assume the rest of the proposal's sequence or acceptance tests have been completed. Current priorities and unverified appearance/runtime checks are in `NEXT_PRIORITIES.md`.
