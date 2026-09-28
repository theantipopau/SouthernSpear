"""
Southern Spear - the left hand's path through a reload, from the ADF Re-Cut reload gestures (W5).

Each frame of a reload clip (e.g. GestureReloadAUG, 165 frames) is posed with the same model as the W2
grip (Tools/Common/adfrc_grip.py): each bone's transform is a rotation about its rest joint, composed down
the hierarchy with `weapon` under Spine1. For every frame this gives the left wrist relative to the right
wrist in the weapon's frame; the right wrist is on the grip throughout a bullpup reload.

The path is written in the weapon's own axes, which the game can rebuild from the mesh's sockets whatever
the import did to the model's axes:
    forward  from the right-hand grip towards the muzzle (RightHandGrip -> Muzzle)
    up       the model's up
    right    the shooter's right
so the target at runtime is RightHandGrip + forward*F + right*R + up*U (cm). `grip` is the same offset for
the static grip pose (SOCKET_LeftHandGrip): the game checks its own right-axis sign against it.

    python Tools/Common/adfrc_reload.py A88 [GestureReloadAUG] [samples]   # -> Build/reload_path_A88.json

Pure Python; tested by Tools/Common/test_adfrc_reload.py.
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adfrc_grip as g  # noqa: E402

ROOT = g.ROOT
# Arma's magazineReloadSwitchPhase for the EF88 family (ADFRC_CONFIG_REGISTRY: 0.48): the fraction of the
# reload at which the old magazine is gone and the new one appears.
SWITCH_PHASE = {"A88": 0.48, "A88G": 0.48}


def weapon_axes(trigger, muzzle):
    """(forward, right, up) unit vectors in the MLOD's space: forward along the barrel's horizontal model
    axis, z up, right = forward x up (Blender is right-handed)."""
    m = g.rest_to_mlod(trigger, muzzle)
    forward = g.mat_vec(m, (0.0, -1.0, 0.0))   # rest forward is -y
    up = (0.0, 0.0, 1.0)
    right = g.cross(forward, up)
    return forward, right, up


def offset_in_axes(rest_offset, trigger, muzzle):
    """A left-minus-right offset in rest space (m) as (forward, right, up) in cm."""
    m = g.rest_to_mlod(trigger, muzzle)
    mlod = g.mat_vec(m, rest_offset)
    forward, right, up = weapon_axes(trigger, muzzle)
    return tuple(round(g.dot(mlod, axis) * 100.0, 2) for axis in (forward, right, up))


def reload_path(stem, trigger, muzzle, samples=33, frames_override=None):
    """{"clip", "frames", "keys": [{"t", "left_cm": [F, R, U]}], "grip_cm", "max_step_cm"} for clip <stem>.
    `frames_override` = (bones, parents, frames) bypasses loading (tests)."""
    bones, parents, frames = frames_override or g.load_clip_frames(stem)
    if len(frames) < 2:
        raise ValueError("clip {} has {} frame(s); a reload needs a path".format(stem, len(frames)))
    offsets = []
    for frame in frames:
        left, right = g.hands_in_weapon_space(bones, parents, frame)
        offsets.append(offset_in_axes(g.sub(left, right), trigger, muzzle))
    samples = max(2, min(samples, len(frames)))
    keys = []
    for k in range(samples):
        position = k * (len(frames) - 1) / (samples - 1)
        i = int(math.floor(position))
        j = min(i + 1, len(frames) - 1)
        f = position - i
        value = tuple(round(offsets[i][a] + (offsets[j][a] - offsets[i][a]) * f, 2) for a in range(3))
        keys.append({"t": round(k / (samples - 1), 4), "left_cm": list(value)})
    steps = [g.norm(g.sub(offsets[i + 1], offsets[i])) for i in range(len(offsets) - 1)]
    return {"clip": stem, "frames": len(frames), "keys": keys, "max_step_cm": round(max(steps), 2),
            "start_cm": list(offsets[0]), "end_cm": list(offsets[-1])}


def grip_offset(grip_clip, trigger, muzzle):
    """The static grip pose's left-minus-right offset, in the same (forward, right, up) cm."""
    bones, parents, frame = g.load_clip(grip_clip)
    left, right = g.hands_in_weapon_space(bones, parents, frame)
    return list(offset_in_axes(g.sub(left, right), trigger, muzzle))


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    weapon = argv[0]
    clip = argv[1] if len(argv) > 1 else "GestureReloadAUG"
    samples = int(argv[2]) if len(argv) > 2 else 33
    with open(os.path.join(ROOT, "Art", "Weapons", weapon, "ADFRC", "manifest.json"), encoding="utf-8") as fh:
        grip = json.load(fh)["grip"]
    trigger, muzzle = grip["trigger_mlod"], grip["muzzle_mlod"]
    result = reload_path(clip, trigger, muzzle, samples)
    result["weapon"] = weapon
    result["switch_phase"] = SWITCH_PHASE.get(weapon)
    result["grip_cm"] = grip_offset(grip["clip"], trigger, muzzle) if grip.get("clip") else None
    if result["grip_cm"]:
        result["start_to_grip_cm"] = round(g.norm(g.sub(result["start_cm"], result["grip_cm"])), 2)
    out = os.path.join(ROOT, "Build", "reload_path_{}.json".format(weapon))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
    print(json.dumps({k: result[k] for k in ("clip", "frames", "max_step_cm", "start_cm", "end_cm", "grip_cm",
                                             "start_to_grip_cm", "switch_phase") if k in result}))
    print("wrote " + out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
