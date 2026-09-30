# Dry River overhaul audit (D-DR-01..07): ground-truth for the fix passes.
# Reports untextured slots, windmill-vs-tree proximity, creek-bed geometry,
# foliage-density comparison against Red Gum, and per-prefix actor counts.
import json, math, os
import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "dryriver_overhaul_audit.json")
MAP = "/Game/Maps/L_DryRiver_01"
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
report = {"ok": False, "steps": [], "errors": []}

def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok

def materials_of(component):
    out = []
    for i in range(component.get_num_materials()):
        m = component.get_material(i)
        out.append(str(m.get_name()) if m else None)
    return out

def main():
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not step("load_map", world is not None, MAP):
        return
    all_actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
    report["actor_total"] = len(all_actors)

    # 1. Prefix census (map composition at a glance)
    from collections import Counter
    census = Counter()
    for a in all_actors:
        l = a.get_actor_label()
        census["_".join(l.split("_")[:3])] += 1
    report["prefix_census"] = dict(census.most_common(20))

    # 2. Untextured: any *visible* mesh whose material slots are all None/DefaultMaterial.
    #    Collision-only helpers (hidden_in_game, e.g. SS_Gum_TrunkCol_*) are counted separately:
    #    a grey default material on an invisible cylinder is not a D-DR-02 defect.
    untextured, collision_only = [], []
    for a in all_actors:
        comp = a.static_mesh_component
        mats = materials_of(comp)
        if not mats or not all(m is None or "DefaultMaterial" in m for m in mats):
            continue
        loc = a.get_actor_location()
        rec = {"label": a.get_actor_label(), "x": round(loc.x), "y": round(loc.y), "mats": mats[:3]}
        try:
            hidden = bool(comp.get_editor_property("hidden_in_game")) or \
                not bool(comp.get_editor_property("visible"))
        except Exception:
            hidden = a.get_actor_label().startswith("SS_Gum_TrunkCol")
        (collision_only if hidden else untextured).append(rec)
    report["untextured"] = untextured
    report["collision_only_default_material"] = collision_only
    step("untextured_scan", True, "%d visible actors with empty/default material slots "
         "(+%d hidden collision-only helpers excluded)" % (len(untextured), len(collision_only)))

    # 3. Windmill vs trees: centre distance to every tree canopy
    windmills = [a for a in all_actors if "Windmill" in a.get_actor_label()]
    trees = [a for a in all_actors if a.get_actor_label().startswith(("SS_RA_Tree", "SS_Dressing_Tree",
             "SS_RedGum_Dress_v1_Tree", "SS_Expand_Tree"))]
    near = []
    for w in windmills:
        wl = w.get_actor_location()
        for t in trees:
            tl = t.get_actor_location()
            d = math.hypot(wl.x - tl.x, wl.y - tl.y)
            if d < 1200.0:  # 12 m: canopies are 6-10 m wide, this is inside the crown
                near.append({"windmill": w.get_actor_label(), "tree": t.get_actor_label(),
                             "dist_cm": round(d)})
    report["windmill_count"] = len(windmills)
    report["windmill_tree_conflicts"] = near
    step("windmill_conflicts", True, "%d windmills, %d conflicts under 12 m" % (len(windmills), len(near)))

    # 4. Creek: terrain height across the creek line vs banks (is there a bed at all?)
    def creek_y(x):
        return 2.5 * math.sin(x / 45.0) * 100.0  # site metres -> cm
    samples = []
    for x in range(-30000, 30001, 6000):
        cy = creek_y(x)
        hit_c = unreal.SystemLibrary.line_trace_single(
            world, unreal.Vector(x, cy, 50000), unreal.Vector(x, cy, -50000),
            unreal.TraceTypeQuery.ECC_VISIBILITY, True, [], unreal.DrawDebugTrace.NONE, True)
        hit_b = unreal.SystemLibrary.line_trace_single(
            world, unreal.Vector(x, cy + 3000, 50000), unreal.Vector(x, cy + 3000, -50000),
            unreal.TraceTypeQuery.ECC_VISIBILITY, True, [], unreal.DrawDebugTrace.NONE, True)
        def z(h):
            if h is None: return None
            hr = h[1] if isinstance(h, (list, tuple)) else h
            d = hr.to_dict()
            p = d.get("impact_point") or d.get("location")
            return round(p.z) if p else None
        samples.append({"x": x, "creek_z": z(hit_c), "bank_z_30m": z(hit_b)})
    report["creek_profile"] = samples
    depths = [s["bank_z_30m"] - s["creek_z"] for s in samples
              if s["creek_z"] is not None and s["bank_z_30m"] is not None]
    report["creek_depth_cm"] = {"min": min(depths), "max": max(depths)} if depths else None
    step("creek_profile", True, "bed depth vs bank: %s" % report["creek_depth_cm"])

    # 5. Small-foliage density vs Red Gum. Counts HISM *instances*, not just actors:
    #    the harvest overhaul scatters bushes/flowers as HISM (one actor, many instances),
    #    so an actor-only census reports the new density as zero. HISM components here were
    #    created as subobjects (Tools/Unreal/harvest_dryriver.py hism()), so they are read the same way.
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    sdl = unreal.SubobjectDataBlueprintFunctionLibrary

    def tally(actor_labels, prefixes, out):
        for l in actor_labels:
            for p in prefixes:
                if l.startswith(p):
                    out[p] += 1
                    break

    def count_prefix(world_path, prefixes):
        unreal.EditorLoadingAndSavingUtils.load_map(world_path)
        w = unreal.EditorLevelLibrary.get_editor_world()
        plain = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.StaticMeshActor)
        c = Counter()
        tally([a.get_actor_label() for a in plain], prefixes, c)
        hism_total = 0
        for a in actors.get_all_level_actors():
            lbl = a.get_actor_label()
            key = next((p for p in prefixes if lbl.startswith(p)), None)
            if key is None:
                continue
            for handle in sub.k2_gather_subobject_data_for_instance(a):
                obj = sdl.get_object(sdl.get_data(handle))
                fn = getattr(obj, "get_instance_count", None)
                n = int(fn()) if callable(fn) else 0
                if n:
                    hism_total += n
                    c[key] += n
        return c, len(plain), hism_total

    SMALL = ("SS_Expand_Scrub", "SS_Expand_Tuft", "SS_Dressing_Scrub", "SS_RA_Scrub", "SS_Expand_Grass",
             "SS_Expand_Stone", "SS_Expand_Bush", "SS_Expand_Small","SS_RedGum_Dress_v1_Bush", "SS_RedGum_Dress_v1_Scrub", "SS_Overhaul_Scatter_")
    dr_counts, dr_total, dr_inst = count_prefix(MAP, SMALL)
    rg_counts, rg_total, rg_inst = count_prefix("/Game/Maps/L_RedGum_01", SMALL)
    report["small_foliage"] = {"dryriver": dict(dr_counts), "redgum": dict(rg_counts),
                               "dryriver_total_actors": dr_total, "redgum_total_actors": rg_total,
                               "dryriver_instanced": dr_inst, "redgum_instanced": rg_inst}
    step("foliage_compare", True,
         "DR small-foliage %d (%d instanced) vs RG %d (%d instanced)"
         % (sum(dr_counts.values()), dr_inst, sum(rg_counts.values()), rg_inst))

    # 6. Backface check: meshes whose bounds are paper-thin on one axis (billboard suspicion)
    thin = []
    for a in all_actors:
        try:
            origin, extent = a.get_actor_bounds(False)
            dims = sorted([extent.x, extent.y, extent.z])
            if dims[2] > 50 and dims[0] < 12.0:  # large in two axes, under 12 cm thick in one
                thin.append({"label": a.get_actor_label(), "thickness_cm": round(dims[0], 1)})
        except Exception:
            pass
    report["paper_thin_candidates"] = thin[:40]
    step("thin_scan", True, "%d paper-thin candidates" % len(thin))

    unreal.EditorLoadingAndSavingUtils.load_map(MAP)  # return to the working map
    report["ok"] = all(s["ok"] for s in report["steps"])

try:
    main()
except Exception:
    report["errors"].append(__import__("traceback").format_exc())
    unreal.log_error("[DROverhaulAudit] raised")
finally:
    with open(REPORT, "w", encoding="utf-8") as s:
        json.dump(report, s, indent=2)
    unreal.log("[DROverhaulAudit] complete ok=%s report=%s" % (report["ok"], REPORT))
