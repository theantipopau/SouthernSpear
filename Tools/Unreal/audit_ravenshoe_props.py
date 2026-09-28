"""Per-prop material and reference audit.

The map-level audit proves the WRECK is on an authored ScanPBR instance. It
does not prove the other nine props are, and a prop with an empty slot renders
with the engine default material - which looks like a working map and is not.

Also answers whether the nine T_WM_* / T_WindMill_* textures left in the Props
folder by the windmill's FBX are referenced by anything. Unreferenced texture
assets are not harmless: they are shipped, they are in the repository, and
ADR-021's "raw packs stay git-ignored" line only holds if the adapted set is
deliberate.

Read-only. Writes JSON; print() and unreal.log() do not reach the commandlet log.
"""
import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
PROP_DEST = "/Game/Art/Environment/Ravenshoe/Props"
REPORT = os.path.join(PROJECT_DIR, "Build", "raven_prop_materials.json")

out = {"meshes": {}, "texture_refs": {}, "orphan_textures": [], "ok": None}

MESHES = ["SS_Raven_wreck_car", "SS_Raven_wreck_junk", "SS_Raven_fuel_drum",
          "SS_Raven_windmill", "SS_Raven_barn", "SS_Raven_sandbag_stack",
          "SS_Raven_trench_wall", "SS_Raven_water_tower", "SS_Raven_hand_pump",
          "SS_Raven_old_barn"]


def main():
    for name in MESHES:
        mesh = unreal.load_asset("{}/{}.{}".format(PROP_DEST, name, name))
        if not isinstance(mesh, unreal.StaticMesh):
            out["meshes"][name] = "NOT A MESH"
            continue
        rec = {"tris": None, "slots": [], "materials": []}
        try:
            rec["tris"] = mesh.get_num_triangles(0)
        except Exception:  # noqa: BLE001
            pass
        try:
            slots = mesh.get_editor_property("static_materials")
        except Exception as exc:  # noqa: BLE001
            rec["error"] = str(exc)[:100]
            slots = []
        for s in slots:
            sn = s.get_editor_property("material_slot_name")
            rec["slots"].append(sn or "")
            mi = s.get_editor_property("material_interface")
            rec["materials"].append(str(mi.get_path_name()) if mi else None)
        rec["all_authored"] = bool(rec["materials"]) and all(
            m and m.startswith("/Game/Art/Environment/Ravenshoe/Materials/")
            for m in rec["materials"])
        # The asset's own slots are the VENDOR's and stay that way - see
        # ADR-029. What matters is how many there are, because the per-instance
        # override loops over get_num_materials() and must cover all of them.
        rec["slot_count"] = len(rec["slots"])
        rec["any_slot_empty"] = any(m is None for m in rec["materials"])
        out["meshes"][name] = rec

    # What references the leftover windmill textures?
    for tex in unreal.EditorAssetLibrary.list_assets(PROP_DEST, recursive=True):
        if not tex.lower().endswith((".t_wm_", ".t_windmill_", ".t_wind_mill_")):
            if "T_WM_" not in tex and "T_Wind" not in tex:
                continue
        asset = unreal.load_asset(tex)
        refs = []
        if isinstance(asset, unreal.Texture2D):
            try:
                for ed in asset.get_editor_property("editable_textures") or []:
                    refs.append(str(ed))
            except Exception:  # noqa: BLE001
                pass
        # A texture is referenced if any material used by a prop samples it.
        for name, rec in out["meshes"].items():
            for mp in rec.get("materials", []):
                if not mp:
                    continue
                mat = unreal.load_asset(mp.split(".")[0])
                if mat is None:
                    continue
                try:
                    for pname in unreal.MaterialEditingLibrary.get_texture_parameter_names(mat):
                        val = unreal.MaterialEditingLibrary \
                            .get_material_instance_texture_parameter_value(mat, pname)
                        if val and tex.split(".")[0] in str(val):
                            refs.append("{}:{}".format(name, pname))
                except Exception:  # noqa: BLE001
                    continue
        out["texture_refs"][tex] = refs
        if not refs:
            out["orphan_textures"].append(tex)

    out["ok"] = not out["orphan_textures"]


try:
    main()
except Exception:  # noqa: BLE001
    out["errors"] = traceback.format_exc()[-1500:]

os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, default=str)
