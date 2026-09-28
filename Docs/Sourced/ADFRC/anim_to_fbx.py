"""Build Blender armatures from the reconstructed ADFRC rigs and export FBX.

Unreal cannot import the RTM JSON, so this turns each rig into a real armature
and each clip into an animated FBX:

  Animations_UE/<rig>/<rig>_skeleton.fbx   armature only (reference skeleton)
  Animations_UE/<rig>/<clip>.fbx          armature + one baked action

Rig and clip data come from Animations/Rig/*.json (see rtm_rigs.py), already
normalised to parent-relative locals, which is exactly what Blender pose bones
and UE animation tracks store.

Run:
  blender --background --python anim_to_fbx.py -- <anim_root> <dst_root> <listfile>
"""
import json
import os
import sys
import time
import traceback

import bpy
from mathutils import Matrix, Quaternion, Vector

ANIM_ROOT = None
DST_ROOT = None
MIN_TAIL = 0.01


def clear_scene():
    """Empty the scene without read_factory_settings (unloads extensions)."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    for blocks in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials,
                   bpy.data.actions, bpy.data.images, bpy.data.node_groups):
        for d in list(blocks):
            if d.users == 0:
                blocks.remove(d)


def build_armature(rig):
    """Create an armature whose rest pose matches the rig's rest world data."""
    names = rig["bones"]
    parents = rig["parents"]
    rest_w = [Vector(p) for p in rig["rest_world"]]
    rest_r = [Matrix((
        (m[0], m[1], m[2], 0.0),
        (m[3], m[4], m[5], 0.0),
        (m[6], m[7], m[8], 0.0),
        (0.0, 0.0, 0.0, 1.0))) for m in rig["rest_rot"]]

    arm_data = bpy.data.armatures.new(rig["rig"])
    obj = bpy.data.objects.new(rig["rig"], arm_data)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    # Bones must be created parent-first.
    made = [False] * len(names)
    remaining = set(range(len(names)))
    while remaining:
        progressed = False
        for i in sorted(remaining):
            p = parents[i]
            if p is not None and not made[p]:
                continue
            head = rest_w[p] if p is not None else rest_w[i]
            tail = rest_w[i]
            direction = tail - head
            if direction.length < MIN_TAIL:
                # Co-located attachment: hang a stub off the bone's own axis.
                axis = (rest_r[i].to_3x3() @ Vector((0.0, 0.0, 1.0)))
                if axis.length < 1e-6:
                    axis = Vector((0.0, 0.0, 1.0))
                direction = axis.normalized() * MIN_TAIL
                tail = head + direction
            eb = arm_data.edit_bones.new(names[i])
            eb.head = head
            eb.tail = tail
            eb.roll = 0.0
            eb.align_roll(rest_r[i].to_3x3() @ Vector((0.0, 0.0, 1.0)))
            if p is not None:
                eb.parent = arm_data.edit_bones[names[p]]
                eb.use_connect = False
            made[i] = True
            remaining.discard(i)
            progressed = True
            if progressed and len(remaining) < len(names):
                continue
        if not progressed:                      # cycle guard
            for i in sorted(remaining):
                eb = arm_data.edit_bones.new(names[i])
                eb.head = rest_w[i]
                eb.tail = rest_w[i] + Vector((0.0, 0.0, MIN_TAIL))
            break

    bpy.ops.object.mode_set(mode="POSE")
    for pb in obj.pose.bones:
        pb.rotation_mode = "QUATERNION"
    bpy.ops.object.mode_set(mode="OBJECT")
    return obj


def attach_action(obj, action):
    """Assign an action, handling Blender 4.4+'s layered/slotted actions.

    In 4.4+ an Action owns *slots* and keyframes only land in a slot that
    `animation_data.action_slot` points at.  Skipping this silently produces
    armatures with no animation at all - the FBX exports, just empty.
    """
    obj.animation_data_create()
    obj.animation_data.action = action
    if hasattr(action, "slots") and hasattr(obj.animation_data, "action_slot"):
        if obj.animation_data.action_slot is None:
            try:
                obj.animation_data.action_slot = action.slots.new("OBJECT", "Object")
            except Exception:  # noqa: BLE001
                pass
    return action


def bake_clip(obj, clip, scene_fps, phase_start, phase_end):
    """Create an action holding the clip, one keyframe per source frame."""
    action = attach_action(obj, bpy.data.actions.new(clip["clip"]))

    frames = clip["frames"]
    if not frames:
        return action, 0

    # Map the RTM phase range onto whole video frames.
    span = phase_end - phase_start
    if span <= 0:
        span = max(len(frames) - 1, 1)
    for idx, pose in enumerate(frames):
        t = idx / max(len(frames) - 1, 1)
        frame_no = phase_start + t * span
        frame_no *= scene_fps
        for i, pb in enumerate(obj.pose.bones):
            if i >= len(pose):
                break
            loc = pose[i]["p"]
            quat = pose[i]["q"]
            pb.location = (loc[0], loc[1], loc[2])
            pb.rotation_quaternion = (quat[0], quat[1], quat[2], quat[3])
            pb.keyframe_insert("location", frame=frame_no)
            pb.keyframe_insert("rotation_quaternion", frame=frame_no)

    # Trim to the clip's own range so each FBX carries a tight animation.
    return action, len(frames)


def _fcurves(action):
    """Version-tolerant fcurve access (4.4+ moved these under layers)."""
    if hasattr(action, "fcurves") and len(getattr(action, "fcurves", [])):
        return list(action.fcurves)
    out = []
    try:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    out.extend(bag.fcurves)
    except Exception:  # noqa: BLE001
        pass
    return out


def set_interpolation(action, mode="LINEAR"):
    n = 0
    for fc in _fcurves(action):
        for kp in fc.keyframe_points:
            kp.interpolation = mode
            n += 1
    return n


def export_fbx(obj, path, only_action=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = os.path.splitext(path)[0] + ".part.fbx"
    # bake_anim=True is mandatory: with it off the FBX exporter writes the
    # armature but silently omits the AnimationStack, so the clip arrives in
    # Unreal as a static pose.
    kwargs = dict(
        filepath=tmp,
        use_selection=False,
        object_types={"ARMATURE"},
        add_leaf_bones=False,
        path_mode="COPY",
        use_armature_deform_only=False,
        bake_anim=True,
        bake_anim_use_all_bones=True,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,
        bake_anim_force_startend_keying=True,
    )
    bpy.ops.export_scene.fbx(**kwargs)
    if not os.path.exists(tmp):
        raise RuntimeError("FBX exporter produced no file")
    os.replace(tmp, path)


def load_rig(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    global ANIM_ROOT, DST_ROOT
    args = sys.argv[sys.argv.index("--") + 1:]
    ANIM_ROOT, DST_ROOT, listfile = args[0], args[1], args[2]

    rig_files = [l.strip() for l in open(listfile, encoding="utf-8") if l.strip()]
    log_path = os.path.join(DST_ROOT, "_anim_log.txt")
    os.makedirs(DST_ROOT, exist_ok=True)

    ok = fail = 0
    t0 = time.time()
    with open(log_path, "a", encoding="utf-8") as log:
        for rig_path in rig_files:
            try:
                rig = load_rig(rig_path)
                key = rig["rig"]
                clips = []
                cdir = os.path.join(ANIM_ROOT, "Rig", key)
                for name in sorted(os.listdir(cdir)):
                    if name.endswith(".json"):
                        clips.append(load_rig(os.path.join(cdir, name)))

                # A rig can hold two clips with the same basename (the same
                # animation shipped in both Source/ and Workshop/), and Windows
                # filesystems fold case, so `Mag58` and `mag58` would land on the
                # same file.  Disambiguate case-insensitively and
                # deterministically, so the resume check below finds the same
                # file on a later run.
                seen, jobs = {}, []
                for clip in clips:
                    stem = clip["clip"]
                    base = stem.lower()
                    n = seen.get(base, 0)
                    if n:
                        stem = "%s__%d" % (stem, n)
                    # Count on the *base* key so the suffix keeps advancing:
                    # three copies need "", "__1" and "__2", not "__1" twice.
                    seen[base] = n + 1
                    jobs.append((clip, stem))

                out_dir = os.path.join(DST_ROOT, key)
                skel = os.path.join(out_dir, key + "_skeleton.fbx")
                if not os.path.exists(skel):
                    clear_scene()
                    bpy.context.scene.render.fps = 30
                    obj = build_armature(rig)
                    export_fbx(obj, skel)

                n = 0
                for clip, stem in jobs:
                    dst = os.path.join(out_dir, stem + ".fbx")
                    if os.path.exists(dst) and os.path.getsize(dst) > 0:
                        n += 1
                        continue
                    clear_scene()
                    bpy.context.scene.render.fps = 30
                    obj = build_armature(rig)
                    action, nf = bake_clip(obj, clip, 30.0, 0.0,
                                           (clip.get("phases") or [0.0, 1.0])[-1])
                    nkeys = set_interpolation(action, "LINEAR")
                    export_fbx(obj, dst)
                    if nkeys == 0:
                        raise RuntimeError("clip produced no keyframes")
                    n += 1
                ok += 1
                log.write("OK   %s skeleton+clips=%d\n" % (key, n))
                print("  %-44s clips=%d  %.0fs" % (key, n, time.time() - t0), flush=True)
            except Exception:  # noqa: BLE001
                fail += 1
                log.write("FAIL %s\n%s\n" % (os.path.basename(rig_path),
                                             traceback.format_exc()))
            log.flush()
    print("DONE rigs_ok=%d fail=%d %.0fs" % (ok, fail, time.time() - t0), flush=True)


main()
