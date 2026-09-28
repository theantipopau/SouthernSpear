"""
Ravenshoe Crossing - greybox preview renders.

A greybox nobody has looked at is not a greybox, it is a guess. This renders
the four views that actually answer design questions:

    axis      the shot the layout is built around: from the south approach,
              straight up the axis, bridge centred, gatehouse at the end
    gate      the objective B arch, close enough to see the voussoirs
    gorge     from inside the creek bed looking up at the span, which is the
              view that decides whether the second lane is worth having
    overview  the whole 200 x 300 m blockout, for rotation and cover rhythm

Workbench, not a path-traced render: this is a shape check, and a greybox that
looks finished stops being treated as one.

Run:
    blender -b --factory-startup Content/Art/Blockout/SS_MAP_Ravenshoe_01_HI.blend \
            --python Tools/Blender/ravenshoe_render.py
"""

import math
import os
import sys

import bpy
import mathutils

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Common")))
import ravenshoe_spec as S  # noqa: E402

OUT_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                 "Build", "ravenshoe"))

EYE = 1.65  # standing eye height, so ground-referenced cameras are eye level


def _eye(x, y, up=EYE):
    """Camera height above the ACTUAL ground, read from the spec.

    Every close camera here is placed on the ground it is standing on. Three of
    the first four were not, and the result was two blank frames and one shot
    from inside solid rock: the gate camera sat at z=8.5 where the terrain is
    14, and the axis camera at z=21.0 where the road is 21.6. A render that
    comes out black is almost always a camera in the dirt, not a lighting bug,
    and reading the height off the spec is the only way to be sure.
    """
    return S.ground_z(x, y) + up


VIEWS = [
    # name,       camera,                    target,               note
    # The axis camera stands at y=-105, not -124: the south deployment zone
    # spans y -145..-115, so a camera at -124 is standing inside a red marker
    # box that fills the bottom third of the frame.
    ("axis", (0.0, -105.0, _eye(0.0, -105.0, 2.4)), (0.0, 30.0, S.DECK_Z),
     "south approach up the axis"),
    ("gate", (0.0, 40.0, _eye(0.0, 40.0)), (0.0, S.GATE_Y, _eye(0.0, S.GATE_Y, 1.8)),
     "objective B arch from the north abutment"),
    ("gorge", (34.0, -14.0, _eye(34.0, -14.0)), (0.0, 2.0, S.DECK_Z - 1.0),
     "creek bed looking up at the span"),
    ("ramp", (70.0, -30.0, _eye(70.0, -30.0, 2.0)), (95.0, -20.0, -2.0),
     "east traverse ramp on the gorge wall"),
    ("plan", (0.0, 0.0, 400.0), (0.0, 0.0, 0.0),
     "top-down plan"),
    ("overview", (-168.0, -186.0, 104.0), (0.0, 8.0, 2.0),
     "whole blockout"),
]


def look_at(cam, target):
    d = mathutils.Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    scene = bpy.context.scene

    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_specular_highlight = False
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (0.55, 0.60, 0.68)

    cam_data = bpy.data.cameras.new("SS_Raven_Cam")
    cam_data.lens = 35.0
    cam_data.clip_end = 3000.0
    cam = bpy.data.objects.new("SS_Raven_Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    for name, loc, target, note in VIEWS:
        cam.location = mathutils.Vector(loc)
        look_at(cam, target)
        # The plan view has to cover 300 m of map on its long axis, so the
        # frame is rolled to put +Y across the width and the ortho scale is
        # set from the SHORT axis: 200 m tall in a 16:9 frame needs 200 /
        # (9/16) = 356. The first attempt used 210, which framed a 210 x 118 m
        # window in the middle of the map and showed neither deployment.
        if name == "plan":
            cam_data.type = "ORTHO"
            cam_data.ortho_scale = 365.0
            cam.rotation_euler = (0.0, 0.0, math.radians(-90.0))
        else:
            cam_data.type = "PERSP"
        scene.render.filepath = os.path.join(OUT_DIR, "raven_%s.png" % name)
        bpy.ops.render.render(write_still=True)
        print("RENDERED %-9s cam_z=%-7.2f %-30s %s" % (
            name, loc[2], note, os.path.basename(scene.render.filepath)))


if __name__ == "__main__":
    main()
