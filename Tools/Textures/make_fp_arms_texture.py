# Southern Spear - first-person arms texture: the Fab FPS pack's bare arms re-dressed as a 3 ACR soldier's
# sleeves and gloves. The pack's own shading (folds, knuckles, tendons) is kept as a luminance ratio and
# multiplied onto the soldiers' AMCU shirt fabric (forearms) and a coyote glove tone (hands). The UV split is
# the pack's layout, from a per-polygon mask (below).
#
#   python Tools/Textures/make_fp_arms_texture.py <Hand_D.jpg> <out.png> <arms.fbx.uvmask.json>
#
# The mask comes from Tools/Blender/fp_arms.py: the pack's polygons labelled sleeve or glove by bone,
# rasterised here (the layout does not split the regions along one UV axis).

import sys

import numpy as np
import json

from PIL import Image, ImageDraw, ImageFilter

SRC, OUT, MASK = sys.argv[1], sys.argv[2], sys.argv[3]
FABRIC = "Art/ADFRC/Textures/adfrc_uniforms/data/crye_g3_shirt_amc_co.png"
FABRIC_CROP = (500, 1000, 1120, 1900)   # px in the 4096 sheet: sleeve panel below the arm patch
GLOVE = np.array([86, 82, 64], dtype=np.float32)   # olive-drab glove (Session 094: coyote read as bare skin in sun)
STRIP_WIDTH_U = 0.21   # the forearm strip width in U; the fabric crop is fitted to it
STRIP_U0 = 0.0         # where the fabric sampling starts in U

skin = np.asarray(Image.open(SRC).convert("RGB"), dtype=np.float32)
h, w, _ = skin.shape
lum = skin @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
blur = np.asarray(Image.fromarray(lum.astype(np.uint8)).filter(ImageFilter.GaussianBlur(24)), dtype=np.float32)
# Local detail only, flat colour removed. Clamped tighter than before (0.55..1.45): the upper end is
# what pushed the crop's bright texels past 150 and made the flat tiles read as pale rectangles.
shade = np.clip(lum / np.maximum(blur, 1.0), 0.62, 1.22)[..., None]

# Sleeve fabric: a patch-free area of the ADFRC G3 shirt's sleeve panel (the soldiers' own AMCU shirt,
# ADR-025; no insignia in the crop), scaled to the arms sheet and mirror-tiled so repeats have no seams.
#
# Session 094: that crop is only 17.9 std overall but 21 % of its 64 px tiles are flat (std < 11), and
# the shade curve below lifts its brightest texels (p95 108, max 157) by up to 1.45x - so the flat
# tiles come out as hard pale rectangles marching down the forearm in first person, which is what the
# producer saw as "textures look terrible". de_plain() swaps every low-variance tile for the crop's
# own camouflage, mirror-tiled (no seams) and brightness-matched to the panel it replaces, so the
# fabric keeps the ADFRC pattern instead of the sheet's quiet areas.

def de_plain(arr, tile=64, max_std=11.0, window=256):
    h, w, _ = arr.shape
    lum = arr.mean(axis=2)
    best = None
    for y in range(0, max(1, h - window), 32):
        for x in range(0, max(1, w - window), 32):
            win = lum[y:y + window, x:x + window]
            if win.shape != (window, window):
                continue
            s = float(win.std())
            if (win < 22).any():
                continue
            if best is None or s > best[0]:
                best = (s, y, x)
    if best is None:
        print("[fp_arms_texture] de-plain: no all-camo window, crop left as authored")
        return arr
    src = arr[best[1]:best[1] + window, best[2]:best[2] + window]
    ys, xs = np.mgrid[0:h, 0:w]
    ty = np.where(ys % (2 * window) < window, ys % (2 * window), 2 * window - 1 - ys % (2 * window))
    tx = np.where(xs % (2 * window) < window, xs % (2 * window), 2 * window - 1 - xs % (2 * window))
    tiled = src[ty, tx]
    out = arr.copy()
    replaced = 0
    for y in range(0, h - tile + 1, tile):
        for x in range(0, w - tile + 1, tile):
            t = arr[y:y + tile, x:x + tile]
            # Luminance std, not colour std: what makes a tile read as a pale block on the arm is that
            # it is flat in brightness, and colour variance hides that (colour std is always higher).
            tl = t.mean(axis=2)
            if float(tl.std()) >= max_std or float(tl.mean()) <= 45.0:
                continue
            fill = tiled[y:y + tile, x:x + tile]
            out[y:y + tile, x:x + tile] = fill * (float(t.mean()) / max(float(fill.mean()), 1.0))
            replaced += 1
    print("[fp_arms_texture] de-plain: %d of %d tiles replaced (source window std %.1f at %d,%d)" % (
        replaced, ((h // tile) * (w // tile)), best[0], best[1], best[2]))
    return out


fab_img = Image.open(FABRIC).convert("RGB").crop(FABRIC_CROP)
fab = Image.fromarray(np.clip(de_plain(np.asarray(fab_img, dtype=np.float32)), 0, 255).astype(np.uint8))
fw = int(w * STRIP_WIDTH_U)
fab = np.asarray(fab.resize((fw, int(fw * fab.height / fab.width))), dtype=np.float32)
fh = fab.shape[0]
tile = np.concatenate([np.concatenate([fab, fab[:, ::-1]], 1), np.concatenate([fab[::-1], fab[::-1, ::-1]], 1)], 0)
ys, xs = np.mgrid[0:h, 0:w]
camo = tile[ys % (2 * fh), (xs - int(STRIP_U0 * w)) % (2 * fw)]

mask_img = Image.new("L", (w, h), 0)  # 255 = glove
draw = ImageDraw.Draw(mask_img)
for label, pts in json.load(open(MASK)):
    if label == "glove":
        draw.polygon([(u * w, (1.0 - v) * h) for u, v in pts], fill=255)
mask_img = mask_img.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(3))  # seal UV seams, soft cuff
glove_w = (np.asarray(mask_img, dtype=np.float32) / 255.0)[..., None]
# Session 094: the glove was a flat fill (the pack's skin has almost no local detail), so the hands read as
# mitts. A fine knit weave breaks the fill up, and the ambient-occlusion bake from the arms mesh itself
# (Tools/Blender/bake_fp_arms_ao.py, optional 4th argument) separates the fingers and darkens the creases.
rng = np.random.default_rng(94)
weave = (np.sin(xs * 1.3) * np.sin(ys * 1.3)) * 0.07 + rng.normal(0.0, 0.06, (h, w))
glove_tex = GLOVE[None, None, :] * (1.0 + weave[..., None])
out = (camo * (1.0 - glove_w) + glove_tex * glove_w) * shade
if len(sys.argv) > 4:
    ao = np.asarray(Image.open(sys.argv[4]).convert("L").resize((w, h)), dtype=np.float32)[..., None] / 255.0
    out = out * (0.30 + 0.70 * ao ** 1.5)
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(OUT)
print("[fp_arms_texture] wrote", OUT)
