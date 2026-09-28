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
GLOVE = np.array([118, 98, 72], dtype=np.float32)   # coyote brown
STRIP_WIDTH_U = 0.21   # the forearm strip width in U; the fabric crop is fitted to it
STRIP_U0 = 0.0         # where the fabric sampling starts in U

skin = np.asarray(Image.open(SRC).convert("RGB"), dtype=np.float32)
h, w, _ = skin.shape
lum = skin @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
blur = np.asarray(Image.fromarray(lum.astype(np.uint8)).filter(ImageFilter.GaussianBlur(24)), dtype=np.float32)
shade = np.clip(lum / np.maximum(blur, 1.0), 0.55, 1.45)[..., None]   # local detail only, flat colour removed

# Sleeve fabric: a patch-free area of the ADFRC G3 shirt's sleeve panel (the soldiers' own AMCU shirt,
# ADR-025; no insignia in the crop), scaled to the arms sheet and mirror-tiled so repeats have no seams.
fab = Image.open(FABRIC).convert("RGB").crop(FABRIC_CROP)
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
out = (camo * (1.0 - glove_w) + GLOVE[None, None, :] * glove_w) * shade
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(OUT)
print("[fp_arms_texture] wrote", OUT)
