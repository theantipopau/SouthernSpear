#!/usr/bin/env python
# Southern Spear - ADFRC disruptive-pattern camo for the Quantum prototype (Session 058).
#
# Criterion 2 of the prototype is "ADFRC camouflage on the shirt and trousers". The previous
# attempt, Tools/Textures/make_g3_shirt_camo.py, was rejected on colour: its pattern generator
# invented greens that the ADF does not wear. So the palette here is not invented either - it is
# measured, by clustering the real Crye_G3_Shirt_DPC_co.png that ships in the ADFRC texture set
# (DPC = Disruptive Pattern Camouflage, the ADF's own pattern), and the tones it produces are
# printed and written to the report so the claim can be checked.
#
# The texture is TILEABLE and does not touch the vendor UV layout. make_maf_uniform.py bakes a
# pattern over a vendor sheet; that is the wrong tool for a second skin on somebody else's mesh,
# because a camo that has to line up with seams it does not own will always seam. A periodic
# pattern mapped through untouched vendor UVs cannot seam, and the per-garment scale difference
# is handled by a UV scalar on the material instance.
#
# Writes:
#   Art/Characters/ADF/T_ADFRC_DPC_camo.png
#   Build/adfrc_camo.json   (palette, tile-seam check, tone areas)
#
# Run: python Tools/Textures/make_adfrc_camo.py
import json
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOURCE_DPC = os.path.join(ROOT, "Art", "ADFRC", "Textures", "adfrc_uniforms", "data", "Crye_G3_Shirt_DPC_co.png")
OUT_PNG = os.path.join(ROOT, "Art", "Characters", "ADF", "T_ADFRC_DPC_camo.png")
REPORT = os.path.join(ROOT, "Build", "adfrc_camo.json")

SIZE = 2048
# Lattice cells across the sheet for the coarsest octave: the camo feature size.
BASE_PERIOD = 10
# Area each tone should occupy. Camo is mostly one mid tone with the others broken across it;
# even areas are the giveaway of a generated pattern.
TONE_AREAS = (0.44, 0.24, 0.21, 0.11)  # olive, brown, tan, light


def measure_palette(path, clusters=10):
    """Dominant sRGB tones of a source texture, by 5-bit quantised histogram."""
    image = np.asarray(Image.open(path).convert("RGB")).reshape(-1, 3).astype(np.float32)
    quantised = (image // 16).astype(np.int32)
    keys = quantised[:, 0] * 1024 + quantised[:, 1] * 32 + quantised[:, 2]
    unique, counts = np.unique(keys, return_counts=True)
    order = np.argsort(-counts)[:clusters]
    tones, weights = [], []
    for slot in order:
        mask = keys == unique[slot]
        tones.append(image[mask].mean(axis=0))
        weights.append(float(counts[slot]) / len(image))
    return np.array(tones), weights


def periodic_noise(height, width, period, rng):
    """Value noise on a wrapping lattice, so the result tiles exactly."""
    rows, cols = period
    lattice = rng.random((rows, cols))
    ys = np.linspace(0.0, rows, height, endpoint=False)
    xs = np.linspace(0.0, cols, width, endpoint=False)
    y0 = np.floor(ys).astype(np.int64) % rows
    x0 = np.floor(xs).astype(np.int64) % cols
    fy = (ys - np.floor(ys))[:, None]
    fx = (xs - np.floor(xs))[None, :]
    # Smoothstep, or the lattice shows through as a grid of straight edges.
    fy = fy * fy * (3.0 - 2.0 * fy)
    fx = fx * fx * (3.0 - 2.0 * fx)
    g00 = lattice[np.ix_(y0, x0)]
    g01 = lattice[np.ix_(y0, (x0 + 1) % cols)]
    g10 = lattice[np.ix_((y0 + 1) % rows, x0)]
    g11 = lattice[np.ix_((y0 + 1) % rows, (x0 + 1) % cols)]
    return (g00 * (1.0 - fx) * (1.0 - fy) + g01 * fx * (1.0 - fy)
            + g10 * (1.0 - fx) * fy + g11 * fx * fy)


def fractal(height, width, rng, base_period=8):
    """Four octaves; the coarsest sets the blob size, the finest breaks the edges.

    base_period is in lattice cells across the whole sheet. At 2 the blobs spanned a third
    of the sheet, which is a poster, not a camo print - tiled over a garment it gave two or
    three shapes. 8 puts the coarsest cell at a quarter of the sheet and the smallest
    feature at the scale a real DPC print breaks down to.
    """
    field = np.zeros((height, width), dtype=np.float32)
    amplitude = 1.0
    total = 0.0
    for octave in range(4):
        period = base_period * (2 ** octave)
        field += amplitude * periodic_noise(height, width, (period, period), rng)
        total += amplitude
        amplitude *= 0.5
    field /= total
    return (field - field.min()) / max(1e-6, (field.max() - field.min()))


def seam_score(image):
    """How much the left/right and top/bottom edges jump, against the interior average.

    A periodic generator makes this near zero by construction; measuring it anyway means a
    later change to the noise cannot quietly turn the sheet into a visible grid.
    """
    a = image.astype(np.float32)
    interior_x = float(np.abs(np.diff(a, axis=1)).mean())
    interior_y = float(np.abs(np.diff(a, axis=0)).mean())
    seam_x = float(np.abs(a[:, -1] - a[:, 0]).mean())
    seam_y = float(np.abs(a[-1, :] - a[0, :]).mean())
    return {
        "interior_step_x": interior_x,
        "interior_step_y": interior_y,
        "seam_step_x": seam_x,
        "seam_step_y": seam_y,
        "seam_ratio_x": seam_x / max(1e-6, interior_x),
        "seam_ratio_y": seam_y / max(1e-6, interior_y),
    }


def main():
    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)

    tones, weights = measure_palette(SOURCE_DPC)
    print("measured from {}".format(os.path.relpath(SOURCE_DPC, ROOT)))
    for tone, weight in zip(tones, weights):
        print("  srgb=({}, {}, {})  area={:.3f}".format(*tone.round().astype(int), weight))

    # Pick four tones out of the measured ones rather than blending new ones. Each pick is
    # scored against a different property and excluded from the next pick: scoring them
    # independently let "greenest" and "darkest" both land on the same cluster, which
    # silently shipped a two-tone pattern.
    def greenness(tones):
        return tones[:, 1] - (tones[:, 0] + tones[:, 2]) / 2.0

    def redness(tones):
        return tones[:, 0] - tones[:, 1]

    lightness = tones.mean(axis=1)
    claimed = set()

    def best(score, largest=True):
        ranked = sorted(range(len(tones)), key=lambda i: score[i], reverse=largest)
        for index in ranked:
            if index not in claimed:
                claimed.add(index)
                return index
        return ranked[0]

    chosen = [
        best(greenness(tones)),   # olive: the ADF green
        best(redness(tones)),     # brown: the red-shifted cluster
        best(lightness),          # tan: the lightest
        best(lightness, False),   # shadow: the dark anchor that gives the pattern depth
    ]
    palette = tones[chosen]
    names = ["olive", "brown", "tan", "shadow"]
    # Deliberately no renormalisation here. Stretching the measured tones to fill a range
    # is what turned this palette into a saturated yellow-green and an orange on the first
    # run; the ADF's own luminance relationships are the thing being reproduced.

    rng = np.random.default_rng(20260928)
    field = fractal(SIZE, SIZE, rng, BASE_PERIOD)

    # Warp the field so blob edges are leaf-shaped rather than round: a second, finer noise
    # displacing the lookup is the cheapest way to break the lattice's regularity. Kept
    # modest - too much and the shapes smear into each other and the pattern goes to mush.
    warp = fractal(SIZE, SIZE, np.random.default_rng(4711), BASE_PERIOD * 2) - 0.5
    field = np.clip(field + warp * 0.22, 0.0, 1.0)

    # Band by quantile, so the tone areas are the ones asked for rather than whatever the
    # noise distribution happened to give.
    edges = np.cumsum(TONE_AREAS)[:-1]
    cuts = np.quantile(field, edges)
    band = np.digitize(field, cuts)

    out = np.zeros((SIZE, SIZE, 3), dtype=np.float32)
    for index, colour in enumerate(palette):
        out[band == index] = colour

    # Fabric grain. Camo printed on cloth is never flat, and a perfectly flat sheet is the
    # other thing that makes a generated pattern look generated. It has to come off the same
    # wrapping lattice as the pattern: per-pixel white noise is not periodic, and it put a
    # visible step at the tile edge on the first run (seam ratio 1.30 against 1.0 for
    # invisible).
    grain_rng = np.random.default_rng(7)
    grain = (periodic_noise(SIZE, SIZE, (SIZE // 2, SIZE // 2), grain_rng) - 0.5) * 9.0
    out = np.clip(out + grain[:, :, None], 0.0, 255.0).astype(np.uint8)

    # A whisper of blur, to take the staircase off the band edges.
    image = Image.fromarray(out)
    try:
        from PIL import ImageFilter
        image = image.filter(ImageFilter.GaussianBlur(0.6))
    except Exception:
        pass

    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
    image.save(OUT_PNG)

    areas = [float((band == i).mean()) for i in range(len(palette))]
    report = {
        "ok": True,
        "source_palette_measured_from": os.path.relpath(SOURCE_DPC, ROOT),
        "measured_tones": [{"srgb": [int(v) for v in tone.round()], "area": round(w, 4)}
                           for tone, w in zip(tones, weights)],
        "chosen_tones": {name: [int(v) for v in colour.round()]
                         for name, colour in zip(names, palette)},
        "requested_areas": dict(zip(names, TONE_AREAS)),
        "actual_areas": {name: round(area, 4) for name, area in zip(names, areas)},
        "size": [SIZE, SIZE],
        "tileable": True,
        "seam": {k: round(v, 4) for k, v in seam_score(np.asarray(image)).items()},
        "output": os.path.relpath(OUT_PNG, ROOT),
    }
    with open(REPORT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1)

    print("chosen: " + ", ".join(
        "{}={}".format(name, tuple(int(v) for v in colour.round()))
        for name, colour in zip(names, palette)))
    print("areas:  " + ", ".join(
        "{}={:.3f}".format(name, area) for name, area in zip(names, areas)))
    print("seam ratio x={:.3f} y={:.3f} (1.0 would be invisible)".format(
        report["seam"]["seam_ratio_x"], report["seam"]["seam_ratio_y"]))
    print("wrote {}".format(os.path.relpath(OUT_PNG, ROOT)))


if __name__ == "__main__":
    main()
