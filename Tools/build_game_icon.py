"""Windows exe icon from Docs/images/logo.png -> Build/Windows/Application.ico
(Unreal's per-project game icon path). 64-256 px use the whole badge (rounded
corners transparent); 16-48 px use the spear-and-map centre, which stays
legible where the lettering would not. Run: python Tools/build_game_icon.py
The producer-supplied Docs/images/SouthernSpear.ico, when present, is installed as-is instead."""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Docs/images/logo.png"
SUPPLIED = ROOT / "Docs/images/SouthernSpear.ico"
OUT = ROOT / "Build/Windows/Application.ico"


def rounded(img, radius_frac):
    mask = Image.new("L", img.size, 0)
    r = int(img.size[0] * radius_frac)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.size[0] - 1, img.size[1] - 1], r, fill=255)
    img.putalpha(mask)
    return img


logo = Image.open(SRC).convert("RGB")
w, h = logo.size
badge = rounded(logo.crop((int(w * 0.085), int(h * 0.075), int(w * 0.918), int(h * 0.918))), 0.13)
centre = rounded(logo.crop((int(w * 0.2), int(h * 0.08), int(w * 0.8), int(h * 0.68))), 0.16)

frames = [(badge if s >= 64 else centre).resize((s, s), Image.LANCZOS) for s in (256, 128, 64, 48, 32, 24, 16)]
OUT.parent.mkdir(parents=True, exist_ok=True)
if SUPPLIED.exists():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(SUPPLIED.read_bytes())
    print("installed", SUPPLIED.name, "->", OUT)
else:
    frames[0].save(OUT, format="ICO", sizes=[f.size for f in frames], append_images=frames[1:])
    print("wrote", OUT, [f.size[0] for f in frames])
