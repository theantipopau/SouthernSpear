"""
Southern Spear - asset helpers shared by the Tools/Unreal commandlet scripts.

EditorAssetLibrary.does_asset_exist() can answer False for an asset under a Game Feature plugin
(/SSExp_ObjectiveAssault/...) when the script runs in a commandlet, although the asset is on disk and
load_asset() resolves it. A script that branches "load if it exists, else create" then tries to create
an asset that is already there: create_asset returns None and the run dies part-way, leaving its
Build/ report half-written (Session 051, setup_adf_soldier.py). asset_exists() falls back to
load_asset(), the check that fix proved on the producer's machine, so a re-run takes the load branch.

Import from a script run by -ExecutePythonScript (the script's own folder is not on sys.path):

    import sys
    sys.path.insert(0, os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Tools", "Unreal"))
    from ss_assets import asset_exists
"""

import unreal


def asset_exists(path):
    """True when the asset at `path` (package path, with or without ".Name") exists on disk."""
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return True
    return unreal.load_asset(path) is not None
