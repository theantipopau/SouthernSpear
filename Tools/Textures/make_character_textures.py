#!/usr/bin/env python
"""Southern Spear - original character textures (ADR-016, ADR-020, ADR-021).

Authors the Southern Spear camouflage and gear fabric used on the licensed
third-party soldier bodies (Fab packs, L-0016). Everything here is generated
from noise, so the pattern is original work: it is NOT traced from, sampled
from, or derived from any real-world camouflage. ADR-016 requires CMECU to be
an original pattern and forbids reproducing AMCU, commercial MultiCam or the
ADFRC/Auscam material in Content/Sourced/ADF_Extracted.

Outputs PNGs (base colour / normal / ORM) into Art/Characters/Textures/.
Run:  python Tools/Textures/make_character_textures.py
"""

import json
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "Art", "Characters", "Textures")

CAME = 2048   # camouflage sets
FABRIC = 1024  # solid gear fabric

# ---------------------------------------------------------------- noise utils


def value_noise(shape, cells, rng):
    """Bilinear value noise with smoothstep interpolation. No scipy needed."""
    g = rng.random((cells, cells)).astype(np.float32)
    h, w = shape
    ys = np.linspace(0, cells - 1, h, dtype=np.float32)
    xs = np.linspace(0, cells - 1, w, dtype=np.float32)
    y0 = np.floor(ys).astype(np.int32)
    x0 = np.floor(xs).astype(np.int32)
    y1 = np.minimum(y0 + 1, cells - 1)
    x1 = np.minimum(x0 + 1, cells - 1)
    fy, fx = ys - y0, xs - x0
    sy = (fy * fy * (3.0 - 2.0 * fy))[:, None]
    sx = (fx * fx * (3.0 - 2.0 * fx))[None, :]
    g00 = g[np.ix_(y0, x0)]
    g01 = g[np.ix_(y0, x1)]
    g10 = g[np.ix_(y1, x0)]
    g11 = g[np.ix_(y1, x1)]
    top = g00 + (g01 - g00) * sx
    bot = g10 + (g11 - g10) * sx
    return top + (bot - top) * sy


def fbm(shape, cells, octaves, rng, gain=0.5):
    total = np.zeros(shape, dtype=np.float32)
    amp, norm, c = 1.0, 0.0, cells
    for _ in range(octaves):
        total += amp * value_noise(shape, c, rng)
        norm += amp
        amp *= gain
        c *= 2
    return total / norm


def warp(shape, rng, strength=0.35, cells=4):
    """Domain warp so pattern blobs are organic rather than round."""
    h, w = shape
    wx = (fbm(shape, cells, 3, rng) - 0.5) * strength
    wy = (fbm(shape, cells, 3, rng) - 0.5) * strength
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    yy = (yy + wy * h) % h
    xx = (xx + wx * w) % w
    return yy.astype(np.int32), xx.astype(np.int32)


def normalise(a):
    lo, hi = float(a.min()), float(a.max())
    return (a - lo) / (hi - lo) if hi > lo else np.zeros_like(a)


# ------------------------------------------------------------- palette + camo


def camo(size, tones, thresholds, seed, softness=0.032):
    """Build a soft-banded disruptive pattern from a noise field.

    Soft transitions keep it looking dyed/printed rather than posterised.
    """
    rng = np.random.default_rng(seed)
    shape = (size, size)
    base = fbm(shape, 4, 6, rng)
    wy, wx = warp(shape, rng)
    n = normalise(0.65 * base + 0.35 * base[wy, wx])
    n = normalise((n - 0.5) * 1.35 + 0.5)  # firm up the contrast

    rgb = np.zeros(shape + (3,), dtype=np.float32)
    cols = [np.asarray(t, dtype=np.float32) for t in tones]
    sig = lambda x: 1.0 / (1.0 + np.exp(-x))
    weights = []
    for i, col in enumerate(cols):
        lo = thresholds[i - 1] if i else -1.0
        hi = thresholds[i] if i < len(thresholds) else 2.0
        # Band i is active between its lower and upper threshold, with a soft
        # shoulder of `softness` so the edges read as dyed rather than posterised.
        w = sig((n - lo) / softness) * (1.0 - sig((n - hi) / softness))
        weights.append(w)
        rgb += col * w[..., None]
    rgb /= np.maximum(sum(weights), 1e-5)[..., None]

    # Fibre grain and large-scale sun/dirt variation.
    grain = fbm(shape, 128, 3, rng)
    dirt = fbm(shape, 3, 4, rng)
    rgb *= (0.94 + 0.12 * grain)[..., None]
    rgb *= (0.90 + 0.24 * dirt)[..., None]

    # Slight dirt line where bands meet.
    edges = np.zeros(shape, dtype=np.float32)
    for t in thresholds:
        edges += np.abs(1.0 / (1.0 + np.exp(-(n - t) / (softness * 0.6))) - 0.5)
    rgb *= (1.0 - 0.16 * np.clip(edges * 2.0, 0, 1))[..., None]
    return np.clip(rgb, 0.0, 1.0)


def weave_normal(size, seed, scale=220, depth=0.55):
    """Twill-ish fabric micro-normal: a height field converted to a normal map."""
    rng = np.random.default_rng(seed)
    h, w = size, size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    s = 2.0 * np.pi * scale / max(h, w)
    warp_y = np.sin(yy * s)
    weft_x = np.sin(xx * s)
    diag = np.sin((xx + yy) * s)
    height = 0.45 * warp_y + 0.45 * weft_x + 0.10 * diag
    height += 0.20 * (fbm((h, w), 256, 2, rng) - 0.5)      # fibre noise
    height = normalise(height) * depth

    gy, gx = np.gradient(height.astype(np.float32))
    strength = 4.0
    nx, ny, nz = -gx * strength, -gy * strength, np.ones_like(height)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.clip(np.stack([nx / ln, ny / ln, nz / ln], axis=-1) * 0.5 + 0.5, 0, 1)


def orm_map(size, seed, roughness=0.86, variance=0.10, ao=0.06):
    """R = ambient occlusion, G = roughness, B = metallic (always 0)."""
    rng = np.random.default_rng(seed)
    h, w = size, size
    r = np.clip(roughness + variance * (fbm((h, w), 64, 4, rng) - 0.5) * 2.0, 0.0, 1.0)
    a = np.clip(1.0 - ao * (1.0 - fbm((h, w), 16, 3, rng)), 0.0, 1.0)
    return np.stack([a, r, np.zeros((h, w), dtype=np.float32)], axis=-1)


# ------------------------------------------------------------------ palettes

# CMECU: sun-bleached dry-country ochre, pale dust, eucalypt grey-green,
# ironbark red-brown. Deliberately not AMCU or any commercial pattern.
CMECU_TONES = [
    (0.451, 0.376, 0.243),   # khaki base
    (0.588, 0.522, 0.376),   # pale dust
    (0.353, 0.373, 0.298),   # eucalypt grey-green
    (0.404, 0.286, 0.212),   # ironbark red-brown
]
CMECU_THRESH = [0.30, 0.52, 0.74]

# MAF: red-earth disruptive - ochre, rust, dark brown, muted burgundy, charcoal.
MAF_TONES = [
    (0.529, 0.388, 0.243),   # ochre
    (0.463, 0.259, 0.169),   # rust
    (0.318, 0.235, 0.180),   # dark brown
    (0.400, 0.220, 0.251),   # muted burgundy
    (0.259, 0.239, 0.220),   # charcoal
]
MAF_THRESH = [0.28, 0.46, 0.64, 0.80]

GEAR_TONE = (0.404, 0.357, 0.259)  # coyote / tan nylon
GEAR_DARK = (0.243, 0.227, 0.180)   # dark webbing for MAF kit


def solid_cloth(size, tone, seed, macro=0.05, grain=0.07):
    """Near-solid dyed fabric: one tone with fine grain and gentle wear.

    Deliberately not run through the camo banding, which made flat gear look
    stained and blotchy.
    """
    rng = np.random.default_rng(seed)
    shape = (size, size)
    col = np.asarray(tone, dtype=np.float32)
    rgb = np.ones(shape + (3,), dtype=np.float32) * col
    rgb *= (1.0 - grain * 0.5 + grain * fbm(shape, 256, 3, rng))[..., None]
    rgb *= (1.0 - macro * 0.5 + macro * fbm(shape, 6, 4, rng))[..., None]
    return np.clip(rgb, 0.0, 1.0)


def save(name, arr):
    img = Image.fromarray((np.clip(arr, 0, 1) * 255.0 + 0.5).astype(np.uint8))
    path = os.path.join(OUT, name)
    img.save(path, optimize=True)
    return {"file": name, "size": list(img.size), "bytes": os.path.getsize(path)}


def main():
    os.makedirs(OUT, exist_ok=True)
    written = []

    for tag, tones, thresh, seed in (
        ("CMECU", CMECU_TONES, CMECU_THRESH, 20260927),
        ("MAF", MAF_TONES, MAF_THRESH, 20260928),
    ):
        bc = camo(CAME, tones, thresh, seed)
        written.append(save("T_SS_%s_Camo_BC.png" % tag, bc))
        written.append(save("T_SS_%s_Camo_N.png" % tag, weave_normal(CAME, seed + 1)))
        written.append(save("T_SS_%s_Camo_ORM.png" % tag, orm_map(CAME, seed + 2)))

    for tag, tone, seed, macro in (
        ("Gear", GEAR_TONE, 4242, 0.05),
        ("GearDark", GEAR_DARK, 4343, 0.05),
    ):
        base = solid_cloth(FABRIC, tone, seed, macro=macro)
        written.append(save("T_SS_%s_BC.png" % tag, base))
        written.append(save("T_SS_%s_N.png" % tag, weave_normal(FABRIC, seed + 1, scale=300)))
        written.append(save("T_SS_%s_ORM.png" % tag, orm_map(FABRIC, seed + 2, roughness=0.72)))

    with open(os.path.join(ROOT, "Build", "character_textures.json"), "w") as fh:
        json.dump({"ok": True, "count": len(written), "files": written}, fh, indent=1)
    print("wrote %d textures to %s" % (len(written), OUT))


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "Build"), exist_ok=True)
    main()
