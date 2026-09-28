#!/usr/bin/env python3
"""Reconstruct Arma BME animation rig hierarchies from decoded RTM JSON.

The .rtm files give a flat bone list plus per-frame transforms, but never the
parent links - Arma derives those from its built-in BME skeleton.  Bone *list
order is not hierarchy order* (one rig stores `weapon` first, another
`spine`), so a purely geometric nearest-neighbour search produces garbage.

Instead we rebuild the hierarchy from the BME bone naming convention, which is
regular and fully enumerable: 231 distinct bone names appear across the 165
clips, and they fall into a handful of chains (spine, neck, arms, legs, hands,
fingers, face, slots, attachments).  Anything the rules do not cover falls back
to nearest-neighbour *in rest-pose space*, guarded by an acyclicity check so the
result is always a tree.

Two on-disk frame shapes are handled:
  BMTR v3/4/5   parent-relative  {"q":[x,y,z,w], "p":[x,y,z]}
  RTM_0101      absolute 3x4     {"bone": name, "m":[12 floats]}

Both are normalised to world space, the hierarchy is solved, then converted back
to parent-relative locals - which is what Blender bones and UE tracks store.

Writes:
  Animations/Rig/<rig>.json        skeleton + rest world poses
  Animations/Rig/_rig_index.json   clip -> rig mapping
  Animations/Rig/<rig>/<clip>.json local-space animation, ready for Blender
"""
import collections
import glob
import json
import math
import os
import sys

EX = r"E:\SouthernSpear\Content\Sourced\ADF_Extracted\Animations"
RIG_DIR = os.path.join(EX, "Rig")

# Geometric sanity bound for a human rig (metres). Anything longer than this is
# reported for review rather than silently accepted.
MAX_LINK = 0.95
# Fallback nearest-neighbour radius.
NEAREST = 0.60


# ------------------------------------------------------------------ math

def mat_from_quat(q):
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w)
    if n == 0:
        return ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    x, y, z, w = x / n, y / n, z / n, w / n
    return (
        (1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
        (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
        (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)),
    )


def mat_mul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))
                 for i in range(3))


def mat_apply(m, v):
    return tuple(m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2] for i in range(3))


def mat_transpose(m):
    return tuple(tuple(m[j][i] for j in range(3)) for i in range(3))


def quat_from_mat(m):
    """Shepperd's method - stable across the full range of 3x3 rotations."""
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        w, x, y, z = 0.25 * s, (m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s, (m[1][0] - m[0][1]) / s
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2
        w, x, y, z = (m[2][1] - m[1][2]) / s, 0.25 * s, (m[0][1] + m[1][0]) / s, (m[0][2] + m[2][0]) / s
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2
        w, x, y, z = (m[0][2] - m[2][0]) / s, (m[0][1] + m[1][0]) / s, 0.25 * s, (m[1][2] + m[2][1]) / s
    else:
        s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2
        w, x, y, z = (m[1][0] - m[0][1]) / s, (m[0][2] + m[2][0]) / s, (m[1][2] + m[2][1]) / s, 0.25 * s
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    return [round(x / n, 6), round(y / n, 6), round(z / n, 6), round(w / n, 6)]


# ------------------------------------------------------- frame accessors

def frame_is_absolute(frame):
    return bool(frame) and isinstance(frame[0], dict) and "m" in frame[0]


def world_from_absolute(m12):
    r = tuple(tuple(m12[i * 4 + j] for j in range(3)) for i in range(3))
    return r, (m12[3], m12[7], m12[11])


def world_from_local(frame, parent):
    """Accumulate parent-relative locals to world.

    Parents are not guaranteed to precede children in the bone *list* (one rig
    stores `weapon` first, another `spine`), so walk in topological order.
    """
    n = len(parent)
    wm, wp = [None] * n, [None] * n
    order = topo_order(parent)
    for i in order:
        lm = mat_from_quat(frame[i]["q"])
        lp = tuple(frame[i]["p"])
        p = parent[i]
        if p is None or wm[p] is None:
            wm[i], wp[i] = lm, lp
        else:
            wm[i] = mat_mul(wm[p], lm)
            wp[i] = tuple(
                wm[p][r][0] * lp[0] + wm[p][r][1] * lp[1] + wm[p][r][2] * lp[2]
                + wp[p][r] for r in range(3))
    return wm, wp


def topo_order(parent):
    """Indices sorted so every parent comes before its children."""
    n = len(parent)
    children = [[] for _ in range(n)]
    roots = []
    for i, p in enumerate(parent):
        (children[p] if p is not None else roots).append(i)
    order, stack = [], list(roots)
    while stack:
        i = stack.pop()
        order.append(i)
        stack.extend(children[i])
    if len(order) < n:                 # cycle fallback: plain list order
        order = [i for i in range(n) if i not in set(order)]
    return order


def local_from_world(wm, wp, parent):
    lm, lp = [None] * len(wm), [None] * len(wp)
    for i in range(len(wm)):
        p = parent[i]
        if p is None:
            lm[i], lp[i] = wm[i], wp[i]
        else:
            inv = mat_transpose(wm[p])          # rotations are orthonormal
            lm[i] = mat_mul(inv, wm[i])
            lp[i] = mat_apply(inv, tuple(wp[i][r] - wp[p][r] for r in range(3)))
    return lm, lp


# ------------------------------------------------- BME hierarchy rules

def build_rules():
    """child (lowercase, no underscores/spaces) -> parent (same form)."""
    r = {}

    def link(child, parent):
        r[child] = parent

    # Torso, neck, head.
    for c, p in (("spine", "pelvis"), ("spine1", "spine"), ("spine2", "spine1"),
                 ("spine3", "spine2"), ("neck", "spine3"), ("neck1", "neck"),
                 ("head", "neck1")):
        link(c, p)

    # Arms: spine3 -> shoulder -> arm -> armroll -> forearm -> forearmroll -> hand.
    for side in ("left", "right"):
        link(side + "shoulder", "spine3")
        link(side + "arm", side + "shoulder")
        link(side + "armroll", side + "arm")
        link(side + "forearm", side + "armroll")
        link(side + "forearmroll", side + "forearm")
        link(side + "hand", side + "forearmroll")

        # Legs: pelvis -> upleg -> uplegroll -> leg -> legroll -> foot -> toebase.
        link(side + "upleg", "pelvis")
        link(side + "uplegroll", side + "upleg")
        link(side + "leg", side + "uplegroll")
        link(side + "legroll", side + "leg")
        link(side + "foot", side + "legroll")
        link(side + "toebase", side + "foot")

        # Hand: hand -> 5 digit bases -> 3 phalanges each.
        hand = side + "hand"
        for digit in ("ring", "pinky", "middle", "index", "thumb"):
            base = hand + digit
            link(base, hand)
            link(base + "1", base)
            link(base + "2", base + "1")
            link(base + "3", base + "2")

    # Attachments.
    link("camera", "head")
    link("headcutscene", "head")
    link("weapon", "righthand")
    link("launcher", "lefthand")
    for slot in ("backpack", "backwpnl", "backwpnr", "buttpack"):
        link("slot" + slot, "spine3")

    # Face / head dressing.  Everything below hangs off `head` unless stated.
    face_head = (
        "chin", "corr", "foreheadl", "foreheadm", "foreheadr",
        "eyeleft", "eyeright", "nosetip", "nosel", "noser",
        "earl", "earr", "jaw", "facehub", "faceeyelids", "facetongue",
    )
    for c in face_head:
        link(c, "head")

    for side in ("l", "r"):
        link("neck" + side, "neck")
        link("cheek" + side, "head")
        for part in ("b", "f", "m"):
            link("cheek" + side + part, "cheek" + side)
            link("zig" + side + part, "head")
        link("eyebrow" + side + "m", "head")
        link("eyebrow" + side + "b", "eyebrow" + side + "m")
        link("eyebrow" + side + "f", "eyebrow" + side + "m")
        link("jaw" + side + "m", "jaw")
        for part in ("f", "s"):
            link("jaw" + side + part, "jaw" + side + "m")

    link("eyeupl", "head")
    link("eyeupr", "head")
    link("eyelwl", "eyeupl")
    link("eyelwr", "eyeupl")
    link("lipupm", "head")
    link("liplwm", "head")
    for side in ("l", "r"):
        for part in ("b", "f"):
            link("lipup" + side + part, "lipupm")
            link("liplw" + side + part, "liplwm")
    link("tonguem", "facetongue")
    link("tongueb", "tonguem")
    link("tonguef", "tonguem")

    link("facebrowmiddle", "facehub")
    for side, word in (("l", "left"), ("r", "right")):
        link("facebrowfront" + side, "facebrowmiddle")
        link("facebrowside" + side, "facebrowmiddle")
        link("faceeyelidupper" + side, "facehub")
        link("faceeyelidlower" + side, "facehub")
        link("facecheekfront" + side, "facehub")
        link("facecheekside" + side, "facehub")
        link("facecheekupper" + side, "facehub")
        link("facechop" + side, "facehub")
        link("facecorner" + side, "facehub")
        link("facelipupper" + side, "facehub")
        link("faceliplower" + side, "facehub")
        link("facenostril" + side, "facehub")
    link("facechin", "facehub")
    link("facejawbone", "facehub")
    link("facejowl", "facehub")
    link("faceforehead", "facehub")

    return r


RULES = build_rules()


def key(name):
    return "".join(ch for ch in name.lower() if ch.isalnum())


def solve_parents(bones, rest_world):
    """Rule-first hierarchy, nearest-neighbour fallback, always a tree."""
    n = len(bones)
    by_key = collections.defaultdict(list)
    for i, b in enumerate(bones):
        by_key[key(b)].append(i)
    # Canonical index for each rule key (first match wins).
    canon = {k: v[0] for k, v in by_key.items()}

    root = canon.get("pelvis", canon.get("hips", canon.get("spine", 0)))

    parent = [None] * n
    assigned = set()

    # 1. Rule-driven links, BFS from the root so order never matters.
    children = collections.defaultdict(list)
    for i, b in enumerate(bones):
        k = key(b)
        pk = RULES.get(k)
        if pk is None:
            continue
        # Skip the self/root case (e.g. `pelvis -> pelvis`).
        pi = canon.get(pk)
        if pi is None or pi == i or pi == root:
            continue
        parent[i] = pi
        assigned.add(i)

    # 2. Anything still unparented: nearest bone in rest space, acyclic.
    def is_descendant(candidate, node):
        seen = 0
        while candidate is not None and seen <= n:
            if candidate == node:
                return True
            candidate = parent[candidate]
            seen += 1
        return False

    for i in range(n):
        if i == root or parent[i] is not None:
            continue
        best, best_d = root, float("inf")
        for j in range(n):
            if j == i:
                continue
            d = math.dist(rest_world[i], rest_world[j])
            if d < best_d and not is_descendant(j, i):
                best, best_d = j, d
        parent[i] = best
        assigned.add(i)

    for i in range(n):
        if parent[i] is not None:
            children[parent[i]].append(i)

    # Break any cycle introduced by step 2 by re-pointing at the root.
    for i in range(n):
        seen, cur = set(), i
        while cur is not None:
            if cur in seen:
                parent[i] = root
                break
            seen.add(cur)
            cur = parent[cur]

    return parent, root, children



def anim_filename(source_rel):
    """Unique per source clip.

    `Source/adfrc_mag58/anim/mag58.json` and
    `Workshop/ADF_Weapons/adfrc_mag58/anim/mag58.json` share a rig *and* a
    basename, so a plain basename silently overwrites one of the pair.
    """
    import hashlib
    stem = os.path.splitext(os.path.basename(source_rel))[0]
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in stem)
    tag = hashlib.sha1(source_rel.encode("utf-8")).hexdigest()[:6]
    return "%s__%s.json" % (safe, tag)


def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vec_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vec_cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def vec_norm(a):
    n = math.sqrt(vec_dot(a, a))
    return (a[0] / n, a[1] / n, a[2] / n) if n else (0.0, 0.0, 1.0)


def orthonormalise(flat):
    """Gram-Schmidt a 3x3 row-major matrix so it is a valid rotation."""
    r0 = vec_norm(tuple(flat[0:3]))
    r1 = vec_sub(tuple(flat[3:6]), tuple(vec_dot(tuple(flat[3:6]), r0) * c for c in r0))
    r1 = vec_norm(r1)
    r2 = vec_cross(r0, r1)
    return (list(r0), list(r1), list(r2))


def rig_key(bones):
    """Readable but collision-free: first bones, count, and a short hash.

    Two rigs share a bone count and a common prefix (`hips_spine_weapon_..._69b`
    appears twice with different bone sets), so the readable part alone is not
    a safe directory name.
    """
    import hashlib
    safe = "-".join(bones[:5]).lower()
    safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in safe)
    digest = hashlib.sha1("\x00".join(bones).encode("utf-8")).hexdigest()[:6]
    return "%s_%db_%s" % (safe, len(bones), digest)


def main():
    files = [f for f in sorted(glob.glob(os.path.join(EX, "**", "*.json"), recursive=True))
             if os.path.basename(os.path.dirname(f)) != "Rig"]
    print("decoded clips: %d" % len(files))

    groups = collections.defaultdict(list)
    for p in files:
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        groups[tuple(d["bones"])].append((p, d))
    print("distinct rigs: %d" % len(groups))

    os.makedirs(RIG_DIR, exist_ok=True)
    index = {}
    all_long = []

    for bones, clips in groups.items():
        n = len(bones)
        ref_path, ref = max(clips, key=lambda c: len(c[1]["frames"]))
        frame0 = ref["frames"][0]
        absolute = frame_is_absolute(frame0)

        if absolute:
            wm0, wp0 = [], []
            for b in frame0:
                r, p = world_from_absolute(b["m"])
                wm0.append(r)
                wp0.append(p)
        else:
            # Seed with a chain so world poses are roughly right, then solve.
            seed = [None] + [i - 1 for i in range(1, n)]
            wm0, wp0 = world_from_local(frame0, seed)

        parent, root, children = solve_parents(bones, wp0)

        # Frame 0 of an arbitrary clip is a *pose*, not a rest pose - a raised
        # arm reads as a 1.3 m "shoulder link". Average the world position of
        # every bone over every frame of every clip on the rig to get a neutral
        # skeleton, then re-derive locals against it.
        if absolute:
            acc = [[0.0, 0.0, 0.0] for _ in range(n)]
            racc = [[0.0] * 9 for _ in range(n)]
            cnt = 0
            for _p, d in clips:
                for fr in d["frames"]:
                    for i, b in enumerate(fr):
                        r, q = world_from_absolute(b["m"])
                        for k in range(3):
                            acc[i][k] += q[k]
                            for j in range(3):
                                racc[i][k * 3 + j] += r[k][j]
                    cnt += 1
            wp0 = [tuple(c / max(cnt, 1) for c in v) for v in acc]
            rot0 = [orthonormalise([c / max(cnt, 1) for c in v]) for v in racc]
        else:
            acc = [[0.0, 0.0, 0.0] for _ in range(n)]
            racc = [[0.0] * 9 for _ in range(n)]
            cnt = 0
            for _p, d in clips:
                for fr in d["frames"]:
                    wfr_m, wfr = world_from_local(fr, parent)
                    for i in range(n):
                        for k in range(3):
                            acc[i][k] += wfr[i][k]
                            for j in range(3):
                                racc[i][k * 3 + j] += wfr_m[i][k][j]
                    cnt += 1
            wp0 = [tuple(c / max(cnt, 1) for c in v) for v in acc]
            rot0 = [orthonormalise([c / max(cnt, 1) for c in v]) for v in racc]

        depth = [0] * n
        for i in range(n):
            d, p, g = 0, parent[i], 0
            while p is not None and g <= n:
                d += 1
                p = parent[p]
                g += 1
            depth[i] = d
        links = [math.dist(wp0[i], wp0[parent[i]])
                 for i in range(n) if parent[i] is not None]
        long_links = [(bones[i], bones[parent[i]], round(d, 3))
                      for i in range(n) if parent[i] is not None
                      and (d := math.dist(wp0[i], wp0[parent[i]])) > MAX_LINK]

        key_ = rig_key(bones)
        os.makedirs(os.path.join(RIG_DIR, key_), exist_ok=True)
        with open(os.path.join(RIG_DIR, key_ + ".json"), "w", encoding="utf-8") as fh:
            json.dump({
                "schema": "adfrc-rig/1",
                "rig": key_,
                "bone_count": n,
                "root": bones[root],
                "bones": list(bones),
                "parents": parent,
                "children": {bones[k]: [bones[c] for c in v] for k, v in children.items()},
                "rest_world": [[round(c, 5) for c in p] for p in wp0],
                "rest_rot": [[round(c, 6) for row in r for c in row] for r in rot0],
                "reference_clip": os.path.relpath(ref_path, EX).replace("\\", "/"),
                "clip_count": len(clips),
                "max_depth": max(depth),
                "max_link": round(max(links), 4) if links else 0.0,
                "links_over_threshold": long_links,
                "hierarchy_source": "BME naming rules + acyclic nearest-neighbour fallback",
            }, fh, indent=1)

        for p, d in clips:
            rel = os.path.relpath(p, EX).replace("\\", "/")
            frames = d["frames"]
            out_frames = []
            for fr in frames:
                if frame_is_absolute(fr):
                    wm, wp = [], []
                    for b in fr:
                        r, q = world_from_absolute(b["m"])
                        wm.append(r)
                        wp.append(q)
                else:
                    wm, wp = world_from_local(fr, parent)
                lm, lp = local_from_world(wm, wp, parent)
                out_frames.append([
                    {"q": quat_from_mat(lm[i]), "p": [round(c, 5) for c in lp[i]]}
                    for i in range(n)
                ])
            with open(os.path.join(RIG_DIR, key_, anim_filename(rel)), "w",
                      encoding="utf-8") as fh:
                json.dump({
                    "schema": "adfrc-anim-local/1",
                    "rig": key_,
                    "clip": os.path.splitext(os.path.basename(p))[0],
                    "source": rel,
                    "source_format": d.get("format", ""),
                    "bone_count": n,
                    "frames": out_frames,
                    "phases": d.get("phases", []),
                }, fh)
            ph = d.get("phases") or []
            index[rel] = {
                "rig": key_,
                "rig_file": "Rig/%s.json" % key_,
                "local_anim": "Rig/%s/%s" % (key_, anim_filename(rel)),
                "frames": len(frames),
                "absolute_source": absolute,
                "phase_start": ph[0] if ph else 0.0,
                "phase_end": ph[-1] if ph else 0.0,
            }

        all_long.extend([(key_, *x) for x in long_links])
        print("  %-42s bones=%3d clips=%3d root=%-10s depth=%2d max=%.2f over=%d"
              % (key_, n, len(clips), bones[root], max(depth),
                 max(links) if links else 0, len(long_links)))

    with open(os.path.join(RIG_DIR, "_rig_index.json"), "w", encoding="utf-8") as fh:
        json.dump({"schema": "adfrc-rig-index/1", "rig_count": len(groups),
                   "clip_count": len(index), "clips": index}, fh, indent=1)

    print("\nrigs: %d   clips: %d" % (len(groups), len(index)))
    if all_long:
        print("links over %.2fm (review):" % MAX_LINK)
        for r, c, p, d in sorted(all_long, key=lambda x: -x[3])[:20]:
            print("   %-38s %-20s -> %-20s %.2fm" % (r, c, p, d))
    print("-> %s" % RIG_DIR)


if __name__ == "__main__":
    main()
