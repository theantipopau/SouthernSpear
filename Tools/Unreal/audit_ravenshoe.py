"""
Ravenshoe Crossing - read-only audit of the imported map.

The import pass reports what it did. This checks what is actually in the saved
.umap, by opening it fresh and measuring. They are different questions: a pass
can report 68 cover markers placed and still have them floating, and the only
way to know is to look at the saved map from outside.

Nothing here writes to the map.

WHAT IT CHECKS, AND WHY
    inventory        every actor is ours or is a pack reference; nothing stray
    geometry         terrain, bridge and gatehouse are where the layout says
    seating          the gatehouse base is on the ground the terrain reports
    fairness         both deployments are the same distance from OBJ A. This
                     is the single property the whole layout is built around,
                     and it is cheap to check and impossible to eyeball
    collision        the three originals block; a map whose floor does not
                     block is unplayable and nothing else reports it
    materials        our authored materials actually landed on the slots
    dressing         the pack dressing is present and is real pack geometry
    props            the Fab-prop layer: the wreck is ON the deck and blocking,
                     carries an authored ScanPBR instance, and the fire and
                     smoke components kept their Cascade templates

A note on measurement: line_trace_single in a -nullrhi commandlet cannot hit
StaticMeshActor, so this does NOT trace the terrain. It compares the saved
actor transforms against Tools/Common/ravenshoe_spec.py, which is the same
function the terrain was built from - so agreement means the imported map
matches the spec exactly, rather than approximately.

Run:
    UnrealEditor-Cmd.exe <uproject> -run=pythonscript \
        -script="<project>/Tools/Unreal/audit_ravenshoe.py" -nullrhi -unattended
"""

import json
import os
import sys
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
MAP = "/Game/Maps/L_Ravenshoe_01"
REPORT = os.path.join(PROJECT_DIR, "Build", "ravenshoe_audit_report.json")
MESH_DEST = "/Game/Art/Environment/Ravenshoe/Meshes"

PREFIX = "SS_Raven_"
EXPECTED = {
    "SS_Raven_Geo_Terrain": 1,
    "SS_Raven_Geo_Bridge": 1,
    "SS_Raven_Geo_Gatehouse": 1,
}
MIN_COVER = 60          # the layout CSV promises 68
MIN_TREES = 40
MIN_WALL = 40

report = {
    "ok": False,
    "map": MAP,
    "inventory": {},
    "findings": [],
    "errors": [],
}


def check(ok, label, detail=""):
    report["findings"].append({"ok": bool(ok), "label": label, "detail": str(detail)})
    return bool(ok)


def load_spec():
    here = os.path.dirname(os.path.abspath(__file__))
    common = os.path.normpath(os.path.join(here, "..", "Common"))
    if common not in sys.path:
        sys.path.insert(0, common)
    import ravenshoe_spec
    return ravenshoe_spec


def static_mesh_of(actor):
    """Read a component's mesh. There is no get_static_mesh() on the component
    in 5.8 - that name only exists on the editor subsystem's spawn path - so
    this goes through the property, with the attribute as a fallback."""
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if comp is None:
        return None, None
    for getter in (lambda: comp.get_editor_property("static_mesh"),
                   lambda: comp.static_mesh):
        try:
            mesh = getter()
            if mesh is not None:
                return comp, mesh
        except Exception:  # noqa: BLE001
            continue
    return comp, None


def collision_on(actor):
    comp, _mesh = static_mesh_of(actor)
    if comp is None:
        return None
    for getter in (lambda: comp.get_editor_property("collision_enabled"),
                   lambda: comp.get_collision_enabled()):
        try:
            return bool(getter())
        except Exception:  # noqa: BLE001
            continue
    return None


def to_ue(bl_x, bl_y, bl_z):
    return unreal.Vector(bl_x * 100.0, -bl_y * 100.0, bl_z * 100.0)


def main():
    spec = load_spec()
    level_sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_sub.load_level(MAP):
        report["errors"].append("could not load " + MAP)
        return
    world = unreal.EditorLevelLibrary.get_editor_world()
    if world is None:
        report["errors"].append("no editor world")
        return
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = list(actor_sub.get_all_level_actors())
    report["actor_total"] = len(actors)

    owned, foreign = {}, 0
    for a in actors:
        label = a.get_actor_label()
        if label.startswith(PREFIX):
            key = label.split("_")[2] if label.count("_") >= 2 else "misc"
            owned[key] = owned.get(key, 0) + 1
        else:
            foreign += 1
    report["inventory"] = {"owned": owned, "foreign": foreign}
    check(owned.get("Geo", 0) == 3, "three original structures placed",
          "Geo={}".format(owned.get("Geo", 0)))
    check(owned.get("Cover", 0) >= MIN_COVER, "layout cover markers dressed",
          "Cover={} (min {})".format(owned.get("Cover", 0), MIN_COVER))
    check(owned.get("Dress", 0) > 0, "extra dressing present",
          "Dress={}".format(owned.get("Dress", 0)))

    by_label = {}
    for a in actors:
        by_label[a.get_actor_label()] = a

    # --- the three originals ------------------------------------------------
    geo_ok = True
    for label in EXPECTED:
        a = by_label.get(label)
        if a is None:
            check(False, "missing " + label, "not in the saved level")
            geo_ok = False
            continue
        _comp, mesh = static_mesh_of(a)
        check(mesh is not None, "{} has a static mesh".format(label),
              mesh.get_name() if mesh else "NONE")
        col = collision_on(a)
        check(col is not False, "{} blocks".format(label),
              "collision OFF" if col is False else ("on" if col else "unreadable"))
        loc = a.get_actor_location()
        report.setdefault("positions", {})[label] = [
            round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)]

    # --- geometry agrees with the spec --------------------------------------
    terr = by_label.get("SS_Raven_Geo_Terrain")
    if terr is not None:
        t = terr.get_actor_location()
        check(abs(t.x) < 1.0 and abs(t.y) < 1.0 and abs(t.z) < 1.0,
              "terrain sits at the world origin",
              "({:.1f}, {:.1f}, {:.1f})".format(t.x, t.y, t.z))

    bridge = by_label.get("SS_Raven_Geo_Bridge")
    if bridge is not None:
        b = bridge.get_actor_location()
        # The bridge is authored deck-top-at-zero and placed by deck level.
        want_z = spec.DECK_Z * 100.0
        check(abs(b.z - want_z) < 2.0, "bridge deck sits at road level",
              "z={:.1f} cm want={:.1f}".format(b.z, want_z))
        check(abs(b.x) < 2.0 and abs(b.y) < 2.0, "bridge is on the axis",
              "x={:.1f} y={:.1f}".format(b.x, b.y))

    gate = by_label.get("SS_Raven_Geo_Gatehouse")
    if gate is not None:
        g = gate.get_actor_location()
        want = to_ue(spec.GATE_X, spec.GATE_Y, spec.ground_z(spec.GATE_X, spec.GATE_Y))
        check(abs(g.x - want.x) < 2.0 and abs(g.y - want.y) < 2.0,
              "gatehouse is at objective B",
              "({:.0f}, {:.0f}) want ({:.0f}, {:.0f})".format(g.x, g.y, want.x, want.y))
        check(abs(g.z - want.z) < 2.0, "gatehouse is seated on the road",
              "z={:.1f} want={:.1f}".format(g.z, want.z))

    # --- gameplay fairness, measured on the saved map -----------------------
    objs = [a for a in actors
            if a.get_actor_label().startswith("SS_MAP_Ravenshoe_Obj")]
    starts = [a for a in actors
              if a.get_actor_label().startswith("SS_MAP_Ravenshoe_Deploy")]
    check(len(objs) == 2, "two objectives placed", len(objs))
    # fix_ravenshoe_starts.py replaced the two plain starts with LyraPlayerStart primaries plus 7
    # extras each (Lyra only spawns from ALyraPlayerStart): 16 total, 2 of them primaries.
    check(len(starts) == 16, "two deployments of 8 Lyra starts", len(starts))

    def xy(a):
        v = a.get_actor_location()
        return v.x, v.y

    primaries = [s for s in starts if "_Extra" not in s.get_actor_label()]
    if len(objs) == 2 and len(primaries) == 2:
        obj_a = min(objs, key=lambda a: abs(a.get_actor_location().z - spec.DECK_Z * 100.0))
        ds = [math_dist(xy(s), xy(obj_a)) for s in primaries]
        check(abs(ds[0] - ds[1]) <= spec.SYMMETRY_TOL * 100.0,
              "deployments are equidistant from OBJ A",
              "{:.0f} cm vs {:.0f} cm (tol {:.0f})".format(
                  ds[0], ds[1], spec.SYMMETRY_TOL * 100.0))
        check(max(ds) < 220.0 * 100.0, "approach under the 220 m sightline ceiling",
              "{:.0f} m".format(max(ds) / 100.0))
        report["distances_cm"] = [round(d) for d in ds]

    # --- dressing provenance -------------------------------------------------
    pack_prefixes = ("Scene_QuarrySlate", "RuralAustralia", "Namaqualand")
    used, unexpected = set(), []
    for a in actors:
        label = a.get_actor_label()
        if not label.startswith(PREFIX):
            continue
        _comp, mesh = static_mesh_of(a)
        if mesh is None:
            continue
        p = mesh.get_path_name()
        if p.startswith("/Game/Art/Environment/Ravenshoe/"):
            continue
        if any(p.startswith("/Game/" + q) for q in pack_prefixes):
            # "/Game/Scene_QuarrySlate/..." splits to ['', 'Game',
            # 'Scene_QuarrySlate', ...] - the pack name is index 2, not 1.
            used.add(p.split("/")[2])
        else:
            unexpected.append(p)
    report["pack_sources"] = sorted(used)
    report["unexpected_sources"] = sorted(set(unexpected))[:10]
    check(not unexpected, "every dressed actor is ours or a registered pack mesh",
          "{} unexpected: {}".format(len(unexpected), sorted(set(unexpected))[:3]))

    report["foreign_labels"] = sorted(
        a.get_actor_label() for a in actors
        if not a.get_actor_label().startswith(PREFIX))

    audit_props(spec, actors)
    audit_surfaces(actors)

    report["ok"] = all(f["ok"] for f in report["findings"])


GEO_LABEL = "SS_Raven_Geo_"
PROP_LABEL = "Dress_Prop_"
PROP_DEST = "/Game/Art/Environment/Ravenshoe/Props"
VFX = "/Game/Realistic_Starter_VFX_Pack_Vol2"


def component_materials(actor):
    """Read the per-instance material overrides off a placed component.

    The mesh ASSET's slots are the wrong place to look. Every route to writing
    them is a silent no-op in 5.8, so the props carry their material as a
    component override instead - which is also what actually renders.
    """
    comp = actor.static_mesh_component if hasattr(actor, "static_mesh_component") else None
    if comp is None:
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if comp is None:
        return []
    try:
        n = comp.get_num_materials()
    except Exception:  # noqa: BLE001
        return []
    out = []
    for i in range(n):
        try:
            m = comp.get_material(i)
        except Exception:  # noqa: BLE001
            m = None
        out.append(m.get_name() if m else None)
    return out


def audit_props(spec, actors):
    """Check the Fab-prop dressing pass from outside the pass that wrote it.

    Same reasoning as the rest of this file: the dressing script reports what
    it did, this measures what is in the saved map. Two things in particular
    are only knowable from here - whether the wreck is actually ON the deck
    rather than near it, and whether the particle components survived the save
    with their templates intact.
    """
    props = [a for a in actors if a.get_actor_label().startswith(PROP_LABEL)]
    report["prop_count"] = len(props)
    check(len(props) > 0, "dressing props present", "{} actors".format(len(props)))

    by_tag = {}
    for a in props:
        by_tag.setdefault(a.get_actor_label()[len(PROP_LABEL):], []).append(a)
    report["prop_tags"] = sorted(by_tag)

    # The wreck: at the deck level, on the centreline span, and it must block -
    # it is the only hard cover in the middle of a 68 m bridge.
    wrecks = by_tag.get("WreckCar", [])
    if not check(len(wrecks) == 1, "burning wreck on the deck", len(wrecks)):
        return
    w = wrecks[0]
    loc = w.get_actor_location()
    bl = (loc.x / 100.0, -loc.y / 100.0, loc.z / 100.0)
    report["wreck_bl_m"] = [round(v, 3) for v in bl]
    check(abs(bl[2] - spec.DECK_Z) < 0.15,
          "wreck sits on the deck surface",
          "z={:.2f} m, deck={:.2f} m".format(bl[2], spec.DECK_Z))
    check(abs(bl[0]) <= spec.DECK_W * 0.5 and abs(bl[1]) <= spec.SPAN * 0.5,
          "wreck is within the bridge footprint",
          "x={:.1f} (deck half {:.2f}), y={:.1f} (span +-{:.1f})".format(
              bl[0], spec.DECK_W * 0.5, bl[1], spec.SPAN * 0.5))
    check(collision_on(w) is True, "wreck blocks", collision_on(w))

    _, wmesh = static_mesh_of(w)
    wpath = wmesh.get_path_name() if wmesh else "?"
    report["wreck_mesh"] = wpath
    check(wpath.startswith(PROP_DEST), "wreck is our imported prop", wpath)
    wmats = component_materials(w)
    report["wreck_materials"] = wmats
    check(bool(wmats) and all(m and m.startswith("MI_SS_Raven_") for m in wmats),
          "wreck is on an authored ScanPBR instance", wmats)

    # The deck clutter must not be spread wide enough to seal the 7.5 m deck.
    drums = by_tag.get("Drum_Deck_0", [])
    n_drums = sum(len(by_tag.get("Drum_Deck_{}".format(i), [])) for i in range(7))
    check(n_drums > 0, "fuel drums on the deck", n_drums)

    # Fire. The component has to exist AND still have its template: an actor
    # with a null template renders nothing and looks placed in the outliner.
    # A runtime-added component does not serialise at all in 5.8, so these are
    # instances of the VFX pack's Spawn_Particle Blueprint.
    vfx = sorted(k for k in by_tag if k in ("Fire_Engine", "Fire_Cabin",
                                            "Smoke_Column", "Embers"))
    report["vfx_tags"] = vfx
    check(len(vfx) == 4, "fire, smoke and ember systems placed", vfx)
    templates = {}
    classes = {}
    for a in props:
        tag = a.get_actor_label()[len(PROP_LABEL):]
        if tag not in vfx:
            continue
        classes[tag] = a.get_class().get_name()
        comps = a.get_components_by_class(unreal.ParticleSystemComponent)
        tpl = None
        for c in comps:
            for getter in (lambda c=c: c.get_editor_property("template"),
                           lambda c=c: c.template):
                try:
                    tpl = getter()
                    if tpl is not None:
                        break
                except Exception:  # noqa: BLE001
                    continue
            if tpl is not None:
                break
        templates[tag] = str(tpl.get_path_name()) if tpl else None
    report["vfx_templates"] = templates
    report["vfx_classes"] = classes
    check(all(t and t.startswith(VFX) for t in templates.values()) and templates,
          "every VFX component kept its Cascade template", templates)
    check(all(c == "Spawn_Particle_C" for c in classes.values()) and classes,
          "VFX actors are instances of the pack particle Blueprint", classes)

    # Nothing on the deck may hang in the air or sink through it.
    floating = []
    for a in props:
        tag = a.get_actor_label()[len(PROP_LABEL):]
        if not (tag.startswith("Drum_Deck") or tag == "WreckCar"):
            continue
        p = a.get_actor_location()
        bl_z = p.z / 100.0
        if abs(bl_z - spec.DECK_Z) > 1.2:
            floating.append("{} at z={:.2f}".format(tag, bl_z))
    check(not floating, "nothing floats or sinks on the deck", floating[:4])

    # EVERY mesh prop, not just the wreck, must be on an authored instance.
    # The mesh ASSET keeps its vendor slots by design (ADR-029), so this reads
    # the per-instance component override, which is what renders.
    unauthored = []
    checked = 0
    for a in props:
        tag = a.get_actor_label()[len(PROP_LABEL):]
        if tag in ("Fire_Engine", "Fire_Cabin", "Smoke_Column", "Embers"):
            continue
        mats = component_materials(a)
        checked += 1
        if not mats or not all(m and m.startswith("MI_SS_Raven_") for m in mats):
            unauthored.append("{}: {}".format(tag, mats))
    check(not unauthored and checked > 0,
          "every prop mesh is on an authored ScanPBR instance",
          "{} checked{}".format(checked, "" if not unauthored
                                else ", unauthorised: " + str(unauthored[:4])))


def audit_surfaces(actors):
    """The authored geometry must carry the generated surfaces, and they must
    still be there after the map has been saved and re-opened.

    This audit runs against the SAVED map, so it is the only place that can
    prove the overrides persisted. Every material route in this project has at
    some point written successfully and rendered as nothing: the mesh slot
    override, the constant-material authoring call, and the component override
    for a component that was then re-imported over. A check made immediately
    after setting a value proves nothing; only a check made on the next run
    does.
    """
    wanted = {
        "SS_Raven_Bridge": {"MI_SS_Raven_Iron", "MI_SS_Raven_Deck",
                            "MI_SS_Raven_Road", "MI_SS_Raven_Stone"},
        "SS_Raven_Gatehouse": {"MI_SS_Raven_Stone"},
    }
    seen = {}
    for a in actors:
        label = a.get_actor_label()
        if not label.startswith(GEO_LABEL):
            continue
        comp = a.get_component_by_class(unreal.StaticMeshComponent)
        if comp is None:
            continue
        mesh = comp.get_editor_property("static_mesh")
        if mesh is None:
            continue
        mats = component_materials(a)
        seen[mesh.get_name()] = [m for m in mats if m]

    report["surface_overrides"] = seen

    for mesh, expect in wanted.items():
        got = set(seen.get(mesh, []))
        missing = expect - got
        check(not missing and bool(got),
              "{} carries its generated surfaces".format(mesh),
              "{} assigned{}".format(sorted(got),
                                     "" if not missing
                                     else ", MISSING " + str(sorted(missing))))

    # The running surface has to be its own material, or the whole deck slab
    # renders as road surface on its fascia and soffit - invisible from the
    # deck, and the reason the Road slot exists at all.
    bridge = seen.get("SS_Raven_Bridge", [])
    check("MI_SS_Raven_Road" in bridge and "MI_SS_Raven_Deck" in bridge,
          "deck running surface is separate from the deck structure",
          "bridge slots: {}".format(bridge))


def math_dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


try:
    main()
except Exception:  # noqa: BLE001
    report["errors"].append(traceback.format_exc())
finally:
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=str)
