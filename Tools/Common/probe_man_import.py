"""Probe: does a `class = man` P3D import in a bare background Blender?

The earlier "import_p3d never returns" finding came from BIS.CLI batch mode,
which spawns several Blenders against one scratch directory and deadlocks
(R-30). This runs a single Blender with no harness in the way, and reports
where it actually gets to. Nothing is saved to the project.

    "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b \
        --factory-startup --python Tools/Common/probe_man_import.py -- <p3d>
"""

from __future__ import annotations

import os
import sys
import time
import traceback

import bpy

START = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - START:7.2f}s] {message}", flush=True)


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if not argv:
        print("usage: probe_man_import.py <p3d> [<p3d> ...]")
        return
    path = os.path.abspath(argv[0])
    log(f"file {path} ({os.path.getsize(path)} bytes)")

    log("enabling Arma3ObjectBuilder")
    bpy.ops.preferences.addon_enable(module="bl_ext.user_default.Arma3ObjectBuilder")
    # A3OB v2.5 registers its operators under the `a3ob` category; the older
    # `arma3tools` name does not exist and raises "could not be found".
    log(f"addon enabled; a3ob.import_p3d present: {hasattr(bpy.ops.a3ob, 'import_p3d')}")

    log("calling import_p3d ...")
    try:
        result = bpy.ops.a3ob.import_p3d(
            filepath=path,
            first_lod_only=True,
            validate_meshes=False,
        )
        log(f"import_p3d returned {result}")
    except Exception:
        log("import_p3d raised:\n" + traceback.format_exc())
        return

    armatures = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    log(f"objects: {len(armatures)} armature(s), {len(meshes)} mesh(es)")
    for arm in armatures:
        bones = arm.data.bones
        log(f"armature {arm.name!r}: {len(bones)} bones")
        for bone in bones:
            log(f"  BONE {bone.name} parent={bone.parent.name if bone.parent else ''}")
    for mesh in meshes:
        groups = [g.name for g in mesh.vertex_groups]
        log(
            f"mesh {mesh.name!r}: verts={len(mesh.data.vertices)} "
            f"polys={len(mesh.data.polygons)} vgroups={len(groups)}"
        )
        log(f"  vgroups: {groups[:20]}{' ...' if len(groups) > 20 else ''}")
        log(f"  modifiers: {[m.type for m in mesh.modifiers]}")

    out = os.environ.get("PROBE_OUT", "")
    if out:
        with open(out, "w", encoding="utf-8") as handle:
            for arm in armatures:
                for bone in arm.data.bones:
                    handle.write(f"{bone.name}\t{bone.parent.name if bone.parent else ''}\n")
        log(f"wrote bone list to {out}")


main()
log("done")
