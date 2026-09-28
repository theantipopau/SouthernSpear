# Southern Spear - tactical damage model (Session 032).
#
# Lyra: rifle 12 per hit (nine body hits to kill 100 HP), head x1.5, half damage beyond 28 m;
# only the head is a zone. Tactical target (100 HP): head one hit, torso ~3 rifle hits, limbs ~4-5,
# the A25 (7.62) two to the torso; damage flat to 300 m. All in our own assets; Lyra untouched:
#   1. PM_SS_Head / PM_SS_Torso / PM_SS_Limb (PhysicalMaterialWithTags: SS.Zone.*, the head also
#      Gameplay.Zone.WeakSpot for Lyra's headshot hit marker), on Lyra's character surface type;
#   2. ASSCharacter sets the zone material on each of the soldier's physics bodies by bone name at
#      BeginPlay (head/neck, torso = pelvis/spine/clavicles, limbs = the rest), server and clients;
#   3. B_SS_WeaponInstance_<W>: copies of Lyra's rifle / pistol weapon instance with per-zone
#      multipliers and a flat falloff; each ID_SS_<W> uses its own.
# LyraDamageExecution multiplies by every matching tag on the hit surface. Report:
# Build/damage_model_setup.json.

import json
import os
import traceback

import unreal
import sys

# does_asset_exist() misses Game Feature assets in a commandlet; see Tools/Unreal/ss_assets.py.
sys.path.insert(0, os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Tools", "Unreal"))
from ss_assets import asset_exists  # noqa: E402

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "damage_model_setup.json")
PHYS = "/SSExp_ObjectiveAssault/Characters/Physics"
WEAPONS = "/SSExp_ObjectiveAssault/Weapons"
eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.SSObjectivesEditorLibrary
report = {"ok": False, "steps": [], "weapons": {}, "errors": []}

# Base damage per hit comes from Lyra's effects: rifle 12 (GE_Damage_RifleAuto), pistol 18.
# Multiplier = wanted damage / base.  (head, torso, limb) wanted per hit, for 100 HP:
WANTED = {
    "A88": ("rifle", 110, 38, 24), "A88G": ("rifle", 110, 38, 24), "A4": ("rifle", 110, 36, 23),
    "A416": ("rifle", 110, 37, 24), "A89": ("rifle", 110, 36, 23),
    "A25": ("rifle", 150, 60, 36),   # 7.62: two to the torso
    "A9": ("pistol", 110, 30, 20),
}
BASE = {"rifle": (12.0, "/ShooterCore/Weapons/Rifle/B_WeaponInstance_Rifle"),
        "pistol": (18.0, "/ShooterCore/Weapons/Pistol/B_WeaponInstance_Pistol")}
# Flat to 300 m, then 80%.
FALLOFF = "(EditorCurveData=(Keys=((Value=1.000000),(Time=30000.000000,Value=1.000000),(Time=30001.000000,Value=0.800000))))"
ZONES = {
    "Head": ('(GameplayTags=((TagName="SS.Zone.Head"),(TagName="Gameplay.Zone.WeakSpot")))', ("head", "neck")),
    "Torso": ('(GameplayTags=((TagName="SS.Zone.Torso")))', ("pelvis", "spine", "clavicle")),
    "Limb": ('(GameplayTags=((TagName="SS.Zone.Limb")))', ()),
}


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def physical_material(zone, tags_text):
    name = "PM_SS_" + zone
    path = PHYS + "/" + name
    if not asset_exists(path):
        eal.duplicate_asset("/Game/Characters/Heroes/PhysMat_Player_WeakSpot", path)  # keeps class and surface
    pm = unreal.load_asset(path)
    ok = lib.set_property_from_text(pm, "Tags", tags_text)
    eal.save_loaded_asset(pm, False)
    return pm, ok


def main():
    mats = {}
    for zone, (tags, _) in ZONES.items():
        pm, ok = physical_material(zone, tags)
        mats[zone] = pm
        step("pm_" + zone, ok, lib.get_property_as_text(pm, "Tags"))

    for w, (kind, head, torso, limb) in WANTED.items():
        base, src = BASE[kind]
        path = "{0}/{1}/B_SS_WeaponInstance_{1}".format(WEAPONS, w)
        if not asset_exists(path):
            eal.duplicate_asset(src, path)
        bp = unreal.load_asset(path)
        cdo = unreal.get_default_object(bp.generated_class())
        mult = '(((TagName="SS.Zone.Head"), {:.4f}),((TagName="SS.Zone.Torso"), {:.4f}),((TagName="SS.Zone.Limb"), {:.4f}))'.format(
            head / base, torso / base, limb / base)
        ok = lib.set_property_from_text(cdo, "MaterialDamageMultiplier", mult)
        ok = lib.set_property_from_text(cdo, "DistanceDamageFalloff", FALLOFF) and ok
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        saved = eal.save_loaded_asset(bp, False)
        eid = unreal.load_asset("{0}/{1}/WID_SS_{1}".format(WEAPONS, w))  # equipment definition
        ecdo = unreal.get_default_object(eid.generated_class())
        before = lib.get_property_as_text(ecdo, "InstanceType")
        ok = lib.set_property_from_text(ecdo, "InstanceType", '"{}"'.format(bp.generated_class().get_path_name())) and ok
        unreal.BlueprintEditorLibrary.compile_blueprint(eid)
        saved = eal.save_loaded_asset(eid, False) and saved
        report["weapons"][w] = {"multipliers": lib.get_property_as_text(cdo, "MaterialDamageMultiplier"),
                                "instance_before": before, "instance": lib.get_property_as_text(ecdo, "InstanceType"),
                                "hits_to_kill": {"head": -(-100 // head), "torso": -(-100 // torso), "limb": -(-100 // limb)}}
        step("weapon_" + w, ok and saved and "B_SS_WeaponInstance" in report["weapons"][w]["instance"], report["weapons"][w]["instance"])


try:
    main()
    report["ok"] = all(s["ok"] for s in report["steps"])
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[DamageModel] ok={}".format(report["ok"]))
