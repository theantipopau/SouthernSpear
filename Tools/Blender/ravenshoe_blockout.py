"""
Southern Spear - Ravenshoe Crossing blockout generator (class F, original work).

Generates the greybox described in Docs/MAPS_RAVENSHOE.md (ADR-027).

This is a GREYBOX. It deliberately uses untextured primitives. A greybox that
looks finished stops being treated as one.

WHY THE BRIDGE AND GATEHOUSE ARE MODELLED HERE RATHER THAN DRESSED
    A keyword sweep of all of Content/ for bridge, gate, arch, tunnel, pier,
    stone and wall returns 430 hits, every one of them Scene_QuarrySlate rock
    ledges, Singapore_Canal stone *materials*, or Lyra audio. Not one structural
    mesh exists in the project or in any installed pack. The only packs with
    buildings are Asian canal architecture (ruled out on look and culture,
    ADR-016) and the Rural Australia pack, which has none at all.
    So the crossing is modelled here, from scratch, by us. That is also the only
    route L-0008 leaves open: the map takes the *design principle* of a
    chokepoint crossing and none of any other game's content.

WHAT IS REUSED, AND FROM WHERE
    Nothing third-party is modelled or copied. What this script borrows is our
    OWN class F work and our own house conventions:
      - the primitive/join/export helpers below follow redgum_homestead.py, and
        every dimension is read from Tools/Common/ravenshoe_spec.py so the CI
        verifier and this generator cannot disagree;
      - the base-at-origin convention, the flat shading, the 2 m box-projected
        UVs and the measured-footprint CSV columns are the Red Gum homestead's,
        because the import pass is the same and a second convention would be a
        second class of bug.
    The gorge walls, boulders, scrub, gum trees and fences that will dress this
    are Scene_QuarrySlate / RuralAustralia / Namaqualand meshes referenced in
    place by Tools/Unreal, never reskinned.

WHAT IT EXPORTS
    SS_MAP_Ravenshoe_01_HI.blend   source, LFS, authoritative per ADR-009
    SS_MAP_Ravenshoe_01.fbx        terrain only
    SS_Raven_Bridge.fbx            the truss, authored at the ORIGIN
    SS_Raven_Gatehouse.fbx         the stone gatehouse, at the ORIGIN
    SS_MAP_Ravenshoe_01_Layout.csv everything the import needs to place them

CSV columns:
    name,kind,x_m,y_m,z_m,yaw_deg,half_x_m,half_y_m,base_z_m,top_z_m,faces
    kind is one of: Objective, Deployment, Structure, CoverRock, CoverBush.
    Objective/Deployment/Structure rows are placed by the import. Cover rows are
    the dressing contract: the import swaps each greybox marker for the named
    Class A pack mesh at the same position, scale and yaw.

    The bridge and gatehouse are authored base-at-origin so the import can
    place them with the actor origin on the measured ground, exactly as
    import_redgum_homestead.py does. The base_z_m column lets the importer
    ASSERT that convention instead of assuming it.

Run headless:
    blender -b --factory-startup --python Tools/Blender/ravenshoe_blockout.py

Standards (TECHNICAL_DESIGN_DOCUMENT.md 12.2):
    Metric units, +Y forward, +Z up, transforms applied, SS_ naming.
"""

import math
import os
import sys

import bpy
import mathutils

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Common")))
import ravenshoe_spec as S  # noqa: E402

OUT_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                 "Content", "Art", "Blockout"))

# Terrain sampling. 2 m is the finest that still keeps the greybox honest: the
# gorge wall is an 8 m run for 32 m of drop, so 2 m samples describe it as a
# slope rather than as a staircase, at 15k quads for the whole map.
TERRAIN_STEP = 2.0

SLOTS = ("Terrain", "Rock", "Bush", "Iron", "Stone", "Deck", "Marker")
MAT = {name: None for name in SLOTS}

VIEWS = {
    # Viewport colours only. They exist so a Workbench render reads as a shape
    # check rather than a black frame - the real look is the authored UE
    # material assigned at import. Terrain is deliberately the lightest value:
    # in the first preview pass a dark terrain read as a lighting fault when it
    # was actually two cameras buried in it, and a lighter ground makes that
    # class of mistake obvious next time.
    "Terrain": (0.46, 0.44, 0.40, 1.0),
    "Rock": (0.56, 0.54, 0.51, 1.0),
    "Bush": (0.30, 0.42, 0.24, 1.0),
    "Iron": (0.34, 0.36, 0.40, 1.0),
    "Stone": (0.66, 0.64, 0.60, 1.0),
    "Deck": (0.44, 0.42, 0.38, 1.0),
    "Marker": (0.80, 0.26, 0.20, 1.0),
}


# ---------------------------------------------------------------------------
# Scene helpers - deliberately the same shape as redgum_homestead.py
# ---------------------------------------------------------------------------

def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.meshes):
        bpy.data.meshes.remove(block)
    for block in list(bpy.data.materials):
        bpy.data.materials.remove(block)


def make_materials():
    for name in SLOTS:
        mat = bpy.data.materials.new("SS_Raven_" + name)
        mat.use_nodes = True
        mat.diffuse_color = VIEWS[name]
        MAT[name] = mat


def apply(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return obj


def tag(obj, slot):
    obj.data.materials.clear()
    obj.data.materials.append(MAT[slot])
    for poly in obj.data.polygons:
        poly.material_index = 0
        poly.use_smooth = False
    return obj


def box(name, size, loc, slot, rot=(0.0, 0.0, 0.0)):
    """Axis-aligned box by FULL dimensions in metres, then applied."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    return apply(tag(obj, slot))


def cylinder(name, radius, depth, loc, slot, rot=(0.0, 0.0, 0.0), verts=10):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    return apply(tag(obj, slot))


def join(objects, name):
    objects = [o for o in objects if o is not None]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name + "_Mesh"
    return apply(obj)


def rebase(obj):
    """Move a joined structure's mesh so the object origin is its own footprint
    centre, with its base at z = 0.

    join() leaves the object origin wherever the first part's origin was - for
    the gatehouse, 3.1 m west and 2.3 m up, inside the north pier - so a joined
    structure is neither base-at-origin nor plan-centred by default even
    though every part was authored that way. The Red Gum import places a
    structure with its actor origin on the traced ground and reads the
    footprint from the CSV, both of which are only correct after this.

    The offset is computed from the mesh's OWN vertex coordinates rather than
    from matrix_world. An earlier version used matrix_world and silently did
    nothing: matrix_world is not refreshed until the depsgraph updates, so
    straight after join() it still carried the pre-join transform and the
    offset came out as exactly zero. The gatehouse ended up 2.3 m buried with
    no error anywhere.

    The bridge is deliberately NOT rebased: it is authored with the DECK TOP
    at 0 and its own plan centre at the origin, because its placement anchor
    is the road surface rather than its underside. Its abutments reach 8.8 m
    below the deck by design.
    """
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.y for v in obj.data.vertices]
    zs = [v.co.z for v in obj.data.vertices]
    cx = (min(xs) + max(xs)) / 2.0
    cy = (min(ys) + max(ys)) / 2.0
    lo = min(zs)
    for v in obj.data.vertices:
        v.co.x -= cx
        v.co.y -= cy
        v.co.z -= lo
    return obj


def export_at_origin(obj, filename, offset=(0.0, 0.0, 0.0)):
    """Export an FBX with the mesh rebased to (0, 0, 0), then restore.

    The .blend keeps every structure at its real design position so the
    blockout, the renders and the verifier all see the map as it is. The FBX is
    the import artefact, and the import places a structure from the layout CSV
    - so the FBX must carry the structure relative to that row, not relative to
    the world. Both conventions are documented in the module docstring.
    """
    saved = [v.co.copy() for v in obj.data.vertices]
    for v in obj.data.vertices:
        v.co.x -= offset[0]
        v.co.y -= offset[1]
        v.co.z -= offset[2]
    try:
        return export_fbx(obj, filename)
    finally:
        for v, co in zip(obj.data.vertices, saved):
            v.co = co


def world_extents(obj, centre=None):
    """Half-extents and vertical extent of a joined object, in metres.

    Measured ABOUT a centre, defaulting to the object origin. This matters:
    the first version returned max(|x|) and max(|y|) from the WORLD origin, so
    the gatehouse - which stands at y=62 - reported a 130 m footprint instead
    of 6.8 m, and any keep-out test or seating assertion reading that number
    would have cleared a 65 m radius around objective B.
    """
    corners = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
    if centre is None:
        cx = cy = cz = 0.0
    else:
        cx, cy, cz = centre
    return (
        max(abs(c.x - cx) for c in corners),
        max(abs(c.y - cy) for c in corners),
        min(c.z for c in corners) - cz,
        max(c.z for c in corners) - cz,
    )


def export_fbx(obj, filename, planar=False):
    path = os.path.join(OUT_DIR, filename)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if planar:
        # The terrain is a heightfield: a world-space planar UV keeps the
        # ground texture at a true scale instead of smearing box projections
        # across a 30-degree slope.
        me = obj.data
        uv = me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            for li in poly.loop_indices:
                v = me.vertices[me.loops[li].vertex_index].co
                uv.data[li].uv = (v.x / 4.0, v.y / 4.0)
    else:
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.cube_project(cube_size=2.0)
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=True,
        apply_unit_scale=True,
        global_scale=1.0,
        apply_scale_options="FBX_SCALE_NONE",
        axis_forward="-Z",
        axis_up="Y",
        object_types={"MESH"},
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        path_mode="COPY",
    )
    return path


# ---------------------------------------------------------------------------
# Terrain
# ---------------------------------------------------------------------------

def build_terrain():
    """Heightfield over the whole playable area, displaced by S.ground_z.

    The road, the ramps and the gorge are all carved by the spec's corridor
    logic, so the terrain here is a single uniform grid and every feature in it
    is defined in one bpy-free file that CI can also read.
    """
    nx = int((2.0 * S.MAP_HALF_X) / TERRAIN_STEP) + 1
    ny = int((S.MAP_N - S.MAP_S) / TERRAIN_STEP) + 1
    x0, y0 = -S.MAP_HALF_X, S.MAP_S

    verts = []
    for j in range(ny):
        y = y0 + j * TERRAIN_STEP
        for i in range(nx):
            x = x0 + i * TERRAIN_STEP
            verts.append((x, y, S.ground_z(x, y)))

    faces = []
    for j in range(ny - 1):
        for i in range(nx - 1):
            a = j * nx + i
            b = a + 1
            c = a + nx + 1
            d = a + nx
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new("SS_MAP_Ravenshoe_01_Terrain_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("SS_MAP_Ravenshoe_01_Terrain", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return apply(tag(obj, "Terrain"))


# ---------------------------------------------------------------------------
# The bridge
# ---------------------------------------------------------------------------

def build_bridge():
    """A wrought-iron lattice-girder road bridge, authored base-at-origin.

    Authored so the DECK TOP sits at z = 0, which makes the parapet, the truss
    bottom chord and the lamp bases all measure up from a known datum, and the
    layout row's base_z_m carries the thickness downward. The import places
    the actor origin on the traced road surface, so the deck top is the surface
    players stand on.

    The lattice is not decoration. The 68 m span is the map's one sanctioned
    exception to the 20 m open-crossing rule, and the uprights are the
    mitigation: 21 per side at 3.4 m is what makes the lane a rhythm of short
    exposures instead of one long one.
    """
    parts = []
    half = S.SPAN / 2.0
    chord_z = S.DECK_T + S.CHORD_T / 2.0            # bottom chord centreline
    top_z = S.DECK_T + S.TRUSS_DEPTH                 # top chord centreline

    # The truss frame stands just OUTSIDE the deck edge and the parapet stands
    # on the deck edge inside it. The first pass put both on the same line, so
    # the parapet and the bottom chord occupied the same 1 m of space - which
    # is not how a through truss works at all. In a through truss the deck
    # passes through the frame and the frame IS the railing, so the two must
    # be separate members: an inboard parapet for crouch cover, an outboard
    # lattice for structure and for the high cover the lattice gives you.
    truss_x = S.DECK_W / 2.0 + S.TRUSSOUT

    # Deck slab, with a raised kerb strip each side of the walking surface.
    parts.append(box("Deck_Slab", (S.DECK_W, S.SPAN, S.DECK_T),
                     (0.0, 0.0, S.DECK_T / 2.0), "Deck"))
    for sx in (-1.0, 1.0):
        parts.append(box("Kerb", (0.30, S.SPAN, 0.10),
                         (sx * (S.DECK_W / 2.0 - S.PARAPET_T - 0.15),
                          0.0, S.DECK_T + 0.05), "Deck"))

    # Parapets. 1.05 m is the Dry River rail height: crouch cover, and it
    # makes the deck a firing step rather than a flat lane.
    for sx in (-1.0, 1.0):
        px = sx * (S.DECK_W / 2.0 - S.PARAPET_T / 2.0)
        parts.append(box("Parapet", (S.PARAPET_T, S.SPAN, S.PARAPET_H),
                         (px, 0.0, S.DECK_T + S.PARAPET_H / 2.0), "Iron"))

    # Chords, uprights, diagonals, top lateral bracing.
    for sx in (-1.0, 1.0):
        x = sx * truss_x
        parts.append(box("Chord_Bottom", (S.CHORD_T, S.SPAN, S.CHORD_T),
                         (x, 0.0, chord_z), "Iron"))
        parts.append(box("Chord_Top", (S.CHORD_T, S.SPAN, S.CHORD_T),
                         (x, 0.0, top_z), "Iron"))

        for i in range(S.N_UPRIGHT):
            y = -half + i * S.BAY
            h = top_z - chord_z
            parts.append(box("Upright", (0.28, 0.28, h),
                             (x, y, chord_z + h / 2.0), "Iron"))
            # Outrigger bracket tying the frame back to the deck edge. Without
            # it the truss appears to hover 14 cm outboard of the deck, which
            # reads as a modelling error rather than as a cantilever.
            if i % 2 == 0:
                parts.append(box("Outrigger", (S.TRUSSOUT + 0.3, 0.22, 0.22),
                                 (sx * (S.DECK_W / 2.0 + S.TRUSSOUT / 2.0),
                                  y, S.DECK_T + 0.11), "Iron"))

        # Alternating diagonals, which is what makes a lattice read as one
        # rather than as a picket fence.
        for i in range(S.N_BAYS):
            y0 = -half + i * S.BAY
            y1 = y0 + S.BAY
            down = (i % 2 == 0)
            ya, yb = (y0, y1) if down else (y1, y0)
            span = math.hypot(yb - ya, top_z - chord_z)
            ang = math.atan2(top_z - chord_z, yb - ya)
            mid_y = (y0 + y1) / 2.0
            mid_z = (chord_z + top_z) / 2.0
            parts.append(box("Diagonal", (S.DIAG_T, span, S.DIAG_T),
                             (x, mid_y, mid_z), "Iron", rot=(ang, 0.0, 0.0)))

    # Top lateral bracing between the two trusses, at every upright.
    for i in range(S.N_UPRIGHT):
        y = -half + i * S.BAY
        parts.append(box("Lateral", (2.0 * truss_x, 0.2, 0.2),
                         (0.0, y, top_z), "Iron"))

    # Overhead sway frames. A real lattice has the two trusses tied together
    # across the top, not just at the panels - without these the span reads as
    # two separate walls with a gap rather than as one structure. Placed every
    # third panel so it does not become a solid roof over the deck.
    for k in range(0, S.N_BAYS + 1, 3):
        y = -half + k * S.BAY
        span = 2.0 * truss_x
        diag = math.hypot(span, S.DECK_T)
        ang = math.atan2(S.DECK_T, span)
        for s in (-1.0, 1.0):
            parts.append(box("Sway", (diag, 0.16, 0.16),
                             (0.0, y, top_z - S.DECK_T / 2.0), "Iron",
                             rot=(0.0, 0.0, s * ang)))

    # Deck cross-beams under the slab, one per bay. Invisible from the deck,
    # which is exactly why they are worth having: they are what stops the deck
    # reading as a floating plank when seen from the creek bed.
    for i in range(S.N_BAYS + 1):
        y = -half + i * S.BAY
        parts.append(box("Cross_Beam", (2.0 * truss_x, 0.30, 0.45),
                         (0.0, y, -0.225), "Iron"))

    # Portal bracing at both ends: a knee brace each side plus a head beam,
    # which is what closes the frame off at the abutments.
    for sy in (-1.0, 1.0):
        py = sy * (half - 0.6)
        parts.append(box("Portal_Head", (2.0 * truss_x, 0.30, 0.30),
                         (0.0, py, top_z), "Iron"))
        for sx in (-1.0, 1.0):
            parts.append(box("Knee", (2.4, 0.20, 0.20),
                             (sx * (truss_x - 0.9), py - sy * 0.5,
                              top_z - 0.55), "Iron",
                             rot=(sy * math.radians(22.0), 0.0, 0.0)))
        # Bearing blocks, sitting on the abutment under each chord.
        for sx in (-1.0, 1.0):
            parts.append(box("Bearing", (0.9, 1.0, 0.30),
                             (sx * truss_x, py, S.DECK_T + 0.15), "Iron"))

    # Lamp standards: 5 per side at uprights 0, 5, 10, 15, 20. They sit on the
    # parapet, not the deck, so they do not narrow the fighting width.
    for sx in (-1.0, 1.0):
        for k in range(S.LAMP_PER_SIDE):
            i = k * S.LAMP_STRIDE
            y = -half + i * S.BAY
            px = sx * (S.DECK_W / 2.0 - S.PARAPET_T / 2.0)
            base_z = S.DECK_T + S.PARAPET_H
            parts.append(cylinder("Lamp_Post", S.LAMP_R, S.LAMP_H,
                                  (px, y, base_z + S.LAMP_H / 2.0), "Iron"))
            parts.append(box("Lamp_Head", (0.52, 0.52, 0.62),
                             (px, y, base_z + S.LAMP_H + 0.31), "Iron"))

    # Abutments. They sit in solid ground at each lip, not in the void: the
    # gorge falls away from y = 34 inward, so the abutment block is embedded in
    # the approach and the span is what crosses the gap. An earlier version
    # added wing walls splaying forward past the lip, which put masonry
    # cantilevered over a 32 m drop with nothing under it.
    for sy in (-1.0, 1.0):
        ay = sy * (half + S.ABUT_X / 2.0)
        parts.append(box("Abutment", (2.0 * S.ABUT_HALF_W, S.ABUT_X, 9.0),
                         (0.0, ay, S.DECK_T / 2.0 - 9.0 / 2.0), "Stone"))

    obj = join(parts, "SS_Raven_Bridge")
    return obj


# ---------------------------------------------------------------------------
# The gatehouse
# ---------------------------------------------------------------------------

def _arch_radius():
    """Radius of the segmental arch intrados.

    A semicircular arch over a 3.4 m span would rise 1.7 m and need a 5.3 m
    wall. A segmental arch of 1.0 m rise is what a 3.4 m granite span is
    actually built as, and it leaves 1.0 m of spandrel under a 4.6 m wall.
    """
    s = S.PASSAGE_W / 2.0
    return (s * s + S.ARCH_RISE * S.ARCH_RISE) / (2.0 * S.ARCH_RISE)


def _arch_z(x):
    """Intradso height at x. Outside the opening the wall is solid from the
    springing up."""
    r = _arch_radius()
    zc = S.PASSAGE_H - r
    if abs(x) >= S.PASSAGE_W / 2.0:
        return S.ARCH_SPRING_Z
    return zc + math.sqrt(max(0.0, r * r - x * x))


def build_gatehouse():
    """A stone road-gate house with an arched road passage through it.

    The passage IS objective B, so the building is a hard-cover volume with one
    soft contested mouth. The spandrel above the arch is built as vertical
    slices from the intrados curve up to the eaves: building it as a flat slab
    would leave holes at the haunches, which is the single easiest way to make
    an arch look wrong.
    """
    parts = []
    hw, hd = S.GATE_W / 2.0, S.GATE_D / 2.0
    pw = S.PASSAGE_W / 2.0
    r = _arch_radius()
    zc = S.PASSAGE_H - r

    # Side piers, full depth, from grade to the eaves.
    for sx in (-1.0, 1.0):
        parts.append(box("Pier", (hw - pw, 2.0 * hd, S.GATE_EAVES),
                         (sx * (hw + pw) / 2.0, 0.0, S.GATE_EAVES / 2.0), "Stone"))

    # Spandrel slices over the opening.
    n = S.N_VOUSSOIR
    dx = S.PASSAGE_W / n
    for i in range(n):
        x = -pw + (i + 0.5) * dx
        z0 = _arch_z(x)
        h = S.GATE_EAVES - z0
        if h <= 0.01:
            continue
        parts.append(box("Spandrel", (dx, 2.0 * hd, h),
                         (x, 0.0, z0 + h / 2.0), "Stone"))

    # The visible arch rings, one at each face. Voussoirs radiate about the
    # arch centre and the box's local Z is rotated onto the radius.
    #
    # The sweep runs from the SPRINGING angle to 180 minus it, measured from
    # +X. The springing point is (half-span, ARCH_SPRING_Z), so the angle is
    # atan2(springing_dz, half_span) - NOT asin(half_span / radius). Those two
    # differ because the arch centre sits below the springing line. Using asin
    # put the ring on the wrong part of the circle and drove the outermost
    # voussoirs 0.44 m below grade, which is how this was found.
    phi0 = math.degrees(math.atan2(S.ARCH_SPRING_Z - zc, S.PASSAGE_W / 2.0))
    phi1 = 180.0 - phi0
    for sy in (-1.0, 1.0):
        ry = sy * (hd - S.RING_T / 2.0)
        for i in range(n):
            f0 = math.radians(phi0 + (phi1 - phi0) * (i / float(n)))
            f1 = math.radians(phi0 + (phi1 - phi0) * ((i + 1) / float(n)))
            tm = (f0 + f1) / 2.0
            dth = abs(f1 - f0)
            chord = 2.0 * (r + S.VOUSSOIR_T / 2.0) * math.sin(dth / 2.0) * 1.06
            rad = r + S.VOUSSOIR_T / 2.0
            parts.append(box("Voussoir", (chord, S.RING_T, S.VOUSSOIR_T),
                             (rad * math.cos(tm), ry, zc + rad * math.sin(tm)),
                             "Stone",
                             rot=(0.0, math.radians(90.0) - tm, 0.0)))

    # Parapet, slightly proud of the wall, with a coping lip.
    parts.append(box("Parapet", (S.GATE_W + 0.4, S.GATE_D + 0.4, S.GATE_PARAPET_H),
                     (0.0, 0.0, S.GATE_EAVES + S.GATE_PARAPET_H / 2.0), "Stone"))
    parts.append(box("Coping", (S.GATE_W + 0.6, S.GATE_D + 0.6, 0.16),
                     (0.0, 0.0, S.GATE_H + 0.08), "Stone"))

    # Quoins at the four corners: a small detail that stops a 9 m box reading
    # as a 9 m box.
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            for k in range(5):
                parts.append(box("Quoin", (0.5, 0.5, 0.82),
                                 (sx * (hw - 0.25), sy * (hd - 0.25),
                                  0.41 + k * 0.9), "Stone"))

    obj = join(parts, "SS_Raven_Gatehouse")
    # Author it WHERE IT GOES. The first pass built it at the origin on the
    # assumption that the layout CSV would place it, which is true of the FBX
    # and false of the .blend: in the blockout the gatehouse sat at y=0,
    # inside the bridge at mid-span, and the preview renders showed a map with
    # no gatehouse and a solid collision where objective B should be. The .blend
    # is the authoritative artwork (ADR-009) and has to be correct on its own.
    obj.location = (S.GATE_X, S.GATE_Y, 0.0)
    bpy.context.view_layer.objects.active = obj
    rebase(obj)
    # rebase leaves the object origin at the building's footprint centre with
    # its base at z=0, so the object still has to be lifted onto the road -
    # which is at 15.2 m here, not 0. Leaving it at z=0 buries the building
    # 15 m under the approach.
    obj.location = (S.GATE_X, S.GATE_Y, S.ground_z(S.GATE_X, S.GATE_Y))
    return obj


# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------

def build_markers():
    """Greybox stand-ins for the dressing the import will swap for pack meshes.

    These are emitted as geometry so the blockout is readable on its own, and
    as layout rows so Tools/Unreal/import_ravenshoe.py can replace each one
    with the named Class A pack mesh at the same transform. The scene is then
    cleared of them, because a greybox that carries its own fake boulders
    invites someone to ship the fake boulders.
    """
    objs = []
    rows = []

    for name, xy, kind, radius, half in (
        ("SS_MAP_Ravenshoe_ObjA_Span", S.OBJ_A_XY, "Objective", S.OBJ_A_R, 0.6),
        ("SS_MAP_Ravenshoe_ObjB_GravelGate", S.OBJ_B_XY, "Objective", S.OBJ_B_R, 0.6),
        ("SS_MAP_Ravenshoe_DeployAlpha", S.DEPLOY_S_XY, "Deployment", 0.0, 0.5),
        ("SS_MAP_Ravenshoe_DeployBravo", S.DEPLOY_N_XY, "Deployment", 0.0, 0.5),
    ):
        if kind == "Deployment":
            size = (S.DEPLOY_HALF_X * 2.0, S.DEPLOY_HALF_Y * 2.0, 0.3)
            z = S.ground_z(*xy) + 0.15
        elif name.endswith("Span"):
            # On the deck, base flush with the deck surface.
            size = (radius * 2.0, radius * 2.0, 0.3)
            z = S.DECK_Z + 0.15
        else:
            # In the PASSAGE, at chest height, which is where a capture
            # volume belongs. The first version put this on the parapet at
            # eaves height, which would have made objective B a rooftop
            # objective and left the arch - the whole point of the building -
            # empty.
            size = (radius * 2.0, radius * 2.0, 0.3)
            z = S.ground_z(S.GATE_X, S.GATE_Y) + 0.9
        objs.append(box(name, size, (xy[0], xy[1], z), "Marker"))
        rows.append((name, kind, xy[0], xy[1], z, 0.0, radius, half, z - 0.15,
                     z + 0.15, 6))

    for name, x, y, kind, half_r in S.cover_markers():
        z = S.ground_z(x, y)
        slot = "Rock" if kind == "rock" else "Bush"
        # Bushes are wider and lower than rocks, so the greybox does not lie
        # about how much of the sightline each one actually blocks.
        if kind == "rock":
            size = (half_r * 2.0, half_r * 1.8, half_r * 1.7)
        else:
            size = (half_r * 2.6, half_r * 2.4, half_r * 1.5)
        objs.append(box(name, size, (x, y, z + size[2] / 2.0), slot))
        rows.append((name, "Cover" + kind.capitalize(), x, y, z, 0.0,
                     half_r, half_r, z, z + size[2], 6))

    obj = join(objs, "SS_Raven_Markers")
    return obj, rows


# ---------------------------------------------------------------------------

def main():
    reset_scene()
    make_materials()
    os.makedirs(OUT_DIR, exist_ok=True)

    # Refuse to build a map that fails its own spec. The verifier in CI reads
    # the same spec, so this is the fast half of the same check.
    problems = S.check_spec()
    fails = [p for p in problems if p[0] == "FAIL"]
    if fails:
        for sev, msg in problems:
            print("%s  %s" % (sev, msg))
        raise SystemExit("ravenshoe_blockout: spec has %d FAIL(s); refusing to "
                         "generate a map that breaks its own rules" % len(fails))

    terrain = build_terrain()
    bridge = build_bridge()
    gate = build_gatehouse()
    markers, marker_rows = build_markers()

    # The bridge is authored at its own design anchor (x=0, y=0, deck top
    # z=0), so it is measured about the origin. The gatehouse stands at its
    # design point, so it is measured about THAT - the footprint columns are
    # half-widths of the building, not distances from the map origin.
    bh = world_extents(bridge)
    gh = world_extents(gate, (S.GATE_X, S.GATE_Y, S.ground_z(S.GATE_X, S.GATE_Y)))
    th = world_extents(terrain)
    if gh[2] > 0.001:
        raise SystemExit("ravenshoe_blockout: gatehouse base is %.3f m above "
                         "its own origin; rebase() did not run" % gh[2])

    export_fbx(terrain, "SS_MAP_Ravenshoe_01.fbx", planar=True)
    export_fbx(bridge, "SS_Raven_Bridge.fbx")
    # The gatehouse is authored at (0, 62); the FBX carries it relative to its
    # own layout row, which is the (0, 0) the import will place it at.
    export_at_origin(gate, "SS_Raven_Gatehouse.fbx",
                     (S.GATE_X, S.GATE_Y, 0.0))

    blend = os.path.join(OUT_DIR, "SS_MAP_Ravenshoe_01_HI.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)

    # Structure rows. The bridge is placed by the import at the road surface so
    # its deck top lands on DECK_Z; the gatehouse at its own measured ground.
    rows = list(marker_rows)
    rows.append(("SS_Raven_Bridge", "Structure", 0.0, 0.0, S.DECK_Z, 0.0,
                 bh[0], bh[1], bh[2], bh[3], len(bridge.data.polygons)))
    rows.append(("SS_Raven_Gatehouse", "Structure", S.GATE_X, S.GATE_Y,
                 S.ground_z(S.GATE_X, S.GATE_Y), 0.0,
                 gh[0], gh[1], gh[2], gh[3], len(gate.data.polygons)))

    csv_path = os.path.join(OUT_DIR, "SS_MAP_Ravenshoe_01_Layout.csv")
    with open(csv_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("name,kind,x_m,y_m,z_m,yaw_deg,half_x_m,half_y_m,"
                 "base_z_m,top_z_m,faces\n")
        for r in rows:
            fh.write("%s,%s,%.3f,%.3f,%.3f,%.1f,%.3f,%.3f,%.4f,%.3f,%d\n" % r)

    print("TERRAIN      faces=%-6d extent=%.0fx%.0f z=%.1f..%.1f" % (
        len(terrain.data.polygons), th[0] * 2.0, th[1] * 2.0, th[2], th[3]))
    print("BRIDGE       faces=%-6d span=%.0f m  bay=%.2f m  uprights=%d/side  "
          "lamps=%d  base_z=%+.2f" % (len(bridge.data.polygons), S.SPAN, S.BAY,
                                     S.N_UPRIGHT, S.LAMP_PER_SIDE * 2, bh[2]))
    print("GATEHOUSE    faces=%-6d %.1fx%.1fx%.1f  passage %.1fx%.1f  at "
          "y=%+.0f base_z=%+.3f" % (
              len(gate.data.polygons), gh[0] * 2.0, gh[1] * 2.0, gh[3] - gh[2],
              S.PASSAGE_W, S.PASSAGE_H, S.GATE_Y, gh[2]))
    print("MARKERS      %d rows (%d cover)" % (
        len(marker_rows), sum(1 for r in marker_rows if r[1].startswith("Cover"))))
    print("SPEC         0 FAIL, %d WARN" % len([p for p in problems if p[0] == "WARN"]))
    print("EXPORTED_BLEND=%s" % blend)
    print("EXPORTED_CSV=%s" % csv_path)


if __name__ == "__main__":
    main()
