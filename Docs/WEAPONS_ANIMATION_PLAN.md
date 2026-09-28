# Weapons and Animation — What the ADF Re-Cut Registry Unlocks

**Status:** proposal, 2026-09-28 (Session 049). Written from the committed `Docs/Sourced/ADFRC/` registry,
`Docs/LOCOMOTION_AUDIT.md`, and the weapon pipeline as it stands. Nothing here has been built yet.
The measured per-weapon values are in `Docs/WEAPON_SOURCE_DATA.md` (generated; `python Tools/Weapons/adfrc_weapon_data.py`).

## Where we are

| Area | State | Producer verdict |
|---|---|---|
| Meshes | ADFRC MLOD rebuilds with their real optics (`Tools/build_adfrc_weapons.py`); `SOCKET_Muzzle`, sight sockets on the optical axis; SMDI mapped | "much better, still not amazing" |
| First person | Fab M4/G17 gloved arms carry every A-series weapon on the arms' weapon bone, with their draw, fire, reload and holster; sway, bob and kick are procedural | — |
| Third person | Lyra's stylised animation on the Quantum/ADFRC body; Lyra's hand IK is tuned for Lyra's rifle, so the left hand misses our longer and bullpup handguards (LOCOMOTION_AUDIT F2/F3/F5) | "animations are still terrible" |
| Gameplay tuning | **Every A-series weapon is a copy of Lyra's rifle or pistol definition** (`setup_weapons.py`): same fire rate, spread and 30-round magazine for the A88, A416, A25 and even the A89 LMG | — |
| Audio | A88 family uses the ADFRC AUG recordings (Session 035); reload and dry-fire not wired | — |

## What the registry adds that we did not have

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

## The plan, in order of payoff for effort

Each step is one commit with evidence, like the rest of the project.

### W1. Per-weapon gameplay stats from data (biggest feel change, no animation needed)

**Session 050: built (uncompiled).** The table is `[/Script/SouthernSpearCore.SSWeaponStatsSettings]`. The Lyra
bridge's `USSWeaponStatsSubsystem` applies magazine size, a full magazine and spare rounds (server) and scales
spread (every machine) as each weapon spawns. **Rate of fire** is set per weapon, on that weapon's own fire-ability
instance (`FireDelayTimeSecs` = 60 / rpm, the variable the producer's probe run found). **Semi-auto is still pending**
for the A25 and A9: it needs the item to grant Lyra's semi-automatic fire ability instead of the rifle's.
- A committed table `Config/DefaultGame.ini [SSWeaponStats]` (or a DataTable), seeded from
  `WEAPON_SOURCE_DATA.json`: rpm, spread, magazine, fire modes, and ADS/sway factors from inertia and dexterity.
  A88 and its MAF counterpart still share one row (ADR-016).
- `setup_weapons.py` writes the magazine size into each `ID_SS_*` (`Lyra.ShooterGame.Weapon.MagazineSize`
  tag stack) and the spread into each `WID_SS_*` instance. Rate of fire is set on the fire ability; if
  Lyra's Blueprint property isn't reachable from Python, the Lyra bridge applies it at equip (in C++, no
  Lyra change).
- The A89 gets its 200-round belt and a bipod-deployed mode later (W6).
- **Test:** an automation test asserts each A-series row matches the table; a live log prints rpm measured
  from shot timestamps.

### W2. Left-hand grip sockets from the `handAnim` poses (fixes the hands on every weapon)
- A stdlib tool (`Tools/Weapons/grip_sockets_from_handanim.py`) reads each weapon's grip clip from
  `Art/ADFRC/Animations/Rig/…` and rebuilds world transforms with the rig hierarchy (`rtm_rigs.world_from_local`).
  It expresses `lefthand` and `righthand` in the `weapon` bone's space and writes `SOCKET_LeftHandGrip` /
  `SOCKET_RightHandGrip` per weapon into the manifest that `setup_weapons.py` already reads.
- **This doesn't need the Arma rest pose (R-32).** It uses only the relative transform of two bones in the
  same frame, so the missing `SkeletonPivots.p3d` doesn't block it.
- Then drive **left-hand IK** to that socket, in third person (LOCOMOTION_AUDIT stage S0) and on the
  first-person arms: the left hand lands on the EF88's foregrip and the F89's handguard, not where Lyra's
  rifle had it. The MAF counterparts use the AK grip clips.
- **Test:** the tool reports hand-to-socket distances. A capture per weapon shows both hands on it.

### W3. Muzzle flash and shell ejection from the memory points
- Extend `Tools/Blender/adfrc_weapon.py` (it already reads memory points for the muzzle and the sight) to
  emit `SOCKET_Eject` from `nabojnicestart`, with the direction to `nabojniceend`.
- A shell-casing Niagara (or pooled static-mesh casings) and a muzzle flash on `SOCKET_Muzzle`, in first and
  third person. Presentation only (ADR-004).

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

## Recommendation

Start with **W1, then W2**. W1 changes how every weapon feels with no art or animation risk. W2 puts the hands
where they belong on every weapon, uses data we now have, and doesn't wait on R-32. Both can be built and
unit-tested without new assets.
