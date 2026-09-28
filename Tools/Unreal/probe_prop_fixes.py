"""Two things the audit caught that the dressing pass reported as done.

1. Material slots read back as None. get_editor_property("static_materials")
   returns COPIES of the slot array; writing into them changes the copies and
   the asset. The array has to be assigned back with set_editor_property.

2. Particle components do not survive a save. They are created at runtime and
   never registered, because ActorComponent.register_component() is not exposed
   to Python, so the serialised actor has no component at all.

Both are tested here against a scratch map that is saved, closed and reopened,
because "it worked in this session" is exactly the claim that is in doubt.

Writes JSON; print() and unreal.log() do not reach the commandlet log.
"""
import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SCRATCH = "/Game/Maps/_Scratch_ParticleAndMaterial"
REPORT = os.path.join(PROJECT_DIR, "Build", "probe_prop_fixes.json")

MESH = "/Game/Art/Environment/Ravenshoe/Props/SS_Raven_wreck_car.SS_Raven_wreck_car"
MAT = "/Game/Art/Environment/Ravenshoe/Materials/MI_SS_Raven_Wreck"
PS = "/Game/Realistic_Starter_VFX_Pack_Vol2/Particles/Fire/P_Fire_Small.P_Fire_Small"

out = {"material": {}, "component": {}, "methods": {}}


def comp_methods():
    """What can we actually call on a ParticleSystemComponent from Python?"""
    c = unreal.ParticleSystemComponent()
    names = [m for m in dir(c) if not m.startswith("_")]
    interesting = [m for m in names if any(
        k in m.lower() for k in ("register", "create", "attach", "destroy",
                                 "activate", "world", "owner"))]
    out["methods"]["interesting"] = interesting
    out["methods"]["has_register_component"] = hasattr(c, "register_component")
    out["methods"]["actor_methods"] = [
        m for m in dir(unreal.Actor) if any(
            k in m.lower() for k in ("register", "rerun", "component",
                                     "recreate", "finish"))
    ]
    out["methods"]["component_methods"] = [
        m for m in dir(c) if not m.startswith("_")
    ][:80]


def fix_materials():
    """Assign the slot array back, which is the part the old pass missed."""
    mesh = unreal.load_asset(MESH)
    mat = unreal.load_asset(MAT)
    if mesh is None or mat is None:
        out["material"]["error"] = "missing asset mesh={} mat={}".format(
            mesh is not None, mat is not None)
        return
    before = []
    try:
        for s in mesh.get_editor_property("static_materials"):
            mi = s.get_editor_property("material_interface")
            before.append(mi.get_name() if mi else None)
    except Exception as exc:  # noqa: BLE001
        out["material"]["read_error"] = str(exc)[:120]
    out["material"]["before"] = before

    try:
        slots = mesh.get_editor_property("static_materials")
        for s in slots:
            s.set_editor_property("material_interface", mat)
        # THE MISSING LINE. Without this the write lands on local copies.
        mesh.set_editor_property("static_materials", slots)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        out["material"]["assigned"] = True
    except Exception:  # noqa: BLE001
        out["material"]["assign_error"] = traceback.format_exc()[-500:]

    after = []
    try:
        for s in mesh.get_editor_property("static_materials"):
            mi = s.get_editor_property("material_interface")
            after.append(mi.get_name() if mi else None)
    except Exception as exc:  # noqa: BLE001
        after = ["<err {}>".format(str(exc)[:60])]
    out["material"]["after"] = after
    out["material"]["worked"] = bool(after) and all(a == "MI_SS_Raven_Wreck" for a in after)


def try_component_route(name, fn):
    try:
        fn()
        out["component"][name] = "ok"
        return True
    except Exception as exc:  # noqa: BLE001
        out["component"][name] = "raised: {}".format(str(exc)[:120])
        return False


def build_scratch():
    """Build the scratch level with every candidate registration route."""
    subs = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    subs.new_level(SCRATCH, is_partitioned_world=False)
    world = unreal.EditorLoadingAndSavingUtils.load_map(SCRATCH)

    ps = unreal.load_asset(PS)
    # Route A: new_object + add_instance_component, then rerun construction
    # scripts - that is what the editor itself does after adding a component in
    # the details panel.
    for route in ("new_object+add_instance+rerun",
                  "new_object+add_instance+on_component_created",
                  "add_component_by_class"):
        loc = unreal.Vector(0, 0, 0)
        actor = unreal.get_editor_subsystem(
            unreal.EditorActorSubsystem).spawn_actor_from_class(
                unreal.Actor, loc, unreal.Rotator())
        if not actor:
            out["component"][route] = "spawn failed"
            continue
        comp = None
        if route == "add_component_by_class":
            try:
                comp = actor.add_component_by_class(unreal.ParticleSystemComponent)
            except Exception as exc:  # noqa: BLE001
                out["component"][route] = "add_component_by_class: {}".format(
                    str(exc)[:100])
        else:
            comp = unreal.new_object(unreal.ParticleSystemComponent, outer=actor,
                                     name="FX")
            comp.set_editor_property("template", ps)
            actor.add_instance_component(comp)
            if route.endswith("on_component_created"):
                try:
                    comp.on_component_created()
                except Exception:  # noqa: BLE001
                    pass
            else:
                try:
                    actor.rerun_construction_scripts()
                except Exception as exc:  # noqa: BLE001
                    out["component"][route + " (rerun)"] = str(exc)[:100]
        if comp is not None:
            comp.set_editor_property("template", ps)
        actor.set_actor_label("SCRATCH_" + route.replace("+", "_"))
        out["component"][route] = "built"

    saved = bool(unreal.EditorLoadingAndSavingUtils.save_current_level())
    out["component"]["scratch_saved"] = saved
    out["component"]["scratch_path"] = SCRATCH


def read_back():
    """Reopen the scratch level and see which routes actually persisted."""
    unreal.EditorLoadingAndSavingUtils.load_map(SCRATCH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    found = {}
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        lbl = a.get_actor_label()
        if not lbl.startswith("SCRATCH_"):
            continue
        comps = a.get_components_by_class(unreal.ParticleSystemComponent)
        tpl = None
        if comps:
            for c in comps:
                try:
                    tpl = c.get_editor_property("template")
                except Exception:  # noqa: BLE001
                    pass
                if tpl is not None:
                    break
        found[lbl] = str(tpl.get_path_name()) if tpl else None
    out["component"]["after_reload"] = found
    out["component"]["persisted"] = sorted(k for k, v in found.items() if v)


try:
    comp_methods()
    fix_materials()
    build_scratch()
    read_back()
except Exception:  # noqa: BLE001
    out["errors"] = traceback.format_exc()[-2000:]

os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, default=str)
