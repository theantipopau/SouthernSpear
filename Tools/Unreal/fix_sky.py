"""Maps built from Fab demo levels keep the pack's sky-sphere Blueprint
(BP_Sky_*) beside the SkyAtmosphere the lighting pass adds; in game the sphere
drew a dark dome from about 45 degrees up (producer: "can't aim upwards",
"no sky box"). Maps without a SkyAtmosphere get one (plus volumetric clouds;
the existing sun drives it, the sky light captures it in real time); then
the sphere is hidden in game.
Report: Build/sky_fix_report.json."""
import json
import unreal

MAPS = ["/Game/Maps/L_RedGum_01", "/Game/Maps/L_DryRiver_01", "/Game/Maps/L_Saltbush_01", "/Game/Maps/L_SelatCanal_01"]
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
out = {}
for m in MAPS:
    if not les.load_level(m):
        continue
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    has_atmos = any(isinstance(a, unreal.SkyAtmosphere) for a in actors)
    spheres = [a for a in actors if a.get_class().get_name().lower().startswith("bp_sky")
               or any(c.get_editor_property("static_mesh") and "skysphere" in c.get_editor_property("static_mesh").get_name().lower()
                      for c in a.get_components_by_class(unreal.StaticMeshComponent))]
    hidden = []
    added = []
    # The demo's painted horizon ring (SM_Horizon_*) is a bowl whose inside
    # showed as the dome from our spawns; the atmosphere and terrain replace it.
    for a in actors:
        if any(c.get_editor_property("static_mesh") and c.get_editor_property("static_mesh").get_name().lower().startswith("sm_horizon")
               for c in a.get_components_by_class(unreal.StaticMeshComponent)) and not a.is_hidden_ed():
            a.set_actor_hidden_in_game(True)
            hidden.append(a.get_actor_label())
    if spheres and not has_atmos:
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        for cls, label in ((unreal.SkyAtmosphere, "SS_SkyAtmosphere"), (unreal.VolumetricCloud, "SS_VolumetricCloud")):
            actor = eas.spawn_actor_from_class(cls, unreal.Vector(0, 0, 0))
            actor.set_actor_label(label)
            added.append(label)
        for a in actors:
            if isinstance(a, unreal.DirectionalLight):
                a.light_component.set_editor_property("atmosphere_sun_light", True)
            if isinstance(a, unreal.SkyLight):
                a.light_component.set_editor_property("real_time_capture", True)
                a.light_component.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
        has_atmos = True
    if has_atmos:
        for a in spheres:
            a.set_actor_hidden_in_game(True)
            hidden.append(a.get_actor_label())
        if hidden or added:
            les.save_current_level()
    out[m] = {"sky_atmosphere": has_atmos, "spheres": [a.get_actor_label() for a in spheres], "hidden": hidden, "added": added}
json.dump(out, open("E:/SouthernSpear/Build/sky_fix_report.json", "w"), indent=1)
unreal.log("SS_SKYFIX " + json.dumps(out))
