"""The fire, last attempt: spawn the VFX pack's own particle Blueprint.

There is no Python route in 5.8 that persists a runtime-added component - no
Actor.add_instance_component, no ActorComponent.register_component, no
EditorActorSubsystem.add_actor_component. Every one was tested against a real
save-and-reload and none survived.

What DOES persist is a component property on a placed actor, which is how the
per-instance material override was made to stick. So the question becomes: is
there a Blueprint class in the pack that already HAS a ParticleSystemComponent,
that can be spawned and then have its template set?

Realistic_Starter_VFX_Pack_Vol2/Blueprints/Spawn_Particle is the only
Blueprint in the project whose asset references a ParticleSystemComponent.

Verified by save, close, reopen, read back.

Writes JSON; print() and unreal.log() do not reach the commandlet log.
"""
import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SCRATCH = "/Game/Maps/_Scratch_ParticleBP"
REPORT = os.path.join(PROJECT_DIR, "Build", "probe_particle_bp.json")

BP = "/Game/Realistic_Starter_VFX_Pack_Vol2/Blueprints/Spawn_Particle"
PS = "/Game/Realistic_Starter_VFX_Pack_Vol2/Particles/Fire/P_Fire_Small.P_Fire_Small"

out = {"bp": {}, "build": {}, "after_reload": {}}


def generated_class_of(bp):
    """The Blueprint asset is not spawnable - the GENERATED CLASS is.

    Passing the Blueprint to spawn_actor_from_class fails to nativise
    'actor_class'. Blueprint.generated_class() is the supported accessor;
    EditorAssetLibrary.load_blueprint_class is the fallback.
    """
    for label, fn in (("generated_class", lambda: bp.generated_class()),
                      ("load_blueprint_class",
                       lambda: unreal.EditorAssetLibrary.load_blueprint_class(bp)),
                      ("get_property", lambda: bp.get_editor_property("generated_class"))):
        try:
            c = fn()
            out["bp"].setdefault("candidates", {})[label] = str(c)
            if c is not None:
                out["bp"]["generated_class_via"] = label
                return c
        except Exception as exc:  # noqa: BLE001
            out["bp"].setdefault("candidates", {})[label] = "err {}".format(
                str(exc)[:80])
    return None


def inspect():
    bp = unreal.load_asset(BP)
    if bp is None:
        out["bp"]["loaded"] = False
        return None
    out["bp"]["loaded"] = True
    out["bp"]["class"] = type(bp).__name__
    return generated_class_of(bp)


def build():
    subs = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    subs.new_level(SCRATCH, is_partitioned_world=False)
    unreal.EditorLoadingAndSavingUtils.load_map(SCRATCH)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    ps = unreal.load_asset(PS)

    bp = unreal.load_asset(BP)
    gen = generated_class_of(bp)
    out["build"]["generated_class"] = str(gen)
    if gen is None:
        out["build"]["spawned"] = "no generated class"
        return
    actor = eas.spawn_actor_from_class(
        gen, unreal.Vector(0, 0, 100), unreal.Rotator())
    if not actor:
        out["build"]["spawned"] = "no - spawn_actor_from_class returned None"
        return
    out["build"]["spawned"] = "yes"
    comps = actor.get_components_by_class(unreal.ParticleSystemComponent)
    out["build"]["components_on_instance"] = len(comps)
    if comps:
        tpl = comps[0].get_editor_property("template")
        out["build"]["template_before"] = str(tpl.get_path_name()) if tpl else None
        comps[0].set_editor_property("template", ps)
        t2 = comps[0].get_editor_property("template")
        out["build"]["template_after"] = str(t2.get_path_name()) if t2 else None
    out["build"]["saved"] = bool(unreal.EditorLoadingAndSavingUtils.save_current_level())


def read_back():
    unreal.EditorLoadingAndSavingUtils.load_map(SCRATCH)
    rows = []
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        comps = a.get_components_by_class(unreal.ParticleSystemComponent)
        if not comps:
            continue
        tpl = None
        for c in comps:
            try:
                tpl = c.get_editor_property("template")
            except Exception:  # noqa: BLE001
                pass
            if tpl is not None:
                break
        rows.append({"actor": a.get_actor_label(),
                     "actor_class": a.get_class().get_name(),
                     "components": len(comps),
                     "template": str(tpl.get_path_name()) if tpl else None})
    out["after_reload"]["particle_actors"] = rows
    out["after_reload"]["survived"] = any(r["template"] for r in rows)


try:
    inspect()
    build()
    read_back()
except Exception:  # noqa: BLE001
    out["errors"] = traceback.format_exc()[-2000:]

os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, default=str)
