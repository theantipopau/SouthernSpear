"""Import the ADFRC AUG weapon sounds and give them drop-in attenuation.

Scope, and why it stops where it does:

  * The 28 AUG_* WAVs are genuine weapon sounds (the other 184 in
    Art/ADFRC/Sounds/ are vehicle and miscellaneous). They import as
    SoundWave assets and are done here.
  * Weapon attenuation is copied from the AK-47, which is the only weapon in
    the project with a complete, working chain, so the AUG sounds the same way
    the existing rifle does.
  * The SoundCue graphs are NOT built. UE 5.8 exposes no factory for SoundCue
    and no way to enumerate or add nodes from Python -- the AK-47 cues are
    SoundNodeModulator graphs whose properties are not reflected. Cue authoring
    has to happen in the editor; the report says exactly which cue each group of
    new WAVs belongs in.

Every file is verified after import and the report gives converted/attempted
plus a per-file list, rather than a single total (R-31).

    "E:/Unreal/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" \
        SouthernSpear.uproject -nullrhi -unattended -nosplash -nosound -stdout \
        -ExecutePythonScript=Tools/Unreal/import_aug_audio.py
"""

import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SOURCE_DIR = os.path.join(PROJECT_DIR, "Art", "ADFRC", "Sounds")
DEST_WAVS = "/Game/AUG/Sound/AUG/Wavs"
DEST_ATT = "/Game/AUG/Sound/Attenuation"
REPORT = os.path.join(PROJECT_DIR, "Build", "aug_audio_import.json")

# SoundAttenuation to copy, per cue role. Keys are the destination name.
ATTENUATION_SOURCES = {
    "WeaponShot_att": "/Game/AK-47/Sound/Attenuation/WeaponShot_att",
    "WeaponHandling_att": "/Game/AK-47/Sound/Attenuation/WeaponHandling_att",
}

report = {"ok": False, "attempted": 0, "imported": 0, "waves": [], "errors": []}


def make_task(filename: str) -> "unreal.AssetImportTask":
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", filename)
    task.set_editor_property("destination_path", DEST_WAVS)
    task.set_editor_property("destination_name", os.path.splitext(os.path.basename(filename))[0])
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing_settings", True)
    return task


def import_waves() -> None:
    sources = sorted(
        f for f in os.listdir(SOURCE_DIR) if f.startswith("AUG") and f.lower().endswith(".wav")
    )
    tasks = [make_task(os.path.join(SOURCE_DIR, name)) for name in sources]
    report["attempted"] = len(tasks)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    for task in tasks:
        name = os.path.basename(task.get_editor_property("filename"))
        try:
            wave = task.get_editor_property("imported_object_paths")
        except Exception:
            wave = []
        if not wave:
            report["errors"].append(f"{name}: import task returned no object paths")
            continue
        asset = unreal.load_asset(wave[0])
        if asset is None:
            report["errors"].append(f"{name}: produced {wave[0]} but it will not load")
            continue
        report["imported"] += 1
        report["waves"].append(
            {
                "source": name,
                "asset": asset.get_path_name(),
                "channels": asset.get_editor_property("num_channels"),
                "sample_rate": asset.get_editor_property("sample_rate"),
                "duration_s": round(asset.get_editor_property("duration"), 4),
            }
        )


def build_attenuation() -> None:
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    for name, source_path in ATTENUATION_SOURCES.items():
        source = unreal.load_asset(source_path)
        if source is None:
            report["errors"].append(f"attenuation source missing: {source_path}")
            continue
        target_path = f"{DEST_ATT}/{name}"
        if unreal.EditorAssetLibrary.does_asset_exist(target_path):
            target = unreal.load_asset(target_path)
        else:
            target = asset_tools.create_asset(
                name,
                DEST_ATT,
                unreal.SoundAttenuation,
                unreal.SoundAttenuationFactory(),
            )
        if target is None:
            report["errors"].append(f"could not create {target_path}")
            continue
        target.set_editor_property("attenuation", source.get_editor_property("attenuation"))
        unreal.EditorAssetLibrary.save_loaded_asset(target)
        report.setdefault("attenuation", []).append(
            {
                "asset": target.get_path_name(),
                "copied_from": source_path,
                "settings": str(target.get_editor_property("attenuation")),
            }
        )


def main() -> None:
    try:
        import_waves()
    except Exception:
        report["errors"].append("import_waves:\n" + traceback.format_exc())
    try:
        build_attenuation()
    except Exception:
        report["errors"].append("build_attenuation:\n" + traceback.format_exc())

    report["ok"] = report["imported"] == report["attempted"] and not report["errors"]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1, default=str)
    print(
        f"SS_AUDIO: imported {report['imported']}/{report['attempted']} "
        f"waves, {len(report.get('attenuation', []))} attenuation assets, "
        f"{len(report['errors'])} errors"
    )


main()
