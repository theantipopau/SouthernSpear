# Southern Spear - look at a texture sheet the way the mesh uses it.
#
#   python Tools/Common/ss_sheet_probe.py <sheet.png> <out.html> <v0> <v1> "u,v;u,v;..."
#
# The ADFRC sheets carry several garments at once (the G3 shirt's own panel plus the model's plain
# under-shirt), so "the camo looks wrong" and "there is a white band" can both be the same sheet read
# in the wrong place. This crops the sheet to a V band and marks the UV points the mesh actually
# samples, so the answer comes from the sheet rather than from guessing at the render.

import base64
import io
import sys

from PIL import Image, ImageDraw

sheet, out, v0, v1, points = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]

image = Image.open(sheet).convert("RGB")
width, height = image.size
# UV origin is bottom-left; image rows run top-down.
top = int((1.0 - v1) * height)
bottom = int((1.0 - v0) * height)
crop = image.crop((0, top, width, bottom))
draw = ImageDraw.Draw(crop)
for pair in [p for p in points.split(";") if p.strip()]:
    u, v = (float(x) for x in pair.split(","))
    x = int(u * width)
    y = int(v * height) - top
    draw.ellipse([x - 14, y - 14, x + 14, y + 14], outline=(255, 0, 255), width=6)
    draw.line([x - 26, y, x + 26, y], fill=(255, 0, 255), width=4)
    draw.line([x, y - 26, x, y + 26], fill=(255, 0, 255), width=4)
shown = crop.resize((crop.width * 2, crop.height * 2), Image.LANCZOS) if crop.width < 700 else crop
buffer = io.BytesIO()
shown.save(buffer, "JPEG", quality=88)
uri = "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()
with open(out, "w") as handle:
    handle.write('<!doctype html><meta charset=utf-8><body style="background:#111;color:#eee;'
                 'font:12px system-ui;margin:0;padding:8px">'
                 '<img src="{}" style="width:{}px"><div>sheet v {}-{} of {}, {} marked points</div>'
                 '</body>'.format(uri, min(1100, shown.width), v0, v1, sheet, len(points.split(";"))))
print("wrote", out, shown.size)
