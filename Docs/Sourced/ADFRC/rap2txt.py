#!/usr/bin/env python3
"""Decode binarised Arma config/material files (`\\0raP`) back to text.

About three quarters of the ADFRC `.rvmat` files ship in the binarised "rap"
container rather than as readable scripts, which makes their texture bindings
unreadable.  This is a faithful port of the derapifier in the Arma 3 Object
Builder (`io/config/derapifier.py`, which cites the BI community wiki's
"raP File Format - Elite"), plus a serializer that writes the result back out
as an ordinary Arma config script.

Container layout (all little-endian):
    [0..3]   b"\\x00raP"
    [4..11]  two u32 that the reference reader skips
    [12..15] u32 offset of the enum table, relative to the signature
    then     body: 1 empty-parent byte, compressed-uint entry count, entries
    at enum_offset: u32 count, then (asciiz name, 4 bytes) per enum

Entry tags:
    0 class (name, u32 body offset; body = parent asciiz + entry count + entries)
    1 property (sign, name asciiz, value)
    2 property with an implicit array value
    3 forward-declared class
    4 delete statement (dumped)
    5 property with the "extends" flag

Value signs: 0 asciiz string, 1 float, 2 long, 3 array.

Usage:  python rap2txt.py <root> [out_dir]
"""
import glob
import os
import struct
import sys

SIG = b"\x00raP"


class RAPError(Exception):
    pass


class Reader:
    __slots__ = ("f", "base")

    def __init__(self, f, base=0):
        self.f = f
        self.base = base

    def tell(self):
        return self.f.tell() - self.base

    def seek(self, off):
        self.f.seek(self.base + off)

    def peek(self):
        return self.f.read(1)

    def byte(self):
        b = self.f.read(1)
        if not b:
            raise RAPError("unexpected EOF")
        return b[0]

    def raw(self, n):
        b = self.f.read(n)
        if len(b) != n:
            raise RAPError("unexpected EOF")
        return b

    def u32(self):
        return struct.unpack("<I", self.raw(4))[0]

    def f32(self):
        return struct.unpack("<f", self.raw(4))[0]

    def asciiz(self):
        out = bytearray()
        while True:
            c = self.byte()
            if c == 0:
                break
            out.append(c)
        return out.decode("latin1")

    def compressed_uint(self):
        """Variable-length uint, high bit = continuation."""
        shift = 0
        result = 0
        while True:
            b = self.byte()
            result |= (b & 0x7F) << shift
            if not b & 0x80:
                return result
            shift += 7


# ------------------------------------------------------------- compression

def lzss_decompress(src, max_out=1 << 22):
    """BIS LZSS (N=4096, F=18, threshold=2), as in Arma3ObjectBuilder.

    Some ADFRC materials ship as an LZSS-compressed rap container: the very
    first bytes are the LZSS flag stream, not a `\0raP` signature, which is why
    a plain rap reader rejects them with a nonsense entry sign.  Decompressing
    the whole stream and re-checking the signature identifies them.
    """
    N, F, THRESHOLD = 4096, 18, 2
    text_buf = bytearray(b" " * (N + F - 1))
    out = bytearray()
    r = N - F
    flags = 0
    pos = 0
    n = len(src)
    while pos < n and len(out) < max_out:
        flags >>= 1
        if (flags & 256) == 0:
            if pos >= n:
                break
            flags = src[pos] | 0xFF00
            pos += 1
        if flags & 1:
            if pos >= n:
                break
            out.append(src[pos])
            pos += 1
            text_buf[r] = out[-1]
            r = (r + 1) & (N - 1)
        else:
            if pos + 1 >= n:
                break
            i = src[pos]
            j = src[pos + 1]
            pos += 2
            i |= (j & 0xF0) << 4
            j = (j & 0x0F) + THRESHOLD
            ii = r - i
            for _ in range(j + 1):
                if len(out) >= max_out:
                    break
                c = text_buf[ii & (N - 1)]
                out.append(c)
                text_buf[r] = c
                r = (r + 1) & (N - 1)
                ii += 1
    return bytes(out)


def looks_like_rap(data):
    return data[:4] == SIG


# ------------------------------------------------------------------ values

class Str:
    kind = "str"

    def __init__(self, v):
        self.v = v

    def text(self):
        # Arma text config uses `\` as the path separator verbatim; only the
        # quote needs escaping, or every texture path comes out doubled.
        return '"%s"' % self.v.replace('"', '\\"')


class Float:
    kind = "float"

    def __init__(self, v):
        self.v = v

    def text(self):
        return repr(self.v)


class Long:
    kind = "long"

    def __init__(self, v):
        self.v = v

    def text(self):
        return str(self.v)


class Arr:
    kind = "array"

    def __init__(self, members, extends=False):
        self.members = members
        self.extends = extends

    def text(self):
        return "{" + ",".join(m.text() for m in self.members) + "}"


class Cls:
    kind = "class"

    def __init__(self, name, parent=None, external=False):
        self.name = name
        self.parent = parent
        self.external = external
        self.entries = []

    def text(self, indent=0):
        pad = "\t" * indent
        head = "%sclass %s" % (pad, self.name)
        if self.parent:
            head += " : %s" % self.parent
        if not self.entries:
            return head + "\n%s{\n%s};\n" % (pad, pad)
        body = "".join(e.text(indent + 1) for e in self.entries)
        return "%s\n%s{\n%s%s};\n" % (head, pad, body, pad)


class Prop:
    kind = "prop"

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def text(self, indent=0):
        pad = "\t" * indent
        if isinstance(self.value, Arr):
            return "%s%s[]=%s;\n" % (pad, self.name, self.value.text())
        return "%s%s=%s;\n" % (pad, self.name, self.value.text())


# ------------------------------------------------------------------ reader

def read_value(r, sign):
    if sign == 0:
        return Str(r.asciiz())
    if sign == 1:
        return Float(r.f32())
    if sign == 2:
        return Long(r.u32())
    if sign == 3:
        return read_array(r)
    raise RAPError("unsupported value sign %d" % sign)


def read_array(r):
    count = r.compressed_uint()
    return Arr([read_value(r, r.byte()) for _ in range(count)])


def read_class(r, main):
    name = r.asciiz()
    offset = r.u32()
    current = r.tell()
    r.seek(offset)
    parentname = r.asciiz()
    parent = None
    if parentname:
        # A config.bin routinely inherits from vanilla Arma classes
        # (B_Soldier_base_F, V_PlateCarrier1_blk, NVGoggles) that live in the
        # game data, not in this file.  Record the name rather than failing, so
        # the rest of the class still decodes.
        parent = next((c for c in main if c.name == parentname), None)
        if parent is None:
            parent = parentname
    out = Cls(name, parent)
    out.entries = read_entries(r, r.compressed_uint(), main)
    r.seek(current)
    return out


def read_entries(r, count, main):
    out = []
    for _ in range(count):
        sign = r.byte()
        if sign == 0:
            out.append(read_class(r, main))
        elif sign == 1:
            vsign = r.byte()
            out.append(Prop(r.asciiz(), read_value(r, vsign)))
        elif sign == 2:
            out.append(Prop(r.asciiz(), read_value(r, 3)))
        elif sign == 3:
            out.append(Cls(r.asciiz(), None, external=True))
        elif sign == 4:
            r.asciiz()                      # delete statement, dropped
        elif sign == 5:
            name = r.asciiz()
            r.raw(4)                        # flag, always 1
            val = read_value(r, 3)
            val.extends = True
            out.append(Prop(name, val))
        else:
            raise RAPError("unsupported entry sign %d" % sign)
    return out


def decode(data):
    """Decode a rap container, transparently LZSS-decompressing if needed."""
    if not looks_like_rap(data):
        plain = lzss_decompress(data)
        if not looks_like_rap(plain):
            i = data.find(SIG)
            if i < 0:
                raise RAPError("no \\0raP signature, and not LZSS-compressed")
            plain = data
        data = plain
    import io
    r = Reader(io.BytesIO(data), base=0)
    r.seek(4)
    r.raw(8)                                # skipped by the reference reader
    enum_offset = r.u32()
    r.byte()                                # empty parent byte
    root = read_entries(r, r.compressed_uint(), [])
    return root, enum_offset


def serialise(root):
    return "".join(e.text(0) for e in root)


def main():
    root_dir = sys.argv[1] if len(sys.argv) > 1 else r"E:\SouthernSpear\Content\Sourced\ADF_Extracted"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(root_dir, "Materials_Text")

    targets = []
    for ext in (".rvmat", ".bin"):
        for p in glob.glob(os.path.join(root_dir, "**", "*" + ext), recursive=True):
            targets.append(p)

    ok = skipped = fail = 0
    fails = []
    for p in targets:
        data = open(p, "rb").read()
        if SIG not in data and not (data[:1] == b"\x5f" or data[:2] == b"_\x00"):
            skipped += 1
            continue
        rel = os.path.relpath(p, root_dir)
        # Keep the original extension so .rvmat and config.bin stay
        # distinguishable, and provenance survives the decode.
        dst = os.path.join(out_dir, rel + ".txt")
        if os.path.exists(dst) and os.path.getsize(dst) > 0:
            ok += 1
            continue
        try:
            entries, _enum = decode(data)
            text = serialise(entries)
            if not text.strip():
                raise RAPError("decoded to nothing")
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w", encoding="utf-8") as fh:
                fh.write(text)
            ok += 1
        except Exception as ex:  # noqa: BLE001
            fail += 1
            if len(fails) < 15:
                fails.append((rel, repr(ex)))

    print("scanned : %d" % len(targets))
    print("decoded : %d" % ok)
    print("skipped : %d (already plaintext / not rap)" % skipped)
    print("failed  : %d" % fail)
    for r, e in fails:
        print("   FAIL %-70s %s" % (r, e))
    print("-> %s" % out_dir)


if __name__ == "__main__":
    main()
