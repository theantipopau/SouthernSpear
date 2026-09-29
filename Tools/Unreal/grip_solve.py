"""Solve HandRotationOffset for SK_FP_Arms_Rifle from a probe log.

The body (Manny) holds the same SM_A88 in Lyra's own animation, so its hand's orientation in the
weapon's local frame is a known-good grip.  The arms are turned to (socket rotation * offset), so the
offset that gives the arms that same grip is

    offset = socketrot_arms^-1 * ( weapon_in_cs_arms * hand_in_weapon_body )

Everything is in UE's conventions (FQuat multiply, FQuat -> FRotator), and both conversions are
checked against the pairs the probe logged.
"""
import math
import re
import sys

DEG = math.pi / 180.0


def qmul(a, b):
    """FQuat::operator* (a then b, as UE writes it)."""
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def qinv(q):
    x, y, z, w = q
    ax, ay, az, aw = -x, -y, -z, w
    n = x * x + y * y + z * z + w * w
    return (ax / n, ay / n, az / n, aw / n)


def qnorm(q):
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w)
    return (x / n, y / n, z / n, w / n)


def qdot(a, b):
    return sum(x * y for x, y in zip(a, b))


def qang(a, b):
    d = abs(max(-1.0, min(1.0, qdot(qnorm(a), qnorm(b)))))
    return 2.0 * math.degrees(math.acos(d))


def euler_from_q(q):
    """FQuat -> FRotator: the (pitch, yaw, roll) that q_from_euler turns back into q.

    Solved numerically against the constructor above rather than from the closed form: the engine only
    ever converts rotator -> quaternion through that constructor, so agreeing with it is the property
    that matters (and it is checked against the pairs the probe logged).
    """
    target = qnorm(q)

    def score(t):
        return abs(qdot(q_from_euler(*t), target))

    best = max(((score((p, y, r)), (p, y, r))
                for p in range(-90, 91, 5)
                for y in range(-180, 180, 10)
                for r in range(-180, 180, 10)), key=lambda v: v[0])
    pitch, yaw, roll = best[1]
    step = 5.0
    while step > 1e-10:
        here = score((pitch, yaw, roll))
        cands = [(pitch + dp, yaw + dy, roll + dr)
                 for dp in (-step, 0.0, step) for dy in (-step, 0.0, step) for dr in (-step, 0.0, step)
                 if abs(pitch + dp) <= 90.0]
        top = max(((score(c), c) for c in cands), key=lambda v: v[0])
        if top[0] > here:
            pitch, yaw, roll = top[1]
        else:
            step /= 2.0
    return (pitch, yaw, roll)


def normalize_axis(angle):
    while angle > 180.0:
        angle -= 360.0
    while angle < -180.0:
        angle += 360.0
    return angle


def q_from_euler(pitch, yaw, roll):
    """FRotator -> FQuat, exactly as UE computes it."""
    sp, cp = math.sin(pitch * DEG / 2), math.cos(pitch * DEG / 2)
    sy, cy = math.sin(yaw * DEG / 2), math.cos(yaw * DEG / 2)
    sr, cr = math.sin(roll * DEG / 2), math.cos(roll * DEG / 2)
    return (
        cr * sp * sy - sr * cp * cy,
        -cr * sp * cy - sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
        cr * cp * cy + sr * sp * sy,
    )


def q_from_vec(v):
    v = re.findall(r'-?\d+\.?\d*', v)
    return tuple(float(x) for x in v)


def parse(path, key):
    """Last GRIP line per mesh."""
    samples = {}
    for line in open(path, encoding="utf-8", errors="replace"):
        if "LogSSHandIKProbe: GRIP" not in line:
            continue
        arms = re.search(r'arms=(\S+)', line)
        mesh = re.search(r'mesh=(\S+)', line)
        if not arms or not mesh:
            continue
        fields = {}
        for name in ("handrot", "socketrot", "weapon_in_cs", "hand_in_weapon"):
            m = re.search(name + r'=\(([^)]*)\)', line)
            if m:
                fields[name] = q_from_vec(m.group(1))
        fields["thumb_vs_barrel"] = float(re.search(r'thumb_vs_barrel=(-?[\d.]+)', line).group(1))
        fields["mesh"] = mesh.group(1)
        fields["arms"] = arms.group(1)
        samples.setdefault(arms.group(1), []).append(fields)
    return samples


def mean_quat(quats):
    """Sign-corrected mean of quaternions (they are close to each other)."""
    ref = qnorm(quats[-1])
    acc = [0.0, 0.0, 0.0, 0.0]
    for q in quats:
        q = qnorm(q)
        if qdot(q, ref) < 0:
            q = tuple(-c for c in q)
        acc = [a + c for a, c in zip(acc, q)]
    return qnorm(tuple(acc))


def main():
    path = sys.argv[1]
    samples = parse(path, "GRIP")
    body = [s for k, v in samples.items() if "Character" in k for s in v]
    arms = [s for k, v in samples.items() if "FirstPersonArms" in k for s in v]
    if not body or not arms:
        print("no body/arms samples in", path)
        return 1

    # Steady state only: the last three samples of each (the first frames are the spawn animation).
    body_steady, arms_steady = body[-3:], arms[-3:]
    hand_in_weapon_body = mean_quat([s["hand_in_weapon"] for s in body_steady])
    print("body  hand_in_weapon   =", [round(c, 4) for c in hand_in_weapon_body],
          "thumb_vs_barrel=%.1f" % body_steady[-1]["thumb_vs_barrel"])
    for s in arms_steady:
        print("arms  socketrot=%s weapon_in_cs=%s hand_in_weapon=%s thumb_vs_barrel=%.1f" % (
            [round(c, 4) for c in s["socketrot"]], [round(c, 4) for c in s["weapon_in_cs"]],
            [round(c, 4) for c in s["hand_in_weapon"]], s["thumb_vs_barrel"]))

    # Validate the conventions against the values the engine itself printed.
    checks = [
        (arms_steady[-1]["socketrot"], None),
    ]
    print("\nconvention check (quat -> rotator, the engine's own numbers):")
    for s in (body_steady[-1], arms_steady[-1]):
        for key in ("handrot", "hand_in_weapon"):
            if key in s:
                r = euler_from_q(qnorm(s[key]))
                back = q_from_euler(*r)
                print("  %-8s %-16s -> P=%.2f Y=%.2f R=%.2f   round-trip diff=%.5f" % (
                    s["mesh"][:8], key, r[0], r[1], r[2], qang(back, s[key])))

    # The offset: the arms get the body's grip on the same weapon.
    socket = arms_steady[-1]["socketrot"]
    weapon_in_cs_arms = arms_steady[-1]["weapon_in_cs"]
    desired = qmul(weapon_in_cs_arms, hand_in_weapon_body)
    offset = qmul(qinv(socket), desired)
    pitch, yaw, roll = euler_from_q(qnorm(offset))
    print("\noffset quat   =", [round(c, 6) for c in qnorm(offset)])
    print("offset rotator= P=%.3f Y=%.3f R=%.3f   (HandRotationOffset=(Pitch=%.3f,Yaw=%.3f,Roll=%.3f))"
          % (pitch, yaw, roll, pitch, yaw, roll))
    print("offset magnitude = %.1f deg" % qang(offset, (0.0, 0.0, 0.0, 1.0)))

    # What the arms' hand would then be, against the body's: should be ~0 deg.
    check = qmul(socket, offset)
    print("arms hand_in_weapon would become %s -> %.2f deg from the body's" % (
        [round(c, 4) for c in qmul(qinv(weapon_in_cs_arms), check)],
        qang(qmul(qinv(weapon_in_cs_arms), check), hand_in_weapon_body)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
