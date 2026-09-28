#!/usr/bin/env python
"""Southern Spear - original surface textures for Ravenshoe Crossing.

The bridge, its abutments and the gatehouse were greybox: four constant
materials, so the one structure the map is named for read as untextured blockout
no matter how good the geometry was. This authors real surfaces for them.

Everything here is generated from noise, so it is original work (L-0011, Class F)
and the same ground the character camo sets stand on (CH-TEX-001). It is not
sampled from, traced from, or derived from any scanned or licensed texture.

Four sets, one per surface the bridge actually presents:

  Gravel       the running surface on the deck - a sealed gravel road, the
               surface players fight on and the one most in need of reading as
               a road rather than as grey
  RustIron     the lattice truss and parapet - dark protective paint breaking
               down into oxide, with the vertical rust runs that ironwork
               always has
  PaintedSteel the deck slab, kerbs and soffit - same paint family, far less
               breakdown, so the deck structure reads as a different member
               from the lattice it hangs on
  Granite      the abutments and the gatehouse - coursed rubble masonry

Emits five maps per set because M_SS_ScanPBR takes five separate texture
parameters (BaseColor / Normal / Roughness / AO / Metalness), not a packed ORM.
That matches the existing MI_SS_CorrugatedIron, so the bridge feeds the same
shader the props already use.

Every field is periodic, so the sets tile. The noise wraps on the cell lattice
and the masonry joints are generated as a function of x modulo the tile width,
rather than by clamping, which is what stopped make_character_textures.py from
being reusable here.

Outputs PNGs into Art/Environment/Ravenshoe/Surfaces/.
Run:  python Tools/Textures/make_ravenshoe_surfaces.py
"""

import json
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "Art", "Environment", "Ravenshoe", "Surfaces")

SIZE = 1024

MAPS = ("BC", "N", "R", "AO", "M")   # the five M_SS_ScanPBR texture parameters

# The wrap step may be at most this multiple of the tile's strongest interior
# detail (p99 of adjacent-pixel differences). 1.0 means the seam is no more
# pronounced than the roughest thing already in the texture, so it disappears.
SEAM_TOL = 1.0


# ---------------------------------------------------------------- noise utils


def pvalue_noise(shape, cells, rng):
    """Bilinear value noise that TILES. `cells` is int or (cells_y, cells_x).

    The non-periodic version in make_character_textures.py samples linspace
    across the full cell grid and clamps at the edges, so its first and last
    rows differ. Here the sample position is a fraction of the grid and both
    the interpolation indices and the weights wrap, so opposite edges match.
    """
    cy, cx = (cells, cells) if np.isscalar(cells) else cells
    h, w = shape
    g = rng.random((cy, cx)).astype(np.float32)
    ys = np.arange(h, dtype=np.float32) * (cy / float(h))
    xs = np.arange(w, dtype=np.float32) * (cx / float(w))
    y0 = np.floor(ys).astype(np.int32) % cy
    x0 = np.floor(xs).astype(np.int32) % cx
    y1 = (y0 + 1) % cy
    x1 = (x0 + 1) % cx
    fy = (ys - np.floor(ys))[:, None]
    fx = (xs - np.floor(xs))[None, :]
    sy = (fy * fy * (3.0 - 2.0 * fy))
    sx = (fx * fx * (3.0 - 2.0 * fx))
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
        total += amp * pvalue_noise(shape, c, rng)
        norm += amp
        amp *= gain
        # Elementwise, NOT `c * 2`: tuple repetition turns (3, 26) into
        # (3, 26, 3, 26) on the first octave and a 4-tuple on the second.
        c = (c[0] * 2, c[1] * 2) if not np.isscalar(c) else c * 2
    return total / norm


def voronoi(shape, cells, rng, jitter=0.85):
    """Periodic Worley. Returns (F1 distance, site_y, site_x).

    The site coordinates are returned WRAPPED to the lattice, not as integer
    cell ids. A stone that straddles the tile edge is one stone, but it is
    addressed as cell 45 on one side of the seam and cell 0 on the other, so
    anything hashed from the integer id changes value across the seam and puts
    a hard line in the texture. The wrapped site is the same value from both
    sides, so a hash of it is continuous.
    """
    h, w = shape
    cy, cx = (cells, cells) if np.isscalar(cells) else cells
    gy, gx = cy / float(h), cx / float(w)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    py = yy * gy
    px = xx * gx
    ci = np.floor(py).astype(np.int32)
    cj = np.floor(px).astype(np.int32)
    best = np.full(shape, 1e9, dtype=np.float32)
    site_y = np.zeros(shape, dtype=np.float32)
    site_x = np.zeros(shape, dtype=np.float32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            # Jitter is per SITE, so it is sampled on the cell lattice and
            # gathered per pixel by the cell index. The neighbour index is
            # wrapped BEFORE the lookup: without that, the site across the
            # wrap reads the jitter of an out-of-range row and the pattern
            # breaks at the tile edge.
            n = rng.random((cy, cx, 2)).astype(np.float32) * jitter \
                + (1.0 - jitter) * 0.5
            jy, jx = (ci + dy) % cy, (cj + dx) % cx
            ny = ci + dy + n[jy, jx, 0]
            nx = cj + dx + n[jy, jx, 1]
            # shortest wrapped distance to the jittered site
            ddy = ny - py
            ddx = nx - px
            ddy -= np.round(ddy)
            ddx -= np.round(ddx)
            d = np.sqrt(ddy * ddy + ddx * ddx)
            hit = d < best
            best = np.where(hit, d, best)
            site_y = np.where(hit, ny % cy, site_y)
            site_x = np.where(hit, nx % cx, site_x)
    return best, site_y, site_x


def warp_p(shape, rng, strength=0.35, cells=4):
    """Periodic domain warp. Returns integer sample indices for x and y.

    Wrapping the warped index is what keeps the result tileable. Used instead of
    a lattice-stretched fbm for the tar bleed: stretching the lattice makes
    features tall and thin, which for a stain means hard vertical bars rather
    than a sinuous one.
    """
    h, w = shape
    wx = (fbm(shape, cells, 3, rng) - 0.5) * strength
    wy = (fbm(shape, cells, 3, rng) - 0.5) * strength
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    yi = ((yy + wy * h) % h).astype(np.int32)
    xi = ((xx + wx * w) % w).astype(np.int32)
    return yi, xi


def box_blur(a, radius):
    """Separable box blur via cumulative sums. Cheaper than a Gaussian and
    enough for an ambient-occlusion approximation."""
    if radius < 1:
        return a
    out = np.asarray(a, dtype=np.float64)
    for axis in (0, 1):
        n = out.shape[axis]
        r = int(radius)
        pad = [(0, 0), (0, 0)]
        pad[axis] = (r, r)
        p = np.pad(out, pad, mode="wrap")
        # float64 throughout: the running sum reaches ~500 while the window sum
        # is ~20, so in float32 the subtraction cancels away most of the signal
        # and the AO comes out as directional noise.
        cs = np.cumsum(p, axis=axis, dtype=np.float64)
        zero = np.zeros_like(np.take(cs, [0], axis=axis))
        cs = np.concatenate([zero, cs], axis=axis)
        hi = np.take(cs, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
        lo = np.take(cs, np.arange(0, n), axis=axis)
        out = (hi - lo) / float(2 * r + 1)
    return out.astype(np.float32)


def normalise(a):
    lo, hi = float(a.min()), float(a.max())
    return (a - lo) / (hi - lo) if hi > lo else np.zeros_like(a)


def height_to_normal(height, strength=4.0):
    """Central-difference normal map, computed PERIODICALLY.

    np.gradient is one-sided at the first and last row and column, so its
    boundary normals never match their neighbours and every normal map in the
    set fails the seam check. Rolling the difference is periodic by
    construction and costs nothing.
    """
    h = height.astype(np.float32)
    gx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5
    gy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5
    nx, ny, nz = -gx * strength, -gy * strength, np.ones_like(h)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / ln, ny / ln, nz / ln], axis=-1) * 0.5 + 0.5


def ao_from_height(height, radius=14, strength=0.55):
    """Crevice occlusion: how far a texel sits below its own neighbourhood.

    The height is blurred BEFORE the comparison. Differentiating the raw height
    puts the finest noise octave straight into the AO, which on a 1024 map
    comes out as per-pixel dither rather than as contact shadow.
    """
    h = box_blur(height, radius)
    local = box_blur(h, radius)
    d = np.clip((local - h) * 5.0, 0.0, 1.0)
    return np.clip(1.0 - strength * d, 0.0, 1.0)


def seam_error(arr):
    """Is the wrap seam distinguishable from ordinary interior detail?

    Returns seam_step / p99(interior_steps) per axis, where seam_step is the
    mean absolute difference across the wrap and p99 is the 99th percentile of
    every adjacent-pixel difference inside the tile.

    Two earlier attempts at this were wrong, and both were wrong in a way that
    sent me after faults that did not exist:

      - An ABSOLUTE difference threshold. On a high-frequency field adjacent
        samples always differ, so this flags perfectly good sets. It reported
        the gravel aggregate as broken when the only real fault was the
        one-sided normal-map gradient.
      - A ratio against the MEAN interior step. The wrap is a single sample
        pair out of ~1000, and in a piecewise-smooth field the step size varies
        enormously by chance depending on where the wrap lands relative to a
        cell boundary. Correct sets scored 2.7.

    Against the 99th PERCENTILE the wrap step has to exceed the strongest
    detail in the entire tile to fail, which is what a real discontinuity does
    and what a merely high-frequency field does not. A correct set scores well
    under 1.
    """
    a = np.asarray(arr, dtype=np.float32)
    if a.ndim == 3:
        a = a.mean(axis=-1)
    out = []
    for axis in (0, 1):
        b = np.moveaxis(a, axis, 0)
        seam = float(np.abs(b[0] - b[-1]).mean())
        inner = np.abs(np.diff(b, axis=0)).ravel()
        p99 = float(np.percentile(inner, 99.0))
        out.append(seam / p99 if p99 > 1e-6 else (1.0 if seam < 1e-6 else 99.0))
    return out[0], out[1]


def mix(a, b, t):
    """Blend colour arrays a and b by mask t.

    a and b may be (3,) or (h, w, 3); t may be (h, w) or (h, w, 1). The mask is
    squeezed rather than assumed, because half the call sites already carry the
    trailing axis and half do not.
    """
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    t = np.asarray(t, dtype=np.float32)
    if a.ndim == 1:
        a = a[None, None, :]
    if b.ndim == 1:
        b = b[None, None, :]
    if t.ndim == 3:
        t = t[..., 0]
    return a * (1.0 - t[..., None]) + b * t[..., None]


def pack(rough, ao, metal):
    return (np.clip(ao, 0, 1), np.clip(rough, 0, 1), np.clip(metal, 0, 1))


# ------------------------------------------------------------------- surfaces


def gravel(seed=7301):
    """Sealed gravel road: coarse aggregate bound in bitumen, tar bleeding out
    of the cracks, the binder polished smooth between the stones.

    Deliberately carries NO low-frequency gradient. The set tiles across a 7.5 m
    deck at more than one repeat, so a baked-in crown or a wheel-wear band would
    come back every tile and read as stripes running the length of the bridge.
    Large-scale interest has to come from tiling the set at different scales,
    not from writing a gradient into the map.
    """
    rng = np.random.default_rng(seed)
    shape = (SIZE, SIZE)

    # Aggregate: Worley cells give distinct stones; the crackle between them is
    # the binder, which is darker, smoother and much less reflective.
    f1, site_y, site_x = voronoi(shape, 46, rng)
    stone = normalise(1.0 - f1 * 9.0)
    per_stone = (np.sin(site_y * 12.9898 + site_x * 78.233) * 43758.5453) % 1.0
    per_stone = per_stone.astype(np.float32)

    grit = fbm(shape, 110, 3, rng)
    dust = fbm(shape, 9, 4, rng)

    stone_col = np.array([0.475, 0.452, 0.408], dtype=np.float32)
    stone_col = stone_col[None, None, :] * (0.82 + 0.36 * per_stone)[..., None]
    binder_col = np.array([0.205, 0.192, 0.176], dtype=np.float32)

    binder_t = np.clip((f1 - 0.24) * 6.0, 0.0, 1.0)
    rgb = mix(stone_col * (0.90 + 0.20 * grit)[..., None], binder_col, binder_t)

    # Tar bleed: soft, sinuous, and warped rather than lattice-stretched.
    yi, xi = warp_p(shape, rng, 0.30, 5)
    base = fbm(shape, 6, 4, rng)
    tar = normalise(0.45 * base + 0.55 * base[yi, xi])
    tar_t = np.clip((tar - 0.60) * 4.0, 0.0, 1.0) * 0.55
    rgb = mix(rgb, np.array([0.150, 0.140, 0.129], dtype=np.float32), tar_t)

    rgb = rgb * (0.92 + 0.16 * dust)[..., None]

    height = normalise(0.60 * stone + 0.40 * grit
                       - 0.30 * binder_t - 0.10 * tar_t)
    rough = np.clip(0.88 - 0.30 * tar_t + 0.10 * (grit - 0.5)
                    - 0.12 * binder_t, 0.35, 1.0)
    metal = np.zeros(shape, dtype=np.float32)
    return rgb, height, pack(rough, ao_from_height(height, 22, 0.45), metal)


def ironwork(seed=7302, rust_level=1.0, paint=(0.128, 0.150, 0.143),
             flake_cells=(26, 130), seam_strength=0.10):
    """Wrought iron under protective paint that has failed.

    The read that matters is that metalness and roughness are driven by the
    SAME rust mask as the colour. Paint intact is a dielectric-ish coating over
    metal: low roughness, high metalness. Bare oxide is not metal at all: very
    rough, zero. Driving all three from one mask is what stops rusted iron
    looking like orange plastic, which is what a single blended colour always
    produced.
    """
    rng = np.random.default_rng(seed)
    shape = (SIZE, SIZE)

    # Rust runs DOWN. The lattice is coarse in y and fine in x, so the features
    # come out tall and thin; a second finer pass gives the flaking.
    run = fbm(shape, (3, 15), 4, rng)
    flake = fbm(shape, flake_cells, 4, rng)
    macro = fbm(shape, 5, 4, rng)
    rust = normalise(0.62 * run + 0.26 * flake + 0.12 * macro)
    rust = np.clip((rust - (0.66 - 0.20 * rust_level)) * (3.4 * rust_level + 0.6), 0.0, 1.0)
    rust = np.clip(rust * rust_level, 0.0, 1.0)

    paint_col = np.array(paint, dtype=np.float32)
    rust_col = np.array([0.372, 0.176, 0.078], dtype=np.float32)
    rust_hi = np.array([0.545, 0.290, 0.129], dtype=np.float32)

    warm = np.clip((rust - 0.45) * 2.0, 0.0, 1.0)[..., None]
    rust_rgb = mix(rust_col[None, None, :], rust_hi[None, None, :], warm)
    # Chalking and dark staining in the heaviest oxide.
    chalk = fbm(shape, 90, 3, rng)
    rust_rgb = rust_rgb * (0.82 + 0.30 * chalk)[..., None]

    paint_rgb = paint_col[None, None, :] * np.ones(shape + (1,), dtype=np.float32)
    paint_rgb = paint_rgb * (0.86 + 0.26 * fbm(shape, 60, 3, rng))[..., None]

    rgb = mix(paint_rgb, rust_rgb, rust)

    # Plate seams: the truss is fabricated from length of plate. Kept faint and
    # jittered - a perfectly even seam every half tile reads as wallpaper.
    jitter = (fbm((1, SIZE), 12, 2, rng) - 0.5) * 0.010
    seam = np.abs(np.sin((np.arange(SIZE, dtype=np.float32) / float(SIZE)
                          + jitter[0]) * np.pi * 4.0))
    seam = np.clip((seam - 0.995) * 200.0, 0.0, 1.0)
    seam = np.repeat(seam[None, :], SIZE, axis=0)
    rgb = rgb * (1.0 - seam_strength * seam)[..., None]

    height = normalise(0.45 * flake + 0.34 * run + 0.21 * macro + 0.18 * rust
                       - 0.06 * seam)
    rough = 0.42 + 0.44 * rust + 0.06 * (flake - 0.5) - 0.05 * seam
    metal = 0.62 * (1.0 - rust) + 0.02
    return rgb, height, pack(rough, ao_from_height(height, 14, 0.5), metal)


def granite(seed=7303, courses=8, blocks=6):
    """Coursed rubble masonry, as the gatehouse and the abutments are built.

    Courses divide the tile height exactly and the vertical joints are a
    function of x modulo the tile width, so both directions wrap.

    BED JOINTS ARE ESSENTIAL and the first pass did not have them. It generated
    vertical joints only, which is not coursed masonry at all - it is a wall of
    vertical strips, and it rendered as flat grey slabs. Masonry is defined by
    the horizontal bed joint between courses as much as by the perpends, and
    without it the blocks never read as separate stones.

    Each block draws its own tone and its own weathering, and the variation sits
    at BLOCK scale rather than pixel scale. That is the whole difference between
    rubble and brick.
    """
    rng = np.random.default_rng(seed)
    shape = (SIZE, SIZE)
    h, w = shape

    # Perpend positions across one tile: a random partition of the width. Because
    # the block lookup wraps, a block may straddle the seam; it then appears
    # identically at both edges, which is exactly what a tile needs.
    nb = blocks
    bounds = np.sort(rng.random(nb) * w)
    per_block_tone = (rng.random(nb) * 0.26 - 0.13).astype(np.float32)
    per_block_weather = rng.random(nb).astype(np.float32)

    ci = np.arange(h, dtype=np.float32) * (courses / float(h))
    course = np.floor(ci).astype(np.int32) % courses
    # Each course is shifted along x, so perpends never line up into a cross.
    phase = ((np.sin(course * 78.233) * 43758.5453) % 1.0).astype(np.float32) * w
    fx = np.arange(w, dtype=np.float32)[None, :] + phase[:, None]
    u = fx % w

    # Distance to the nearest perpend is a circular min, which is right. Block
    # identity is NOT: taking argmin of the same distance splits every block
    # down its middle, so one stone gets two tones and gains a seam that is not
    # in the masonry. The owning block is a searchsorted instead, which gives
    # each block one tone across its whole width.
    rel = (u[..., None] - bounds[None, None, :]) % w
    dist = np.abs(np.minimum(rel, w - rel))
    which = np.clip(np.searchsorted(bounds, u, side="right") - 1, 0, nb - 1)

    mortar_half = 0.016 * w          # ~20 mm at the tiling the material uses
    joint_v = np.clip((mortar_half - dist) / (0.35 * mortar_half), 0.0, 1.0)
    arris_v = np.clip((dist - mortar_half) / (0.30 * mortar_half), 0.0, 1.0)

    # Bed joints: distance in pixels from a row to the course boundary above or
    # below it. frac is in [0, 1) of a course, and one course is h/courses px.
    frac = ci - np.floor(ci)
    rowdist = np.minimum(frac, 1.0 - frac) * (h / float(courses))
    joint_h = np.clip((mortar_half - rowdist) / (0.35 * mortar_half), 0.0, 1.0)

    # Expand back over the pixel rows, or these cannot broadcast against the
    # full-size noise fields. joint_v/arris_v are (courses, w, n_bounds) and must
    # lose the boundary axis with the [:, :, 0]; which is (courses, w) and does
    # not have one, so plain axis-0 indexing is right for it.
    joint_v = joint_v[course, :, 0]                      # h x w
    arris_v = arris_v[course, :, 0]
    joint = np.maximum(joint_v, joint_h[:, None])        # perpend OR bed
    arris = np.minimum(arris_v, (np.abs(rowdist - mortar_half)
                                 / (0.30 * mortar_half))[:, None])
    tone = per_block_tone[which[course]]                  # h x w
    weather = per_block_weather[which[course]]

    grain = fbm(shape, 90, 4, rng)
    mottle = fbm(shape, 20, 4, rng)
    pits = fbm(shape, 220, 2, rng)

    # Local granite: warm mid grey with a faint pink cast, the colour of the
    # stone quarried through this country rather than a neutral grey.
    base = np.array([0.404, 0.383, 0.361], dtype=np.float32)[None, None, :]
    stone_rgb = base * (1.0 + tone)[..., None]
    stone_rgb = stone_rgb * (0.86 + 0.28 * mottle)[..., None]
    stone_rgb = stone_rgb * (0.92 + 0.16 * grain)[..., None]
    # The odd block is a different stone: cooler and darker.
    cool = (weather > 0.78)[..., None]
    stone_rgb = mix(stone_rgb, np.array([0.300, 0.297, 0.306], dtype=np.float32)
                    [None, None, :], cool * 0.55)

    mortar_rgb = np.array([0.352, 0.336, 0.308], dtype=np.float32)[None, None, :] \
        * np.ones(shape + (1,), dtype=np.float32)
    mortar_rgb = mortar_rgb * (0.88 + 0.24 * grain)[..., None]

    rgb = mix(stone_rgb, mortar_rgb, joint[..., None])
    rgb = rgb * (1.0 - 0.10 * (1.0 - arris) * (1.0 - joint))[..., None]

    # Height: blocks stand proud, mortar is recessed, arrises roll off. The
    # joint term carries most of the weight, so the normal map is dominated by
    # the masonry rather than by the stone grain - which is what makes the
    # courses read at a distance.
    height = 0.70 * (1.0 - joint) + 0.11 * grain + 0.09 * mottle \
        + 0.10 * (arris - 0.5) * (1.0 - joint) + 0.03 * pits

    rough = np.clip(0.78 + 0.16 * (1.0 - grain) - 0.10 * joint
                    + 0.06 * (mottle - 0.5), 0.35, 1.0)
    metal = np.zeros(shape, dtype=np.float32)
    return np.clip(rgb, 0, 1), height, pack(
        rough, ao_from_height(height, 20, 0.70), metal)


# ------------------------------------------------------------------ packaging


def save(name, arr):
    if arr.ndim == 2:
        arr = np.repeat(arr[..., None], 3, axis=-1)
    img = Image.fromarray((np.clip(arr, 0, 1) * 255.0 + 0.5).astype(np.uint8))
    path = os.path.join(OUT, name)
    img.save(path, optimize=True)
    return {"file": name, "size": list(img.size), "bytes": os.path.getsize(path)}


def emit(tag, rgb, height, orm, written, normal_strength=4.0):
    rough, ao, metal = orm[1], orm[0], orm[2]
    normal = height_to_normal(height, normal_strength)
    maps = {"BC": rgb, "N": normal, "R": rough, "AO": ao, "M": metal}

    # Verify periodicity on the float data, before quantisation to 8-bit adds
    # its own +-1/255 of noise. Anything over the threshold is a set that will
    # show a hard grid the moment it is repeated on the deck.
    seams = {}
    for k, arr in maps.items():
        dx, dy = seam_error(arr)
        seams[k] = {"x": round(dx, 5), "y": round(dy, 5),
                    "ok": max(dx, dy) <= SEAM_TOL}
    written.append({"set": tag, "seams": seams,
                    "seam_ok": all(v["ok"] for v in seams.values())})

    for k, arr in maps.items():
        save("T_SS_Raven_%s_%s.png" % (tag, k), arr)
    return seams


def main():
    os.makedirs(OUT, exist_ok=True)
    written = []
    seams = {}

    rgb, height, orm = gravel()
    seams["Gravel"] = emit("Gravel", rgb, height, orm, written,
                            normal_strength=5.0)

    # The truss has failed badly; the deck slab and soffit have barely started.
    # Same paint, same shader, different breakdown, so the two read as one
    # structure with one sheltered member.
    rgb, height, orm = ironwork(seed=7302, rust_level=1.0)
    seams["RustIron"] = emit("RustIron", rgb, height, orm, written)

    # Near-isotropic flake for the painted set. The rusted truss wants a 5:1
    # stretch, because oxide really does flake in streaks; at that anisotropy
    # on a surface with almost no rust the same noise reads as woven fabric
    # rather than as steel, and the normal map comes out as a diagonal weave.
    rgb, height, orm = ironwork(seed=7305, rust_level=0.26,
                                paint=(0.152, 0.171, 0.166),
                                flake_cells=(78, 96), seam_strength=0.06)
    seams["PaintedSteel"] = emit("PaintedSteel", rgb, height, orm, written)

    rgb, height, orm = granite()
    seams["Granite"] = emit("Granite", rgb, height, orm, written,
                            normal_strength=4.5)

    bad = sorted(k for k, v in seams.items()
                 for m, s in v.items() if not s["ok"])
    with open(os.path.join(ROOT, "Build", "ravenshoe_surfaces.json"), "w") as fh:
        json.dump({"ok": not bad, "size": SIZE, "maps": list(MAPS),
                   "seam_tolerance": SEAM_TOL, "seam_failures": bad,
                   "seams": seams, "sets": written}, fh, indent=1)
    print("wrote %d sets x %d maps to %s" % (len(written), len(MAPS), OUT))
    if bad:
        print("SEAM FAILURES: %s" % ", ".join(bad))
    else:
        print("seam check: all sets periodic within %.4f" % SEAM_TOL)


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "Build"), exist_ok=True)
    main()
