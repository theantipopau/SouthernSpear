"""Survey the decoded ADFRC animation clips against the Quantum skeleton.

Answers, from the files rather than from guesswork:

  * how many of the 146 clips are real animations rather than static poses,
  * which of them are humanoid at all (the pack also carries Chinook and
    fighter-aircrew rigs, and those rigs pass a naive "has a spine and arms"
    test just as well as a soldier does),
  * how many of each clip's bones actually land on a Quantum bone.

Inputs:
  Art/ADFRC/Animations/*.json                  decoded BMTR clips
  Art/ADFRC/Config/*/model.cfg                 OFP2_ManSkeleton bone hierarchy
  Build/quantum_reference_skeleton.json        from Tools/Unreal/dump_quantum_skeleton.py

Writes Build/adfrc_animation_survey.json and a short markdown summary.

    python Tools/Unreal/adfrc_animation_survey.py
"""

from __future__ import annotations

import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLIP_DIR = os.path.join(ROOT, "Art", "ADFRC", "Animations")
CFG_GLOB = os.path.join(ROOT, "Art", "ADFRC", "Config", "*", "model.cfg")
QUANTUM = os.path.join(ROOT, "Build", "quantum_reference_skeleton.json")
OUT_JSON = os.path.join(ROOT, "Build", "adfrc_animation_survey.json")
OUT_MD = os.path.join(ROOT, "Build", "adfrc_animation_survey.md")

# Bones that must all be present for a clip to be usable as a soldier animation.
CORE_BONES = (
    "pelvis",
    "spine",
    "head",
    "leftarm",
    "rightarm",
    "leftforearm",
    "rightforearm",
    "leftupleg",
    "rightupleg",
)

# Clip name fragments that indicate a vehicle or aircrew rig rather than a soldier.
# "bushmaster_ffv" is the Bushmaster Future Fighting Vehicle, so its "ffv" mocaps
# are gunner-seat views, not a soldier's body animation.
VEHICLE_HINTS = ("ch47", "pilot_", "gunner_", "passenger_", "bushmaster", "ffv")


def read_arma_hierarchy() -> dict[str, str]:
    """Pull the OFP2_ManSkeleton bone -> parent table out of any ADFRC model.cfg."""
    for path in sorted(glob.glob(CFG_GLOB)):
        text = open(path, encoding="utf-8", errors="replace").read()
        match = re.search(
            r"class\s+OFP2_ManSkeleton.*?skeletonBones\[\]\s*=\s*\{(.*?)\};", text, re.S
        )
        if not match:
            continue
        bones: dict[str, str] = {}
        for name, parent in re.findall(r'"([^"]*)"\s*,\s*"([^"]*)"', match.group(1)):
            if name:
                bones[name.lower()] = parent.lower()
        if bones:
            return bones
    return {}


def build_bone_map(arma_hierarchy: dict[str, str], quantum_bones: set[str]) -> dict:
    """Map the Arma rig onto Quantum by name.

    BMTR bones are the Arma rig's (`Spine`, `Spine1`, `rightarm`); Quantum uses
    `spine_01`, `upperarm_r`. There is no naming scheme that lines the two rigs
    up, so each family of bones is mapped explicitly here. Anything not listed
    has to be renamed by hand or driven procedurally.
    """
    mapping: dict[str, str] = {
        "pelvis": "pelvis",
        "spine": "spine_01",
        "spine1": "spine_02",
        "spine2": "spine_03",
        "spine3": "spine_04",
        "neck": "neck_01",
        "neck1": "neck_02",
        "head": "head",
    }
    for side, suffix in (("left", "_l"), ("right", "_r")):
        mapping[f"{side}shoulder"] = f"clavicle{suffix}"
        mapping[f"{side}arm"] = f"upperarm{suffix}"
        mapping[f"{side}armroll"] = f"upperarm{suffix}"
        mapping[f"{side}forearm"] = f"lowerarm{suffix}"
        mapping[f"{side}forearmroll"] = f"lowerarm{suffix}"
        mapping[f"{side}hand"] = f"hand{suffix}"
        mapping[f"{side}upleg"] = f"thigh{suffix}"
        mapping[f"{side}uplegroll"] = f"thigh{suffix}"
        mapping[f"{side}leg"] = f"calf{suffix}"
        mapping[f"{side}legroll"] = f"calf{suffix}"
        mapping[f"{side}foot"] = f"foot{suffix}"
        mapping[f"{side}toebase"] = f"ball{suffix}"
        for finger in ("index", "middle", "ring", "pinky", "thumb"):
            for joint in (1, 2, 3):
                # Quantum puts the side last on finger bones (index_01_r), and
                # carries a lot of extra helper bones per joint that the Arma rig
                # has no equivalent for; only the main chain is mapped.
                mapping[f"{side}hand{finger}{joint}"] = f"{finger}_0{joint}{suffix}"

    resolved = {src: dst for src, dst in mapping.items() if dst in quantum_bones}
    unresolved = sorted(
        {
            dst
            for dst in mapping.values()
            if dst not in quantum_bones
        }
    )
    covered = sorted(set(resolved) & set(arma_hierarchy))
    return {
        "mapping": dict(sorted(resolved.items())),
        "arma_bones_without_mapping": sorted(set(arma_hierarchy) - set(resolved)),
        "quantum_targets_not_found": unresolved,
        "arma_bones_covered": len(covered),
        "arma_bones_total": len(arma_hierarchy),
    }


def main() -> None:
    quantum = json.load(open(QUANTUM, encoding="utf-8"))
    quantum_bones = {b["name"] for b in quantum["bones"]}
    arma_hierarchy = read_arma_hierarchy()
    bone_map = build_bone_map(arma_hierarchy, quantum_bones)
    mapping = bone_map["mapping"]

    clips = []
    for path in sorted(glob.glob(os.path.join(CLIP_DIR, "*.json"))):
        data = json.load(open(path, encoding="utf-8"))
        bones = [b.lower() for b in data["bones"]]
        boneset = set(bones)
        frames = len(data["frames"])

        # How much of this particular clip the bone map can actually drive.
        mapped = sorted(b for b in boneset if b in mapping)
        core_present = [b for b in CORE_BONES if b in boneset]

        lowered = os.path.basename(path).lower()
        if any(hint in lowered for hint in VEHICLE_HINTS):
            kind = "vehicle/aircrew"
        elif frames <= 2:
            kind = "static pose"
        elif len(core_present) == len(CORE_BONES):
            kind = "soldier animation"
        else:
            kind = "non-humanoid"

        clips.append(
            {
                "file": os.path.basename(path),
                "frames": frames,
                "bones": len(bones),
                "phases": len(data.get("phases", [])),
                "kind": kind,
                "core_bones": f"{len(core_present)}/{len(CORE_BONES)}",
                "mapped": len(mapped),
                "unmapped": sorted(boneset - set(mapped)),
                "mapped_sample": mapped[:8],
            }
        )

    kinds: dict[str, int] = {}
    for clip in clips:
        kinds[clip["kind"]] = kinds.get(clip["kind"], 0) + 1

    report = {
        "clips": len(clips),
        "by_kind": kinds,
        "arma_hierarchy_bones": len(arma_hierarchy),
        "quantum_bones": len(quantum_bones),
        "bone_map": bone_map,
        "clip_list": sorted(
            (c for c in clips if c["frames"] > 2),
            key=lambda c: (-c["frames"], c["file"]),
        ),
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1)

    lines = [
        "# ADFRC animation survey",
        "",
        f"- decoded clips: **{report['clips']}**",
        f"- Quantum reference bones: **{report['quantum_bones']}**",
        f"- OFP2_ManSkeleton bones recovered from model.cfg: **{report['arma_hierarchy_bones']}**",
        "",
        "## Clip kinds",
        "",
    ]
    lines += [f"- {kind}: {count}" for kind, count in sorted(kinds.items())]
    lines += [
        "",
        "## Clips with more than two frames",
        "",
        "| clip | frames | bones | mapped | core | kind |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for clip in report["clip_list"]:
        lines.append(
            f"| {clip['file']} | {clip['frames']} | {clip['bones']} | "
            f"{clip['mapped']} | {clip['core_bones']} | {clip['kind']} |"
        )
    with open(OUT_MD, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")

    print(f"clips={report['clips']} kinds={kinds}")
    print(f"arma hierarchy bones={report['arma_hierarchy_bones']}")
    bone_map = report["bone_map"]
    print(
        f"bone map: {bone_map['arma_bones_covered']}/{bone_map['arma_bones_total']} "
        f"Arma bones map onto a Quantum bone"
    )
    print(f"wrote {OUT_JSON} and {OUT_MD}")


if __name__ == "__main__":
    main()
