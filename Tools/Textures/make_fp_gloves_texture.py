# Southern Spear - first-person glove textures from the Fab "Gloves for fps game" asset (CC BY 4.0, Bobeer).
# 4096 base colour -> 2048 with its baked occlusion multiplied in and a slight darkening (ADF issue gloves read
# black/dark in the reference screenshots); the 2048 normal map is copied. Output beside the arms textures.
#
#   python Tools/Textures/make_fp_gloves_texture.py
import numpy as np
from PIL import Image

SRC = "Content/Sourced/Gloves/textures/"
OUT = "Build/fp_arms/"
DARKEN = 0.72

bc = Image.open(SRC + "initialShadingGroup_Base_Color.png").convert("RGB").resize((2048, 2048), Image.LANCZOS)
ao = Image.open(SRC + "initialShadingGroup_Ambient_occlusion.png").convert("L").resize((2048, 2048), Image.LANCZOS)
a = np.asarray(bc, dtype=np.float32) * (0.45 + 0.55 * np.asarray(ao, dtype=np.float32)[..., None] / 255.0) * DARKEN
Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(OUT + "T_FP_Gloves_BC.png")
Image.open(SRC + "Normal.png").convert("RGB").save(OUT + "T_FP_Gloves_N.png")
print("[fp_gloves_texture] wrote", OUT + "T_FP_Gloves_BC.png")
