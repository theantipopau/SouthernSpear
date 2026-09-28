# Southern Spear - FEASIBILITY GATE for the Quantum runtime-retarget prototype.
#
# The producer's other agent flagged runtime retargeting as "buildable headlessly but unproven here",
# and ADR-037 retired the Quantum pack on the strength of that unproven claim. ADR-038 already
# corrected the *usability* half (leader pose works for the 159 shared bones). This probe settles the
# buildability half with evidence instead of assertion, because criterion 1 of the prototype is
# "Quantum shirt/trousers/head on the runtime retargeter, fingers mapped".
#
# It answers four questions and writes the answers to Build/probe_retargeter.json:
#   1. Do the IKRetargeter asset classes exist in the 5.8 Python API, and can a factory create one?
#   2. Can retarget chains (the source->target bone map, incl. fingers) be authored on it?
#   3. Can an Anim Blueprint's graph be constructed headlessly, so it can hold
#      AnimNode_RetargetPoseFromMesh?
#   4. If not, is the C++ route available - a USkeletalMeshComponentPostProcessAnimInstance
#      subclass in SouthernSpearLyraBridge, which copies and remaps a pose in code with no AnimBP
#      asset at all? (Needs only a module dep on a plugin that already ships.)
#
# Read-only: creates nothing except a throwaway asset under Build/, which it never saves to /Game.
import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "probe_retargeter.json")
SCRATCH = PROJECT_DIR + "/Build/RetargetScratch"

MANNY = "/Game/Characters/Heroes/Mannequin/Meshes/SK_Mannequin"
QSKEL = "/Game/QuantumCharacter/Mesh/SK_Military_Character_Skeleton"
QSHIRT = "/Game/QuantumCharacter/Mesh/Modules/SKM_Shirt_RolledUp_Blue"

report = {"ok": False, "classes": {}, "factory": {}, "chains": {},
          "anim_blueprint": {}, "cpp_route": {}, "errors": []}


def note(bucket, key, value):
    report[bucket][key] = value
    unreal.log("SS_GATE {} {} = {}".format(bucket, key, value))


def has(cls_name):
    """True when the named type is exposed to Python at all (UE 5.8 hides some editor-only types)."""
    return hasattr(unreal, cls_name)


def members(obj, names):
    """Which of `names` the object actually exposes - the difference between 'exists' and 'usable'."""
    return [n for n in names if hasattr(obj, n)]


# ---------------------------------------------------------------- 1. classes exist
CLASSES = [
    # the retarget asset + factory
    "IKRetargeter", "IKRetargeterFactory", "IKRetargetChain", "RetargetChainMapping",
    "RetargetChainSettings", "RetargetPose", "BatchRetargetSettings", "ChainMap",
    # the runtime node that does the work
    "AnimNode_RetargetPoseFromMesh", "FAnimNode_RetargetPoseFromMesh",
    # the anim-blueprint route
    "AnimBlueprint", "AnimBlueprintFactory", "AnimBlueprintGeneratedClass", "AnimGraphNode_RetargetPose",
    # a C++ post-process instance, the fallback
    "SkeletalMeshComponentPostProcessAnimInstance",
]
for c in CLASSES:
    note("classes", c, has(c))

# The factory and the asset are the load-bearing pair; if either is missing the asset route is dead.
FACTORY_CLS = getattr(unreal, "IKRetargeterFactory", None)
RETARGETER_CLS = getattr(unreal, "IKRetargeter", None)

# ---------------------------------------------------------------- 2. buildable?
if FACTORY_CLS is not None:
    f = FACTORY_CLS()
    note("factory", "instantiated", True)
    # What can the factory be told to retarget *from* and *to*? These are the two properties that
    # decide whether the asset is worth anything, so name them explicitly.
    for prop in ("retarget_ik_rig", "preview_skeleton", "ik_rig", "target_skeleton",
                 "retarget_root", "source_skeleton"):
        try:
            f.set_editor_property(prop, None)
            note("factory", "settable:" + prop, True)
        except Exception as exc:
            note("factory", "settable:" + prop, "no ({})".format(type(exc).__name__))
else:
    note("factory", "instantiated", "no IKRetargeterFactory")

if RETARGETER_CLS is not None and FACTORY_CLS is not None:
    # Real assets carry a retarget root and a map of chains. Enumerate so the report shows what a
    # chain edit would actually touch, rather than a bare True/False.
    try:
        names = [n for n in dir(RETARGETER_CLS) if not n.startswith("_")]
        note("factory", "retargeter_members", [n for n in names if "chain" in n.lower()
                                               or "retarget" in n.lower() or "root" in n.lower()])
    except Exception as exc:
        report["errors"].append("dir(IKRetargeter): " + str(exc))

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    try:
        asset = tools.create_asset("SSR_RetargetScratch", SCRATCH, unreal.IKRetargeter, FACTORY_CLS())
        note("factory", "created", None if asset is None else asset.get_path_name())
    except Exception:
        report["errors"].append("create_asset(IKRetargeter): " + traceback.format_exc()[-600:])

# ---------------------------------------------------------------- 3. chains (fingers)
# The fingers are the whole point of criterion 1: Quantum has 192 bones Manny lacks, and they are
# fingers, toes and face. A retargeter only moves them if a chain names each one.
CHAIN_CLS = getattr(unreal, "RetargetChain", None) or getattr(unreal, "IKRetargetChain", None)
note("chains", "chain_class", None if CHAIN_CLS is None else CHAIN_CLS.__name__)
if CHAIN_CLS is not None:
    try:
        c = CHAIN_CLS()
        note("chains", "instantiated", True)
        note("chains", "settable", [n for n in dir(CHAIN_CLS) if not n.startswith("_")])
    except Exception as exc:
        report["errors"].append("chain instantiate: " + str(exc))

# ---------------------------------------------------------------- 4. AnimBP graph
# An Anim Blueprint is a graph asset. Python in 5.8 exposes the Blueprint object but, on this
# project's evidence so far, not the AnimGraph editor, so establish that rather than assume it.
try:
    af = unreal.AnimBlueprintFactory()
    note("anim_blueprint", "factory_instantiated", True)
    note("anim_blueprint", "factory_props", [n for n in dir(af)
                                              if "graph" in n.lower() or "parent" in n.lower()])
except Exception as exc:
    report["errors"].append("AnimBlueprintFactory: " + str(exc))

try:
    AB = getattr(unreal, "AnimBlueprint", None)
    note("anim_blueprint", "graph_api", members(AB, [
        "add_graph", "get_graph", "create_graph", "set_graph", "ubergraph_pages", "function_graphs",
        "get_animation_graph", "variables", "add_variable",
    ]) if AB is not None else "no AnimBlueprint")
except Exception as exc:
    report["errors"].append("AnimBlueprint members: " + str(exc))

# ---------------------------------------------------------------- 5. the C++ fallback route
# A post-process anim instance needs no AnimBP asset: it is a component that takes the pose the
# pawn already produced and rewrites it. It lives in the bridge module, which already depends on
# LyraGame, so the only question is whether the engine exposes the hooks to a Southern Spear module.
note("cpp_route", "postprocess_class_exposed", has("SkeletalMeshComponentPostProcessAnimInstance"))
note("cpp_route", "eap_exposed", has("AnimNode_RetargetPoseFromMesh"))
note("cpp_route", "bridge_exists", os.path.isdir(PROJECT_DIR + "/Plugins/SouthernSpearLyraBridge/Source"))
report["cpp_route"]["note"] = ("C++ needs no Python API: UAnimInstance::NativeUpdateAnimation and "
                               "FAnimationPose are engine C++ the bridge module can call directly.")

# ---------------------------------------------------------------- skeletons still load
# The retarget is only meaningful if both ends are present, so confirm the three assets.
for label, path in (("manny", MANNY), ("quantum_skeleton", QSKEL), ("quantum_shirt", QSHIRT)):
    a = unreal.load_asset(path)
    note("classes", "loads:" + label, None if a is None else type(a).__name__)

report["ok"] = True
with open(REPORT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=1)
unreal.log("SS_GATE_DONE")
