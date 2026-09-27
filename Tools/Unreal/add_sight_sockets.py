"""Add a "Sight" socket to each ADFRC weapon with an optic: the optic's optical
axis, estimated from its bounds (mount below, tube above the centre). The
first-person view uses it to put the optic on the line of sight when aiming.
Blender-to-Unreal axes are inferred from the existing Muzzle socket."""
import json
import os
import unreal

ROOT = "E:/SouthernSpear/Art/Weapons"
eal = unreal.EditorAssetLibrary
out = {}
for name in ["A88", "A88G", "A89", "A4", "A416", "A25", "A9"]:
    manifest = os.path.join(ROOT, name, "ADFRC", "manifest.json")
    mesh = unreal.load_asset("/SSExp_ObjectiveAssault/Weapons/{0}/SM_{0}".format(name))
    if not mesh or not os.path.exists(manifest):
        out[name] = "missing"
        continue
    data = json.load(open(manifest))
    optic, muzzle_b = data.get("optic"), data.get("muzzle_m")
    muzzle = mesh.find_socket("Muzzle")
    if not optic or not muzzle or not muzzle_b:
        out[name] = "no optic"
        continue
    m = muzzle.get_editor_property("relative_location")
    ue = [m.x, m.y, m.z]
    # Blender x (forward) and z (up) are the two big muzzle components.
    fwd = max(range(3), key=lambda i: abs(ue[i]))
    fsign = 1.0 if ue[fwd] * muzzle_b[0] > 0 else -1.0
    up = 2 if fwd != 2 else 1
    usign = 1.0 if ue[up] * muzzle_b[2] >= 0 else -1.0
    c, size = optic["centre_m"], optic["size_m"]
    sight = [0.0, 0.0, 0.0]
    sight[fwd] = fsign * c[0] * 100.0
    sight[up] = usign * (c[2] + 0.2 * size[2]) * 100.0
    socket = mesh.find_socket("Sight")
    if not socket:
        socket = unreal.StaticMeshSocket(mesh)
        socket.set_editor_property("socket_name", "Sight")
        mesh.add_socket(socket)
    socket.set_editor_property("relative_location", unreal.Vector(*sight))
    ok = eal.save_loaded_asset(mesh)
    out[name] = {"sight_cm": [round(v, 2) for v in sight], "muzzle_cm": [round(v, 2) for v in ue], "saved": ok}
unreal.log("SS_SIGHT " + json.dumps(out))
