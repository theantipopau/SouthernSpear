"""Read-only diagnosis of the two open Ravenshoe questions.

1. Why 0/32 routes when the deck and the creek bed are both navigable.
   The existing verifier checks that the OBJECTIVES project onto the navmesh
   but never checks the DEPLOYMENTS, so a deployment sitting off the mesh
   fails every route silently and looks like a map problem.

2. What the three level geometry actors are actually rendering. The
   surfaces pass reports "SS_MAP_Ravenshoe_01 = 0/1" and the audit only
   checks the bridge and the gate house, so the terrain is never verified.

Writes Build/ravenshoe_diagnosis.json. Changes nothing.
"""
import json
import os
import traceback

import unreal

MAP = "/Game/Maps/L_Ravenshoe_01"
OUT = os.path.join(
    unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()),
    "Build", "ravenshoe_diagnosis.json")

report = {"map": MAP, "deployment_nav": [], "bounds": [], "materials": {},
          "terrain_nav": [], "warnings": []}


def dump_material_params():
    """Read every texture and scalar parameter back off the surface instances.

    A material can be correctly assigned and still render as a flat default
    if the parameter writes never stuck - which is exactly what happened to
    the flat safety-net materials (M-008h). Assignment is not the question;
    the bindings are.
    """
    want = ("MI_SS_Raven_Road", "MI_SS_Raven_Iron", "MI_SS_Raven_Deck",
            "MI_SS_Raven_Stone", "MI_SS_RavenFlat_Terrain")
    rows = {}
    for n in want:
        m = unreal.load_asset("/Game/Art/Environment/Ravenshoe/Materials/" + n)
        if m is None:
            rows[n] = {"loaded": False}
            continue
        row = {"loaded": True, "parent": str(m.get_editor_property("parent"))}
        # Material instances do NOT expose their parameters as editor
        # properties. MaterialEditingLibrary.get_material_property does not
        # exist on 5.8, but the instance-specific accessors do.
        mel = unreal.MaterialEditingLibrary
        for p in ("BaseColor", "Normal", "Roughness", "AO", "Metalness"):
            try:
                t = mel.get_material_instance_texture_parameter_value(m, p)
                row[p] = t.get_name() if t else "UNSET"
            except Exception as exc:                      # noqa: BLE001
                row[p] = "ERR " + str(exc).splitlines()[0][:50]
        for p in ("Tint", "Tiling"):
            try:
                row[p] = str(mel.get_material_instance_scalar_parameter_value(m, p))
            except Exception as exc:                      # noqa: BLE001
                row[p] = "ERR " + str(exc).splitlines()[0][:50]
        try:
            row["Tint_vector"] = str(
                mel.get_material_instance_vector_parameter_value(m, "Tint"))
        except Exception as exc:                          # noqa: BLE001
            row["Tint_vector"] = "ERR " + str(exc).splitlines()[0][:50]
        rows[n] = row
    return rows


def v3(v):
    """unreal.Vector is not iterable on 5.8."""
    return [round(v.x, 1), round(v.y, 1), round(v.z, 1)]


def step(name, ok, detail=""):
    report.setdefault("steps", []).append(
        {"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def main():
    step("load_map", True, unreal.EditorLoadingAndSavingUtils.load_map(MAP))
    world = unreal.EditorLevelLibrary.get_editor_world()
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = sub.get_all_level_actors()

    # ---- 1. the nav bounds volume, in world units -----------------------
    # Scale alone is meaningless; the default brush is not 200 units, so
    # scale [115,165,45] does not by itself tell you the covered area.
    for a in actors:
        if isinstance(a, unreal.NavMeshBoundsVolume):
            b = a.get_actor_bounds(False)
            report["bounds"].append({
                "label": a.get_actor_label(),
                "location_cm": v3(a.get_actor_location()),
                "scale": [round(a.get_actor_scale3d().x, 3),
                          round(a.get_actor_scale3d().y, 3),
                          round(a.get_actor_scale3d().z, 3)],
                "world_min_cm": v3(b[0]),
                "world_max_cm": v3(b[1]),
            })

    # ---- 2. does each DEPLOYMENT reach the navmesh? ----------------------
    # This is the check that was missing. A deployment off the mesh makes
    # every route from it fail, which reads identically to "bots won't move".
    for a in actors:
        label = a.get_actor_label()
        if "Deploy" not in label and "PlayerStart" not in label:
            continue
        loc = a.get_actor_location()
        hit = unreal.NavigationSystemV1.project_point_to_navigation(
            world,
            unreal.Vector(loc.x, loc.y, loc.z),
            None, None,
            unreal.Vector(2000, 2000, 4000))   # 20 m out, 40 m down
        if hit is None or str(hit) == "None":
            report["deployment_nav"].append({
                "label": label, "z_cm": round(loc.z, 1),
                "on_nav": False, "delta_z_cm": None})
        else:
            report["deployment_nav"].append({
                "label": label, "z_cm": round(loc.z, 1),
                "on_nav": True,
                "nav_z_cm": round(hit.z, 1),
                "delta_z_cm": round(hit.z - loc.z, 1)})

    # ---- 3. is the navmesh present along the road, not just the bridge? --
    # Sample the road corridor. If the mesh stops short of the deployments
    # the bounds volume is too small or the ramps did not build.
    for y_m in (0, 20, 40, 60, 80, 100, 120, 130, 140):
        for x_m in (0,):
            p = unreal.Vector(x_m * 100.0, y_m * 100.0, 3000)
            hit = unreal.NavigationSystemV1.project_point_to_navigation(
                world, p, None, None,
                unreal.Vector(500, 500, 8000))
            report["terrain_nav"].append({
                "x_m": x_m, "y_m": y_m,
                "on_nav": hit is not None and str(hit) != "None",
                "z_cm": round(hit.z, 1) if hit and str(hit) != "None" else None})

    # ---- 4. what are the level geometry actors really rendering? --------
    for a in actors:
        if not a.get_actor_label().startswith("SS_Raven_Geo_"):
            continue
        comp = a.get_component_by_class(unreal.StaticMeshComponent)
        if comp is None:
            continue
        mesh = comp.get_editor_property("static_mesh")
        mats = comp.get_editor_property("override_materials")
        rows = []
        for i, m in enumerate(mats):
            rows.append({
                "slot": i,
                "override": m.get_name() if m else None,
            })
        # the mesh asset's own slots, for comparison: these read back None
        # after an override write, which is why they are only informative
        asset_slots = []
        try:
            for i in range(mesh.get_num_sections(0)):
                asset_slots.append(mesh.get_material(i))
        except Exception as exc:                      # noqa: BLE001
            asset_slots = ["err: %s" % str(exc).splitlines()[0][:80]]
        report["materials"][a.get_actor_label()] = {
            "mesh": mesh.get_name() if mesh else None,
            "sections": len(asset_slots),
            "override_materials": rows,
            "asset_slots": [m.get_name() if m else None for m in asset_slots],
        }

    for d in report["deployment_nav"]:
        if not d["on_nav"]:
            report["warnings"].append(
                "{} is {} m off the navmesh".format(d["label"], "?"))
    step("wrote", True, OUT)


try:
    main()
    report["material_params"] = dump_material_params()
    with open(OUT, "w") as fh:
        json.dump(report, fh, indent=2, default=str)
    print("DIAGNOSIS_WRITTEN", OUT)
except Exception:                                       # noqa: BLE001
    report["exception"] = traceback.format_exc()
    with open(OUT, "w") as fh:
        json.dump(report, fh, indent=2, default=str)
    print("DIAGNOSIS_FAILED", report["exception"][-400:])
