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
MENU = os.path.join(SRC, "mainmenu.png")        # 1536x1024, main menu key art (clean)
LOADING = os.path.join(SRC, "loadingscreen.png")  # 1536x1024, designed title screen
CONCEPT1 = os.path.join(SRC, "conceptart1.png")    # 1536x1024
CONCEPT2 = os.path.join(SRC, "conceptart2.png")    # 1672x941

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


def save_alpha(img, name, stem, width):
    """Write an alpha-carrying derivative set: AVIF, WebP and PNG.

    The brand marks are RGBA, and a 420px plate saved as indexed PNG runs to
    55 KB. AVIF and WebP both carry the alpha channel and come in around a
    tenth of that, which matters here because the lockup sits on the critical
    path as the first thing under the header.
    """
    img = at_width(img, width)
    target = ensure(os.path.dirname(name))
    base = os.path.join(target, stem)
    img.save(base + ".avif", quality=58, method=6)
    img.save(base + ".webp", quality=82, method=6)
    # The PNG is the fallback for browsers without AVIF or WebP, so it still
    # has to be a reasonable size. An indexed palette cuts it by roughly 6x
    # and the marks are flat colour, so there is nothing to lose.
    img.quantize(colors=192, method=Image.FASTOCTREE).save(base + ".png", optimize=True)
    return img.size


def build_brand():
    logo = Image.open(LOGO).convert("RGBA")

    plate = logo.crop(PLATE)
    for width in (256, 420):
        size = save_alpha(plate, "brand/southern-spear-logo-stacked",
                          "southern-spear-logo-stacked-{}".format(width), width)
        print("  brand/southern-spear-logo-stacked-{}.*".format(width), size)

    # Emblem-only mark: the spear, the continent and the Southern Cross, cropped
    # from inside the plate. A crop, not a redraw. The nav renders it at 44px.
    emblem = logo.crop(EMBLEM_ART)
    for width in (128, 256):
        size = save_alpha(emblem, "brand/southern-spear-emblem",
                          "southern-spear-emblem-{}".format(width), width)
        print("  brand/southern-spear-emblem-{}.*".format(width), size)


    # Favicon suite, derived from the same emblem crop.
    icon = at_width(emblem, 256).crop((16, 0, 240, 224)).resize((256, 256), Image.LANCZOS)
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
    """Art-directed crops of the main-menu key art.

    Unlike the earlier loading screen, mainmenu.png carries no composited logo,
    wordmark or interface text, so nothing has to be avoided and the whole
    composition is available. The phone crop is taken from the right, where the
    sky and the light source sit, because a 3:2 frame cropped to a tall phone
    viewport otherwise loses the subject entirely.
    """
    art = Image.open(MENU).convert("RGB")
    w, h = art.size

    yield "hero/hero-outback-wide", art, None
    yield "hero/hero-outback-mobile", art.crop((w - 700, 0, w, h)), None


def build_hero():
    for name, img, _ in hero_crops():
        stem = name.split("/")[-1]
        widths = [640, 960, 1280, 1536] if stem.endswith("wide") else [480, 700]
        for width in widths:
            save(at_width(img, width), name, "{}-{}".format(stem, width))
        print("  {}-* (source {}x{})".format(stem, img.width, img.height))


def build_concepts():
    """Gallery imagery, labelled honestly by the page rather than by the file.

    Every item here is concept art. None of it is captured gameplay, and the
    page labels it accordingly.
    """
    menu = Image.open(MENU).convert("RGB")
    loading = Image.open(LOADING).convert("RGB")

    save(menu, "concepts/main-menu-concept-01", "main-menu-concept-01", jpeg_max=1536)
    print("  concepts/main-menu-concept-01-* (from mainmenu.png)")

    # The designed title screen, kept as its own gallery item. It has the emblem
    # and menu labels composited into the pixels, which is part of what it is.
    save(loading, "concepts/loading-screen-concept-01", "loading-screen-concept-01",
         jpeg_max=1536)
    print("  concepts/loading-screen-concept-01-* (from loadingscreen.png)")

    save(Image.open(CONCEPT1).convert("RGB"), "concepts/concept-art-01",
         "concept-art-01", jpeg_max=1536)
    print("  concepts/concept-art-01-* (from conceptart1.png)")

    save(Image.open(CONCEPT2).convert("RGB"), "concepts/concept-art-02",
         "concept-art-02", jpeg_max=1672)
    print("  concepts/concept-art-02-* (from conceptart2.png)")

    # Detail crops of the hero art, so the gallery is not one image repeated.
    w, h = menu.size
    save(menu.crop((0, 0, 768, 512)), "concepts/environment-detail-01",
         "environment-detail-01", jpeg_max=768)
    save(menu.crop((w - 768, h - 432, w, h)), "concepts/environment-detail-02",
         "environment-detail-02", jpeg_max=768)
    print("  concepts/environment-detail-0{1,2}-*")


def build_social():
    art = Image.open(MENU).convert("RGB")
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
