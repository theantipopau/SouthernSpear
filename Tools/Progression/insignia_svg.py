"""
Southern Spear - the rank insignia sheet as an SVG, for the README (ADR-034). Runs without Unreal.

Compiles the same engine-free rasteriser the game draws the scoreboard insignia with
(SSInsigniaRaster.h, via Tools/Progression/insignia_sheet.cpp), reads the rank ladder from
Config/DefaultGame.ini, and writes one brass tile per rank with its abbreviation and first level.
SVG because the repository's PNGs live in Git LFS and GitHub shows only pointers (R-14).

    python Tools/Progression/insignia_svg.py [out.svg]      # default Site/assets/readme/rank-insignia.svg
"""

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rank_preview as rp  # noqa: E402

TILE = 64          # rasterised size, px
SCALE = 1          # SVG units per pixel
LEVELS = 6         # alpha quantisation steps
BRASS = "#D6B260"
FIELD = "#181C16"
LABEL = "#C9C3B0"


def raster(ranks, scale, exponent, max_level):
    with tempfile.TemporaryDirectory() as tmp:
        exe = os.path.join(tmp, "insignia_sheet")
        subprocess.run(["g++", "-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror", "-I", rp.CORE_PUBLIC,
                        os.path.join(rp.ROOT, "Tools", "Progression", "insignia_sheet.cpp"), "-o", exe], check=True)
        raw = os.path.join(tmp, "sheet.raw")
        stdin = "\n".join(" ".join(r) for r in ranks) + "\n"
        subprocess.run([exe, raw, str(TILE), scale, exponent, max_level], input=stdin, text=True,
                       capture_output=True, check=True)
        return open(raw, "rb").read()


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(rp.ROOT, "Site", "assets", "readme", "rank-insignia.svg")
    max_level, scale, exponent, ranks = rp.read_settings()
    alpha = raster(ranks, scale, exponent, max_level)
    count = len(ranks)
    width = TILE * count
    if len(alpha) != width * TILE:
        raise SystemExit("unexpected raster size {} for {} ranks".format(len(alpha), count))
    gap, label_h = 10, 34
    cell = TILE + gap
    svg_w, svg_h = cell * count + gap, TILE + label_h + gap * 2
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {} {}" width="{}" height="{}" '
             'role="img" aria-label="Southern Spear rank insignia, Private to General">'.format(svg_w, svg_h, svg_w * 2, svg_h * 2),
             '<rect width="100%" height="100%" rx="10" fill="{}"/>'.format(FIELD)]
    for index, rank in enumerate(ranks):
        abbrev, min_level = rank[0], rank[1]
        ox, oy = gap + index * cell, gap
        parts.append('<g transform="translate({},{})">'.format(ox, oy))
        parts.append('<rect width="{0}" height="{0}" rx="6" fill="#222820"/>'.format(TILE))
        # One path per brightness step: "M x y h w v 1 h -w z" per horizontal run of equal alpha.
        runs = {}
        for y in range(TILE):
            x = 0
            while x < TILE:
                level = round(alpha[y * width + index * TILE + x] / 255 * (LEVELS - 1))
                start = x
                while x < TILE and round(alpha[y * width + index * TILE + x] / 255 * (LEVELS - 1)) == level:
                    x += 1
                if level:
                    runs.setdefault(level, []).append("M{} {}h{}v1h-{}z".format(start, y, x - start, x - start))
        for level in sorted(runs):
            parts.append('<path fill="{}" fill-opacity="{:.2f}" d="{}"/>'.format(BRASS, level / (LEVELS - 1), "".join(runs[level])))
        parts.append('<text x="{}" y="{}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" '
                     'font-size="11" font-weight="700" fill="{}">{}</text>'.format(TILE / 2, TILE + 16, LABEL, abbrev))
        parts.append('<text x="{}" y="{}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" '
                     'font-size="9" fill="{}">L{}</text>'.format(TILE / 2, TILE + 29, BRASS, min_level))
        parts.append('</g>')
    parts.append('</svg>')
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(parts) + "\n")
    print("wrote {} ({} ranks, {} KB)".format(out, count, os.path.getsize(out) // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
