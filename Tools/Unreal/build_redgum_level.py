# Southern Spear - Red Gum Station (L_RedGum_01), pass 1 (ADR-022).
#
# Copies the Fab "Rural Australia" example map (1 km landscape, not World
# Partition) into /Game/Maps/L_RedGum_01 and wires Objective Assault:
# two deployments (LyraPlayerStarts + extras), three objectives along the
# centre line, the director, a NavMeshBoundsVolume and the SS experience.
# Everything is placed by ground trace. Pass 2 (build_redgum_nav.py) builds nav.
# Idempotent (recopies the source map each run). Writes Build/redgum_level.json.

import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "redgum_level.json")
SRC = "/Game/RuralAustralia/Maps/RuralAustralia_Example_01"
MAP = "/Game/Maps/L_RedGum_01"
EXP_CLASS = "/SSExp_ObjectiveAssault/Experiences/B_SS_ObjectiveAssault.B_SS_ObjectiveAssault_C"
CAPTURE_RADIUS_CM = 1200.0
# Centre line along X, metres. Deployments face each other across 560 m.
DEPLOY_X_M = 280.0
OBJECTIVES = [(-110.0, 0.0, "SS_MAP_RedGum_ObjA_BorePump", "Bore Pump"),
              (0.0, 0.0, "SS_MAP_RedGum_ObjB_Homestead", "Homestead"),
              (110.0, 0.0, "SS_MAP_RedGum_ObjC_ShearingShed", "Shearing Shed")]
EXTRA_STARTS = 7
FENCE_MESHES = ["/Game/RuralAustralia/StaticMeshes/Props/Fence_01/SM_Fence_Wires_01",
                "/Game/RuralAustralia/StaticMeshes/Props/Fence_01/SM_Fence_02"]
SPACING_CM = 400.0

eal = unreal.EditorAssetLibrary
report = {"ok": False, "steps": [], "errors": []}


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def ground(world, x, y):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, 50000.0), unreal.Vector(x, y, -50000.0),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    if hit is None:
        return None, None
    d = hit.to_dict()
    actor = d.get("hit_object_handle") or d.get("actor")
    return d["impact_point"].z, str(actor.get_class().get_name()) if actor else "?"


def main():
    # Load the source and "save as" MAP at the end; the source is never saved.
    # (duplicate_asset keeps the copied world referenced -> World Memory Leaks.)
    if eal.does_asset_exist(MAP):
        eal.delete_asset(MAP)
    world = unreal.EditorLoadingAndSavingUtils.load_map(SRC)
    if not step("load_map", world is not None, SRC):
        return
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.CineCameraActor):
        actors.destroy_actor(a)
    # Wire fences: players climb through the wires (Lyra has no vault), so the
    # fence meshes carry no collision and do not cut the nav mesh. The fence
    # Blueprint rebuilds its components on load, so this is set on the meshes
    # (our local Fab copies; Content/RuralAustralia is git-ignored).
    fenced = []
    for path in FENCE_MESHES:
        mesh = unreal.load_asset(path)
        if mesh is None:
            continue
        unreal.EditorStaticMeshLibrary.remove_collisions(mesh)
        body = mesh.get_editor_property("body_setup")
        if body:
            body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
        eal.save_loaded_asset(mesh)
        fenced.append(mesh.get_name())
    step("fences_passable", len(fenced) == len(FENCE_MESHES), fenced)
    unreal.SystemLibrary.execute_console_command(world, "BUILDPATHS")  # traces need it (CLAUDE.md)

    start_class = unreal.load_class(None, "/Script/LyraGame.LyraPlayerStart")
    report["starts"] = []
    for side, sign in (("A", -1.0), ("B", 1.0)):
        x0 = sign * DEPLOY_X_M * 100.0
        yaw = 0.0 if sign < 0 else 180.0
        offsets = [0.0] + [(i // 2 + 1) * SPACING_CM * (1 if i % 2 == 0 else -1) for i in range(EXTRA_STARTS)]
        for n, dy in enumerate(offsets):
            z, what = ground(world, x0, dy)
            if z is None:
                continue
            s = actors.spawn_actor_from_class(start_class, unreal.Vector(x0, dy, z + 100.0),
                                              unreal.Rotator(roll=0, pitch=0, yaw=yaw))
            s.set_actor_label("SS_MAP_RedGum_Deploy{}{}".format(side, "" if n == 0 else "_Extra{:02d}".format(n)))
            report["starts"].append([side, round(z), what])
    step("starts", len(report["starts"]) == 2 * (EXTRA_STARTS + 1), len(report["starts"]))

    report["objectives"] = []
    for index, (xm, ym, label, name) in enumerate(OBJECTIVES):
        z, what = ground(world, xm * 100.0, ym * 100.0)
        if z is None:
            continue
        o = actors.spawn_actor_from_class(unreal.SSObjectiveActor, unreal.Vector(xm * 100.0, ym * 100.0, z),
                                          unreal.Rotator(roll=0, pitch=0, yaw=0))
        o.set_actor_label(label)
        o.set_editor_property("sequence_index", index)
        o.set_editor_property("objective_name", unreal.Text(name))
        o.get_component_by_class(unreal.SphereComponent).set_sphere_radius(CAPTURE_RADIUS_CM)
        report["objectives"].append([label, round(z), what])
    step("objectives", len(report["objectives"]) == len(OBJECTIVES), report["objectives"])

    d = actors.spawn_actor_from_class(unreal.SSObjectiveAssaultDirector, unreal.Vector(0, 0, 0),
                                      unreal.Rotator(roll=0, pitch=0, yaw=0))
    d.set_actor_label("SS_ObjectiveAssault_Director")
    vol = actors.spawn_actor_from_class(unreal.NavMeshBoundsVolume, unreal.Vector(0, 0, 0),
                                        unreal.Rotator(roll=0, pitch=0, yaw=0))
    # Default brush is 200 cm; cover +-360 m x +-120 m x +-100 m.
    vol.set_actor_scale3d(unreal.Vector(360.0, 120.0, 100.0))
    vol.set_actor_label("SS_MAP_RedGum_NavBounds")

    ws = world.get_world_settings()
    ok = unreal.SSObjectivesEditorLibrary.set_property_from_text(ws, "DefaultGameplayExperience", EXP_CLASS)
    step("world_experience", ok and "B_SS_ObjectiveAssault" in str(ws.get_editor_property("default_gameplay_experience")))
    step("save_map", unreal.EditorLoadingAndSavingUtils.save_map(world, MAP), MAP)


try:
    main()
    report["ok"] = all(s["ok"] for s in report["steps"])
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[RedGum] ok={}".format(report["ok"]))
