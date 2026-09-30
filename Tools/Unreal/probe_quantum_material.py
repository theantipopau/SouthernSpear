# Southern Spear - one-off probe: which Python write path persists material slots on the
# duplicated Quantum meshes? R-91: the historical apply reported ok while the saved assets
# kept the vendor materials. Run headless, read the printed SS_QPROBE lines.
import unreal

mel = unreal.MaterialEditingLibrary
print("SS_QPROBE MEL:", [m for m in dir(mel) if "expr" in m.lower()])

mat = unreal.load_asset("/SSExp_ObjectiveAssault/Characters/QuantumProto/M_SS_ADFRC_Camo")
if mat is not None and hasattr(mel, "get_num_material_expressions"):
    print("SS_QPROBE numexpr:", mel.get_num_material_expressions(mat))

skel = unreal.load_asset("/SSExp_ObjectiveAssault/Characters/QuantumProto/SKM_Jeans")
inst = unreal.load_asset("/SSExp_ObjectiveAssault/Characters/QuantumProto/MI_SS_ADFRC_Camo_Jeans")


def slots_of(mesh, label):
    rows = []
    for s in mesh.get_editor_property("materials"):
        mi = s.get_editor_property("material_interface")
        rows.append(mi.get_path_name() if mi else None)
    print("SS_QPROBE {} {}: {}".format(label, len(rows), rows))


print("SS_QPROBE has_set_material:", hasattr(skel, "set_material"))
slots_of(skel, "loaded")

slots = skel.get_editor_property("materials")
slots[0].set_editor_property("material_interface", inst)
skel.set_editor_property("materials", slots)
slots_of(skel, "after_set_property")

if hasattr(skel, "set_material"):
    skel.set_material(0, inst)
    slots_of(skel, "after_set_material")
    unreal.EditorAssetLibrary.save_loaded_asset(skel, only_if_is_dirty=False)
    slots_of(skel, "after_save")
