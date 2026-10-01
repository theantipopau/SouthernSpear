# Southern Spear - repaint the ADFRC G3 shirt sheet's plain under-shirt panel in pattern.
#
# Measured 2026-10-01 (Tools/Blender/inspect_uniform_fit.py on the fitted SK_ADF_Uniform_G3):
# the torso faces sample UV v 0.02..0.24 of Crye_G3_Shirt_AMC_co.png, and that band is a plain khaki
# under-shirt panel with no camouflage in it -- so the soldier reads with a pale band across the belly
# and waist that looks like a hole in the model. The geometry is continuous (Blender reports trunk
# faces in every 2.5 cm slab from 75 cm to 155 cm), and the matching trouser sheet is camouflaged in
# the same band, so this is the shirt sheet, not the mesh and not the fit.
#
# This writes a derivative sheet: every low-variance, non-background tile is replaced with the sheet's
# own camouflage, mirrored as it tiles so the repeat does not read as a grid. The pattern's spot size
# is unchanged because the source region is copied at its native resolution. The source sheet is left
# untouched (ADR-035: source and derivative stay distinct).
#
#   python Tools/Textures/patch_adfrc_undershirt.py
#
# Output: Art/Characters/ADF/T_ADFRC_G3_Shirt_AmcuCamo.png + Build/adfrc_undershirt_patch.json

import json
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCE = os.path.join(ROOT, "Art", "ADFRC", "Textures", "adfrc_uniforms", "data", "Crye_G3_Shirt_AMC_co.png")
# The camouflage comes from the trouser sheet of the same ADFRC uniform: same pattern, same scale,
# and unlike the shirt sheet it has no plain panel and no black margin in the region used. Copying a
# small window out of the shirt sheet and repeating it produced a visible 64 px checkerboard with
# black tile edges (caught on the sheet before it reached the game).
CAMOUFLAGE = os.path.join(ROOT, "Art", "ADFRC", "Textures", "adfrc_uniforms", "data", "Crye_G3_Pants_AMC_co.png")
CAMO_ROWS = (2440, 3560)   # one trouser leg of the same uniform: the same AMCU pattern at the same
CAMO_COLS = (110, 1330)    # scale, and the widest camouflage window the sheets offer without a black
#                            margin (the shirt sheet is mostly black between UV islands: 24% of that
#                            window was background, which filled the waist with black patches).
OUTPUT = os.path.join(ROOT, "Art", "Characters", "ADF", "T_ADFRC_G3_Shirt_AmcuCamo.png")
REPORT = os.path.join(ROOT, "Build", "adfrc_undershirt_patch.json")

TILE = 64          # analysis and fill tile
MAX_STD = 11.0     # a plain panel varies little; camouflage varies a lot
MIN_MEAN = 45.0    # the sheet's unused background is black and must stay black

report = {"ok": False, "errors": []}
try:
    sheet = np.asarray(Image.open(SOURCE).convert("RGB")).astype(np.float32)
    height, width = sheet.shape[:2]

    rows_per_tile, cols_per_tile = height // TILE, width // TILE
    luminance = sheet.mean(axis=2)

    def tile_at(ty, tx):
        return sheet[ty * TILE:(ty + 1) * TILE, tx * TILE:(tx + 1) * TILE]

    # Plain garment tiles: low variance (no camouflage) and not the sheet's black background.
    plain = [(ty, tx) for ty in range(rows_per_tile) for tx in range(cols_per_tile)
             if tile_at(ty, tx).std() < MAX_STD and tile_at(ty, tx).mean() > MIN_MEAN]
    if not plain:
        raise RuntimeError("no plain panel found in " + SOURCE)
    plain_luminance = float(np.mean([tile_at(ty, tx).mean() for ty, tx in plain]))
    plain_rows = sorted({ty for ty, _ in plain})

    report["plain_panel_luminance"] = round(plain_luminance, 1)
    report["plain_panel_rows"] = plain_rows
    report["camouflage_source"] = os.path.relpath(CAMOUFLAGE, ROOT)

    camo = np.asarray(Image.open(CAMOUFLAGE).convert("RGB")).astype(np.float32)
    camo = camo[CAMO_ROWS[0]:CAMO_ROWS[1], CAMO_COLS[0]:CAMO_COLS[1]]
    report["camouflage_tile_size"] = list(camo.shape[:2])

    # Mirror the camouflage across the whole sheet, so adjacent filled tiles continue the same
    # reflection and no seam or repeat edge is visible, then take each plain tile from it.
    ys = np.arange(height)
    xs = np.arange(width)
    ys = np.where(ys % (2 * camo.shape[0]) < camo.shape[0], ys % (2 * camo.shape[0]),
                  2 * camo.shape[0] - 1 - ys % (2 * camo.shape[0]))
    xs = np.where(xs % (2 * camo.shape[1]) < camo.shape[1], xs % (2 * camo.shape[1]),
                  2 * camo.shape[1] - 1 - xs % (2 * camo.shape[1]))
    mirrored = camo[np.ix_(ys, xs)]
    report["camouflage_black_fraction"] = round(float((mirrored.mean(axis=2) < 22).mean()), 4)

    output = sheet.copy()
    for ty, tx in plain:
        y, x = ty * TILE, tx * TILE
        output[y:y + TILE, x:x + TILE] = mirrored[y:y + TILE, x:x + TILE]
    report["filled_tiles"] = len(plain)
    report["tiles"] = rows_per_tile * cols_per_tile

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    Image.fromarray(output.astype(np.uint8)).save(OUTPUT)
    report["output"] = os.path.relpath(OUTPUT, ROOT)
    report["size"] = [width, height]
    report["ok"] = True
except Exception as exc:  # noqa: BLE001 - a build report, not a library
    import traceback
    report["errors"].append(traceback.format_exc())
    raise
finally:
    with open(REPORT, "w") as handle:
        json.dump(report, handle, indent=1)

print("patched {} of {} tiles -> {} (rows {})".format(
    report.get("filled_tiles"), report.get("tiles"), report.get("output"), report.get("filled_rows")))
