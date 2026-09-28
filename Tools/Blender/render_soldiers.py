"""Studio renders of the player model: 3 ACR in CMECU, MAF in its camo.

The producer directed (2026-09-28) that the website show the two sides as they
appear in the current build, under a recorded risk acceptance covering the
Fab body (L-0016) and the ADFRC-derived gear (L-0021) - the same pattern as the
weapon renders, and not a licence clearance.

What is original here is the camouflage: Art/Characters/Textures/ holds the
CMECU set (3 ACR) and the MAF set, both Class F, script-generated
(Tools/Textures/make_character_textures.py). The body is the UE mannequin the
game's own rig is fitted to, and the gear is the same fitted kit the game uses,
so the render shows the real in-build kit rather than a costume.

    blender --background --factory-startup -P Tools/Blender/render_soldiers.py
"""
import math
import os

import bpy
import mathutils
from mathutils import Vector

ROOT = r"E:\SouthernSpear"
OUT = os.path.join(ROOT, "Docs", "images", "soldiers")
TEX = os.path.join(ROOT, "Art", "Characters", "Textures")
MANNY = os.path.join(ROOT, "Art", "Characters", "ADF", "SKM_Manny_ref.fbx")

RES_X, RES_Y = 1500, 1900
SAMPLES = 140
MARGIN = 1.05

# Per-side exposure trim. The two camo sets differ in inherent value - the
# MAF red-earth is a stop darker than the pale CMECU ground - so a shared
# exposure left the MAF crushing 16% of its surface to black while the 3 ACR sat
# a stop hot. These are matched on the rendered median luminance instead.
SIDES = {
    "3acr": {
        "label": "3 Australian Corps",
        "gear": ["SK_ADF_Uniform_G3.fbx", "SK_ADF_Vest_TBAS.fbx", "SK_ADF_Helmet_OpsCore.fbx"],
        "weapon": r"Art\Weapons\A88\ADFRC\SM_A88.fbx",
        # Class F texture sets: the uniform wears the original CMECU, the kit
        # wears the project's gear tan, which is how the game overrides the
        # friendly material slots.
        "camo": "T_SS_CMECU_Camo",
        "gear_tex": "T_SS_Gear_BC",
        "exposure": 0.75,
        "side": -1.0,
    },
    "maf": {
        "label": "MAF opposition",
        "gear": ["SK_MAF_Vest_Peacekeeper.fbx", "SK_MAF_Helmet_PASGT.fbx"],
        "weapon": r"Art\Weapons\A4\ADFRC\SM_A4.fbx",
        "camo": "T_SS_MAF_Camo",
        "gear_tex": "T_SS_GearDark_BC",
        "exposure": 0.80,
        "side": 1.0,
    },
}

# The carry. Two facts drove the design here, both measured rather than assumed:
#
# 1. The mannequin's rig cannot be IK'd. The chain is upperarm -> lowerarm ->
#    hand with the twist bones out of line, so the bones are not contiguous: the
#    upperarm's tail sits 16 cm from the lowerarm's head, while the mesh spans
#    the gap. Rotating the upperarm therefore does not carry the wrist with it,
#    and an IK solve lands the hand ~600 mm from the target. The arms are posed
#    with fixed angles instead.
# 2. Because of (1) the pose cannot be trusted to put the hands anywhere in
#    particular. So the weapon is fitted to the hands afterwards: the grip is
#    placed on the right wrist and the handguard on the left wrist, whichever way
#    the pose turned out to put them. The rifle is on the hands by construction
#    rather than by hope.
#
# Local points on a rifle as exported: the bore runs along +X from the rear of
# the receiver and the pistol grip hangs below the bore a third of the way
# along. GRIP is the web of the hand on the trigger, SUPPORT the handguard.
GRIP_LOCAL = Vector((0.130, 0.000, -0.075))
# The handguard point is chosen so that the grip-to-handguard distance matches
# the distance the solved pose actually puts between the two wrists (0.28 m).
# With it at the far end of the handguard the support hand lands 110 mm short of
# the rifle; matched, it lands on it.
SUPPORT_LOCAL = Vector((0.400, 0.000, -0.020))

# Roll of the weapon about its own bore, so the flat of the receiver faces the
# firer rather than the sky.
# Roll of the weapon about its own bore, so the flat of the receiver faces the
# firer rather than the sky. Zero keeps the minimal-rotation aim already level
# with the weapon's own up axis; the rifle meshes are exported bore-along-+X with
# +Z up, so no extra roll is wanted.
CARRY_ROLL = 0.0

# The two world-space points the hands have to reach for the rifle to sit right,
# and where the solver put them. Build/audit/solve_carry.py searches the four
# arm angles against these and converges to a 1.4 mm residual, which is what
# makes the hands land on the weapon instead of near it.
TARGET_R = Vector((0.010, 0.250, 1.190))   # right hand, on the grip
TARGET_L = Vector((0.155, 0.480, 1.250))   # left hand, on the handguard

ARM_ROT = {
    "upperarm_l": (31.8, 94.6), "upperarm_r": (93.9, 77.2),
    "lowerarm_l": (-38.3, -7.6), "lowerarm_r": (-79.5, -30.8),
}

GEAR_HINTS = ("tacgear", "tbas", "opscore", "pouch", "acc_", "343", "belt", "bison",
              "holster", "safariland", "ifak", "helmet", "g19", "m4_mag", "heli",
              "pistoldouble", "mags", "peacekeeper", "pasgt", "pouch")
CAMO_HINTS = ("crye_g3", "uniform", "shirt", "jeans", "pants", "boonie", "cap", "g3")


def add_area(name, target, offset, size, energy, color):
    data = bpy.data.lights.new(name, type="AREA")
    data.shape = "RECTANGLE"
    data.size, data.size_y = size
    data.energy = energy
    data.color = color
    ob = bpy.data.objects.new(name, data)
    target = Vector(target)
    ob.location = target + Vector(offset)
    ob.rotation_euler = (target - ob.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(ob)
    return ob


def pbr(name, base_stem):
    """The project's texture sets: BC + N + a packed ORM.

    base_stem is the set prefix, e.g. "T_SS_CMECU_Camo"; the files are
    T_SS_CMECU_Camo_BC.png / _N / _ORM. Splitting the prefix off and looking
    for the bare stem found no file at all, so every soldier rendered as
    untextured default grey. A stem that already ends in _BC is accepted too,
    so the call sites can name the colour map directly.
    """
    base_stem = base_stem[:-3] if base_stem.endswith("_BC") else base_stem
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]

    def tex(stem, kind, socket=None):
        path = os.path.join(TEX, stem + ".png")
        if not os.path.isfile(path):
            print("  MISSING TEXTURE", path)
            return None
        node = nt.nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(path)
        node.label = kind
        if socket == "Normal":
            nmap = nt.nodes.new("ShaderNodeNormalMap")
            nmap.inputs["Strength"].default_value = 0.7
            nt.links.new(node.outputs["Color"], nmap.inputs["Color"])
            nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
        elif socket == "ORM":
            sep = nt.nodes.new("ShaderNodeSeparateColor")
            nt.links.new(node.outputs["Color"], sep.inputs["Color"])
            inv = nt.nodes.new("ShaderNodeInvert")
            nt.links.new(sep.outputs["Green"], inv.inputs["Color"])
            nt.links.new(inv.outputs["Color"], bsdf.inputs["Roughness"])
        else:
            nt.links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
        return node

    tex(base_stem + "_BC", "BC", "Base Color")
    tex(base_stem + "_N", "N", "Normal")
    tex(base_stem + "_ORM", "ORM", "ORM")
    return mat


def assign(mesh, camo, gear):
    """Point every slot at the right material, and tile the UVs to a real scale.

    NOTE: tiling these above 1.0 was tried and reverted. The FBX lays UVs 0..1
    over the whole 1.8 m figure, so the camo is coarse, but at 7x (and 16x for
    the fabric) the pattern turns into high-frequency noise at render resolution
    and looks worse than the coarse version, not better. The real fix is UVs
    authored at the right scale in the source meshes, not a global multiplier.
    """
    CAMO_TILE = 1.0   # the FBX lays UVs 0..1 over the whole figure; this is
    GEAR_TILE = 1.0   # the one-tile default the art was authored against
    for i, slot in enumerate(mesh.data.materials):
        name = (slot.name if slot else "").lower()
        low = name.replace("__", "_")
        is_camo = any(h in low for h in CAMO_HINTS)
        if is_camo:
            mesh.data.materials[i] = camo
        elif any(h in low for h in GEAR_HINTS):
            mesh.data.materials[i] = gear
        else:
            mesh.data.materials[i] = gear if "glass" not in low else camo
            is_camo = "glass" not in low
        tile = CAMO_TILE if is_camo else GEAR_TILE
        uvl = mesh.data.uv_layers.active
        if uvl is None:
            continue
        for item in uvl.data:
            item.uv[0] *= tile
            item.uv[1] *= tile


def _enter_pose(armature):
    """Put Blender into pose mode on `armature`.

    mode_set silently returns CANCELLED - no exception - if the object is not
    selected as well as active, and a pose-bone rotation written while still in
    OBJECT mode is discarded. That is why the first IK pass produced a figure
    with its arms still in the rest A-pose.
    """
    bpy.context.view_layer.objects.active = armature
    try:
        armature.select_set(True)
    except (ReferenceError, RuntimeError):
        pass
    bpy.ops.object.mode_set(mode="POSE")
    if bpy.context.mode != "POSE":
        raise RuntimeError("could not enter pose mode on %s" % armature.name)


def _aim_bone(pb, head, new_dir):
    """Rotate a pose bone so its head->tail axis points along `new_dir`.

    A pose bone's rotation is a delta against its rest matrix *in the parent's
    space*, not a world rotation: assigning a world-space quaternion moves the
    arm a few centimetres and stops. So the wanted bone matrix is built and then
    divided back out of the parent's posed/rest pair, which is Blender's own
    definition of a bone's basis.

    All of this is done in armature space; the rig is scaled 0.01 to match the
    centimetre skeleton, and world space would mix the two.
    """
    rest = pb.bone
    B = rest.matrix_local.copy()
    q = (rest.tail_local - rest.head_local).normalized().rotation_difference(new_dir)
    desired = (mathutils.Matrix.Translation(head) @ q.to_matrix().to_4x4()
               @ mathutils.Matrix.Translation(-head) @ B)
    if pb.parent is not None:
        basis = ((pb.parent.matrix @ pb.parent.bone.matrix_local.inverted() @ B)
                 .inverted() @ desired)
    else:
        basis = B.inverted() @ desired
    pb.rotation_mode = "QUATERNION"
    pb.location = (0.0, 0.0, 0.0)
    pb.scale = (1.0, 1.0, 1.0)
    pb.rotation_quaternion = basis.to_quaternion()


def ik_arm(armature, suffix, target, pole):
    """Two-bone IK: put the wrist at `target` with the elbow pushed toward `pole`.

    The mannequin's chain is upperarm -> lowerarm -> hand with no twist bones in
    between, so the elbow is placed analytically (law of cosines) and the two
    bones are then aimed at it. `target` is world space; everything inside is
    armature space.
    """
    up = armature.pose.bones.get("upperarm_" + suffix)
    lo = armature.pose.bones.get("lowerarm_" + suffix)
    if up is None or lo is None:
        return None
    _enter_pose(armature)

    rest = armature.data
    su, sl = rest.bones["upperarm_" + suffix], rest.bones["lowerarm_" + suffix]
    inv = armature.matrix_world.inverted()
    T = inv @ Vector(target)            # target in armature space
    S = su.head_local.copy()
    a = (su.tail_local - su.head_local).length
    b = (sl.tail_local - sl.head_local).length

    d = (T - S).length
    d = max(min(d, (a + b) * 0.999), abs(a - b) * 1.001 + 1e-4)

    f = (T - S).normalized()
    p = inv.to_3x3() @ Vector(pole)
    p.normalize()
    m = p - f * p.dot(f)
    if m.length < 1e-6:
        m = Vector((0.0, 0.0, -1.0)) - f * f.dot(Vector((0.0, 0.0, -1.0)))
    m.normalize()

    cos_s = (a * a + d * d - b * b) / (2.0 * a * d)
    theta = math.acos(max(-1.0, min(1.0, cos_s)))
    E = S + a * (math.cos(theta) * f + math.sin(theta) * m)

    _aim_bone(up, S, (E - S).normalized())
    bpy.context.view_layer.update()
    _aim_bone(lo, sl.head_local.copy(), (T - E).normalized())

    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.update()
    return armature.matrix_world @ E


def pose(armature, side):
    """Fixed low-ready angles; see the note on ARM_ROT for why not IK."""
    _enter_pose(armature)
    for name, (ry, rz) in ARM_ROT.items():
        pb = armature.pose.bones.get(name)
        if pb is None:
            continue
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (0.0, math.radians(ry), math.radians(rz))
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.update()


def hold_weapon(weapon, right_hand, left_hand):
    """Fit the weapon onto the hands the pose actually produced.

    The transform maps the weapon's own pistol-grip point onto the right wrist
    and swings its bore at the left wrist, so the support hand ends up on the
    handguard whether or not the pose landed exactly on target. The bore is then
    rolled to a sensible attitude, because a rifle held across the body would
    otherwise present its flat to the sky.
    """
    if right_hand is None or left_hand is None:
        return
    right_hand = Vector(right_hand)
    left_hand = Vector(left_hand)
    # Roll about the bore FIRST, then aim. Rolling after aiming swings the
    # handguard round the bore and off the support hand, which is what left it
    # 110 mm short in the first pass.
    roll = mathutils.Quaternion((1.0, 0.0, 0.0), CARRY_ROLL).to_matrix().to_4x4()
    grip_r = roll @ GRIP_LOCAL
    supp_r = roll @ SUPPORT_LOCAL
    want = left_hand - right_hand
    if want.length < 1e-4:
        return
    q = (supp_r - grip_r).normalized().rotation_difference(want.normalized())
    m = (mathutils.Matrix.Translation(right_hand) @ q.to_matrix().to_4x4()
         @ roll @ mathutils.Matrix.Translation(-grip_r))
    for ob in weapon:
        ob.data.transform(m)
        ob.data.update()


def hand_position(armature, suffix):
    bone = armature.pose.bones.get("hand_" + suffix)
    if bone is None:
        return None
    return armature.matrix_world @ bone.tail


def aim(camera, direction):
    """Point the camera down -direction and return the frame it implies."""
    view_dir = Vector(direction).normalized()
    quat = (-view_dir).to_track_quat("-Z", "Y")
    camera.rotation_euler = quat.to_euler()
    tan_x = (camera.data.sensor_width / 2.0) / camera.data.lens
    tan_y = tan_x / (RES_X / RES_Y)
    return view_dir, quat.inverted(), tan_x, tan_y


def fit_distance(camera, target, direction, points):
    """Smallest distance along `direction` at which every point is in frame.

    Solved by iteration: each step pulls the camera back by sqrt(of the worst
    overflow), which converges in a handful of passes because the required
    distance falls off as 1/cos(angle).
    """
    view_dir, inv, tan_x, tan_y = aim(camera, direction)
    target = Vector(target)

    def required(dist):
        loc = target + view_dir * dist
        need = 0.0
        for c in points:
            local = inv @ (c - loc)
            depth = -local.z
            if depth <= 1e-4:
                return 1e9
            need = max(need, abs(local.x / depth) / tan_x, abs(local.y / depth) / tan_y)
        return need

    dist = 1.0
    for _ in range(40):
        need = required(dist)
        if need <= 1e8 and abs(need - 1.0) < 1e-4:
            break
        dist *= math.sqrt(max(need, 1e-6))
    return dist


def place(camera, target, direction, dist):
    view_dir = Vector(direction).normalized()
    camera.location = Vector(target) + view_dir * dist


def frame(camera, target, direction, points, margin=MARGIN):
    dist = fit_distance(camera, target, direction, points) * margin
    place(camera, target, direction, dist)
    return dist / margin


def render(stem, cfg):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    bpy.ops.import_scene.fbx(filepath=MANNY)
    armature = next(o for o in scene.objects if o.type == "ARMATURE")
    # Keep the highest-detail body; the LODs are review copies.
    for ob in list(scene.objects):
        if ob.type == "MESH" and "LOD0" not in ob.name:
            bpy.data.objects.remove(ob, do_unlink=True)
    body = next(o for o in scene.objects if o.type == "MESH" and "LOD0" in o.name)

    # Each gear FBX brings its own armature, scaled 0.01 to match the body's
    # centimetre rig. Deleting it strips that scale and blows the gear up 100x,
    # which is what put a 1.8 m figure inside a 183 m camera frame and left the
    # MAF render with no legs. Keep every rig, pose them all the same way, and
    # the kit follows the body.
    gear_objects = []
    for name in cfg["gear"]:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=os.path.join(ROOT, "Art", "Characters", "ADF", name))
        for ob in scene.objects:
            if ob not in before and ob.type == "MESH":
                gear_objects.append(ob)

    weapon_path = os.path.join(ROOT, cfg["weapon"])
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=weapon_path)
    weapon = [o for o in scene.objects if o not in before and o.type == "MESH"]
    for ob in list(bpy.data.objects):
        if ob not in before and ob not in weapon:
            bpy.data.objects.remove(ob, do_unlink=True)

    # Pose every rig in the scene: the body and each piece of kit carry their own
    # copy of the same skeleton, so the sleeves follow the arms.
    for rig in [o for o in scene.objects if o.type == "ARMATURE"]:
        pose(rig, cfg["side"])
    bpy.context.view_layer.update()

    # Bake the weapon transforms, then fit it to the hands the pose produced.
    for ob in weapon:
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        ob.location = (0.0, 0.0, 0.0)
    hold_weapon(weapon,
                hand_position(armature, "r"),
                hand_position(armature, "l"))
    bpy.context.view_layer.update()

    camo = pbr(stem + "_camo", cfg["camo"])
    gear = pbr(stem + "_gear", cfg["gear_tex"])
    assign(body, camo, gear)
    for ob in gear_objects + weapon:
        assign(ob, camo, gear)

    # Frame the figure, not the scene. Fitting every vertex let the weapon's
    # footprint - the A4 muzzle reaches well forward of the soldier - push the
    # frame wide, so the figure shrank into a big empty plate. A held prop may
    # run past the edge; a third of the frame of empty floor may not.
    figure = [o for o in scene.objects
              if o.type == "MESH" and o not in weapon]
    # Evaluate first: the body and kit are deformed by their armatures, so the
    # rest-pose vertex buffer is the A-pose, not the figure we are framing.
    dg = bpy.context.evaluated_depsgraph_get()

    def world_points(objs):
        out = []
        for ob in objs:
            ev = ob.evaluated_get(dg)
            me = ev.to_mesh()
            mw = ob.matrix_world
            out.extend(mw @ v.co for v in me.vertices)
            ev.to_mesh_clear()
        return out

    points = world_points(figure)
    lo = Vector((min(p[i] for p in points) for i in range(3)))
    hi = Vector((max(p[i] for p in points) for i in range(3)))
    target = (lo + hi) / 2.0
    # Light the figure's own size, so both sides get the same exposure whatever
    # the weapon contributes. Previously energy scaled with the whole-scene
    # radius and the A88 carry made the 3 ACR read a stop brighter than the MAF.

    scene.render.engine = "CYCLES"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Base Contrast"
    scene.view_settings.exposure = -0.6 + cfg["exposure"]

    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.035, 0.042, 0.050, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.35
    scene.world = world

    # Key the rig off the figure's height, not the scene radius. Both sides are
    # the same mannequin, so a figure-relative rig gives the two renders the
    # same exposure - which is the whole point of a matched pair.
    h = max(hi.z - lo.z, 0.5)
    d = h / 2.0
    p = (d / 0.90) ** 2
    add_area("Key", target, (-d * 1.5, -d * 1.8, d * 1.6), (d * 1.4, d * 0.9), 380 * p, (1.0, 0.88, 0.70))
    add_area("Fill", target, (d * 2.0, -d * 1.5, d * 0.3), (d * 1.8, d * 1.3), 110 * p, (0.58, 0.70, 0.68))
    add_area("Rim", target, (d * 0.7, d * 1.7, d * 1.3), (d * 1.0, d * 0.7), 620 * p, (0.95, 0.58, 0.32))
    add_area("Top", target, (0.0, -d * 0.3, d * 2.6), (d * 2.2, d * 1.4), 180 * p, (0.85, 0.88, 1.0))

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 85
    cam_data.sensor_fit = "HORIZONTAL"
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    # A three-quarter view from the front: the figure faces +Y.
    direction = (-0.50, 1.0, 0.14)
    # Fit the figure, then let the weapon widen the plate by at most 12%: a held
    # rifle should not dominate the composition, but the muzzle running past the
    # edge reads better than a third of the frame of empty floor.
    d_fig = frame(cam, target, direction, points)
    held = world_points(weapon)
    if held:
        d_all = fit_distance(cam, target, direction, points + held)
        d_use = min(d_all, d_fig * 1.12) * MARGIN
        place(cam, target, direction, d_use)

    os.makedirs(OUT, exist_ok=True)
    scene.render.filepath = os.path.join(OUT, "soldier-%s.png" % stem)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scene.render.filepath,
          "hands", [tuple(round(c, 3) for c in (hand_position(armature, "r") or Vector()))])


if __name__ == "__main__":
    for stem, cfg in SIDES.items():
        render(stem, cfg)
    print("done")
