"""Apply ADFRC texture import settings inside the Unreal editor.

Run from the UE Python console or via -ExecutePythonScript:

    import ue_apply_texture_settings
    ue_apply_texture_settings.run()

It finds every Texture2D whose asset name matches a manifest entry and forces
sRGB + compression.  Safe to re-run; it only touches ADFRC textures.
"""
import json
import os

import unreal

MANIFEST = os.path.join(unreal.Paths.project_dir(), "Sourced", "ADF_Extracted",
                        "Textures", "_ue_manifest.json")

# Unreal's ETextureCompression equivalent enum names.
COMPRESSION = {
    "TC_Default": unreal.TextureCompressionSettings.TC_DEFAULT,
    "TC_Normalmap": unreal.TextureCompressionSettings.TC_NORMALMAP,
    "TC_Masks": unreal.TextureCompressionSettings.TC_MASKS,
    "TC_Grayscale": unreal.TextureCompressionSettings.TC_GREYSCALE,
    "TC_Emissive": unreal.TextureCompressionSettings.TC_EMISSIVE,
}


def load_manifest(path=MANIFEST):
    if not os.path.exists(path):
        unreal.log_warning("ADFRC manifest not found: %s" % path)
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def run(manifest_path=MANIFEST):
    data = load_manifest(manifest_path)
    wanted = {e["name"]: e for e in data.get("textures", [])}
    if not wanted:
        return 0

    changed = 0
    for tex in unreal.EditorAssetLibrary.list_assets("T_", recursive=True, include_folder=True):
        name = os.path.basename(tex.split(".")[0])
        entry = wanted.get(name + ".png") or wanted.get(name)
        if not entry:
            continue
        obj = unreal.EditorAssetLibrary.load_asset(tex)
        if not isinstance(obj, unreal.Texture2D):
            continue
        obj.set_editor_property("srgb", entry["srgb"])
        obj.set_editor_property(
            "compression_settings", COMPRESSION[entry["compression"]])
        obj.set_editor_property("filter", unreal.TextureFilter.TFILTER_ANISOTROPIC
                                if entry["srgb"] else unreal.TextureFilter.TFILTER_DEFAULT)
        changed += 1
        if changed % 200 == 0:
            unreal.log("ADFRC: %d textures configured" % changed)

    unreal.EditorAssetLibrary.save_directory("/Game/T_", only_if_is_dirty=False,
                                            recursive=True)
    unreal.log("ADFRC: configured %d / %d manifest textures" % (changed, len(wanted)))
    return changed
