"""Follow-up to optimize_nanite.py (producer recording, session 026):
- vegetation with authored LODs goes back to non-Nanite (Nanite recoloured the
  Rural Australia leaves);
- weapons go back to non-Nanite (their optic lenses need translucency);
- optic lens slots (Arma *_ca / glass textures) get a translucent glass material.
Report: Build/visual_fix_report.json."""
import json
import unreal

eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
report = json.load(open("E:/SouthernSpear/Build/nanite_report.json"))
VEG = ("vegetation", "tree", "plant", "grass", "bush", "foliage", "shrub", "scrub", "leaf", "leaves", "fern", "spinifex", "saltbush")
WEAPONS = ["A88", "A88G", "A89", "A4", "A416", "A25", "A9"]
out = {"vegetation_reverted": [], "weapons_reverted": [], "glass_slots": []}


def set_nanite(mesh, on):
    s = mesh.get_editor_property("nanite_settings")
    if s.get_editor_property("enabled") != on:
        s.set_editor_property("enabled", on)
        mesh.set_editor_property("nanite_settings", s)
        return eal.save_loaded_asset(mesh)
    return False


# Vegetation: every mesh the maps use, found again from the asset registry paths.
registry = unreal.AssetRegistryHelpers.get_asset_registry()
for root in ["/Game"]:
    for data in registry.get_assets_by_path(root, recursive=True):
        if str(data.asset_class_path.asset_name) != "StaticMesh":
            continue
        path = str(data.package_name)
        if not any(k in path.lower() for k in VEG):
            continue
        mesh = unreal.load_asset(path)
        # Authored LODs mean the pack built it as a classic mesh.
        if mesh and mesh.get_num_lods() > 1 and set_nanite(mesh, False):
            out["vegetation_reverted"].append(path)

glass_path = "/SSExp_ObjectiveAssault/Materials/M_SS_OpticGlass"
glass = unreal.load_asset(glass_path) if eal.does_asset_exist(glass_path) else None
if not glass:
    glass = tools.create_asset("M_SS_OpticGlass", "/SSExp_ObjectiveAssault/Materials", unreal.Material, unreal.MaterialFactoryNew())
    glass.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    glass.set_editor_property("two_sided", True)
    col = mel.create_material_expression(glass, unreal.MaterialExpressionConstant3Vector, -400, 0)
    col.set_editor_property("constant", unreal.LinearColor(0.02, 0.03, 0.05, 1.0))
    op = mel.create_material_expression(glass, unreal.MaterialExpressionConstant, -400, 200)
    op.set_editor_property("r", 0.08)
    rough = mel.create_material_expression(glass, unreal.MaterialExpressionConstant, -400, 300)
    rough.set_editor_property("r", 0.05)
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(glass)
    eal.save_loaded_asset(glass)

for name in WEAPONS:
    mesh = unreal.load_asset("/SSExp_ObjectiveAssault/Weapons/{0}/SM_{0}".format(name))
    if not mesh:
        continue
    if set_nanite(mesh, False):
        out["weapons_reverted"].append(name)
    changed = False
    for i, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("material_slot_name")).lower()
        # Lenses only: "glass" slots, and the Specter's _ca (its lens; no glass slot).
        # Reticle and body alpha slots keep their own instance.
        if "glass" in slot_name or slot_name == "adfrc_spectr_ca":
            mesh.set_material(i, glass)
            out["glass_slots"].append(name + ":" + slot_name)
            changed = True
        elif slot_name.endswith("_ca"):
            own = "/SSExp_ObjectiveAssault/Weapons/{0}/MI_{0}_{1}".format(name, slot_name)
            if eal.does_asset_exist(own) and slot.get_editor_property("material_interface") == glass:
                mesh.set_material(i, unreal.load_asset(own))
                changed = True
    if changed:
        eal.save_loaded_asset(mesh)
json.dump(out, open("E:/SouthernSpear/Build/visual_fix_report.json", "w"), indent=1)
unreal.log("SS_VISFIX veg={} weapons={} glass={}".format(len(out["vegetation_reverted"]), len(out["weapons_reverted"]), out["glass_slots"]))
