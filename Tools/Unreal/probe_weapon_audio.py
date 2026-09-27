"""Probe the existing weapon audio chain so new cues replicate it.

The AK-47 is the one weapon in the project with a complete set of WAVs, cues
and attenuation, so it is the pattern to copy. This dumps the asset classes and
the SoundCue node graphs without modifying anything.

    "E:/Unreal/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" \
        SouthernSpear.uproject -nullrhi -unattended -nosplash -nosound -stdout \
        -ExecutePythonScript=Tools/Unreal/probe_weapon_audio.py
"""

import json
import os

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
OUT = os.path.join(PROJECT_DIR, "Build", "weapon_audio_probe.json")

PATHS = [
    "/Game/AK-47/Sound/AK-47/Cues/AK47_Fire_Cue",
    "/Game/AK-47/Sound/AK-47/Cues/AK47_Empty_Cue",
    "/Game/AK-47/Sound/AK-47/Cues/Reload_Cue",
    "/Game/AK-47/Sound/AK-47/Cues/ReloadInsert_Cue",
    "/Game/AK-47/Sound/AK-47/Cues/AK47_FireLoop_Cue",
    "/Game/AK-47/Sound/AK-47/Wavs/AK-47_Fire_1",
    "/Game/AK-47/Sound/Attenuation/WeaponShot_att",
    "/Game/AK-47/Sound/Attenuation/WeaponHandling_att",
    "/Game/Audio/Sounds/Weapons/MS_GatedWavePlayer",
    "/Game/Audio/Sounds/Weapons/MS_EqualPowerCrossfade",
]

report = {"ok": False, "assets": {}, "errors": []}


def describe_sound_cue(cue) -> dict:
    info = {"class": cue.get_class().get_name()}
    # Reflect rather than guess: the node-collection property name differs
    # between engine versions, so read whatever the class actually exposes.
    editable = [
        p.get_name()
        for p in cue.get_class().get_default_object().get_class()
    ] if False else None
    info["properties"] = sorted(
        p.get_name()
        for p in unreal.SoundCue.static_class()
        .get_properties()
    ) if hasattr(unreal.SoundCue.static_class(), "get_properties") else "n/a"

    for prop in ("attenuation_settings", "duration", "root_nodes", "all_nodes",
                 "sound_wave", "meta_sound_source"):
        try:
            value = cue.get_editor_property(prop)
            if hasattr(value, "get_path_name"):
                info[prop] = value.get_path_name()
            elif isinstance(value, (list, tuple)):
                info[prop] = [
                    v.get_path_name() if hasattr(v, "get_path_name") else str(v) for v in value
                ]
            else:
                info[prop] = str(value)
        except Exception as exc:
            info[prop] = f"n/a ({type(exc).__name__})"
    return info


def main() -> None:
    for path in PATHS:
        asset = unreal.load_asset(path)
        if asset is None:
            report["errors"].append(f"missing {path}")
            continue
        name = asset.get_class().get_name()
        if name == "SoundCue":
            report["assets"][path] = describe_sound_cue(asset)
        else:
            entry = {"class": name}
            if name == "SoundWave":
                for prop in ("duration", "num_channels", "sample_rate", "sound_class"):
                    try:
                        entry[prop] = str(asset.get_editor_property(prop))
                    except Exception:
                        pass
            if "Attenuation" in name or "Submix" in name:
                try:
                    entry["fallback"] = asset.get_editor_property(
                        "fallback_settings"
                    ).get_path_name()
                except Exception:
                    pass
            report["assets"][path] = entry

    report["ok"] = bool(report["assets"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1, default=str)
    print(f"SS_AUDIO: wrote {OUT} with {len(report['assets'])} assets")


main()
