import json, os, traceback
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()),
                 "Build", "probe_fog_props.json")
out = {"fog": {}, "sun": {}}
try:
    unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/L_Ravenshoe_01")
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    fog = sun = None
    for a in sub.get_all_level_actors():
        if a.get_actor_label().startswith("SS_Raven_Light_"):
            if isinstance(a, unreal.ExponentialHeightFog): fog = a
            if isinstance(a, unreal.DirectionalLight): sun = a
    if fog:
        c = fog.component
        for name, val in (("start_distance", 14000.0), ("fog_density", 0.055),
                          ("fog_max_opacity", 0.82), ("fog_height_falloff", 0.02),
                          ("fog_height_offset", -1800.0), ("fog_height_density", 0.04),
                          ("fog_max_height", 6000.0), ("fog_cutoff_distance", 60000.0),
                          ("start_density", 0.0), ("volumetric_fog", False)):
            try:
                c.set_editor_property(name, val)
                out["fog"][name] = "OK -> %r" % (c.get_editor_property(name),)
            except Exception as e:
                out["fog"][name] = "NO: " + str(e).split("\n")[0][:80]
    if sun:
        c = sun.light_component
        for name, val in (("intensity", 9.0),
                          ("light_color", unreal.Color(1.0, 0.94, 0.84)),
                          ("light_color", unreal.LinearColor(1.0, 0.94, 0.84))):
            key = name + ("(Color)" if val.__class__.__name__ == "Color"
                          else "(LinearColor)" if "Linear" in val.__class__.__name__ else "")
            try:
                c.set_editor_property(name, val)
                out["sun"][key] = "OK -> %r" % (c.get_editor_property(name),)
            except Exception as e:
                out["sun"][key] = "NO: " + str(e).split("\n")[0][:80]
except Exception:
    out["err"] = traceback.format_exc()
json.dump(out, open(P, "w"), indent=1, default=str)
