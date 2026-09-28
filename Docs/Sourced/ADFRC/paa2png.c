/*
 * paa2png - convert Arma PAA textures (DXT1/DXT5, optional LZO mip compression) to PNG.
 *
 * Format notes (verified against KoffeinFlummi/armake paa2img.c and real ADFRC files):
 *   [u16 paatype]                        0xFF01=DXT1, 0xFF05=DXT5, 0xFF03=DXT3, 0x4444=ARGB4444...
 *   repeated tag:  "GGAT" [4-byte name] [u32 len] [len bytes]   (skipped until name == "SFFO")
 *   "SFFO" payload: u32 offsets[16]; offsets[0] = file offset of mip0 header
 *   mip0 header:   u16 width_raw (bit15 = LZO compressed, width &= 0x7FFF), u16 height,
 *                  u8[3] datalen, then datalen bytes of data
 *
 * Usage: paa2png <input.paa> <output.png>
 * Exit codes: 0 ok, 1 usage/IO, 2 bad format, 3 LZO failure, 4 DXT decode, 5 png write
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define MINILZO_LIBRARY
#include "minilzo.h"

#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

#define PAAT_DXT1 0xFF01
#define PAAT_DXT3 0xFF03
#define PAAT_DXT5 0xFF05

static uint16_t rd16(const uint8_t *p) { return (uint16_t)(p[0] | (p[1] << 8)); }
static uint32_t rd32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

/* Expand one RGB565 colour to 8-bit. */
static void rgb565(uint16_t c, int out[3]) {
    int r = (c >> 11) & 0x1F, g = (c >> 5) & 0x3F, b = c & 0x1F;
    out[0] = (r << 3) | (r >> 2);
    out[1] = (g << 2) | (g >> 4);
    out[2] = (b << 3) | (b >> 2);
}

/* Decode a 4x4 DXT colour block (8 bytes) into 16 RGBA pixels at (bx,by). */
static void decode_color_block(const uint8_t *blk, int four_color,
                               uint8_t *img, int width, int height, int bx, int by) {
    uint16_t c0 = rd16(blk), c1 = rd16(blk + 2);
    uint32_t idx = rd32(blk + 4);
    int pal[4][4]; /* rgba */

    rgb565(c0, pal[0]); pal[0][3] = 255;
    rgb565(c1, pal[1]); pal[1][3] = 255;

    if (four_color || c0 > c1) {
        for (int i = 0; i < 3; i++) {
            pal[2][i] = (2 * pal[0][i] + pal[1][i]) / 3;
            pal[3][i] = (pal[0][i] + 2 * pal[1][i]) / 3;
        }
        pal[2][3] = pal[3][3] = 255;
    } else {
        for (int i = 0; i < 3; i++) {
            pal[2][i] = (pal[0][i] + pal[1][i]) / 2;
            pal[3][i] = 0;
        }
        pal[2][3] = 255;
        pal[3][3] = 0; /* transparent black */
    }

    for (int row = 0; row < 4; row++) {
        for (int col = 0; col < 4; col++) {
            int px = bx * 4 + col, py = by * 4 + row;
            if (px >= width || py >= height) continue;
            int ci = (int)((idx >> (2 * (row * 4 + col))) & 3u);
            uint8_t *dst = img + (size_t)(py * width + px) * 4;
            dst[0] = (uint8_t)pal[ci][0];
            dst[1] = (uint8_t)pal[ci][1];
            dst[2] = (uint8_t)pal[ci][2];
            dst[3] = (uint8_t)pal[ci][3];
        }
    }
}

/* Decode a DXT5 alpha block (8 bytes): returns 16 alpha values. */
static void decode_alpha_block(const uint8_t *blk, int alpha[16]) {
    int a0 = blk[0], a1 = blk[1];
    int tab[8];
    tab[0] = a0; tab[1] = a1;
    if (a0 > a1) {
        for (int i = 1; i <= 6; i++) tab[i + 1] = ((7 - i) * a0 + i * a1) / 7;
    } else {
        for (int i = 1; i <= 4; i++) tab[i + 1] = ((5 - i) * a0 + i * a1) / 5;
        tab[6] = 0;
        tab[7] = 255;
    }
    uint64_t bits = 0;
    for (int i = 0; i < 6; i++) bits |= (uint64_t)blk[2 + i] << (8 * i);
    for (int i = 0; i < 16; i++) alpha[i] = tab[(bits >> (3 * i)) & 7u];
}

static int convert(const char *src, const char *dst) {
    FILE *f = fopen(src, "rb");
    if (!f) { fprintf(stderr, "open failed: %s\n", src); return 1; }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (sz < 32) { fclose(f); fprintf(stderr, "too small: %s\n", src); return 2; }
    uint8_t *buf = (uint8_t *)malloc((size_t)sz);
    if (!buf || fread(buf, 1, (size_t)sz, f) != (size_t)sz) { fclose(f); free(buf); return 1; }
    fclose(f);

    uint16_t paatype = rd16(buf);
    if (paatype != PAAT_DXT1 && paatype != PAAT_DXT5 && paatype != PAAT_DXT3) {
        fprintf(stderr, "unsupported paatype 0x%04X: %s\n", paatype, src);
        free(buf);
        return 2;
    }

    /* Walk tags until "SFFO" (offset table); first u32 = mip0 offset.
     * Some files (official ImageToPAA output) leave the offset table as
     * 0xFF filler; in that case the mip chain simply follows the header,
     * 2 bytes (palette) after the end of the SFFO payload. */
    size_t pos = 2;
    long mip0 = -1;
    size_t fallback = (size_t)-1;
    for (int guard = 0; guard < 64; guard++) {
        if (pos + 12 > (size_t)sz) break;
        if (memcmp(buf + pos, "GGAT", 4) != 0) break;
        char name[5];
        memcpy(name, buf + pos + 4, 4);
        name[4] = 0;
        uint32_t len = rd32(buf + pos + 8);
        if (strcmp(name, "SFFO") == 0) {
            if (pos + 12 + 4 <= (size_t)sz) {
                long cand = (long)rd32(buf + pos + 12);
                if (cand >= 0 && (size_t)cand + 7 <= (size_t)sz) mip0 = cand;
            }
            fallback = pos + 12 + (size_t)len + 2; /* +2: palette u16 */
            break;
        }
        pos += 12 + (size_t)len;
    }
    if (mip0 < 0 && fallback != (size_t)-1 && fallback + 7 <= (size_t)sz) {
        mip0 = (long)fallback;
    }
    if (mip0 < 0 || (size_t)mip0 + 7 > (size_t)sz) {
        fprintf(stderr, "no SFFO/mip offset: %s\n", src);
        free(buf);
        return 2;
    }

    uint16_t w_raw = rd16(buf + mip0);
    uint16_t height = rd16(buf + mip0 + 2);
    uint32_t datalen = (uint32_t)buf[mip0 + 4] | ((uint32_t)buf[mip0 + 5] << 8) | ((uint32_t)buf[mip0 + 6] << 16);
    int compressed = (w_raw & 0x8000) != 0;
    int width = (int)(w_raw & 0x7FFF);
    int h = (int)height;
    const uint8_t *data = buf + mip0 + 7;

    if (width <= 0 || h <= 0 || (width % 4) || (h % 4)) {
        fprintf(stderr, "bad dimensions %dx%d: %s\n", width, h, src);
        free(buf);
        return 2;
    }
    if ((size_t)mip0 + 7 + datalen > (size_t)sz) {
        /* Seen in official ImageToPAA output (e.g. TacGear_NOHQ): the stored
         * datalen is garbage/overlong but the mip data runs exactly to EOF.
         * Clamp and continue; LZO length check still validates the stream. */
        fprintf(stderr, "warning: datalen overruns EOF, clamping: %s\n", src);
        datalen = (uint32_t)((size_t)sz - ((size_t)mip0 + 7));
    }

    size_t expected = (size_t)width * (size_t)h;          /* DXT5/DXT3: 16 bytes per 16 px */
    if (paatype == PAAT_DXT1) expected /= 2;             /* DXT1: 8 bytes per 16 px */

    uint8_t *dxt = (uint8_t *)calloc(1, expected ? expected : 1);
    if (!dxt) { free(buf); return 1; }

    if (compressed) {
        lzo_uint out_len = (lzo_uint)expected;
        int rc = lzo1x_decompress_safe(data, (lzo_uint)datalen, dxt, &out_len, NULL);
        if (rc != LZO_E_OK) {
            if (out_len == 0 || out_len > (lzo_uint)expected) {
                fprintf(stderr, "LZO decompress failed (rc=%d, %lu vs expected %zu): %s\n",
                        rc, (unsigned long)out_len, expected, src);
                free(dxt);
                free(buf);
                return 3;
            }
            /* Truncated stream in the published file: keep decoded bytes. */
            fprintf(stderr, "warning: truncated LZO stream (%lu < %zu), tail zero-filled: %s\n",
                    (unsigned long)out_len, expected, src);
        } else if (out_len != (lzo_uint)expected) {
            fprintf(stderr, "warning: LZO short (%lu < %zu), tail zero-filled: %s\n",
                    (unsigned long)out_len, expected, src);
        }
    } else {
        if ((size_t)datalen < expected) {
            fprintf(stderr, "raw mip too short (%u < %zu): %s\n", datalen, expected, src);
            free(dxt);
            free(buf);
            return 2;
        }
        memcpy(dxt, data, expected);
    }
    free(buf);

    size_t img_sz = (size_t)width * (size_t)h * 4;
    uint8_t *img = (uint8_t *)malloc(img_sz);
    if (!img) { free(dxt); return 1; }
    memset(img, 0, img_sz);

    int bx_count = width / 4, by_count = h / 4;
    if (paatype == PAAT_DXT1) {
        for (int by = 0; by < by_count; by++)
            for (int bx = 0; bx < bx_count; bx++)
                decode_color_block(dxt + (size_t)(by * bx_count + bx) * 8, 0, img, width, h, bx, by);
    } else {
        for (int by = 0; by < by_count; by++) {
            for (int bx = 0; bx < bx_count; bx++) {
                const uint8_t *blk = dxt + (size_t)(by * bx_count + bx) * 16;
                int alpha[16];
                decode_alpha_block(blk, alpha);
                decode_color_block(blk + 8, 1, img, width, h, bx, by);
                for (int row = 0; row < 4; row++) {
                    for (int col = 0; col < 4; col++) {
                        int px = bx * 4 + col, py = by * 4 + row;
                        if (px >= width || py >= h) continue;
                        img[(size_t)(py * width + px) * 4 + 3] = (uint8_t)alpha[row * 4 + col];
                    }
                }
            }
        }
    }
    free(dxt);

    if (!stbi_write_png(dst, width, h, 4, img, width * 4)) {
        fprintf(stderr, "png write failed: %s\n", dst);
        free(img);
        return 5;
    }
    free(img);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s <in.paa> <out.png>\n", argv[0]);
        return 1;
    }
    if (lzo_init() != LZO_E_OK) {
        fprintf(stderr, "lzo_init failed\n");
        return 3;
    }
    return convert(argv[1], argv[2]);
}
