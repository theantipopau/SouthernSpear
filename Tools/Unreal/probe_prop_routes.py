"""Find the routes that actually work, by testing each one across a reload.

Route 1 (materials). Neither writing into the array returned by
get_editor_property("static_materials") nor assigning it back via
set_editor_property changed the asset. Candidates left: the static mesh editor
subsystem, and - more robustly - a per-instance override on the placed
component, which is what actually decides what renders.

Route 2 (particles). Actor has no add_instance_component in 5.8 and
ActorComponent has no register_component, so a runtime-added component is never
owned by the actor and never serialises. Both classes expose call_method, which
is the documented way to reach a non-reflected C++ method from Python; that is
the last route worth testing before falling back to a Blueprint.

Every candidate is built into a scratch level, saved, closed and reopened, and
only what survives that round trip counts.

Writes JSON; print() and unreal.log() do not reach the commandlet log.
"""
import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SCRATCH = "/Game/Maps/_Scratch_Routes"
REPORT = os.path.join(PROJECT_DIR, "Build", "probe_prop_routes.json")

MESH = "/Game/Art/Environment/Ravenshoe/Props/SS_Raven_wreck_car.SS_Raven_wreck_car"
MAT = "/Game/Art/Environment/Ravenshoe/Materials/MI_SS_Raven_Wreck"
PS = "/Game/Realistic_Starter_VFX_Pack_Vol2/Particles/Fire/P_Fire_Small.P_Fire_Small"

out = {"material_routes": {}, "component_routes": {}, "capabilities": {}}


def capabilities():
    out["capabilities"]["Actor_has_call_method"] = hasattr(unreal.Actor, "call_method")
    out["capabilities"]["Component_has_call_method"] = hasattr(
        unreal.ParticleSystemComponent, "call_method")
    out["capabilities"]["StaticMeshEditorSubsystem"] = hasattr(
        unreal, "StaticMeshEditorSubsystem")
    out["capabilities"]["EditorStaticMeshLibrary"] = hasattr(
        unreal, "EditorStaticMeshLibrary")
    for name in dir(unreal):
        if "StaticMesh" in name and ("Subsystem" in name or "Library" in name):
            out["capabilities"].setdefault("staticmesh_helpers", []).append(name)
    smc = unreal.StaticMeshComponent()
    out["capabilities"]["StaticMeshComponent_set_material"] = hasattr(smc, "set_material")
    out["capabilities"]["StaticMeshComponent_get_num_materials"] = hasattr(
        smc, "get_num_materials")
    if hasattr(unreal, "StaticMeshEditorSubsystem"):
        sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        methods = [m for m in dir(sub) if "material" in m.lower()]
        out["capabilities"]["smes_material_methods"] = methods
    if hasattr(unreal, "EditorStaticMeshLibrary"):
        out["capabilities"]["esml_material_methods"] = [
            m for m in dir(unreal.EditorStaticMeshLibrary) if "material" in m.lower()]


def material_routes():
    """Try every way of putting MI_SS_Raven_Wreck on the wreck mesh."""
    mesh = unreal.load_asset(MESH)
    mat = unreal.load_asset(MAT)

    # Route A: the static mesh editor subsystem.
    if hasattr(unreal, "StaticMeshEditorSubsystem"):
        sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        try:
            sub.set_material(mesh, 0, mat)
            sub.set_material(mesh, 1, mat)
            out["material_routes"]["StaticMeshEditorSubsystem.set_material"] = "called"
        except Exception as exc:  # noqa: BLE001
            out["material_routes"]["StaticMeshEditorSubsystem.set_material"] = \
                "raised: {}".format(str(exc)[:110])
    else:
        out["material_routes"]["StaticMeshEditorSubsystem.set_material"] = "no subsystem"

    # Route B: the legacy editor library.
    if hasattr(unreal, "EditorStaticMeshLibrary"):
        try:
            unreal.EditorStaticMeshLibrary.set_material(mesh, 0, mat)
            out["material_routes"]["EditorStaticMeshLibrary.set_material"] = "called"
        except Exception as exc:  # noqa: BLE001
            out["material_routes"]["EditorStaticMeshLibrary.set_material"] = \
                "raised: {}".format(str(exc)[:110])
    else:
        out["material_routes"]["EditorStaticMeshLibrary.set_material"] = "no library"

    try:
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    except Exception:  # noqa: BLE001
        pass

    got = []
    try:
        for s in mesh.get_editor_property("static_materials"):
            mi = s.get_editor_property("material_interface")
            got.append(mi.get_name() if mi else None)
    except Exception as exc:  # noqa: BLE001
        got = ["<err {}>".format(str(exc)[:60])]
    out["material_routes"]["asset_slots_after"] = got
    out["material_routes"]["asset_worked"] = bool(got) and all(
        g and g.startswith("MI_SS_Raven_") for g in got)


def component_routes():
    """Spawn an actor per candidate route, into the scratch level."""
    subs = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    subs.new_level(SCRATCH, is_partitioned_world=False)
    unreal.EditorLoadingAndSavingUtils.load_map(SCRATCH)
    ps = unreal.load_asset(PS)

    for route in ("call_method AddInstanceComponent+RegisterComponent",
                  "call_method AddInstanceComponent only",
                  "new_object with actor as outer, no add"):
        actor = unreal.get_editor_subsystem(
            unreal.EditorActorSubsystem).spawn_actor_from_class(
                unreal.Actor, unreal.Vector(0, 0, 0), unreal.Rotator())
        if not actor:
            out["component_routes"][route] = "spawn failed"
            continue
        comp = unreal.new_object(unreal.ParticleSystemComponent, outer=actor, name="FX")
        comp.set_editor_property("template", ps)
        note = []
        if route.startswith("call_method AddInstanceComponent+RegisterComponent"):
            for m in ("AddInstanceComponent", "RegisterComponent"):
                try:
                    comp.call_method(m) if m == "RegisterComponent" else None
                except Exception as exc:  # noqa: BLE001
                    note.append("comp.{}: {}".format(m, str(exc)[:60]))
            try:
                actor.call_method("AddInstanceComponent", (comp,))
                note.append("actor.AddInstanceComponent ok")
            except Exception as exc:  # noqa: BLE001
                note.append("actor.AddInstanceComponent: {}".format(str(exc)[:70]))
            try:
                comp.call_method("RegisterComponent")
                note.append("comp.RegisterComponent ok")
            except Exception as exc:  # noqa: BLE001
                note.append("comp.RegisterComponent: {}".format(str(exc)[:70]))
        elif route.startswith("call_method AddInstanceComponent only"):
            try:
                actor.call_method("AddInstanceComponent", (comp,))
                note.append("actor.AddInstanceComponent ok")
            except Exception as exc:  # noqa: BLE001
                note.append("actor.AddInstanceComponent: {}".format(str(exc)[:70]))
        else:
            note.append("outer set only")
        actor.set_actor_label("SCR_" + str(abs(hash(route)) % 10000))
        out["component_routes"][actor.get_actor_label()] = {
            "route": route, "notes": note}

    out["component_routes"]["scratch_saved"] = bool(
        unreal.EditorLoadingAndSavingUtils.save_current_level())


def read_back():
    unreal.EditorLoadingAndSavingUtils.load_map(SCRATCH)
    found = {}
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        lbl = a.get_actor_label()
        if not lbl.startswith("SCR_"):
            continue
        comps = a.get_components_by_class(unreal.ParticleSystemComponent)
        tpl = None
        for c in comps:
            try:
                tpl = c.get_editor_property("template")
            except Exception:  # noqa: BLE001
                pass
            if tpl is not None:
                break
        found[lbl] = {"components": len(comps),
                      "template": str(tpl.get_path_name()) if tpl else None}
    out["component_routes"]["after_reload"] = found
    out["component_routes"]["persisted"] = sorted(
        k for k, v in found.items() if v["template"])


try:
    capabilities()
    material_routes()
    component_routes()
    read_back()
except Exception:  # noqa: BLE001
    out["errors"] = traceback.format_exc()[-2000:]

os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, default=str)
