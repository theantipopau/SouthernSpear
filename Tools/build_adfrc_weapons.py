"""Rebuild every ADFRC-sourced weapon mesh (Art/Weapons/<NAME>/ADFRC/SM_<NAME>.fbx + manifest.json) from its
Arma MLOD blend, with its optic, through Tools/Blender/adfrc_weapon.py. Replaces the in-place optic patching of
Tools/Blender/fix_weapon_optics.py (which edited the exported FBX and compounded on every run).

    python Tools/build_adfrc_weapons.py [NAME ...]        (then Tools/Unreal/setup_weapons.py)

Blender: $BLENDER or the default install path.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLENDER = os.environ.get("BLENDER", r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
B = os.path.join(ROOT, "Art", "ADFRC_BLEND")
OPTICS = os.path.join(B, "adfrc_optics")

# Verified optic centres (m along the weapon from the trigger), where the rules do not fit: the EF88's optic proxy
# sits at the front of the upper; the Spectr belongs mid-rail (the Session 041 placement, checked in game).
OPTIC_X = {"A88": 0.01, "A88G": 0.01}

# W2: each weapon's ADFRC handAnim pose (Docs/WEAPON_SOURCE_DATA.md) -> SOCKET_LeftHandGrip / RightHandGrip.
# The A9 has none (pistols carry no handAnim in the pack). EF88_Vg_static supplies position only; the A88
# mesh has no vertical grip, so the hold below is the plain handguard - "Vg" names the clip, not the gun.
GRIP_CLIPS = {"A88": "EF88_Vg_static", "A88G": "AUG_GL", "A4": "ar15_8in_cgrip_static",
              "A416": "hk416_cgrip_static", "A25": "ar15_10in_cgrip_static", "A89": "Minimi_Standard"}

# W2b: the hold the left hand takes on each weapon, recorded in manifest.json -> "hold" as a record of
# what the game's own frame should come out as (FSSHandIK::BuildGripHold builds it at run time from
# the socket positions, because the FBX export transposes an empty's rotation; the angle itself is read
# from Config/DefaultGame.ini's GripPalmTiltDeg). A profile name from adfrc_grip.HOLD_PROFILES,
# optionally with per-axis overrides of the form ("tilt", base, towards, degrees) or a plain
# (forward, right, up) triple. Data, not code.
#
# Only the A88 is authored. Its mesh was measured (Session 073): no geometry below the bore line
# beyond 9.1 cm ahead of the trigger, so the hand goes under the handguard, and the handguard runs
# from +9 cm to the front sight. The others keep their bare socket until someone measures their mesh
# the same way - a hold guessed from the weapon's real-world type is exactly the borrow this replaced.
GRIP_HOLDS = {"A88": "plain_handguard"}

# name -> (source MLOD blend, optic blend or None). Optics as the ADF fits them: Spectr on the EF88 family,
# TA31 ACOG on the M4 / HK416 types, TA648 on the marksman rifle, C79 (ELCAN) on the F89.
WEAPONS = {
    "A88": ("adfrc_ef88/ADFRC_EF88_MLOD.blend", "ADFRC_Spectr_RAR_MLOD.blend"),
    "A88G": ("adfrc_ef88/ADFRC_EF88_SL40_MLOD.blend", "ADFRC_Spectr_RAR_MLOD.blend"),
    "A4": ("adfrc_m4a5/adfrc_m4A5_NOFS_MLOD.blend", "ADFRC_TA31_BLK_MLOD.blend"),
    "A416": ("adfrc_hk416/adfrc_HK416_MLOD.blend", "ADFRC_TA31_BLK_MLOD.blend"),
    "A25": ("adfrc_SR25/adfrc_SR25_MLOD.blend", "ADFRC_TA648_MLOD.blend"),
    "A89": ("adfrc_minimi/ADFRC_F89_Minimi_MLOD.blend", "ADFRC_C79_MLOD.blend"),
    "A9": ("adfrc_g19/G19_MLOD.blend", None),
}


def main(names):
    failed = []
    for name in names or WEAPONS:
        src, optic = WEAPONS[name]
        args = [BLENDER, "-b", "--factory-startup", "--python", os.path.join(ROOT, "Tools", "Blender", "adfrc_weapon.py"),
                "--", os.path.join(B, src), name] + ([os.path.join(OPTICS, optic)] if optic else [])
        env = dict(os.environ)
        if name in OPTIC_X:
            env["SS_OPTIC_X"] = str(OPTIC_X[name])
        if name in GRIP_CLIPS:
            env["SS_GRIP_CLIP"] = GRIP_CLIPS[name]
        if name in GRIP_HOLDS:
            env["SS_GRIP_HOLD"] = json.dumps(GRIP_HOLDS[name])
        run = subprocess.run(args, capture_output=True, text=True, errors="replace", env=env)
        line = next((l for l in run.stdout.splitlines() if l.startswith("[ADFRC weapon]")), None)
        grip = next((l for l in run.stdout.splitlines() if l.startswith("[ADFRC grip]")), None)
        hold = next((l for l in run.stdout.splitlines() if l.startswith("[ADFRC hold]")), None)
        print(name, "OK" if line else "FAILED", line or run.stdout[-600:] + run.stderr[-600:])
        if grip:
            print("   ", grip)
        if hold:
            print("   ", hold)
        if not line:
            failed.append(name)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
