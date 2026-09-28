# Southern Spear - prove the Quantum runtime retarget without a renderer (Session 058).
#
# A -game capture needs a display this machine does not currently have (Tools/run_map_capture.sh
# stalls at 32 log lines on every map, including known-good ones, with and without RHI), so the
# retarget cannot be shown in a screenshot this session. It can still be shown to work.
#
# This calls ASSQuantumProtoStage::ProveRetarget, which runs the SAME BuildBoneMap and
# EvaluateRetarget the runtime tick runs - the proof and the shipping path are one function, not
# a re-implementation - and checks three invariants. See the header for why each one matters.
#
# Writes Build/quantum_retarget_proof.json.
import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "quantum_retarget_proof.json")

# SKM_Manny, not SK_Mannequin: in this project SK_Mannequin is the Skeleton and the two share
# a name, so loading the latter returns a USkeleton and the SkeletalMesh cast fails quietly.
SOURCE = "/Game/Characters/Heroes/Mannequin/Meshes/SKM_Manny.SKM_Manny"
TARGETS = [
    ("shirt", "/SSExp_ObjectiveAssault/Characters/QuantumProto/SKM_Shirt_RolledUp_Blue.SKM_Shirt_RolledUp_Blue"),
    ("jeans", "/SSExp_ObjectiveAssault/Characters/QuantumProto/SKM_Jeans.SKM_Jeans"),
    ("head", "/SSExp_ObjectiveAssault/Characters/QuantumProto/SKM_Head.SKM_Head"),
    ("arms", "/SSExp_ObjectiveAssault/Characters/QuantumProto/SKM_Arms.SKM_Arms"),
]

report = {"ok": False, "source": SOURCE, "modules": {}, "errors": []}

try:
    stage = unreal.SSQuantumProtoStage
    for label, path in TARGETS:
        result = {}
        try:
            # Finger curl 1.0, 55 degrees per joint: the values the stage ships with.
            # Python turns the UPARAM(ref) out-param into a return value and drops the C++
            # bool, so the verdict comes back inside the JSON.
            raw = stage.prove_retarget(SOURCE, path, 1.0, 55.0)
            parsed = json.loads(raw) if raw else {}
            result["returned"] = bool(parsed.get("ok"))
        except Exception:
            parsed = {"error": traceback.format_exc()[-800:]}
            result["returned"] = False
        report["modules"][label] = {"path": path, "returned": result.get("returned"), **parsed}
        unreal.log("SS_QPROOF_RESULT {} ok={} {}".format(label, result.get("returned"), parsed))

    # The stage also measures whether the plate carrier still fits Quantum's torso
    # (criterion 3). Same class, called the same way, from the same commandlet.
    try:
        stage.log_fit_report()
        report["fit_report_requested"] = True
    except Exception as exc:
        report["errors"].append("LogFitReport: " + str(exc))

    report["ok"] = all(m.get("returned") for m in report["modules"].values())
except Exception:
    report["errors"].append(traceback.format_exc())

with open(REPORT, "w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=1)
unreal.log("SS_QPROOF_DONE ok={}".format(report["ok"]))
