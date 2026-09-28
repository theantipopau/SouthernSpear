"""
Probe: where does Lyra keep each weapon's fire interval? (W1, Docs/WEAPONS_ANIMATION_PLAN.md)

Rate of fire is not a C++ property in Lyra: the fire ability Blueprint decides it. This walks
WID_SS_<weapon> -> AbilitySetsToGrant -> granted abilities, and the item and weapon-instance classes, and
writes every Blueprint-declared property with its value (USSObjectivesEditorLibrary.ListPropertiesAsText,
stopping at the C++ base so only Blueprint variables show). Read-only: loads, never saves.

    "E:/Unreal/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" "E:/SouthernSpear/SouthernSpear.uproject" \
        -run=pythonscript -script="E:/SouthernSpear/Tools/Unreal/probe_weapon_fire.py" -nullrhi -unattended -nosplash

Output: Build/probe_weapon_fire.json. Look for a delay/interval/rate variable on the fire ability; that is
what USSWeaponStatsSubsystem needs to set from RoundsPerMinute.
"""

import json
import os
import traceback

import unreal

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "Build", "probe_weapon_fire.json")
WEAPONS = ["A88", "A89", "A25", "A9"]
BASE = "/SSExp_ObjectiveAssault/Weapons"
lib = unreal.SSObjectivesEditorLibrary


def blueprint_props(obj):
    """Properties declared by the object's Blueprint classes (owner class name ends in _C)."""
    return [line for line in lib.list_properties_as_text(obj, None) if line.split(".", 1)[0].endswith("_C")]


def main():
    report = {"weapons": {}}
    for weapon in WEAPONS:
        row = report["weapons"].setdefault(weapon, {})
        try:
            wid = unreal.load_asset("{0}/{1}/WID_SS_{1}".format(BASE, weapon))
            if not wid:
                row["error"] = "WID_SS_{} not found".format(weapon)
                continue
            cdo = unreal.get_default_object(wid.generated_class())
            row["wid_all"] = list(lib.list_properties_as_text(cdo, None))
            row["abilities"] = {}
            for ability_set in cdo.get_editor_property("ability_sets_to_grant") or []:
                for entry in ability_set.get_editor_property("granted_gameplay_abilities") or []:
                    ability = entry.get_editor_property("ability")
                    if not ability:
                        continue
                    ability_cdo = unreal.get_default_object(ability)
                    row["abilities"][ability.get_name()] = blueprint_props(ability_cdo)
            instance = cdo.get_editor_property("instance_type")
            if instance:
                row["instance_class"] = instance.get_name()
                row["instance_props"] = blueprint_props(unreal.get_default_object(instance))
        except Exception:
            row["exception"] = traceback.format_exc()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as handle:
        json.dump(report, handle, indent=1)
    unreal.log("PROBE wrote {}".format(OUT))


main()
