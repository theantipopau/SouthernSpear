"""Southern Spear - offline probe of Fab material texture-parameter names.

The Fab character packs ship .uasset-only, so their material parameter names
are not visible from Python (UE 5.8 exposes no texture-parameter enumeration
API). FName entries are stored as plain strings in the package, so scanning
the binary recovers them. Read-only; used to build Tools/Unreal/setup_character_textures.py.

Usage: python Tools/Common/uv_material_params.py <file.uasset> [...]
"""

import re
import sys

# FName table entries are length-prefixed ASCII; keep plausible identifier-ish runs.
TOKEN = re.compile(rb"[A-Za-z_][A-Za-z0-9_ .\-]{2,48}")

# Noise that shows up in every material; drop it so real parameter names stand out.
BORING = {
    "None", "Default", "Material", "MaterialExpression", "TextureSample", "Sampler",
    "StaticSwitch", "VectorParameter", "ScalarParameter", "ShadingModel", "BlendMode",
    "TwoSided", "TwoSidedSign", "bCastDynamicShadowAsMasked", "OpacityMaskClipValue",
    "StartDeferredNaniteTextures", "HasNaniteFallback", "DisplacementMap", "WorldPosition",
    "PixelDepthOffset", "ShadeSmooth", "bUsedWithStaticLighting", "bUsedWithInstanced",
    "TranslucencyLightingMode", "bEnableSeparateTranslucency", "RefractionDepthBias",
    "TranslucencyShadowDensity", "TranslucencyMultipleScattering", "TranslucencyAmbientOcclusion",
    "AmbientOcclusionStrength", "Occlusion", "Specular", "Metallic", "Roughness", "Normal",
    "Emissive", "BaseColor", "Bump", "Tangent", "UV", "Color", "Param", "Texture",
    "Base", "Mask", "Alpha", "SSS", "Curvature", "AO", "ORM",
}


def names(path):
    with open(path, "rb") as fh:
        blob = fh.read()
    out = []
    for m in TOKEN.finditer(blob):
        s = m.group().decode("ascii", "replace").strip()
        if len(s) < 3 or s in BORING:
            continue
        if s not in out:
            out.append(s)
    return out


def main(paths):
    for p in paths:
        try:
            found = names(p)
        except OSError as exc:
            print("!! %s: %s" % (p, exc))
            continue
        print("== %s" % p)
        print("   " + ", ".join(found) if found else "   (no candidate names)")


if __name__ == "__main__":
    main(sys.argv[1:])
