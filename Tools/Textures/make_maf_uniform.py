"""MAF uniform textures: the original red-earth disruptive camouflage (ADR-016, C-015) on the G3 uniform layout.

    python Tools/Textures/make_maf_uniform.py

The MAF wore the ADFRC G3's plain green texture (Tools/Unreal/setup_adf_soldier.py MAF_SWAP), which read as a
flat olive soldier in play (producer, Session 047: "the OPFOR need to be MAF, and have the correct camo"). This
lays an original red-earth disruptive pattern over the G3 layout:
  1. the pattern is generated here: seamless layered noise cut into the five ADR-016 colours (ochre, rust, dark
     brown, muted burgundy, charcoal), crisp shapes with a soft one-pixel edge (the earlier soft-blob swatch,
     Art/Characters/Textures/T_SS_MAF_Camo_BC.png, is not seamless and read as a smudge);
  2. it repeats TILES times across the sheet in UV space;
  3. the green texture's own shading (folds, seams, pockets, stitching) is kept as a luminance ratio against its
     blurred self, and its background (unused UV space) and the dark hook-and-loop panels stay as they were.
Outputs Art/Characters/Textures/T_SS_MAF_G3_{Shirt,Pants}_co.png (4096^2). Original work (Class F) over the
ADFRC layout (L-0021).
"""
import os

from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "Art", "ADFRC", "Textures", "adfrc_uniforms", "data")
OUT = os.path.join(ROOT, "Art", "Characters", "Textures")
PALETTE = [(142, 104, 60),   # ochre (field-worn: toned down from the swatch)
           (122, 66, 40),    # rust
           (78, 55, 39),     # dark brown
           (88, 40, 45),     # muted burgundy
           (52, 49, 46)]     # charcoal
TILES = 3.0


def periodic_noise(n, cells, rng):
    """Seamless fractal value noise on an n x n torus: random lattices, wrapped bicubic upsampling."""
    import numpy as np
    total = np.zeros((n, n), np.float32)
    amp, weight = 1.0, 0.0
    for octave in range(4):
        c = cells * (2 ** octave)
        grid = rng.random((c, c)).astype(np.float32)
        big = np.tile(grid, (3, 3))
        img = Image.fromarray((big * 255).astype(np.uint8)).resize((3 * n, 3 * n), Image.BICUBIC)
        layer = np.asarray(img, np.float32)[n:2 * n, n:2 * n] / 255.0
        total += amp * layer
        weight += amp
        amp *= 0.5
    return total / weight


def crisp_pattern(size):
    """Original red-earth disruptive pattern, seamless: layered noise fields cut into the five colours (each
    layer's shapes sit over the one below, as printed camouflage does), repeated TILES times across the sheet."""
    import numpy as np
    rng = np.random.default_rng(20260928)
    n = int(size / TILES)
    base = np.zeros((n, n), np.int32)                      # ochre ground
    for index, (cells, cut) in enumerate(((3, 0.50), (4, 0.56), (5, 0.60), (6, 0.66)), start=1):
        field = periodic_noise(n, cells, rng)
        base[field > np.quantile(field, cut)] = index      # rust, dark brown, burgundy, charcoal
    colours = np.array(PALETTE, np.uint8)[base]
    tile = Image.fromarray(colours, "RGB").filter(ImageFilter.GaussianBlur(1.0))
    out = Image.new("RGB", (size, size))
    for y in range(0, size, n):
        for x in range(0, size, n):
            out.paste(tile, (x, y))
    return out


def make(src_name, out_name):
    src = Image.open(os.path.join(SRC, src_name)).convert("RGB")
    size = src.width
    pattern = crisp_pattern(size)
    lum = src.convert("L")
    blur = lum.filter(ImageFilter.GaussianBlur(24))
    L, B, P, S = lum.load(), blur.load(), pattern.load(), src.load()
    out = Image.new("RGB", (size, size))
    O = out.load()
    for y in range(size):
        for x in range(size):
            l, b = L[x, y], B[x, y]
            if l < 18 or b < 22:          # unused UV space, hook-and-loop panels: keep the original
                O[x, y] = S[x, y]
                continue
            shade = max(0.55, min(1.45, l / max(b, 1)))
            p = P[x, y]
            O[x, y] = tuple(min(255, int(c * shade)) for c in p)
    out.save(os.path.join(OUT, out_name))
    print("wrote", out_name, size)


if __name__ == "__main__":
    make("Crye_G3_Shirt_Green_co.png", "T_SS_MAF_G3_Shirt_co.png")
    make("Crye_G3_Pants_green_co.png", "T_SS_MAF_G3_Pants_co.png")
