"""G3 shirt: camo the flat olive under-shirt panels that the ADFRC sheet leaves as a solid fill.

    python Tools/Textures/make_g3_shirt_camo.py

Producer, Session 049: "the shoulders look weird, the patch between the webbing and the waist is
just a weird green." Both are one thing. Crye_G3_Shirt_AMC_co paints the G3 as a camo jacket over a
plain olive under-shirt, and the under-shirt owns the whole torso, both forearms and the shoulder
caps. Those panels are a solid fill -- 53% of the sheet has no local detail, and the fill sits in a
73..86 luminance band -- so the soldier renders with a smooth green slab from the webbing down to the
waistband, smooth forearms below the elbow, and a hard edge where a camo panel meets the fill that
reads as a bad shoulder. The FrontEnd capture measured rgb(60,57,35) there with a local std of 1.7:
flat, not merely dark, and not a missing texture, not the 64x64 fallback and not the mannequin.

No shirt variant avoids it. AMP, DPC, DPD and the rest are the same Arma base mesh with the same
under-shirt, so swapping texture cannot fix this. Following make_maf_uniform.py, the pattern is
generated here over the ADFRC layout:

  1. the panels are found by local detail (std over a 50 px window below 5) inside the narrow
     45..118 luminance band the fill occupies, grown from the large components only so the speckle
     of flat blobs sitting inside real camo is left alone, and snapped back to the island edge;
  2. the pattern is seamless, cut into six colours k-means'd from this sheet's own camo (so it is
     the ADFRC palette and the same blob scale, not a new design), repeated TILES times in UV space;
  3. the fill's own shading -- folds, seams, the zip, the dark hook-and-loop panels -- is kept as a
     luminance ratio against its blurred self, and the mask is feathered so the repaint has no seam.

Outputs Art/Characters/Textures/T_SS_ADF_G3_Shirt_co.png (4096^2). Original work (Class F) over the
ADFRC layout and palette (L-0021); setup_adf_soldier.py binds it to the shirt slot.
"""
import os

import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "Art", "ADFRC", "Textures", "adfrc_uniforms", "data")
OUT = os.path.join(ROOT, "Art", "Characters", "Textures")
SRC_NAME = "Crye_G3_Shirt_AMC_co.png"
OUT_NAME = "T_SS_ADF_G3_Shirt_co.png"

# Sampled from the sheet itself, not designed: six colours by k-means over its camo pixels, plus the
# two greens that a global k-means averages away (mean of pixels more than 18 green over red+blue).
# Darkest first. ADFRC's own AMC blobs, so the repaint matches the panels it sits beside.
PALETTE = [(20, 18, 14), (46, 42, 33), (61, 55, 42), (73, 66, 51),
           (85, 89, 50), (95, 88, 62), (103, 107, 64), (122, 116, 98)]
# Share of the sheet each colour occupies in the real panels, so the repaint matches their balance.
SHARES = [0.208, 0.088, 0.117, 0.144, 0.070, 0.135, 0.050, 0.188]
TILES = 16.0                # camo blobs land near 40-130 px, the scale of the sheet's own
GRAIN = 0.55                # how much of the fill's own print grain to keep on top of the pattern
HALF = 2                    # detail and region growing run at half resolution
DETAIL_HALF = 12            # 24 px window at half resolution -> 12 px here
DETAIL_MAX = 5.0            # local std under this counts as "no detail" (a flat fill)
FILL_LO, FILL_HI = 45, 118  # the luminance band the olive under-shirt occupies
BLOCK = 16                  # component growing step, in half-resolution pixels
SEED_SHARE = 0.50           # a block this masked starts the region
JOIN_SHARE = 0.02           # ...and grows into blocks at least this masked
GROW_STEPS = 200            # 3x3 dilation rounds; spans the panels at BLOCK=16
FEATHER = 10                # half-res mask blur: the blend zone into the camo panels
SHADE_BLUR = 24             # the blur the fill's own shading is measured against
SHADE_RANGE = (0.60, 1.40)  # how far the fold shading may push the pattern


def box_std(field, k):
    """Local standard deviation over a (2k+1)-square window, via integral images."""
    h, w = field.shape
    pad = np.pad(field, ((k, k), (k, k)), mode="edge").astype(np.float64)
    s1 = np.cumsum(np.cumsum(pad, 0), 1)
    s2 = np.cumsum(np.cumsum(pad * pad, 0), 1)
    m = 2 * k + 1

    def window(acc):
        return acc[m:, m:] - acc[:-m, m:] - acc[m:, :-m] + acc[:-m, :-m]

    n = float(m * m)
    out = np.sqrt(np.maximum(window(s2) / n - (window(s1) / n) ** 2, 0.0))
    return np.pad(out, ((0, h - out.shape[0]), (0, w - out.shape[1])), mode="edge").astype(np.float32)


def dilate(mask, rounds=1):
    out = mask.copy()
    for _ in range(rounds):
        nxt = out.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nxt |= np.roll(np.roll(out, dy, 0), dx, 1)
        out = nxt
    return out


def grow(share):
    """Keep the large flat panels; drop the isolated flat blobs sitting inside real camo."""
    region = share >= SEED_SHARE
    joinable = share >= JOIN_SHARE
    for _ in range(GROW_STEPS):
        grown = dilate(region) & joinable
        if grown.sum() == region.sum():
            break
        region = grown
    return region


def periodic_noise(n, cells, rng):
    """Seamless fractal value noise on an n x n torus: random lattices, wrapped bicubic upsampling."""
    total = np.zeros((n, n), np.float32)
    amp, weight = 1.0, 0.0
    for octave in range(4):
        c = cells * (2 ** octave)
        grid = rng.random((c, c)).astype(np.float32)
        big = np.tile(grid, (3, 3))
        img = Image.fromarray((big * 255).astype(np.uint8)).resize((3 * n, 3 * n), Image.BICUBIC)
        total += amp * (np.asarray(img, np.float32)[n:2 * n, n:2 * n] / 255.0)
        weight += amp
        amp *= 0.5
    return total / weight


def camo(size):
    """Seamless camo in the sheet's own palette. Two independent noise fields are added and the result
    ranked, then cut into bands of exactly SHARES: that gives organic blobs at the right scale and the
    real panels' colour balance, where layered threshold cuts drift dark. Repeated TILES times."""
    rng = np.random.default_rng(20260928)
    n = int(size / TILES)
    field = 0.62 * periodic_noise(n, 2, rng) + 0.38 * periodic_noise(n, 3, rng)
    rank = np.argsort(np.argsort(field.ravel(), axis=None), axis=None).reshape(n, n) / float(n * n)
    base = np.clip(np.searchsorted(np.cumsum(SHARES), rank, side="right"), 0, len(SHARES) - 1)
    colours = np.array(PALETTE, np.uint8)[base]
    tile = Image.fromarray(colours, "RGB").filter(ImageFilter.GaussianBlur(1.0))
    out = Image.new("RGB", (size, size))
    for y in range(0, size, n):
        for x in range(0, size, n):
            out.paste(tile, (x, y))
    return np.asarray(out, np.float32)


def main():
    src = Image.open(os.path.join(SRC, SRC_NAME)).convert("RGB")
    size = src.width
    rgb = np.asarray(src, np.float32)
    lum_img = src.convert("L")
    lum = np.asarray(lum_img, np.float32)

    half = np.asarray(lum_img.resize((size // HALF, size // HALF), Image.LANCZOS), np.float32)
    flat_h = (box_std(half, DETAIL_HALF) < DETAIL_MAX) & (half > FILL_LO) & (half < FILL_HI)

    # Coarsen, keep only the large panels, lift back to sheet resolution.
    side = flat_h.shape[0] // BLOCK
    share = flat_h[:side * BLOCK, :side * BLOCK].reshape(side, BLOCK, side, BLOCK).mean((1, 3))
    region = grow(share)
    near = region.repeat(BLOCK, 0).repeat(BLOCK, 1)[:flat_h.shape[0], :flat_h.shape[1]]

    alpha_h = np.asarray(Image.fromarray((near * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(FEATHER)), np.float32) / 255.0
    # Re-sharpen: solid inside the panel, a soft FEATHER-pixel transition at the edge.
    alpha_h = np.clip((alpha_h - 0.5) * 2.2 + 0.5, 0.0, 1.0)
    alpha = np.asarray(Image.fromarray((alpha_h * 255).astype(np.uint8)).resize(
        (size, size), Image.BILINEAR), np.float32)[..., None] / 255.0

    blur = np.asarray(lum_img.filter(ImageFilter.GaussianBlur(SHADE_BLUR)), np.float32)
    shade = np.clip(lum / np.maximum(blur, 1.0), *SHADE_RANGE)[..., None]
    pattern = camo(size) * shade
    if GRAIN:      # the print's own fine grain, so the pattern is not a flat cut-out
        pattern += (lum - blur)[..., None] * GRAIN
    out = rgb * (1.0 - alpha) + np.clip(pattern, 0, 255) * alpha

    os.makedirs(OUT, exist_ok=True)
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(os.path.join(OUT, OUT_NAME))

    painted = alpha[..., 0] > 0.5
    detail_new = box_std(out[..., 0] * 0.3 + out[..., 1] * 0.6 + out[..., 2] * 0.1, 12)
    print("panels repainted: %d px (%.1f%% of sheet)" % (painted.sum(), 100.0 * painted.mean()))
    print("local detail in those panels: %.2f -> %.2f" % (
        box_std(lum, 12)[painted].mean(), detail_new[painted].mean()))
    print("luminance in those panels: %.0f -> %.0f" % (lum[painted].mean(), out[..., 0][painted].mean()
                                                        * 0.3 + out[..., 1][painted].mean() * 0.6
                                                        + out[..., 2][painted].mean() * 0.1))
    print("wrote", OUT_NAME, size)


if __name__ == "__main__":
    main()
