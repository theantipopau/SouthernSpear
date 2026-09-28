"""Website typefaces for the game UI (SIL OFL 1.1; Art/Fonts, converted from
Site/fonts with fontTools): font faces FF_BarlowCondensed (display: headings,
labels, buttons), FF_Inter_Regular / FF_Inter_SemiBold (body) and
FF_IBMPlexMono under /SouthernSpearUI/Fonts, loaded inline. SSWidgetKit
builds the composite fonts from them at runtime (Python cannot author
UFont typefaces). Report: Build/fonts_setup.json."""
import json
import unreal
import os
import sys

# does_asset_exist() misses Game Feature assets in a commandlet; see Tools/Unreal/ss_assets.py.
sys.path.insert(0, os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Tools", "Unreal"))
from ss_assets import asset_exists  # noqa: E402

DEST = "/SouthernSpearUI/Fonts"
ART = "E:/SouthernSpear/Art/Fonts/"
eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
report = {}
for stale in ("F_SS_Display", "F_SS_Body", "F_SS_Mono"):
    if asset_exists(DEST + "/" + stale):
        eal.delete_asset(DEST + "/" + stale)
for ttf in ("BarlowCondensed.ttf", "Inter-Regular.ttf", "Inter-SemiBold.ttf", "IBMPlexMono.ttf"):
    name = "FF_" + ttf.replace(".ttf", "").replace("-", "_")
    task = unreal.AssetImportTask()
    task.filename = ART + ttf
    task.destination_path = DEST
    task.destination_name = name
    task.replace_existing = True
    task.automated = True
    task.save = True
    tools.import_asset_tasks([task])
    face = unreal.load_asset(DEST + "/" + name)
    ok = isinstance(face, unreal.FontFace)
    if ok:
        face.set_editor_property("loading_policy", unreal.FontLoadingPolicy.INLINE)
        ok = eal.save_loaded_asset(face)
    report[name] = ok
json.dump(report, open("E:/SouthernSpear/Build/fonts_setup.json", "w"), indent=1)
unreal.log("SS_FONTS " + json.dumps(report))
