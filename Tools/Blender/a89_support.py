# Southern Spear - A89 light support weapon, first pass (ADR-016, ADR-020).
#
# Original, fictional design: angular receiver with a raised top cover,
# squared ammunition box under the receiver ahead of the grip, heavy shrouded
# barrel, carry handle, folded bipod, fixed skeleton stock. Not traced from or
# dimensioned after any real weapon.
#
# Run: blender --background --factory-startup --python Tools/Blender/a89_support.py
# Out: Art/Weapons/A89/SM_A89.fbx, A89.blend, Build/sm_a89_report.json

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ss_weapon_kit as k  # noqa: E402

k.reset()
# Stock: skeleton frame (top bar, bottom bar, butt plate).
k.box("StockTop", -0.33, -0.10, 0.018, 0.020, 0.048, bevel=0.005)
k.slanted("StockBottom", -0.33, -0.13, -0.33, -0.18, 0.018, -0.030, -0.058)
k.box("ButtPlate", -0.355, -0.330, 0.024, -0.075, 0.055, slot="Metal", bevel=0.004)
k.slanted("StockWeb", -0.16, -0.10, -0.20, -0.13, 0.016, 0.020, -0.040)
# Receiver and raised top cover.
k.box("Receiver", -0.10, 0.26, 0.034, -0.045, 0.060, taper_top=0.006, bevel=0.006)
k.box("TopCover", -0.06, 0.20, 0.036, 0.060, 0.090, taper_top=0.010, bevel=0.006, slot="Metal")
k.rail(-0.04, 0.18, 0.090)
# Pistol grip and trigger guard (origin at the grip top).
k.slanted("PistolGrip", -0.015, 0.022, -0.045, -0.010, 0.017, -0.043, -0.140)
k.box("TriggerGuard", 0.018, 0.085, 0.008, -0.075, -0.067, slot="Metal", bevel=0.002)
k.box("TriggerGuardFront", 0.078, 0.088, 0.008, -0.075, -0.045, slot="Metal", bevel=0.002)
# Ammunition box: squared, slightly canted, ahead of the grip.
k.slanted("AmmoBox", 0.100, 0.230, 0.105, 0.225, 0.045, -0.045, -0.175, slot="Polymer", bevel=0.008)
k.box("AmmoBoxLatch", 0.150, 0.180, 0.047, -0.120, -0.095, slot="Metal", bevel=0.002)
# Handguard, heavy shrouded barrel, gas tube, muzzle.
k.box("Handguard", 0.26, 0.47, 0.030, -0.030, 0.045, taper_top=0.006, bevel=0.005)
k.cylinder("BarrelShroud", 0.47, 0.62, 0.020, 0.010, slot="Metal", vertices=12)
k.cylinder("Barrel", 0.62, 0.78, 0.013, 0.010, vertices=16)
k.cylinder("GasTube", 0.47, 0.70, 0.007, -0.018, vertices=8)
k.cylinder("Muzzle", 0.775, 0.835, 0.018, 0.010, vertices=8)
# Carry handle over the barrel shroud.
k.rod("HandleFront", (0.52, 0.0, 0.030), (0.52, 0.0, 0.090), 0.008)
k.rod("HandleRear", (0.40, 0.0, 0.045), (0.40, 0.0, 0.090), 0.008)
k.rod("HandleTop", (0.395, 0.0, 0.092), (0.525, 0.0, 0.092), 0.011)
# Folded bipod under the barrel.
k.box("BipodClamp", 0.60, 0.635, 0.016, -0.020, 0.030, slot="Metal", bevel=0.002)
k.rod("BipodLegL", (0.62, 0.012, -0.020), (0.40, 0.014, -0.040), 0.0065)
k.rod("BipodLegR", (0.62, -0.012, -0.020), (0.40, -0.014, -0.040), 0.0065)
# Charging handle.
k.box("ChargingHandle", 0.18, 0.21, 0.050, 0.020, 0.035, slot="Metal", bevel=0.002)

k.finish("SM_A89", (0.835, 0.010), os.path.join("Art", "Weapons", "A89"), (1.0, 1.3))
