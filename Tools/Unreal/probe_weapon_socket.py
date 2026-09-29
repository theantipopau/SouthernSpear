"""Print the grip sockets of the ADFRC weapon static meshes, as the game sees them.

    UnrealEditor-Cmd.exe <proj> -run=pythonscript -script=<this file> -nullrhi -unattended

The Blender empties arrive as sockets (SOCKET_ prefix dropped). This reads the rotation the FBX
import actually gave them, which is the only number the hand-IK offset can be solved against.
"""
import json
import os

import unreal

OUT = os.path.join(unreal.Paths.project_dir(), "Build", "weapon_sockets.json")
found = {}

for path in unreal.EditorAssetLibrary.list_assets("/Game", recursive=True, include_folder=False):
    name = path.split(".")[0]
    if "/SM_" not in name:
        continue
    mesh = unreal.load_asset(name)
    if not isinstance(mesh, unreal.StaticMesh):
        continue
    sockets = {}
    for socket_name in ("Muzzle", "LeftHandGrip", "RightHandGrip", "Eject", "EjectEnd"):
        transform = mesh.find_socket(socket_name) if hasattr(mesh, "find_socket") else None
        if transform is None:
            continue
        sockets[socket_name] = {
            "location_cm": [round(c * 100.0, 3) for c in transform.translation],
            "rotator": [round(c, 3) for c in transform.rotation.to_euler()],
            # The socket's own axes in mesh space, which is what the hand-IK offset reads.
            "x_axis": [round(c, 4) for c in transform.rotation.rotate_vector(unreal.Vector(1, 0, 0))],
            "y_axis": [round(c, 4) for c in transform.rotation.rotate_vector(unreal.Vector(0, 1, 0))],
            "z_axis": [round(c, 4) for c in transform.rotation.rotate_vector(unreal.Vector(0, 0, 1))],
        }
    box = mesh.get_bounding_box()
    size = box.max - box.min
    if sockets:
        found[name] = {
            "size_cm": [round(size.x, 1), round(size.y, 1), round(size.z, 1)],
            "sockets": sockets,
        }

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(found, fh, indent=1, sort_keys=True)
unreal.log("SS_SOCKETS_WRITTEN " + OUT + " " + str(len(found)))
