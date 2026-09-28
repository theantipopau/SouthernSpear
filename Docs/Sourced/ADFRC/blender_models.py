"""Headless batch converter: binarised Arma .p3d -> .fbx via Arma 3 Object Builder.

Run:
  blender --background --python blender_models.py -- <src_root> <dst_root> <listfile>

Each model is imported fresh into an empty scene and exported as FBX.
Results (per file) are appended to <dst_root>/_convert_log.txt.
"""
import os
import sys
import time
import traceback

import bpy

SRC_ROOT = None
DST_ROOT = None


def install_pydata_patch():
    """Work around a Blender bmesh hang.

    Some ADFRC LODs contain faces with a repeated vertex index (a self-loop
    edge, e.g. [876, 876, 1581]).  Arma's engine ignores those slivers, but
    bmesh.normal_update() spins forever on them, so the A3OB import never
    returns.  Duplicate the offending vertex instead: geometry is unchanged,
    the face count stays the same (TAGG/selection indices stay valid) and
    Blender stops hanging.  Clean files pass through untouched.
    """
    import importlib
    p3d = importlib.import_module(
        "bl_ext.user_default.Arma3ObjectBuilder.io.data_p3d")
    orig = p3d.P3D_LOD.pydata

    def pydata(self):
        verts, edges, faces = orig(self)
        cleaned = []
        for face in faces:
            if len(set(face)) != len(face):
                face = list(face)
                seen = set()
                for i, vi in enumerate(face):
                    if vi in seen:
                        verts.append(verts[vi])
                        face[i] = len(verts) - 1
                    else:
                        seen.add(vi)
            cleaned.append(face)
        return verts, edges, cleaned

    p3d.P3D_LOD.pydata = pydata


def clear_scene():
    """Empty the scene WITHOUT read_factory_settings (which would unload
    the A3OB extension)."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll, do_unlink=True)
    for datablocks in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials,
                       bpy.data.actions, bpy.data.images, bpy.data.curves,
                       bpy.data.textures):
        for d in list(datablocks):
            if d.users == 0:
                datablocks.remove(d)


def dst_for(src):
    """Output FBX path for a source p3d (strips the debinarizer's _MLOD tag)."""
    rel = os.path.relpath(src, SRC_ROOT)
    base = os.path.splitext(rel)[0]
    if base.endswith("_MLOD"):  # debinarizer suffix -> keep output names clean
        base = base[:-5]
    return rel, os.path.join(DST_ROOT, base + ".fbx")


def convert(src):
    rel, dst = dst_for(src)
    tmp = os.path.splitext(dst)[0] + ".part.fbx"  # atomic: only finished files
    os.makedirs(os.path.dirname(dst), exist_ok=True)

    clear_scene()
    bpy.ops.a3ob.import_p3d(filepath=src)

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    verts = sum(len(o.data.vertices) for o in meshes)
    if not meshes:
        raise RuntimeError("no mesh objects imported")

    bpy.ops.export_scene.fbx(
        filepath=tmp,
        use_selection=False,
        object_types={"MESH", "ARMATURE"},
        bake_anim=False,
        add_leaf_bones=False,
        use_mesh_modifiers=True,
        path_mode="COPY",
    )
    if not os.path.exists(tmp):
        raise RuntimeError("FBX exporter produced no file")
    os.replace(tmp, dst)
    return rel, len(meshes), len(arms), verts, os.path.getsize(dst)


def main():
    global SRC_ROOT, DST_ROOT
    import addon_utils
    addon_utils.enable('bl_ext.user_default.Arma3ObjectBuilder', default_set=False)
    if 'a3ob' not in dir(bpy.ops):
        raise RuntimeError("A3OB extension not loaded")
    install_pydata_patch()

    args = sys.argv[sys.argv.index("--") + 1:]
    SRC_ROOT, DST_ROOT, listfile = args[0], args[1], args[2]
    with open(listfile, encoding="utf-8") as fh:
        paths = [line.strip() for line in fh if line.strip()]

    log_path = os.path.join(DST_ROOT, "_convert_log.txt")
    os.makedirs(DST_ROOT, exist_ok=True)
    ok = fail = skip = 0
    t0 = time.time()
    with open(log_path, "a", encoding="utf-8") as log:
        for i, src in enumerate(paths, 1):
            rel, dst = dst_for(src)
            if os.path.exists(dst) and os.path.getsize(dst) > 0:
                skip += 1
                continue
            try:
                rel2, nm, na, verts, size = convert(src)
                ok += 1
                log.write(f"OK   {rel2} meshes={nm} arms={na} verts={verts} "
                          f"fbx={size / 1e6:.1f}MB\n")
            except Exception:  # noqa: BLE001
                fail += 1
                log.write(f"FAIL {rel}\n{traceback.format_exc()}\n")
            log.flush()
            if ok + fail == 1 or (ok + fail) % 25 == 0:
                print(f"  {ok + fail}/{len(paths)} (ok={ok} fail={fail} "
                      f"skip={skip}) {time.time() - t0:.0f}s", flush=True)
    print(f"DONE {ok} ok, {fail} failed, {skip} already done, "
          f"{time.time() - t0:.0f}s", flush=True)


main()
