"""Fictional Murasian Armed Forces (MAF) flag, original design (ADR-016): clay
field, charcoal hoist triangle, sand ring. Not modelled on any real flag.
Writes Art/Flags/T_SS_Flag_MAF.png, 1024x640 (the World Flags cloth is
121x76 cm). Run: python Tools/Textures/maf_flag.py"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[2] / "Art/Flags/T_SS_Flag_MAF.png"
W, H = 1024, 640
CLAY, CHARCOAL, SAND = (164, 86, 58), (38, 38, 34), (226, 212, 180)

img = Image.new("RGB", (W, H), CLAY)
d = ImageDraw.Draw(img)
d.rectangle([0, int(H * 0.82), W, H], fill=CHARCOAL)          # lower band
d.polygon([(0, 0), (int(W * 0.42), H // 2), (0, H)], fill=CHARCOAL)  # hoist triangle
cx, cy, r = int(W * 0.15), H // 2, int(H * 0.13)
d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=SAND, width=int(r * 0.32))
OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT)
print("wrote", OUT)
