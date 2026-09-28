#!/usr/bin/env python3
"""Convert Arma .wss sounds to standard .wav.

WSS0 layout (verified against ADFRC files):
  char[4] "WSS0"
  u32     unknown (0)
  u16     version (1)
  u16     channels
  u32     sample rate
  u32     byte rate
  u16     block align
  u16     bits per sample
  u16     unknown (0)
  s16 PCM data until EOF
"""
import os
import struct
import sys
import wave

EX = r"E:\SouthernSpear\Content\Sourced\ADF_Extracted"


def convert(path):
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:4] != b"WSS0":
        raise ValueError("not WSS0")
    (unknown, version, channels, rate, byte_rate, align, bits, pad) = \
        struct.unpack("<IHHIIHHH", data[4:26])
    pcm = data[26:]
    if align == 0:
        align = channels * bits // 8
    if byte_rate and byte_rate != rate * align:
        byte_rate = rate * align
    out = path + ".wav.tmp"
    with wave.open(out, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(bits // 8)
        w.setframerate(rate)
        w.writeframes(pcm)
    os.replace(out, path[:-4] + ".wav" if path.lower().endswith(".wss") else path + ".wav")
    return channels, rate, bits, len(pcm)


def main():
    n = ok = 0
    for r, _d, fs in os.walk(EX):
        for name in fs:
            if not name.lower().endswith(".wss"):
                continue
            src = os.path.join(r, name)
            dst = os.path.join(r, name[:-4] + ".wav")
            n += 1
            if os.path.exists(dst):
                ok += 1
                continue
            try:
                convert(src)
                ok += 1
            except Exception as ex:  # noqa: BLE001
                print("FAIL", os.path.relpath(src, EX), "->", ex)
    print(f"converted {ok}/{n} wss files")


if __name__ == "__main__":
    main()
    sys.exit(0)
