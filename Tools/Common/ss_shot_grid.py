# Southern Spear - draw a labelled coordinate grid over a capture crop.
#
#   python Tools/Common/ss_shot_grid.py <png> <out.png> x0 y0 x1 y1 [scale] [step]
#
# Sampling a render by guessing pixel coordinates wasted a cycle: the figure is smaller in the
# 1600x900 frame than it looks, so "the torso" landed on the backdrop. The labels are frame
# coordinates, so a colour sample can be quoted straight from what is on screen.

import sys

from PIL import Image, ImageDraw

source, out = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = (int(v) for v in sys.argv[3:7])
scale = int(sys.argv[7]) if len(sys.argv) > 7 else 2
step = int(sys.argv[8]) if len(sys.argv) > 8 else 50

image = Image.open(source).convert("RGB").crop((x0, y0, x1, y1))
image = image.resize((image.width * scale, image.height * scale), Image.LANCZOS)
draw = ImageDraw.Draw(image)
for x in range(x0 - x0 % step + step, x1, step):
    px = (x - x0) * scale
    draw.line([(px, 0), (px, image.height)], fill=(255, 0, 255), width=1)
    draw.text((px + 2, 2), str(x), fill=(255, 0, 255))
for y in range(y0 - y0 % step + step, y1, step):
    py = (y - y0) * scale
    draw.line([(0, py), (image.width, py)], fill=(0, 255, 255), width=1)
    draw.text((2, py + 2), str(y), fill=(0, 255, 255))
image.save(out)
print("wrote", out, image.size)
