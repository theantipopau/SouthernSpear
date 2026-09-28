"""Probe: what are the existing SS_Dressing props and the windmill, really?

The user described "a windmill, a fuel barrel, a damaged car" among newly
available assets. The barrel and the windmill exist. Whether a car exists is
the open question - a keyword sweep of all of Content/ and all of
VaultCache/ found no vehicle mesh under any plausible name, so before building
around one this measures what the candidates actually ARE: their real world
dimensions, triangle counts, collision and material slots.

Writes JSON; print() and unreal.log() do not reach the commandlet log.

Run:
    UnrealEditor-Cmd.exe <uproject> -run=pythonscript \
        -script="<project>/Tools/Unreal/probe_ravenshoe_props.py" -nullrhi -unattended
"""
import json
import os

import unreal

TARGETS = [
    "/Game/Art/Dressing/SS_Dressing_Wreck",
    "/Game/Art/Dressing/SS_Dressing_Barrel",
    "/Game/Art/Dressing/SS_Dressing_Crate",
    "/Game/Art/Dressing/SS_Dressing_Scrub",
    "/Game/Art/Dressing/SS_Dressing_FencePost",
    "/Game/Art/Dressing/SS_Dressing_FenceRail",
    "/Game/Art/Environment/RedGum/SS_RedGum_Windmill",
    "/Game/Art/Environment/RedGum/SS_RedGum_Farmhouse",
]

out = {}


def prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:  # noqa: BLE001
        return default


for path in TARGETS:
    asset = unreal.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        out[path] = "NOT A STATIC MESH"
        continue
    bounds = asset.get_bounds()
    org = bounds.origin
    ext = bounds.box_extent
    mats = []
    try:
        for s in asset.get_editor_property("static_materials"):
            m = s.get_editor_property("material_interface")
            mats.append(m.get_name() if m else None)
    except Exception as exc:  # noqa: BLE001
        mats = ["<err {}>".format(exc)]

    collision = None
    try:
        body = prop(asset, "body_setup")
        if body is not None:
            agg = body.get_editor_property("agg_geom")
            if agg is not None:
                collision = len(agg.get_editor_property("to_elem"))
    except Exception:  # noqa: BLE001
        pass

    out[path] = {
        "size_m": [round(ext.x * 2, 2), round(ext.y * 2, 2), round(ext.z * 2, 2)],
        "origin_cm": [round(org.x, 1), round(org.y, 1), round(org.z, 1)],
        "tris": asset.get_num_triangles(-1) if hasattr(asset, "get_num_triangles") else None,
        "collision_elements": collision,
        "materials": mats,
        "lod_group": str(prop(asset, "lod_group", "?")),
    }

path_out = os.path.join(
    unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()),
    "Build", "probe_ravenshoe_props.json")
os.makedirs(os.path.dirname(path_out), exist_ok=True)
with open(path_out, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, default=str)
