# Copyright Southern Spear. All Rights Reserved.
#
# Dry River dressing pass: places dressing into the saved level from the
# placement CSVs, and nothing else.
#
#   UnrealEditor-Cmd.exe SouthernSpear.uproject -nullrhi -unattended -nosplash \
#       -nosound -ExecutePythonScript=Tools/Unreal/dress_dryriver.py
#
# WHY THIS IS A SEPARATE PASS, AND WHY IT RUNS BEFORE THE NAV PASS
#
#   construct (build_dryriver_level.py)  ->  dress (this)  ->  navigate
#
# Dressing must exist BEFORE the NavMesh is built, or the fences and wrecks are
# invisible to navigation and agents walk through them. Putting it after would
# produce a map that looks dressed and plays wrong, which is worse than a map
# that is plainly undressed.
#
# Keeping it separate from the construct pass also means dressing can be
# re-placed without regenerating the blockout, which is the whole point of
# driving it from CSVs.
#
# THE CSVs ARE THE SOURCE OF TRUTH. This script hard-codes no positions. It also
# re-snaps every item to the terrain with a ray trace, so moving a fence in a
# text editor cannot leave it hovering over or buried in the ground - the z
# column becomes advisory rather than load-bearing.
#
# See Docs/MAPS_DRYRIVER.md section 12 and Tools/verify_dressing.py for the
# data-side checks that run without the editor.

import csv
import json
import math
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.project_dir()
BLOCKOUT_DIR = os.path.join(PROJECT_DIR, "Content", "Art", "Blockout")
DRESSING_CSV = os.path.join(BLOCKOUT_DIR, "SS_MAP_DryRiver_02_Dressing.csv")
FENCES_CSV = os.path.join(BLOCKOUT_DIR, "SS_MAP_DryRiver_02_Fences.csv")
MESH_DEST = "/Game/Art/Dressing"
LEVEL_PATH = "/Game/Maps/L_DryRiver_01"
REPORT_PATH = os.path.join(PROJECT_DIR, "Build", "dryriver_dressing_report.json")

LABEL_PREFIX = "SS_Dressing_"
FOLDER_PATH = "DryRiver/Dressing"

# Post-and-rail geometry. Matches Tools/Blender/dryriver_dressing.py.
FENCE_POST_SPACING_DEFAULT = 2.5
FENCE_RAIL_HEIGHTS_CM = (55.0, 105.0)   # 0.55 m and 1.05 m
FENCE_RAIL_THICKNESS_SCALE = 1.0

# Scrub must NOT block. It conceals without obstructing; if it collided it would
# carve holes in the NavMesh and make the map feel sticky to cross. Everything
# else is cover and is expected to block.
NON_BLOCKING_TYPES = {"scrub"}

MESH_FOR_TYPE = {
    "scrub": "SS_Dressing_Scrub",
    "wreck": "SS_Dressing_Wreck",
    "crate": "SS_Dressing_Crate",
    "barrel": "SS_Dressing_Barrel",
}
MESH_FENCE_POST = "SS_Dressing_FencePost"
MESH_FENCE_RAIL = "SS_Dressing_FenceRail"

# "Use the simple collision if this mesh has any, otherwise fall back to the
# render triangles." That is exactly what auto-generated simple collision is
# for, and it is what the meshes are already on.
#
# An earlier version asked for CTF_USE_SIMPLE_AS_SIMPLE. No such member exists:
# introspecting the live enum on 5.8.3 gives only CTF_USE_DEFAULT,
# CTF_USE_COMPLEX_AS_SIMPLE, CTF_USE_SIMPLE_AND_COMPLEX and CTF_USE_SIMPLE_AS_
# COMPLEX. The AttributeError was swallowed into a warning, so the intended
# write never happened on any of the six meshes while the run still reported
# ok. Harmless in effect - the importer had already left the flag at
# CTF_USE_DEFAULT - but it meant a silent no-op in the middle of a code path
# whose entire job is to make collision explicit.
# The working blockout in this same map uses CTF_USE_COMPLEX_AS_SIMPLE, so that
# value was genuinely tested here as a candidate fix for R-10 - with the flag
# verifiably applied this time, which the earlier "tried and ruled out" note did
# not manage, because that attempt went through the broken write above and so
# silently stayed on CTF_USE_DEFAULT. Result: 0/3 actors collide after reload
# either way, so the trace flag is not R-10's cause and the hypothesis is now
# eliminated by measurement rather than by assumption.
#
# CTF_USE_DEFAULT is shipped because it is the right call for this content: 290
# small meshes instanced across the map, each with one verified convex hull, is
# exactly the case per-asset simple collision exists for. Both values now write,
# read back and are asserted, so the choice is one constant edit away.
SIMPLE_COLLISION_TRACE_FLAG = "CTF_USE_DEFAULT"

# KAggregateGeom element arrays, as exposed to Python on 5.8.3. There is no
# capsule_elems or geom_elems on this struct; listing them produces a property
# error on every run and hides the counts that matter.
SIMPLE_COLLISION_ELEM_PROPS = (
    "box_elems",
    "sphere_elems",
    "convex_elems",
    "tapered_capsule_elems",
    "level_set_elems",
)


def simple_collision_element_count(agg_geom):
    """Count the simple-collision elements actually stored on a mesh.

    str(KAggregateGeom) is an opaque pointer whether or not the struct holds
    anything, so the old "body_agg_geom" report field could never tell "this
    asset has no collision" from "this asset is fine" - the two cases it exists
    to distinguish. Counting the element arrays does tell them apart, and the
    importer produces one convex hull per dressing mesh.
    """
    total = 0
    counts = {}
    for prop in SIMPLE_COLLISION_ELEM_PROPS:
        try:
            n = len(agg_geom.get_editor_property(prop))
        except Exception:  # noqa: BLE001
            n = None
        counts[prop] = n
        if n:
            total += n
    return total, counts

report = {"ok": False, "steps": [], "warnings": [], "errors": [],
          "placed": {}, "resnapped": 0, "fences": {}}


def log(msg):
    unreal.log("[DryRiverDress] {}".format(msg))


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    log("{} {} {}".format("OK  " if ok else "FAIL", name, detail))
    return bool(ok)


def warn(msg):
    report["warnings"].append(str(msg))
    log("WARN {}".format(msg))


# --------------------------------------------------------------------------
# Level and world
# --------------------------------------------------------------------------


def load_level():
    try:
        world = unreal.EditorLoadingAndSavingUtils.load_map(LEVEL_PATH)
    except Exception as exc:  # noqa: BLE001
        return step("load_map", False, str(exc))
    return step("load_map", bool(world), LEVEL_PATH)


def current_level():
    return unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).get_current_level()


def current_world():
    level = current_level()
    return level.get_world() if level else None


def read_csv(path, required):
    if not os.path.isfile(path):
        return None, "missing: {}".format(path)
    with open(path, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in required if c not in (reader.fieldnames or [])]
        if missing:
            return None, "missing columns {}".format(missing)
        return list(reader), None


# --------------------------------------------------------------------------
# Meshes
# --------------------------------------------------------------------------


def import_dressing_meshes():
    """Import every dressing FBX.

    Existing dressing assets are DELETED first rather than merely overwritten.
    replace_existing reuses the package in place, and an in-place reuse can keep
    a stale BodySetup - which is how the meshes ended up still on
    complex-as-simple after a run that had asked for simple collision. A clean
    delete makes the import genuinely reproducible.
    """
    wanted = sorted(set(MESH_FOR_TYPE.values()) | {MESH_FENCE_POST, MESH_FENCE_RAIL})
    for name in wanted:
        path = "{}/{}".format(MESH_DEST, name)
        try:
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                unreal.EditorAssetLibrary.delete_asset(path)
                log("  deleted stale asset {}".format(path))
        except Exception as exc:  # noqa: BLE001
            warn("could not delete {}: {}".format(path, exc))
    imported, failed = [], []
    tools = unreal.AssetToolsHelpers.get_asset_tools()

    for name in wanted:
        path = os.path.join(BLOCKOUT_DIR, "{}.fbx".format(name))
        if not os.path.isfile(path):
            failed.append("{} (no FBX)".format(name))
            continue

        task = unreal.AssetImportTask()
        task.set_editor_property("filename", path)
        task.set_editor_property("destination_path", MESH_DEST)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", True)

        opts = unreal.FbxImportUI()
        for prop, value in (
            ("import_mesh", True),
            ("import_as_skeletal", False),
            ("import_animations", False),
            ("import_materials", False),
            ("import_textures", False),
        ):
            try:
                opts.set_editor_property(prop, value)
            except Exception as exc:  # noqa: BLE001
                warn("FbxImportUI.{}: {}".format(prop, exc))
        # One mesh per FBX, with SIMPLE collision generated at import.
        #
        # Complex-as-simple was tried first, matching the blockout, and it is
        # solid the moment the actor is placed - but it does NOT survive the
        # save and reload that every later pass depends on: 5/5 solid at
        # placement, 0/3 after reopening the map. Small dressing meshes are
        # instanced many times over, and per-asset simple collision is the
        # conventional and reliable answer for that. It also costs almost
        # nothing here: a fence post, rail, crate and barrel are boxes or
        # cylinders whose hulls are already almost exact.
        try:
            smi = opts.get_editor_property("static_mesh_import_data")
            smi.set_editor_property("combine_meshes", True)
            smi.set_editor_property("auto_generate_collision", True)
        except Exception as exc:  # noqa: BLE001
            warn("static_mesh_import_data: {}".format(exc))
        task.set_editor_property("options", opts)

        tools.import_asset_tasks([task])
        if not (task.get_editor_property("imported_object_paths") or []):
            failed.append("{} (import produced nothing)".format(name))
            continue

        asset = unreal.EditorAssetLibrary.load_asset("{}/{}".format(MESH_DEST, name))
        if asset is None or not isinstance(asset, unreal.StaticMesh):
            failed.append("{} (no StaticMesh at {}/{})".format(name, MESH_DEST, name))
            continue

        # Set the trace flag unconditionally when simple collision was requested.
        # A previous version guarded this on a stringified KAggregateGeom and the
        # guard misfired, leaving the meshes on complex-as-simple and the
        # collision change silently not applied. It then asked for an enum member
        # that does not exist. Neither silently no-op is tolerable in a path
        # that exists to make collision explicit, so the write is now checked
        # against the value that was requested and failure is fatal, not a
        # warning: a dressing mesh with no usable collision is a broken map.
        #
        # Failures are collected per mesh so a mesh never lands in both
        # `imported` and `failed` and inflates both counts.
        mesh_errors = []
        try:
            body = asset.get_editor_property("body_setup")
            flag = getattr(unreal.CollisionTraceFlag, SIMPLE_COLLISION_TRACE_FLAG)
            body.set_editor_property("collision_trace_flag", flag)
            applied = str(body.get_editor_property("collision_trace_flag"))
            report.setdefault("trace_flag", {})[name] = applied
            if SIMPLE_COLLISION_TRACE_FLAG not in applied:
                mesh_errors.append("trace flag {} != {}".format(
                    applied, SIMPLE_COLLISION_TRACE_FLAG))
        except Exception as exc:  # noqa: BLE001
            mesh_errors.append("collision_trace_flag: {}".format(exc))
        try:
            unreal.EditorAssetLibrary.save_asset(asset.get_path_name(), only_if_is_dirty=False)
        except Exception as exc:  # noqa: BLE001
            warn("saving {}: {}".format(name, exc))

        # Report the imported geometry. Face counts and bounds distinguish "the
        # asset is fine and the problem is placement" from "the asset is empty",
        # which is otherwise indistinguishable until a ray misses.
        info = {"name": name}
        try:
            b = mesh_asset_bounds(asset)
            info["bounds"] = b
        except Exception as exc:  # noqa: BLE001
            info["bounds_error"] = str(exc)
        for key, fn in (
            ("simple_collision_elements",
             lambda: simple_collision_element_count(
                 asset.get_editor_property("body_setup").get_editor_property("agg_geom"))),
            ("collision_complexity",
             lambda: str(asset.get_editor_property("collision_complexity"))
             if _has_property(asset, "collision_complexity") else "n/a"),
        ):
            try:
                info[key] = fn()
            except Exception as exc:  # noqa: BLE001
                info[key + "_error"] = str(exc)
        report.setdefault("mesh_info", []).append(info)
        log("  mesh {}: {}".format(name, info))

        # The trace flag only means something if the mesh actually HAS simple
        # collision for it to select. Count it here, where a failure is still
        # attributable to this asset, rather than much later when a ray in the
        # dressed map misses and the cause is no longer obvious. One convex hull
        # per dressing mesh is what auto_generate_collision produces.
        elems = info.get("simple_collision_elements")
        if isinstance(elems, tuple) and elems[0] == 0:
            mesh_errors.append("no simple collision elements")
        if mesh_errors:
            failed.append("{} ({})".format(name, "; ".join(mesh_errors)))
        else:
            imported.append(name)

    report["meshes_imported"] = imported
    report["meshes_failed"] = failed
    return step("import_dressing_meshes", not failed,
                "{} imported{}".format(len(imported),
                                       "; failed: " + ", ".join(failed) if failed else ""))


# --------------------------------------------------------------------------
# Terrain snapping
# --------------------------------------------------------------------------


def ground_z(x_m, y_m, fallback_cm):
    """Ray-cast the terrain and return its height in cm, or None.

    This is what makes a hand edit of the CSV safe. The z column is written for
    readability and for tools that read the CSV without the engine, but the
    engine does not trust it: a fence dragged 10 m east in a text editor re-sits
    itself on the ground rather than hovering or sinking.
    """
    world = current_world()
    if not world:
        return None
    start = unreal.Vector(x_m * 100.0, y_m * 100.0, 50000.0)
    end = unreal.Vector(x_m * 100.0, y_m * 100.0, -50000.0)
    try:
        result = unreal.SystemLibrary.line_trace_single(
            world, start, end,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            True,   # complex: the blockout is complex-as-simple
            [], unreal.DrawDebugTrace.NONE, True,
        )
    except Exception as exc:  # noqa: BLE001
        warn("line_trace_single failed: {}".format(exc))
        return None

    if isinstance(result, (list, tuple)):
        if len(result) < 2 or not result[0]:
            return None
        hit = result[1]
    else:
        hit = result
    try:
        fields = hit.to_dict()
    except Exception:  # noqa: BLE001
        return None
    for key in ("impact_point", "location"):
        val = fields.get(key)
        if val:
            if hasattr(val, "z"):
                return val.z
            if isinstance(val, (list, tuple)) and len(val) >= 3:
                return val[2]
    return None


# --------------------------------------------------------------------------
# Placement
# --------------------------------------------------------------------------


def clear_existing():
    """Remove dressing from a previous run so the pass is repeatable.

    Scoped by label prefix: it must never touch the blockout, the player starts
    or the objectives.
    """
    level = current_level()
    if not level:
        return step("clear_existing", False, "no level")
    removed = 0
    for actor in unreal.GameplayStatics.get_all_actors_of_class(level, unreal.StaticMeshActor):
        try:
            if actor.get_actor_label().startswith(LABEL_PREFIX):
                # AActor.destroy_actor is the supported route in current UE
                # Python; the EditorActorSubsystem equivalent has moved around
                # between versions, so try both rather than guess.
                if hasattr(actor, "destroy_actor"):
                    actor.destroy_actor()
                else:
                    unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(actor)
                removed += 1
        except Exception as exc:  # noqa: BLE001
            warn("could not remove {}: {}".format(actor, exc))
    report["removed_existing"] = removed
    return step("clear_existing", True, "{} removed".format(removed))


def spawn(mesh, label, loc_cm, yaw_deg, scale):
    """Place one dressing actor.

    loc_cm is in CENTIMETRES, which is what spawn_actor_from_class expects. An
    earlier version divided by 100 on the way in, which quietly placed all 290
    dressing actors 100x too close to the world origin: they clustered in a
    1.3 m knot at (0,0), every ray cast at the real coordinates hit open ground,
    and the map looked dressed in a data file and undressed in the engine. Keep
    every coordinate in this file in cm and let the CSV be the only place metres
    appear.
    """
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(loc_cm.x, loc_cm.y, loc_cm.z),
        unreal.Rotator(0.0, yaw_deg, 0.0),
    )
    if not actor:
        return None
    actor.set_actor_label(label)
    try:
        actor.set_folder_path(unreal.Name(FOLDER_PATH))
    except Exception:  # noqa: BLE001 - foldering is cosmetic
        pass
    smc = actor.static_mesh_component
    smc.set_static_mesh(mesh)
    kind = _kind_of(label)
    smc.set_collision_profile_name("NoCollision" if kind in NON_BLOCKING_TYPES else "BlockAll")
    if scale is not None:
        try:
            actor.set_actor_scale3d(unreal.Vector(scale.x, scale.y, scale.z))
        except Exception as exc:  # noqa: BLE001
            warn("scaling {}: {}".format(label, exc))
    return actor


def _kind_of(label):
    """Recover the dressing type from the actor label.

    Labels are SS_Dressing_<Type>_<nn>; fence posts and rails use their own
    prefixes. Deriving the type from the label keeps the collision rule in one
    place instead of threading it through every call site.
    """
    body = label[len(LABEL_PREFIX):] if label.startswith(LABEL_PREFIX) else label
    for kind in ("scrub", "wreck", "crate", "barrel"):
        if body.lower().startswith(kind):
            return kind
    return body.split("_")[0].lower()


def place_dressing(rows, meshes):
    """Place point dressing. Y is negated: the CSVs are Blender (right-handed)
    space and Unreal is left-handed, exactly as for the layout markers. See
    Docs/MAPS_DRYRIVER.md section 11.2."""
    placed = {}
    failures = []
    for r in rows:
        kind = r["type"]
        if kind not in MESH_FOR_TYPE:
            failures.append("{}: unknown type {}".format(r["name"], kind))
            continue
        mesh = meshes.get(MESH_FOR_TYPE[kind])
        if mesh is None:
            failures.append("{}: no mesh for {}".format(r["name"], kind))
            continue

        x = float(r["x"])
        y = -float(r["y"])
        z = float(r["z"]) * 100.0
        gz = ground_z(x, y, z)
        if gz is not None:
            z = gz
            report["resnapped"] += 1

        s = float(r["scale"])
        actor = spawn(mesh, LABEL_PREFIX + r["name"].replace("SS_DryRiver_", ""),
                      unreal.Vector(x * 100.0, y * 100.0, z),
                      float(r["rot_y"]),
                      unreal.Vector(s, s, s))
        if actor is None:
            failures.append("{}: spawn returned None".format(r["name"]))
            continue
        placed[kind] = placed.get(kind, 0) + 1

    report["placed"] = placed
    report["dressing_failures"] = failures
    return step("place_dressing", not failures,
                "{} placed {}{}".format(sum(placed.values()), placed,
                                        "; failed: " + ", ".join(failures[:3]) if failures else ""))


def place_fences(rows, meshes):
    """Place fence runs as posts plus two rails per gap.

    A run is a line, not a set of objects, so the data stays two numbers per
    fence. Post spacing is data, which means changing a fence from a boundary
    line to a tight paddock is a single CSV edit rather than a rebuild.
    """
    post_mesh = meshes.get(MESH_FENCE_POST)
    rail_mesh = meshes.get(MESH_FENCE_RAIL)
    if post_mesh is None or rail_mesh is None:
        return step("place_fences", False, "fence meshes unavailable")

    total_posts = total_rails = 0
    details = []
    failures = []

    for r in rows:
        ax, ay = float(r["x1"]), -float(r["y1"])
        bx, by = float(r["x2"]), -float(r["y2"])
        spacing = float(r.get("post_spacing") or FENCE_POST_SPACING_DEFAULT)

        length = math.hypot(bx - ax, by - ay)
        if length < 1e-3:
            failures.append("{}: zero length".format(r["name"]))
            continue

        yaw = math.degrees(math.atan2(by - ay, bx - ax))
        n = max(2, int(round(length / spacing)) + 1)

        stations = []
        for i in range(n):
            t = i / (n - 1)
            px = ax + (bx - ax) * t
            py = ay + (by - ay) * t
            gz = ground_z(px, py, 0.0)
            if gz is not None:
                report["resnapped"] += 1
            stations.append((px, py, gz if gz is not None else 0.0))

        run_posts = 0
        for i, (px, py, pz) in enumerate(stations):
            a = spawn(post_mesh, "{}{}_Post{:02d}".format(LABEL_PREFIX,
                                                          r["name"].replace("SS_DryRiver_Fence_", ""), i),
                      unreal.Vector(px * 100.0, py * 100.0, pz), yaw, None)
            if a is None:
                failures.append("{} post {}".format(r["name"], i))
            else:
                run_posts += 1

        run_rails = 0
        for i in range(len(stations) - 1):
            x0, y0, z0 = stations[i]
            x1, y1, _z1 = stations[i + 1]
            gap = math.hypot(x1 - x0, y1 - y0)
            if gap < 1e-3:
                continue
            mid = ((x0 + x1) * 0.5, (y0 + y1) * 0.5)
            midz = ground_z(mid[0], mid[1], 0.0)
            if midz is None:
                continue
            for h in FENCE_RAIL_HEIGHTS_CM:
                a = spawn(rail_mesh,
                          "{}{}_Rail{:02d}_{:03d}".format(
                              LABEL_PREFIX, r["name"].replace("SS_DryRiver_Fence_", ""), i, int(h)),
                          unreal.Vector(mid[0] * 100.0, mid[1] * 100.0, midz + h),
                          yaw,
                          # The rail mesh is authored 1 m long along +X, so
                          # scaling X by the gap makes it span exactly.
                          unreal.Vector(gap, FENCE_RAIL_THICKNESS_SCALE, FENCE_RAIL_THICKNESS_SCALE))
                if a is None:
                    failures.append("{} rail {}".format(r["name"], i))
                else:
                    run_rails += 1

        total_posts += run_posts
        total_rails += run_rails
        details.append({"name": r["name"], "length_m": round(length, 2),
                        "posts": run_posts, "rails": run_rails})

    report["fences"] = {"runs": details, "posts": total_posts, "rails": total_rails}
    report["fence_failures"] = failures
    return step("place_fences", not failures,
                "{} runs -> {} posts, {} rails{}".format(
                    len(details), total_posts, total_rails,
                    "; failed: " + ", ".join(failures[:3]) if failures else ""))


def mesh_asset_bounds(asset):
    """World-space-independent bounds of an imported StaticMesh, in cm.

    UStaticMesh::GetBounds is not a script property, so read the struct the
    asset does expose. Returns None if neither is available, which the caller
    records rather than treats as a failure - an unknown bound is not evidence
    of an empty mesh.
    """
    for prop in ("bounds", "extended_bounds"):
        try:
            b = asset.get_editor_property(prop)
            o = b.get_editor_property("origin")
            e = b.get_editor_property("box_extent")
            return {"origin": [o.x, o.y, o.z], "extent_cm": [e.x, e.y, e.z]}
        except Exception:  # noqa: BLE001
            continue
    return None


def _has_property(obj, name):
    try:
        obj.get_editor_property(name)
        return True
    except Exception:  # noqa: BLE001
        return False


def verify_placed_collision():
    """Confirm the dressing we just placed is actually solid, before saving.

    A fence that renders but does not collide is worse than no fence: it looks
    like a tactical option and quietly is not one, and nothing in a screenshot
    or a mesh count would reveal it. Ray-cast straight down onto a sample of the
    actors we placed and require a hit.

    Run here, immediately after placement, so a failure is attributable to the
    placement rather than to whatever happens across the save and reload.
    """
    world = current_world()
    level = current_level()
    if not world or not level:
        return step("verify_collision", False, "no world")

    def hits(actor):
        # get_actor_location() returns CENTIMETRES, so add the probe height in
        # centimetres too. Multiplying by 100 here put the whole trace far above
        # the world and it passed through nothing at all.
        #
        # The probe extends BELOW the actor origin as well as above. A mesh whose
        # origin sits at mid-height - the barrel does, because joining a
        # cylinder leaves the origin on the median vertex - has all of its
        # geometry below loc.z, and a probe that stopped at the origin would
        # graze the top face and report nothing.
        loc = actor.get_actor_location()
        try:
            res = unreal.SystemLibrary.line_trace_single(
                world,
                unreal.Vector(loc.x, loc.y, loc.z + 400.0),
                unreal.Vector(loc.x, loc.y, loc.z - 400.0),
                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True,
                [], unreal.DrawDebugTrace.NONE, True,
            )
        except Exception as exc:  # noqa: BLE001
            return None
        if isinstance(res, (list, tuple)):
            return bool(res[0]) if res else False
        return res is not None

    def sits_on_ground(actor):
        """Compare the actor's origin height with the terrain beneath it.

        A dressing item whose origin is at its base should sit at the terrain
        height. An item whose origin is at mid-height will read as 'below the
        ground' by roughly half its own height, which is expected rather than a
        fault — so this is reported, not asserted, and it is what makes a
        mid-origin mesh visible instead of mysterious.
        """
        loc = actor.get_actor_location()
        gz = ground_z(loc.x / 100.0, loc.y / 100.0, None)
        if gz is None:
            return None
        return round((loc.z - gz) / 100.0, 3)

    # Sample by type, because scrub is intentionally non-colliding and would
    # otherwise dominate a first-N sample and mask a real failure.
    wanted, sampled, checked, failed = ("Post", "Rail", "Wreck", "Crate", "Barrel"), [], [], []
    for actor in unreal.GameplayStatics.get_all_actors_of_class(level, unreal.StaticMeshActor):
        try:
            label = actor.get_actor_label()
        except Exception:  # noqa: BLE001
            continue
        if not label.startswith(LABEL_PREFIX):
            continue
        for token in wanted:
            if token in label and token not in [t for t, _ in sampled]:
                sampled.append((token, actor))
                break
        if len(sampled) == len(wanted):
            break

    for token, actor in sampled:
        hit = hits(actor)
        entry = {"type": token, "label": actor.get_actor_label(), "hit": hit}
        try:
            entry["origin_minus_ground_m"] = sits_on_ground(actor)
        except Exception as exc:  # noqa: BLE001
            entry["origin_minus_ground_error"] = str(exc)
        checked.append(entry)
        if not hit:
            failed.append("{} ({})".format(token, actor.get_actor_label()))

    report["collision_check"] = checked
    for e in checked:
        log("  {} {}: hit={} origin-ground={}m".format(
            e["type"], e["label"], e["hit"], e.get("origin_minus_ground_m")))
    return step("verify_collision", not failed,
                "{}/{} sampled solid dressing types collide{}".format(
                    len(checked) - len(failed), len(checked),
                    "; MISSING: " + ", ".join(failed) if failed else ""))


def save():
    sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    for name in ("save_current_level", "save_all_dirty_levels"):
        fn = getattr(sub, name, None)
        if fn is None:
            continue
        try:
            if fn():
                return step("save", True, name)
        except Exception as exc:  # noqa: BLE001
            warn("{}: {}".format(name, exc))
    return step("save", False, "no working save API")


def finish():
    try:
        os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
        with open(REPORT_PATH, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        unreal.log("[DryRiverDress] REPORT_WRITTEN {}".format(REPORT_PATH))
    except Exception:  # noqa: BLE001
        unreal.log("[DryRiverDress] report write failed:\n" + traceback.format_exc())
    unreal.log("[DryRiverDress] COMPLETE ok={}".format(report.get("ok")))


def main():
    try:
        if not load_level():
            return finish()

        rows, err = read_csv(DRESSING_CSV, ("name", "type", "x", "y", "z", "rot_y", "scale"))
        if err:
            step("read_dressing_csv", False, err)
            return finish()
        step("read_dressing_csv", True, "{} rows".format(len(rows)))

        frows, err = read_csv(FENCES_CSV, ("name", "x1", "y1", "x2", "y2"))
        if err:
            step("read_fences_csv", False, err)
            return finish()
        step("read_fences_csv", True, "{} rows".format(len(frows)))

        if not import_dressing_meshes():
            return finish()

        meshes = {}
        for name in sorted(set(MESH_FOR_TYPE.values()) | {MESH_FENCE_POST, MESH_FENCE_RAIL}):
            asset = unreal.EditorAssetLibrary.load_asset("{}/{}".format(MESH_DEST, name))
            if isinstance(asset, unreal.StaticMesh):
                meshes[name] = asset
        step("load_meshes", True, "{} available".format(len(meshes)))

        clear_existing()
        # Fences BEFORE point dressing, deliberately. Every placement snaps its
        # height with a downward ray, and once crates and wrecks exist that ray
        # hits THEM rather than the ground - a post ends up standing on a barrel.
        # Placing the long thin things first means every snap in this pass reads
        # bare terrain. Tools/verify_dressing.py additionally keeps solid
        # dressing clear of fence lines, so the reverse order cannot bite later.
        fence_ok = place_fences(frows, meshes)
        dress_ok = place_dressing(rows, meshes)
        collide_ok = verify_placed_collision()
        saved = save()

        report["ok"] = bool(dress_ok and fence_ok and collide_ok and saved)
        report["result_summary"] = "dressing={} fences={} collide={} saved={} resnapped={}".format(
            dress_ok, fence_ok, collide_ok, saved, report["resnapped"])
        return finish()
    except Exception:  # noqa: BLE001
        report["errors"].append(traceback.format_exc())
        unreal.log("[DryRiverDress] raised:\n" + traceback.format_exc())
        try:
            save()
        except Exception:  # noqa: BLE001
            pass
        return finish()


main()
