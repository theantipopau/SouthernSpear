# Southern Spear - turn a capture PNG into an inline-HTML contact sheet for review.
#
#   python Tools/Common/ss_shot_html.py <png> <out.html> [crop x0 y0 x1 y1 in 0..1 fractions]
#
# Crops are written next to the sheet as data URIs, so nothing depends on the browser being able
# to fetch sibling files (the workspace preview server serves only the registered HTML).

import base64
import io
import os
import sys

from PIL import Image


def uri(image, quality=90):
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=quality)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()


def main():
    source, out = sys.argv[1], sys.argv[2]
    # Each crop is x0,y0,x1,y1 as 0..1 fractions, optionally with a zoom factor as a fifth value.
    crops = [tuple(float(v) for v in arg.split(",")) for arg in sys.argv[3:]]
    image = Image.open(source).convert("RGB")
    width, height = image.size
    figures = ['<figure><img src="{}" style="width:{}px"><figcaption>full frame {}x{}</figcaption></figure>'.format(
        uri(image.resize((width // 2, height // 2))), max(360, width // 2), width, height)]
    for crop in crops:
        x0, y0, x1, y1 = crop[:4]
        box = (int(x0 * width), int(y0 * height), int(x1 * width), int(y1 * height))
        piece = image.crop(box)
        scale = int(crop[4]) if len(crop) > 4 else max(1, min(3, 900 // max(1, piece.width)))
        piece = piece.resize((piece.width * scale, piece.height * scale), Image.LANCZOS)
        figures.append('<figure><img src="{}" style="width:{}px"><figcaption>crop {}</figcaption></figure>'.format(
            uri(piece), min(1000, piece.width), crop))
    html = ('<!doctype html><meta charset=utf-8><body style="background:#111;color:#eee;'
            'font:12px system-ui;margin:0;padding:8px;display:flex;gap:10px;flex-wrap:wrap">'
            + "".join(figures) + "</body>")
    with open(out, "w") as handle:
        handle.write(html)
    print("wrote {} for {}".format(os.path.abspath(out), os.path.basename(source)))


main()
