#!/usr/bin/env python3
"""Decode Arma .rtm animations (binarised BMTR v3/4/5 and plain RTM_0101)
to readable JSON, next to each .rtm under ADF_Extracted\\Animations\\.

Format reference: Bohemia wiki (Rtm / Rtm Binarised File Format) as
implemented by MrClock8163/Arma3ObjectBuilder io/data_rtm.py. The LZO1X
decompressor is vendored from its io/compression.py (LZO stream format per
Linux kernel docs/staging/lzo + FFmpeg libavutil/lzo.c).
"""
import io
import json
import os
import struct
import sys

EX = r"E:\SouthernSpear\Content\Sourced\ADF_Extracted\Animations"


# --- vendored from Arma3ObjectBuilder io/compression.py (trimmed) ---
class LZO_Error(Exception):
    pass


def lzo1x_decompress(file, expected):
    state = 0
    output = bytearray()
    struct_le16 = struct.Struct("<H")

    def check_free_space(length):
        if expected - len(output) < length:
            raise LZO_Error("output overrun")

    def copy_match(distance, length):
        check_free_space(length)
        start = len(output) - distance
        output.extend(output[start:] * (length // distance))
        output.extend(output[start:(start + (length % distance))])

    def get_length(x, mask):
        length = x & mask
        if not length:
            while True:
                x = file.read(1)[0]
                if x:
                    break
                length += 255
            length += mask + x
        return length

    x = file.read(1)[0]
    if x > 17:
        length = x - 17
        check_free_space(length)
        output.extend(file.read(length))
        state = min(4, length)
        x = file.read(1)[0]
    while True:
        if x <= 15:
            if not state:
                length = 3 + get_length(x, 15)
                check_free_space(length)
                output.extend(file.read(length))
                state = 4
            elif state < 4:
                length = 2
                state = x & 3
                distance = (file.read(1)[0] << 2) + (x >> 2) + 1
                copy_match(distance, length)
                check_free_space(state)
                output.extend(file.read(state))
            elif state == 4:
                length = 3
                state = x & 3
                distance = (file.read(1)[0] << 2) + (x >> 2) + 2049
                copy_match(distance, length)
                check_free_space(state)
                output.extend(file.read(state))
        elif x > 127:
            state = x & 3
            length = 5 + ((x >> 5) & 3)
            distance = (file.read(1)[0] << 3) + ((x >> 2) & 7) + 1
            copy_match(distance, length)
            check_free_space(state)
            output.extend(file.read(state))
        elif x > 63:
            state = x & 3
            length = 3 + ((x >> 5) & 1)
            distance = (file.read(1)[0] << 3) + ((x >> 2) & 7) + 1
            copy_match(distance, length)
            check_free_space(state)
            output.extend(file.read(state))
        elif x > 31:
            length = 2 + get_length(x, 31)
            extra = struct_le16.unpack(file.read(2))[0]
            distance = (extra >> 2) + 1
            state = extra & 3
            copy_match(distance, length)
            check_free_space(state)
            output.extend(file.read(state))
        else:
            length = 2 + get_length(x, 7)
            extra = struct_le16.unpack(file.read(2))[0]
            distance = 16384 + ((x & 8) << 11) + (extra >> 2)
            state = extra & 3
            if distance == 16384:
                if length != 3:
                    raise LZO_Error("invalid end of stream")
                break
            copy_match(distance, length)
            check_free_space(state)
            output.extend(file.read(state))
        x = file.read(1)[0]
    if expected - len(output):
        raise LZO_Error("short output (expected %d got %d)" % (expected, len(output)))
    return file.tell(), output


# --- helpers ---
def u8(f):
    return f.read(1)[0]


def u32(f):
    return struct.unpack("<I", f.read(4))[0]


def f32(f):
    return struct.unpack("<f", f.read(4))[0]


def asciiz(f):
    out = bytearray()
    while True:
        b = f.read(1)
        if not b or b == b"\x00":
            break
        out += b
    return out.decode("latin-1")


def r3(v):
    return round(v, 5)


def read_transform_raw(f):
    qs = struct.unpack("<4h", f.read(8))
    halves = struct.unpack("<3e", f.read(6))
    qx, qz, qy, qw = [s / 16384 for s in qs]
    x, z, y = halves
    return {
        "q": [r3(qx), r3(qy), r3(qz), r3(qw)],
        "p": [r3(-x), r3(-y), r3(z)],
        "raw_q": list(qs),
        "raw_p": [r3(h) for h in halves],
    }


def parse_bmtr(f, version, props_variant=0, bools_from_v4=False):
    """props_variant: 0 = props block for v>=4 (observed on ADFRC v4 files),
    1 = props block only for v>4 (A3OB reading), 2 = no block for v4.
    bools_from_v4: read per-block compression bools from v4 (A3OB: v>4 only)."""
    if version not in (3, 4, 5):
        raise ValueError("unsupported BMTR version %d" % version)
    f.read(4)  # consume "BMTR" signature
    got = u32(f)
    if got != version:
        raise ValueError("version mismatch")
    f.read(1)
    motion = [f32(f), f32(f), f32(f)]
    count_frames = u32(f)
    f.read(4)
    count_bones = u32(f)
    if u32(f) != count_bones:
        raise ValueError("bone count mismatch")
    bones = [asciiz(f) for _ in range(count_bones)]
    props = []
    has_props = (version >= 4) if props_variant == 0 else (version > 4)
    if version == 4 and props_variant == 2:
        has_props = False
    if has_props:
        f.read(4)
        for _ in range(u32(f)):
            f.read(4)
            name = asciiz(f)
            phase = f32(f)
            props.append([r3(phase), name, asciiz(f)])
    if u32(f) != count_frames:
        raise ValueError("frame count mismatch")

    # phases
    expected = count_frames * 4
    compressed = expected >= 1024
    if version > 4 or (bools_from_v4 and version == 4):
        compressed = u8(f) != 0
    if compressed:
        _, buf = lzo1x_decompress(f, expected)
        phases = list(struct.unpack("<%df" % count_frames, bytes(buf)))
    else:
        phases = [f32(f) for _ in range(count_frames)]

    # frames
    frames = []
    for _ in range(count_frames):
        n = u32(f)
        expected = n * 14
        compressed = expected >= 1024
        if version > 4 or (bools_from_v4 and version == 4):
            compressed = u8(f) != 0
        if compressed:
            _, buf = lzo1x_decompress(f, expected)
            src = io.BytesIO(bytes(buf))
            transforms = [read_transform_raw(src) for _ in range(n)]
            if src.read():
                raise ValueError("trailing bytes in decompressed frame")
        else:
            transforms = [read_transform_raw(f) for _ in range(n)]
        frames.append(transforms)
    if f.read():
        raise ValueError("trailing data after frames")
    return {
        "format": "BMTR v%d (binarised RTM)" % version,
        "motion": [r3(v) for v in motion],
        "bones": bones,
        "props": props,
        "phases": [r3(p) for p in phases],
        "frames": frames,
    }


def parse_rtm0101(f):
    f.seek(4)  # consumed "RTM_"
    if f.read(4) != b"0101":
        f.seek(0)
        if f.read(8) != b"RTM_0101":
            raise ValueError("not RTM_0101")
    motion = [f32(f), f32(f), f32(f)]
    count_frames = u32(f)
    count_bones = u32(f)
    bones = [f.read(32).split(b"\x00")[0].decode("latin-1") for _ in range(count_bones)]
    frames, phases = [], []
    for _ in range(count_frames):
        phases.append(f32(f))
        per_bone = []
        for _ in range(count_bones):
            bone = f.read(32).split(b"\x00")[0].decode("latin-1")
            m = struct.unpack("<12f", f.read(48))
            # stored 3x4 (row-major components with axis swaps); export flat
            per_bone.append({"bone": bone, "m": [r3(v) for v in m]})
        frames.append(per_bone)
    if f.read():
        raise ValueError("trailing data")
    return {
        "format": "RTM_0101 (plain RTM)",
        "motion": [r3(v) for v in motion],
        "bones": bones,
        "props": [],
        "phases": [r3(p) for p in phases],
        "frames": frames,
        "note": "plain RTM: frames store absolute 3x4 matrices per bone "
                "(12 floats, Arma axis layout), not quaternions",
    }


def convert(path):
    with open(path, "rb") as fh:
        data = fh.read()
    f = io.BytesIO(data)
    sig = f.read(4)
    f.seek(0)
    if sig == b"BMTR":
        version = struct.unpack("<I", data[4:8])[0]
        result = None
        last_err = None
        for props_variant, bools_v4 in ((0, False), (0, True), (1, False),
                                        (1, True), (2, False), (2, True)):
            try:
                f.seek(0)
                result = parse_bmtr(f, version, props_variant, bools_v4)
                break
            except Exception as ex:  # noqa: BLE001
                last_err = ex
        if result is None:
            raise last_err
    elif sig == b"RTM_":
        result = parse_rtm0101(f)
    else:
        raise ValueError("unknown signature %r" % sig)
    result["source"] = os.path.basename(path)
    result["notes"] = [
        "BMTR transforms are LOCAL: each bone is a rotation about its own rest joint, relative to "
        "its parent - not a parent-relative bone offset, so p = J - R J for that bone's rest joint J "
        "(Session 057). Multiply up the hierarchy for world-space; plain RTM matrices are absolute.",
        "q = quaternion [x,y,z,w] (component order remapped from file storage) and stored with x and "
        "y conjugated, so the rotation it means is (-x, -y, z, w). p = local position (A3OB axis "
        "convention).",
        "raw_q = signed int16 as stored (divide by 16384), raw_p = half floats as stored.",
        "phases[] = normalised frame times (0..1), frames[i] maps bone -> transform.",
    ]
    return result


def main():
    n = ok = 0
    for r, _d, fs in os.walk(EX):
        for name in fs:
            if not name.lower().endswith(".rtm"):
                continue
            src = os.path.join(r, name)
            dst = os.path.splitext(src)[0] + ".json"
            n += 1
            if os.path.exists(dst):
                ok += 1
                continue
            try:
                result = convert(src)
                with open(dst, "w", encoding="utf-8") as fh:
                    json.dump(result, fh, separators=(",", ":"))
                ok += 1
            except Exception as ex:  # noqa: BLE001
                print("FAIL", os.path.relpath(src, EX), "->", ex)
    print(f"parsed {ok}/{n} rtm files")


if __name__ == "__main__":
    sys.exit(0 if main() is None else 0)
