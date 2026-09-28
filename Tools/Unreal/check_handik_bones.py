# Southern Spear - check the hand IK bone-name lists against the real meshes (Session 059).
#
# USSHandIKMeshComponent::ResolveBones logs "left-hand IK on Upper > Lower > Hand" once per mesh,
# and warns once if the candidate names do not form a chain. That log line needs a live match, and
# this machine's -game launch currently stalls before LoadMap (ADR-039), so the check is done here
# instead: for each mesh the component is actually used on, resolve the same candidate name lists
# and test the same chain condition.
#
# The ancestry test is a PROXY, not FSSHandIK::IsAncestor: a reference skeleton is stored in
# topological order, so requiring Upper < Lower < Hand by index is necessary but not sufficient.
# It is stated as a proxy in the report so nobody reads it as the real thing. The real assertion
# is that the three bones exist, in that order, with real gaps between them - the failure that
# matters is a name that is absent or on the wrong bone, and this catches it.
#
# The body mesh is the one ASSCharacter's mesh wears; the first-person meshes are the two sets
# USSFirstPersonSubsystem loads. Writes Build/handik_bones.json.
import json
import os

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "handik_bones.json")

# The component's defaults, copied from SSHandIKMeshComponent.h. If the lists change there, this
# list is the thing that has to change with them.
CANDIDATES = {
    "upper": ["upperarm_l", "LeftArm"],
    "lower": ["lowerarm_l", "LeftForeArm"],
    "hand": ["hand_l", "LeftHand"],
}

MESHES = {
    "body_mannequin": "/Game/Characters/Heroes/Mannequin/Meshes/SKM_Manny",
    "fp_arms_rifle": "/SSExp_ObjectiveAssault/FirstPerson/Rifle/SK_FP_Arms_Rifle",
    "fp_arms_pistol": "/SSExp_ObjectiveAssault/FirstPerson/Pistol/SK_FP_Arms_Pistol",
    "quantum_jeans": "/SSExp_ObjectiveAssault/Characters/QuantumProto/SKM_Jeans",
}

report = {"ok": False, "meshes": {}, "errors": []}

try:
    for label, path in MESHES.items():
        entry = {"path": path}
        mesh = unreal.load_asset(path)
        if mesh is None:
            entry["loaded"] = False
            report["meshes"][label] = entry
            continue
        entry["loaded"] = True
        try:
            skeleton = mesh.get_editor_property("skeleton")
            names = [str(n) for n in skeleton.get_reference_pose().get_bone_names()]
        except Exception as exc:
            entry["error"] = str(exc)
            report["meshes"][label] = entry
            continue
        entry["bones"] = len(names)
        index_of = {name: i for i, name in enumerate(names)}

        found = {}
        for role, candidates in CANDIDATES.items():
            hit = next((c for c in candidates if c in index_of), None)
            found[role] = hit
            entry[role] = {"matched": hit, "index": index_of.get(hit, -1)}

        all_found = all(found[r] for r in found)
        entry["all_names_found"] = all_found
        if all_found:
            u, l, h = found["upper"], found["lower"], found["hand"]
            ordered = index_of[u] < index_of[l] < index_of[h]
            entry["chain_ordered"] = ordered
            entry["chain_note"] = ("indices %d < %d < %d, topologically ordered (proxy for "
                                   "FSSHandIK::IsAncestor, not the real thing)"
                                   % (index_of[u], index_of[l], index_of[h]))
            # A name that matches a bone far from the arm is the silent failure worth naming.
            entry["would_log"] = "%s > %s > %s" % (u, l, h)
            entry["ok"] = ordered
        else:
            entry["ok"] = False
            entry["would_log"] = "WARNING: no left-arm chain; left-hand IK is off for this mesh"
        report["meshes"][label] = entry

    # The two meshes the component is wired to must both resolve; the rest are informational.
    required = ("body_mannequin", "fp_arms_rifle", "fp_arms_pistol")
    report["ok"] = all(report["meshes"][m].get("ok") for m in required)
    report["quantum_note"] = (
        "Quantum uses the UE mannequin names, so the body-side candidate list resolves on it "
        "unchanged. The first-person arms are a separate mesh and would still need their own "
        "candidates if the prototype is ever shown in first person.")
except Exception:
    import traceback
    report["errors"].append(traceback.format_exc())

with open(REPORT, "w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=1)
unreal.log("SS_BONE_CHECK_DONE ok={}".format(report["ok"]))
