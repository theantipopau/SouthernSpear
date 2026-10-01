"""
Southern Spear - per-weapon data for the A-series, read out of the ADF Re-Cut config registry.

The A-series (ADR-016 names) draw on ADFRC source configs and related assets. This reports source-config
values (not independent service specifications or game tuning): rate of fire, dispersion, magazine,
fire modes, handling (inertia, dexterity, sway), muzzle/ejection memory points, hand-grip pose clips,
reload gestures, and resolved audio. Southern Spear applies selected project-owned stats through
SSWeaponStatsSettings and USSWeaponStatsSubsystem; source fire-mode distinctions are not all enforced.

    python Tools/Weapons/adfrc_weapon_data.py            # writes Docs/WEAPON_SOURCE_DATA.md and .json

Reads Docs/Sourced/ADFRC/config_registry.json (committed). No Unreal, no Blender, stdlib only.
Real product names are fine anywhere (ADR-035); the A-series names are what the game currently uses.
"""

import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REGISTRY = os.path.join(ROOT, "Docs", "Sourced", "ADFRC", "config_registry.json")
OUT_MD = os.path.join(ROOT, "Docs", "WEAPON_SOURCE_DATA.md")
OUT_JSON = os.path.join(ROOT, "Docs", "WEAPON_SOURCE_DATA.json")

# A-series name -> ADFRC base class (the mesh source in Tools/build_adfrc_weapons.py).
A_SERIES = [
    ("A88", "ADFRC_EF88_Base", "service rifle"),
    ("A88G", "ADFRC_EF88GL_Base", "service rifle, grenade launcher"),
    ("A89", "ADFRC_minimi_BASE", "light support weapon"),
    ("A4", "ADFRC_M4A5_556_Base", "carbine"),
    ("A416", "ADFRC_HK416_556_Base", "carbine (SF)"),
    ("A417", "ADFRC_HK417_Base", "battle rifle (SF)"),
    ("A25", "adfrc_SR25_Base", "marksman rifle"),
    ("A9", "ADFRC_G19_Base", "pistol"),
]
# Grip-pose clips shipped for the opposing (MAF) presentation: same gameplay, different hold.
MAF_GRIPS = ["ak_cgrip_static", "ak_afg_static", "ak_vg_static", "ak_vg_tb_static", "ak_under_static"]
# Reload gestures the pack ships as real animation (all others name vanilla Arma states it does not ship).
SHIPPED_GESTURES = {"GestureReloadAUG": 165, "GestureReloadAUGProne": 165, "MPP_Slow_Reload": 91, "MPP_Fast_Reload": 54}


def load():
    with open(REGISTRY, encoding="utf-8") as handle:
        return json.load(handle)


def main():
    registry = load()
    classes = registry["classes"]
    by_path = {}
    for c in classes:
        by_path.setdefault(c["path"].lower(), []).append(c)

    def item(name):
        found = [c for c in classes if c["name"] == name and c["is_item"]]
        # The same name is declared in Source/ and Workshop/; take the fullest declaration.
        return max(found, key=lambda c: len(c["own_properties"])) if found else None

    rows = []
    for short, base, role in A_SERIES:
        c = item(base)
        if not c:
            rows.append({"name": short, "source_class": base, "missing": True})
            continue
        op = c["own_properties"]
        modes = []
        for path, entries in by_path.items():
            parts = path.split(".")
            if len(parts) == 3 and parts[1] == base.lower():
                mode = entries[0]["own_properties"]
                rt = mode.get("reloadTime")
                if isinstance(rt, (int, float)) and rt > 0 and parts[2] in [m.lower() for m in c["fire_modes"]]:
                    disp = mode.get("dispersion")
                    modes.append({
                        "mode": parts[2],
                        "rpm": round(60.0 / rt),
                        "dispersion_rad": disp,
                        "dispersion_moa": round(disp * 180 / math.pi * 60, 2) if isinstance(disp, (int, float)) else None,
                    })
        clips = sorted({a["config_path"].replace("\\", "/").split("/")[-1].replace(".rtm", "")
                        for a in c["animation_clips"] if a["prop"] == "handAnim[]"})
        reload_action = c["animations"].get("reloadAction") if isinstance(c["animations"], dict) else None
        sounds = sorted({u["sound_set"] for u in c.get("sound_sets_used", [])})
        unresolved = sorted(set(c.get("sound_sets_unresolved") or []))
        rows.append({
            "name": short,
            "role": role,
            "source_class": base,
            "source_file": c["source"],
            "fire_modes": modes,
            "magazines": c["magazines"],
            "magazine_wells": c["magazine_wells"],
            "handling": {k: op.get(k) for k in ("inertia", "dexterity", "aimTransitionSpeed", "swayDecaySpeed", "maxRecoilSway", "recoil")
                         if op.get(k) is not None},
            "memory_points": c["attachment_points"],
            "grip_pose_clips": clips,
            "reload_action": reload_action,
            "reload_shipped_frames": SHIPPED_GESTURES.get(reload_action or ""),
            "sound_sets_resolved": sounds,
            "sound_sets_vanilla_only": unresolved[:6],
        })

    data = {
        "generated_from": "Docs/Sourced/ADFRC/config_registry.json",
        "weapons": rows,
        # Shipped in Animations/ (ASSET_MANIFEST.json clips); no ADFRC weapon binds them, so the registry cannot.
        "maf_grip_clips_available": MAF_GRIPS,
        "shipped_reload_gestures": SHIPPED_GESTURES,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=1)

    lines = [
        "# Weapon Source Data — the A-series as the ADF Re-Cut configs describe them",
        "",
        "**Generated** by `python Tools/Weapons/adfrc_weapon_data.py` from `Docs/Sourced/ADFRC/config_registry.json`.",
        "Do not edit by hand. Real names are allowed anywhere (ADR-035); the A-series names are what the game uses today.",
        "",
        "This is descriptive ADFRC source-config data, not an independent service specification or a complete game-tuning prescription.",
        "Southern Spear currently applies configured magazine size, spare ammunition, spread scale and rounds-per-minute through `SSWeaponStatsSettings` and `USSWeaponStatsSubsystem`; the source values are adapted into project-owned rows rather than copied wholesale. The source fire-mode distinction (`bFullAuto=false`) is not enforced yet, and these tables do not establish a sight zero or a measured recoil profile. See `NEXT_PRIORITIES.md` §5 for the implementation boundary.",
        "",
        "| A-series | Role | Source class | Fire modes (rpm, dispersion MOA) | Magazine | Grip pose clip | Reload |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        if r.get("missing"):
            lines.append("| {} | | `{}` | **not in registry** | | | |".format(r["name"], r["source_class"]))
            continue
        modes = ", ".join("{} {} rpm {} MOA".format(m["mode"], m["rpm"], m["dispersion_moa"]) for m in r["fire_modes"]) or "—"
        mags = ", ".join(r["magazines"]) or "— (none declared)"
        reload = r["reload_action"] or "—"
        if r["reload_shipped_frames"]:
            reload += " (**shipped**, {} frames)".format(r["reload_shipped_frames"])
        elif r["reload_action"]:
            reload += " (vanilla Arma, not shipped)"
        lines.append("| {} | {} | `{}` | {} | {} | {} | {} |".format(
            r["name"], r["role"], r["source_class"], modes, mags, ", ".join(r["grip_pose_clips"]) or "—", reload))
    lines += ["", "## Handling and points", "",
              "| A-series | Handling (Arma units) | Muzzle / ejection memory points | Audio resolved in pack |",
              "|---|---|---|---|"]
    for r in rows:
        if r.get("missing"):
            continue
        handling = ", ".join("{} {}".format(k, v) for k, v in r["handling"].items()) or "—"
        points = ", ".join("{}: {}".format(k, v) for k, v in r["memory_points"].items()) or "—"
        audio = ", ".join(r["sound_sets_resolved"]) or "none (vanilla soundsets only)"
        lines.append("| {} | {} | {} | {} |".format(r["name"], handling, points, audio))
    lines += ["",
              "**MAF grip poses** (same gameplay, opposing presentation): " + ", ".join(MAF_GRIPS) + ".",
              "",
              "**Reload gestures shipped as real animation:** " + ", ".join(
                  "{} ({} frames)".format(k, v) for k, v in SHIPPED_GESTURES.items()) + ". Every other `reloadAction` names a",
              "vanilla Arma state the pack does not contain.", ""]
    with open(OUT_MD, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    print("wrote {} and {} ({} weapons, {} missing)".format(os.path.relpath(OUT_MD, ROOT), os.path.relpath(OUT_JSON, ROOT),
          len(rows), sum(1 for r in rows if r.get("missing"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
