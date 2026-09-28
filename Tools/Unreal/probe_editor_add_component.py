"""Last two unknowns, both settled across a save-and-reload round trip.

1. EditorActorSubsystem gained add_actor_component / remove_actor_component in
   5.4 precisely because runtime-created components are not owned by the actor
   and do not serialise. If that is the route, the fire persists.

2. A per-instance material override on the placed component
   (StaticMeshComponent.set_material) should persist even though every route to
   writing the mesh ASSET's slots failed. That is the route that decides what
   actually renders, so it is the one that matters.

Both are verified by saving, closing, reopening and reading back - not by
checking anything in the session that wrote them.

Writes JSON; print() and unreal.log() do not reach the commandlet log.
"""
import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SCRATCH = "/Game/Maps/_Scratch_AddComponent"
REPORT = os.path.join(PROJECT_DIR, "Build", "probe_add_component.json")

MESH = "/Game/Art/Environment/Ravenshoe/Props/SS_Raven_wreck_car.SS_Raven_wreck_car"
MAT = "/Game/Art/Environment/Ravenshoe/Materials/MI_SS_Raven_Wreck"
PS = "/Game/Realistic_Starter_VFX_Pack_Vol2/Particles/Fire/P_Fire_Small.P_Fire_Small"

out = {"capabilities": {}, "build": {}, "after_reload": {}}


def capabilities():
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    out["capabilities"]["editor_actor_subsystem_methods"] = [
        m for m in dir(sub) if "component" in m.lower()]
    for name in ("add_actor_component", "remove_actor_component"):
        out["capabilities"][name] = hasattr(sub, name)


def build():
    subs = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    subs.new_level(SCRATCH, is_partitioned_world=False)
    unreal.EditorLoadingAndSavingUtils.load_map(SCRATCH)

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    ps = unreal.load_asset(PS)
    mat = unreal.load_asset(MAT)
    mesh = unreal.load_asset(MESH)

    # -- particle actor, via add_actor_component if it exists
    actor = eas.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 100),
                                       unreal.Rotator())
    if not actor:
        out["build"]["spawn"] = "failed"
    else:
        actor.set_actor_label("SCR_Fire")
        if hasattr(eas, "add_actor_component"):
            try:
                comp = eas.add_actor_component(actor, unreal.ParticleSystemComponent,
                                              "RavenFX", True)
                if comp:
                    comp.set_editor_property("template", ps)
                    out["build"]["fire"] = "component added via subsystem"
                else:
                    out["build"]["fire"] = "add_actor_component returned None"
            except Exception as exc:  # noqa: BLE001
                out["build"]["fire"] = "raised: {}".format(str(exc)[:160])
        else:
            out["build"]["fire"] = "no add_actor_component on the subsystem"

    # -- a StaticMeshActor with a per-instance material override
    sma = eas.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(200, 0, 100), unreal.Rotator())
    if sma:
        sma.set_actor_label("SCR_Wreck")
        comp = sma.static_mesh_component
        try:
            comp.set_static_mesh(mesh)
            n = comp.get_num_materials()
            applied = []
            for i in range(n):
                comp.set_material(i, mat)
                applied.append(i)
            out["build"]["wreck_slots_set"] = "{} of {}".format(len(applied), n)
            readback = []
            for i in range(n):
                m = comp.get_material(i)
                readback.append(m.get_name() if m else None)
            out["build"]["wreck_slots_in_session"] = readback
        except Exception as exc:  # noqa: BLE001
            out["build"]["wreck"] = "raised: {}".format(str(exc)[:160])

    out["build"]["saved"] = bool(unreal.EditorLoadingAndSavingUtils.save_current_level())


def read_back():
    unreal.EditorLoadingAndSavingUtils.load_map(SCRATCH)
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        lbl = a.get_actor_label()
        if lbl == "SCR_Fire":
            comps = a.get_components_by_class(unreal.ParticleSystemComponent)
            tpl = None
            for c in comps:
                try:
                    tpl = c.get_editor_property("template")
                except Exception:  # noqa: BLE001
                    pass
                if tpl is not None:
                    break
            out["after_reload"]["fire"] = {
                "components": len(comps),
                "template": str(tpl.get_path_name()) if tpl else None}
        elif lbl == "SCR_Wreck":
            comp = a.static_mesh_component
            n = comp.get_num_materials()
            mats = []
            for i in range(n):
                m = comp.get_material(i)
                mats.append(m.get_name() if m else None)
            out["after_reload"]["wreck"] = mats


try:
    capabilities()
    build()
    read_back()
except Exception:  # noqa: BLE001
    out["errors"] = traceback.format_exc()[-2000:]

os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, default=str)
