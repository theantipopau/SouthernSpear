"""Dump the Quantum reference skeleton (bones, parents, rest transforms).

Reads it out of the editor rather than out of the .uasset bytes, because the
FBX name table mixes bones with materials, sockets and object names, and the
rest transforms are needed to retarget anything onto this rig.

    "E:/Unreal/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" \
        SouthernSpear.uproject -nullrhi -unattended -nosplash -nosound \
        -stdout -ExecutePythonScript=Tools/Unreal/dump_quantum_skeleton.py
"""

import json
import os

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
OUT = os.path.join(PROJECT_DIR, "Build", "quantum_reference_skeleton.json")

MESH = "/Game/QuantumCharacter/Mesh/SKM_QuantumCharacter"

report = {"ok": False, "mesh": MESH, "skeleton": "", "bones": [], "errors": []}


def describe_errors() -> str:
    return "\n".join(report["errors"])


def main() -> None:
    mesh = unreal.load_asset(MESH)
    if mesh is None:
        report["errors"].append(f"could not load {MESH}")
        return
    report["skeleton"] = mesh.get_editor_property("skeleton").get_path_name()
    unreal.log(f"SS_SKELETON: reading {report['skeleton']}")

    # Skeleton.get_reference_pose() is the supported route to the ref skeleton in
    # UE 5.8 Python. It hands back an AnimPose, whose get_bone_names() and
    # get_ref_bone_pose() give the reference pose in skeleton order; there is no
    # ReferenceSkeleton / EditorSkeletalMeshSubsystem type exposed.
    skeleton = mesh.get_editor_property("skeleton")
    pose = skeleton.get_reference_pose()
    names = [str(name) for name in pose.get_bone_names()]
    unreal.log(f"SS_SKELETON: {len(names)} bones on {report['skeleton']}")

    for index, name in enumerate(names):
        transform = pose.get_ref_bone_pose(name)
        translation = transform.translation
        rotation = transform.rotation
        scale = transform.scale3d
        report["bones"].append(
            {
                "index": index,
                "name": name,
                "parent": str(
                    unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
                    .get_bone_parent(mesh, name)
                ),
                "translation": [
                    round(float(translation.x), 6),
                    round(float(translation.y), 6),
                    round(float(translation.z), 6),
                ],
                "rotation_xyzw": [
                    round(float(rotation.x), 6),
                    round(float(rotation.y), 6),
                    round(float(rotation.z), 6),
                    round(float(rotation.w), 6),
                ],
                "scale": [
                    round(float(scale.x), 6),
                    round(float(scale.y), 6),
                    round(float(scale.z), 6),
                ],
            }
        )

    report["ok"] = len(report["bones"]) > 0
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1)
    unreal.log(f"SS_SKELETON: wrote {len(report['bones'])} bones to {OUT}")
    if report["errors"]:
        unreal.log_error("SS_SKELETON: " + describe_errors())


main()
