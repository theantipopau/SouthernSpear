"""Probe: what can a burning wreck actually be built from?

Three questions, because the answer changes the design:
  1. Does the Realistic Starter VFX pack contain any ready-to-place fire or
     smoke SYSTEM, or only materials? The keyword search found none, but that
     is not proof - this classifies every asset in the pack by class.
  2. Are the existing authored materials (M_SS_ScanPBR, MI_SS_CorrugatedIron,
     the Ironstone Quarry tints) PARAMETERISED? If they expose a base-colour
     and normal slot, new materials can be made that re-use pack textures
     instead of being flat constants - which is the difference between a
     re-textured wreck and a grey block with a colour on it.
  3. Real triangle counts for the SS_Dressing props. The earlier probe asked
     for LOD -1 and got 0 back, which is not the same as "no geometry".

Every section is individually guarded: a 5.8 API break in one block must not
cost us the answers from the other two.

Writes JSON; print() and unreal.log() do not reach the commandlet log.
"""
import json
import os
import traceback

import unreal

out = {"vfx_pack_classes": {}, "materials": {}, "prop_tris": {}}


def guard(name, fn):
    """Run fn, recording a traceback under out[name] instead of dying."""
    try:
        fn()
    except Exception:  # noqa: BLE001
        out.setdefault("errors", {})[name] = traceback.format_exc()[-1500:]


# --- 1. classify the VFX pack ---------------------------------------------
def probe_vfx_pack():
    paths = unreal.EditorAssetLibrary.list_assets(
        "/Game/Realistic_Starter_VFX_Pack_Vol2", recursive=True)
    counts = {}
    fire_ish = []
    for a in paths:
        apath = a.get_asset_path_name() if hasattr(a, "get_asset_path_name") else str(a)
        asset = unreal.load_asset(apath)
        if asset is None:
            counts["<unloadable>"] = counts.get("<unloadable>", 0) + 1
            continue
        cls = type(asset).__name__
        counts[cls] = counts.get(cls, 0) + 1
        if any(k in apath.lower() for k in ("fire", "flame", "smoke", "burn",
                                            "explosion", "ember", "ash")):
            fire_ish.append((apath, cls))
    out["vfx_pack_total"] = len(paths)
    out["vfx_pack_classes"] = counts
    out["vfx_pack_fire_named"] = sorted(fire_ish)


guard("vfx_pack", probe_vfx_pack)


# --- 2. are the authored materials parameterised? -------------------------
def probe_materials():
    for path in ("/Game/Art/Environment/Fab/M_SS_ScanPBR",
                 "/Game/Art/Environment/Fab/CorrugatedIron/MI_SS_CorrugatedIron",
                 "/Game/Art/Environment/DryRiver/QuarryTint/"
                 "MI_SS_Ironstone_MI_Qua_Sla_Cluster_Rock_M_06",
                 "/Game/Art/Environment/Fab/M_SS_WorldGroundVT",
                 "/Game/Art/Environment/RedGum/Materials/M_SS_RedGum_Timber",
                 "/Game/Art/Dressing/WorldGridMaterial"):
        mat = unreal.load_asset(path)
        if mat is None:
            out["materials"][path] = "NOT FOUND"
            continue
        rec = {"class": type(mat).__name__}
        for prop, key in (("parent", "parent"),):
            try:
                p = mat.get_editor_property(prop)
                rec[key] = p.get_path_name() if p is not None else None
            except Exception as exc:  # noqa: BLE001
                rec[key] = "<err {}>".format(exc)[:80]
        lib = unreal.MaterialEditingLibrary
        for getter, key in ((lib.get_scalar_parameter_names, "scalar_params"),
                            (lib.get_vector_parameter_names, "vector_params"),
                            (lib.get_texture_parameter_names, "texture_params")):
            try:
                names = [str(n) for n in getter(mat)]
                rec[key] = names[:24]
                rec[key + "_count"] = len(names)
            except Exception as exc:  # noqa: BLE001
                rec[key] = "<err {}>".format(exc)[:120]
        out["materials"][path] = rec


guard("materials", probe_materials)


# --- 3. real triangle counts ----------------------------------------------
def probe_tris():
    for path in ("/Game/Art/Dressing/SS_Dressing_Wreck",
                 "/Game/Art/Dressing/SS_Dressing_Barrel",
                 "/Game/Art/Dressing/SS_Dressing_Crate",
                 "/Game/Art/Dressing/SS_Dressing_Scrub",
                 "/Game/Art/Dressing/SS_Dressing_FencePost",
                 "/Game/Art/Environment/RedGum/SS_RedGum_Windmill",
                 "/Game/Art/Environment/RedGum/SS_RedGum_Farmhouse"):
        asset = unreal.load_asset(path)
        if not isinstance(asset, unreal.StaticMesh):
            out["prop_tris"][path] = "NOT A MESH ({})".format(type(asset).__name__)
            continue
        tris = {}
        for lod in (0, 1, 2):
            try:
                tris["lod{}".format(lod)] = asset.get_num_triangles(lod)
            except Exception as exc:  # noqa: BLE001
                tris["lod{}".format(lod)] = str(exc)[:60]
        try:
            tris["verts"] = asset.get_num_vertices(0)
        except Exception as exc:  # noqa: BLE001
            tris["verts"] = str(exc)[:60]
        out["prop_tris"][path] = tris


guard("prop_tris", probe_tris)

path_out = os.path.join(
    unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()),
    "Build", "probe_ravenshoe_vfx.json")
os.makedirs(os.path.dirname(path_out), exist_ok=True)
with open(path_out, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, default=str)
