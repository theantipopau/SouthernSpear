# Weapon Source Data — the A-series as the ADF Re-Cut configs describe them

**Generated** by `python Tools/Weapons/adfrc_weapon_data.py` from `Docs/Sourced/ADFRC/config_registry.json`.
Do not edit by hand. Real names are allowed anywhere (ADR-035); the A-series names are what the game uses today.

This is descriptive ADFRC source-config data, not an independent service specification or a complete game-tuning prescription.
Southern Spear currently applies configured magazine size, spare ammunition, spread scale and rounds-per-minute through `SSWeaponStatsSettings` and `USSWeaponStatsSubsystem`; the source values are adapted into project-owned rows rather than copied wholesale. The source fire-mode distinction (`bFullAuto=false`) is not enforced yet, and these tables do not establish a sight zero or a measured recoil profile. See `NEXT_PRIORITIES.md` §5 for the implementation boundary.

| A-series | Role | Source class | Fire modes (rpm, dispersion MOA) | Magazine | Grip pose clip | Reload |
|---|---|---|---|---|---|---|
| A88 | service rifle | `ADFRC_EF88_Base` | single 682 rpm 2.0 MOA, fullauto 682 rpm 2.0 MOA | ADFRC_30Rnd_aug_ef88 | EF88_Vg_static | GestureReloadAUG (**shipped**, 165 frames) |
| A88G | service rifle, grenade launcher | `ADFRC_EF88GL_Base` | single 682 rpm 2.0 MOA, fullauto 682 rpm 2.0 MOA | ADFRC_30Rnd_aug_ef88 | AUG_GL | GestureReloadAUG (**shipped**, 165 frames) |
| A89 | light support weapon | `ADFRC_minimi_BASE` | fullauto 750 rpm 3.47 MOA, fullautodeployed 750 rpm 3.47 MOA | ADFRC_200Rnd_556_Minimi_TR5 | Minimi_Standard | GestureReloadM200 (vanilla Arma, not shipped) |
| A4 | carbine | `ADFRC_M4A5_556_Base` | single 857 rpm 2.0 MOA, fullauto 857 rpm 2.0 MOA | ADFRC_30Rnd_PMAG | ar15_8in_cgrip_static | GestureReloadSPAR_01 (vanilla Arma, not shipped) |
| A416 | carbine (SF) | `ADFRC_HK416_556_Base` | single 857 rpm 2.0 MOA, fullauto 857 rpm 2.0 MOA | ADFRC_30Rnd_PMAG | hk416_cgrip_static | GestureReloadSPAR_01 (vanilla Arma, not shipped) |
| A417 | battle rifle (SF) | `ADFRC_HK417_Base` | single 857 rpm 2.35 MOA, fullauto 600 rpm 2.35 MOA | ADFRC_20RD_HK417_F4 | hk417_static | GestureReloadSPAR_01 (vanilla Arma, not shipped) |
| A25 | marksman rifle | `adfrc_SR25_Base` | single 600 rpm 1.5 MOA | — (none declared) | ar15_10in_cgrip_static | GestureReloadSPAR_01 (vanilla Arma, not shipped) |
| A9 | pistol | `ADFRC_G19_Base` | single 600 rpm 8.59 MOA | — (none declared) | — | — |

## Handling and points

| A-series | Handling (Arma units) | Muzzle / ejection memory points | Audio resolved in pack |
|---|---|---|---|
| A88 | inertia 0.4, dexterity 1.3, aimTransitionSpeed 1.1, swayDecaySpeed 1.25, maxRecoilSway 0.0125 | muzzleend: konec hlavne, muzzlepos: usti hlavne, cartridgepos: nabojnicestart, cartridgevel: nabojniceend | AUG_InteriorTail_SoundSet, AUG_Shot_SoundSet, AUG_Tail_SoundSet, AUG_silencerInteriorTail_SoundSet, AUG_silencerShot_SoundSet, AUG_silencerTail_SoundSet |
| A88G | inertia 0.55, dexterity 1.7, aimTransitionSpeed 1.1, swayDecaySpeed 1.35, maxRecoilSway 0.0125 | muzzleend: konec hlavne, muzzlepos: usti hlavne, cartridgepos: nabojnicestart, cartridgevel: nabojniceend | AUG_InteriorTail_SoundSet, AUG_Shot_SoundSet, AUG_Tail_SoundSet, AUG_silencerInteriorTail_SoundSet, AUG_silencerShot_SoundSet, AUG_silencerTail_SoundSet |
| A89 | dexterity 100 | — | none (vanilla soundsets only) |
| A4 | inertia 0.3, dexterity 1.3, swayDecaySpeed 1.25, maxRecoilSway 0.0125 | muzzleend: konec hlavne, muzzlepos: usti hlavne, cartridgepos: nabojnicestart, cartridgevel: nabojniceend | none (vanilla soundsets only) |
| A416 | inertia 0.3, dexterity 1.3, swayDecaySpeed 1.25, maxRecoilSway 0.0125 | muzzleend: konec hlavne, muzzlepos: usti hlavne, cartridgepos: nabojnicestart, cartridgevel: nabojniceend | none (vanilla soundsets only) |
| A417 | inertia 0.3, dexterity 1.3, swayDecaySpeed 1.25, maxRecoilSway 0.0125 | muzzleend: konec hlavne, muzzlepos: usti hlavne, cartridgepos: nabojnicestart, cartridgevel: nabojniceend | none (vanilla soundsets only) |
| A25 | inertia 0.99, dexterity 1.8, swayDecaySpeed 1.25, maxRecoilSway 0.0125, recoil recoil_ebr | muzzleend: konec hlavne, muzzlepos: usti hlavne, cartridgepos: nabojnicestart, cartridgevel: nabojniceend | none (vanilla soundsets only) |
| A9 | inertia 0.15, swayDecaySpeed 1.25, maxRecoilSway 0.0125, recoil recoil_pistol_p07 | muzzleend: konec hlavne, muzzlepos: usti hlavne, cartridgepos: nabojnicestart, cartridgevel: nabojniceend | none (vanilla soundsets only) |

**MAF grip poses** (same gameplay, opposing presentation): ak_cgrip_static, ak_afg_static, ak_vg_static, ak_vg_tb_static, ak_under_static.

**Reload gestures shipped as real animation:** GestureReloadAUG (165 frames), GestureReloadAUGProne (165 frames), MPP_Slow_Reload (91 frames), MPP_Fast_Reload (54 frames). Every other `reloadAction` names a
vanilla Arma state the pack does not contain.
