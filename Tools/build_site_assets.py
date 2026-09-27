#!/usr/bin/env python3
"""Build the Southern Spear website's optimised image derivatives.

Source-of-truth artwork lives in Docs/images/ and is never modified. Everything
this script writes goes to Site/assets/ as a web derivative, so the publishing
step (Tools/publish_site.py) only ever copies finished, correctly named files.

Brand variants are strict crops of the approved source: nothing is redrawn, the
spear, the Southern Cross and the approved proportions are untouched, and the
monochrome footer mark is a CSS filter rather than a second drawing.

Usage:
    python Tools/build_site_assets.py
    python Tools/build_site_assets.py --clean     # remove Site/assets first
"""

import argparse
import os
import shutil

from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Docs", "images")
OUT = os.path.join(ROOT, "Site", "assets")

# Approved source files, and the geometry measured off them. These bounds were
# found by profiling the alpha and luminance channels of the originals, not by
# eye, so a re-run on a re-exported logo still lands on the same artwork.
LOGO = os.path.join(SRC, "logo.png")            # 1024x1024 RGBA, full plate
MENU = os.path.join(SRC, "loadingscreen.png")   # 1536x1024, main menu / loading screen

# logo.png: opaque plate spans x 80..943, y 75..946. The wordmark inside the plate
# starts at y~705 (first dense light row), so everything above it is emblem.
PLATE = (80, 75, 944, 947)
EMBLEM_ART = (132, 140, 894, 700)   # spear + continent + Southern Cross, clear of the plate border
LOCKUP = PLATE                       # emblem + approved lettering, as approved


def ensure(*parts):
    path = os.path.join(OUT, *parts)
    os.makedirs(path, exist_ok=True)
    return path


def at_width(img, width):
    """Scale to an exact width. Never upscales past the source, so a 1536px
    source never produces a fake 2560px derivative."""
    width = min(width, img.width)
    if width == img.width:
        return img
    return img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)


def save(img, name, stem, quality=78, avif_q=52, webp_q=76, jpeg_max=None):
    """Write a derivative set at the given size."""
    if jpeg_max:
        img = at_width(img, jpeg_max)

    target = ensure(os.path.dirname(name))
    base = os.path.join(target, stem)

    if img.mode in ("RGBA", "LA", "P"):
        img.save(base + ".png", optimize=True)
        return [stem + ".png"]

    written = []
    img.save(base + ".avif", quality=avif_q, method=6)
    written.append(stem + ".avif")
    img.save(base + ".webp", quality=webp_q, method=6)
    written.append(stem + ".webp")
    img.save(base + ".jpg", quality=quality, optimize=True, progressive=True)
    written.append(stem + ".jpg")
    return written


def build_brand():
    logo = Image.open(LOGO).convert("RGBA")
    plate = at_width(logo.crop(PLATE), 420)
    plate.quantize(colors=192, method=Image.FASTOCTREE).save(
        os.path.join(ensure("brand"), "southern-spear-logo-stacked.png"), optimize=True)
    print("  brand/southern-spear-logo-stacked.png", plate.size)

    # Emblem-only mark: the spear, the continent and the Southern Cross, cropped
    # from inside the plate. A crop, not a redraw. The nav renders it at 44px, so
    # 256px is already 6x oversampled and keeps the file in the low kilobytes.
    emblem = logo.crop(EMBLEM_ART)
    emblem = emblem.resize((256, round(256 * emblem.height / emblem.width)), Image.LANCZOS)
    emblem.quantize(colors=192, method=Image.FASTOCTREE).save(
        os.path.join(ensure("brand"), "southern-spear-emblem.png"), optimize=True)
    print("  brand/southern-spear-emblem.png", emblem.size)

    # Favicon suite, derived from the same emblem crop.
    icon = emblem.crop((16, 0, 240, 224)).resize((256, 256), Image.LANCZOS)
    for px in (32, 48, 96, 180, 192, 512):
        icon.resize((px, px), Image.LANCZOS).convert("RGBA").quantize(
            colors=128, method=Image.FASTOCTREE).save(
            os.path.join(OUT, "favicon-{}.png".format(px)), optimize=True)
    icon.resize((180, 180), Image.LANCZOS).convert("RGBA").quantize(
        colors=128, method=Image.FASTOCTREE).save(
        os.path.join(OUT, "apple-touch-icon.png"), optimize=True)
    icon.resize((32, 32), Image.LANCZOS).save(os.path.join(OUT, "favicon.ico"), sizes=[(16, 16), (32, 32)])
    print("  favicon suite, ico, apple-touch-icon")


def hero_crops():
    """Art-directed crops of the main-menu artwork.

    The source is 1536x1024. Desktop keeps the whole composition; the portrait
    crop favours the sunset valley on the right, which is the part of the frame
    that still reads when a phone crops a 3:2 image to 9:19.5.
    """
    art = Image.open(MENU).convert("RGB")
    w, h = art.size

    wide = art
    yield "hero/hero-outback-wide", wide, None

    # Phone portrait, right-weighted: sunset, valley and gorge. Cropping from
    # x=916 clears the emblem plate, so the phone hero is pure landscape and the
    # brand is carried by the navigation mark rather than by a second wordmark.
    yield "hero/hero-outback-mobile", art.crop((916, 0, w, h)), None


def build_hero():
    for name, img, _ in hero_crops():
        stem = name.split("/")[-1]
        widths = [640, 960, 1280, 1536] if stem.endswith("wide") else [480, 700]
        for width in widths:
            save(at_width(img, width), name, "{}-{}".format(stem, width))
        print("  {}-* (source {}x{})".format(stem, img.width, img.height))


def build_concepts():
    """Gallery imagery, labelled honestly by the page rather than by the file."""
    art = Image.open(MENU).convert("RGB")
    w, h = art.size

    save(art, "concepts/main-menu-concept-01", "main-menu-concept-01", jpeg_max=1536)
    print("  concepts/main-menu-concept-01-*")

    # Detail crops of the same artwork, so the gallery is not one image
    # repeated. Both are chosen to avoid the composited corner labels and the
    # wordmark, which occupy the frame edges and the centre band respectively.
    save(art.crop((0, 256, 768, 768)), "concepts/environment-detail-01",
         "environment-detail-01", jpeg_max=768)
    save(art.crop((768, 616, 1536, 1024)), "concepts/environment-detail-02",
         "environment-detail-02", jpeg_max=768)
    print("  concepts/environment-detail-0{1,2}-*")


def build_social():
    art = Image.open(MENU).convert("RGB")
    # 1200x630 social card: centre the composition, keep the sunset on the right.
    target_ratio = 1200 / 630
    w, h = art.size
    new_h = round(w / target_ratio)
    top = max(0, (h - new_h) // 2 - 40)
    card = art.crop((0, top, w, min(h, top + new_h)))
    if card.height != 630:
        card = card.resize((1200, 630), Image.LANCZOS)
    card.save(os.path.join(ensure("social"), "social-preview-1200x630.jpg"),
              quality=74, optimize=True, progressive=True)
    print("  social/social-preview-1200x630.jpg", card.size)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", action="store_true")
    args = ap.parse_args()

    if args.clean and os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)

    print("building website assets into", OUT)
    build_brand()
    build_hero()
    build_concepts()
    build_social()
    print("done")


if __name__ == "__main__":
    main()
