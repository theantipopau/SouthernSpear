"""What is the particle-system actor actually called in 5.8's Python API?

unreal.ParticleSystemActor raises a bare TypeError whose message is truncated
to the class name, which tells you nothing. Every candidate is probed and the
result recorded, along with the property names a Cascade system needs.

Writes JSON; print() and unreal.log() do not reach the commandlet log.
"""
import json
import os

import unreal

CANDIDATES = ["ParticleSystemActor", "ParticleSystem", "ParticleSystemComponent",
              "Emitter", "NiagaraSystem", "NiagaraActor", "NiagaraComponent",
              "AudioVolume"]

out = {"classes": {}, "particle_system_props": {}, "component_props": {}}

for name in CANDIDATES:
    rec = {"exists": hasattr(unreal, name)}
    if rec["exists"]:
        cls = getattr(unreal, name)
        rec["type"] = str(cls)
        for prop in ("template", "particle_system_component", "asset",
                     "system", "asset_user_data", "auto_activate"):
            try:
                inst = cls()
                rec[prop] = "set ok"
            except Exception as exc:  # noqa: BLE001
                rec[prop] = "err: {}".format(str(exc)[:70]
                                            if "not a property" not in str(exc).lower()
                                            else "no such property")
    out["classes"][name] = rec

# What a loaded Cascade system exposes, and what a component needs set on it.
ps = unreal.load_asset(
    "/Game/Realistic_Starter_VFX_Pack_Vol2/Particles/Fire/P_Fire_Big.P_Fire_Big")
out["particle_system_props"]["loaded"] = ps is not None
if ps is not None:
    for prop in ("template", "emitters", "lODDistances", "bAllowRespawn"):
        try:
            out["particle_system_props"][prop] = str(getattr(ps, prop))[:80]
        except Exception as exc:  # noqa: BLE001
            out["particle_system_props"][prop] = "err: {}".format(str(exc)[:60])

if hasattr(unreal, "ParticleSystemComponent"):
    try:
        comp = unreal.ParticleSystemComponent()
        out["component_props"]["constructible"] = True
        for prop in ("template", "auto_activate", "auto_destroy"):
            try:
                comp.set_editor_property(prop, None)
                out["component_props"][prop] = "set ok"
            except Exception as exc:  # noqa: BLE001
                out["component_props"][prop] = "err: {}".format(str(exc)[:70])
    except Exception as exc:  # noqa: BLE001
        out["component_props"]["constructible"] = "no: {}".format(str(exc)[:90])

# What the editor's spawnable-class list thinks exists, as a cross-check.
try:
    out["spawnable_particle_actors"] = [
        c for c in unreal.EditorLevelLibrary.get_all_level_actors()
        if "Particle" in c.get_class().get_name()
    ][:3]
except Exception:  # noqa: BLE001
    pass

path_out = os.path.join(
    unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()),
    "Build", "probe_particle_actor.json")
os.makedirs(os.path.dirname(path_out), exist_ok=True)
with open(path_out, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, default=str)
