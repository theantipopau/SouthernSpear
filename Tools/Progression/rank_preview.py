"""
Southern Spear - rank ladder preview (ADR-034). Runs without Unreal.

Reads the rank table from Config/DefaultGame.ini, compiles
Tools/Progression/insignia_sheet.cpp against the game's own engine-free headers
(SSInsigniaRaster.h, SSServiceLevelMath.h), prints the level/XP bands and
checks, and writes a PNG sheet of every insignia (brass on field dark, in
rank order) to Build/rank_insignia_sheet.png (or the path given).

    python Tools/Progression/rank_preview.py [out.png]

Exit 0 only if every rank draws (or, for Private, draws nothing) and the level
maths holds at all 100 thresholds.
"""

import os
import re
import struct
import subprocess
import sys
import tempfile
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INI = os.path.join(ROOT, "Config", "DefaultGame.ini")
CORE_PUBLIC = os.path.join(ROOT, "Plugins", "SouthernSpearCore", "Source", "SouthernSpearCore", "Public")
SIZE = 96


def read_settings():
    text = open(INI, encoding="utf-8").read()
    section = text.split("[/Script/SouthernSpearCore.SSRankSettings]", 1)[1].split("\n[", 1)[0]
    value = lambda key: re.search(r"^%s=([\d.]+)" % key, section, re.M).group(1)
    ranks = []
    for line in re.findall(r"^\+Ranks=\((.*)\)\s*$", section, re.M):
        abbrev = re.search(r'Abbreviation=NSLOCTEXT\("[^"]*","[^"]*","([^"]*)"\)', line).group(1)
        get = lambda key: re.search(r"\b%s=(\w+)" % key, line).group(1)
        flag = lambda key: "1" if get(key) == "True" else "0"
        ranks.append((abbrev, get("MinLevel"), get("Chevrons"), get("Pips"), flag("bCrown"), flag("bCrest"), flag("bSwordAndBaton")))
    return value("MaxLevel"), value("LevelXpScale"), value("LevelXpExponent"), ranks


def write_png(path, width, height, alpha):
    # Brass (#C9A24A-ish) over field dark, one pixel of margin between tiles is the art's own margin.
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            a = alpha[y * width + x] / 255.0
            bg = (24, 28, 22)
            fg = (214, 178, 96)
            row += bytes(int(bg[i] + (fg[i] - bg[i]) * a) for i in range(3))
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    open(path, "wb").write(png)


def main():
    out_png = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "Build", "rank_insignia_sheet.png")
    max_level, scale, exponent, ranks = read_settings()
    with tempfile.TemporaryDirectory() as tmp:
        exe = os.path.join(tmp, "insignia_sheet")
        subprocess.run(["g++", "-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror", "-I", CORE_PUBLIC,
                        os.path.join(ROOT, "Tools", "Progression", "insignia_sheet.cpp"), "-o", exe], check=True)
        raw = os.path.join(tmp, "sheet.raw")
        stdin = "\n".join(" ".join(r) for r in ranks) + "\n"
        result = subprocess.run([exe, raw, str(SIZE), scale, exponent, max_level], input=stdin, text=True, capture_output=True)
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        alpha = open(raw, "rb").read()
    write_png(out_png, SIZE * len(ranks), SIZE, alpha)
    print("order: " + "  ".join(r[0] for r in ranks))
    print("wrote " + out_png)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
