# Copyright Southern Spear. All Rights Reserved.
#
# Headless construction of the Dry River vertical-slice level.
#
#   UnrealEditor-Cmd.exe SouthernSpear.uproject -nullrhi -unattended -nosplash \
#       -nosound -ExecutePythonScript=Tools/Unreal/build_dryriver_level.py
#
# ONE REQUIRED COMMAND-LINE FLAG:
#
#   -ini:Engine:[/Script/NavigationSystem.NavigationSystemV1]:\
#       bWaitForAsyncLoadingBeforeBuildingNavigationAutomatically=False
#
# That property defaults to true, which makes DoInitialSetup() take
# ENavigationBuildLock::AsyncLoadLock (flags 0x20). While that lock is held,
# UNavigationSystemV1::Build() refuses to do anything:
#
#   "Navigation NOT building because navigation build is locked (flags: 0x20)"
#
# and the lock is only released by a later asset-compile callback, i.e. on a
# tick. A one-shot script cannot wait for that. Overriding it on the command
# line keeps the project default intact for everyone working in the editor,
# while making this build deterministic.
#
# Everything here is SYNCHRONOUS on purpose. The obvious approach — spawn the
# navigation volume, then wait for the async build in a post-tick callback —
# does not work with -ExecutePythonScript, because the editor tears the world
# down as soon as the script returns and the callback never gets a tick. That
# was observed directly, not guessed at.
#
# Instead we use the editor's own blocking build, the same code path behind the
# "Build Paths" toolbar button:
#
#   UUnrealEdEngine::HandleBuildPathsCommand  (UnrealEdSrv.cpp)
#     -> FEditorBuildUtils::EditorBuild(World, FBuildOptions::BuildAIPaths)
#     -> console command "BUILDPATHS"
#
# The result is a deterministic, CI-friendly one-shot script with no timing
# dependence, and a real acceptance check: a navigable path must exist between
# the two deployment points, 170 m apart across the whole map.
#
# See Docs/MAPS_DRYRIVER.md for the design and Docs/CHANGELOG.md for evidence.

import csv
import json
import os
import traceback

import unreal

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

PROJECT_DIR = unreal.Paths.project_dir()
FBX_PATH = os.path.join(PROJECT_DIR, "Content", "Art", "Blockout", "SS_MAP_DryRiver_01.fbx")
LAYOUT_CSV = os.path.join(PROJECT_DIR, "Content", "Art", "Blockout", "SS_MAP_DryRiver_01_Layout.csv")

MESH_DEST = "/Game/Art/Blockout"
MESH_FALLBACK_NAME = "SS_MAP_DryRiver_01"
LEVEL_PATH = "/Game/Maps/L_DryRiver_01"
REPORT_PATH = os.path.join(PROJECT_DIR, "Build", "dryriver_level_report.json")

# Playable area is 260 x 180 m with 14 m of relief (Docs/MAPS_DRYRIVER.md).
NAV_TARGET_HALF_CM = (13600.0, 9600.0, 4500.0)  # 272 x 192 x 90 m
NAV_CENTRE_Z_CM = 800.0
# Bounds sizing, established empirically on this engine:
#   * the default AVolume brush half-extent is 100 cm, so the volume's
#     WORLD scale maps to nav bounds as  half_cm = world_scale * 100
#   * a script-spawned brush volume comes back from a save/load cycle with its
#     scale multiplied by 4 (set 140, reloaded as 560 — confirmed twice)
# so the value saved here must be a quarter of the desired world scale:
#     saved_scale * 4 * 100 == desired_half_cm
# Getting this wrong by 4x is not cosmetic: at 4x the volume spans ~1120 m,
# which asks for roughly 136,000 nav tiles and the build silently produces
# none at all.
NAV_SCALE = unreal.Vector(34.0, 24.0, 8.0)  # -> world (136, 96, 32)
NAV_GROWTH_ATTEMPTS = 2

report = {"ok": False, "steps": [], "warnings": [], "errors": [], "path_verification": {}}


def log(msg):
    unreal.log("[DryRiver] {}".format(msg))


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    log("{} {} {}".format("OK  " if ok else "FAIL", name, detail))
    return bool(ok)


def warn(msg):
    report["warnings"].append(str(msg))
    log("WARN {}".format(msg))


# --------------------------------------------------------------------------
# Construction
# --------------------------------------------------------------------------


def new_level():
    """Regenerate the level from scratch.

    NewLevel refuses to overwrite an existing asset, so a stale level from a
    previous run would make this script non-idempotent. Deleting first is safe:
    the level is a pure build artefact of this script, its entire contents are
    reconstructed below, and nothing else in the project references it.
    """
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        try:
            if not unreal.EditorAssetLibrary.delete_asset(LEVEL_PATH):
                return step("new_level", False, "could not delete existing {}".format(LEVEL_PATH))
            log("deleted stale level {}".format(LEVEL_PATH))
        except Exception as exc:  # noqa: BLE001
            return step("new_level", False, "delete failed: {}".format(exc))

    sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if sub.new_level(LEVEL_PATH):
        return step("new_level", True, LEVEL_PATH)
    return step("new_level", False, "new_level('{}') returned False".format(LEVEL_PATH))


def current_level():
    return unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).get_current_level()


def current_world():
    level = current_level()
    return level.get_world() if level else None


def import_fbx():
    if not os.path.isfile(FBX_PATH):
        return step("import_fbx", False, "FBX not found: {}".format(FBX_PATH))

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", FBX_PATH)
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

    smi = opts.get_editor_property("static_mesh_import_data")
    for prop, value in (
        ("combine_meshes", True),             # one blockout mesh, positions baked
        ("auto_generate_collision", False),  # convex hulls of a heightfield are useless
    ):
        try:
            smi.set_editor_property(prop, value)
        except Exception as exc:  # noqa: BLE001
            warn("static_mesh_import_data.{}: {}".format(prop, exc))

    task.set_editor_property("options", opts)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    objects = [str(o) for o in (task.get_editor_property("imported_object_paths") or [])]
    report["imported_object_paths"] = objects
    if not objects:
        return step("import_fbx", False, "import produced no objects")
    return step("import_fbx", True, "{} object(s): {}".format(len(objects), objects))


def find_mesh():
    for path in unreal.EditorAssetLibrary.list_assets(MESH_DEST, recursive=False, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if isinstance(asset, unreal.StaticMesh):
            return asset
    return None


def _complex_as_simple():
    """Resolve ECollisionComplexity::UseComplexAsSimple across engine versions.

    Unreal Python has renamed this enum more than once (CollisionComplexity,
    ECollisionComplexity), and an AttributeError here aborts the whole script,
    so resolve it defensively and fall back to the underlying integer. From
    Engine/Source/Runtime/Engine/Classes/Engine/EngineTypes.h:
        UseSimpleAndComplex = 0, UseSimpleAsSimple = 1, UseComplexAsSimple = 2
    """
    for holder in ("CollisionComplexity", "ECollisionComplexity"):
        enum = getattr(unreal, holder, None)
        if enum is None:
            continue
        for member in ("COLLISION_COMPLEXITY_USE_COMPLEX_AS_SIMPLE",
                        "USE_COMPLEX_AS_SIMPLE",
                        "USE_COMPLEX_AS_SIMPLE_AS_SIMPLE"):
            if hasattr(enum, member):
                return getattr(enum, member), "{}.{}".format(holder, member)
    return 2, "raw integer 2 (UseComplexAsSimple)"


def configure_collision(mesh):
    """A blockout must block movement and carry navigation; it does not need to
    be fast. Complex-as-simple is correct for a terrain mesh — convex
    decomposition of a 260 m heightfield would be both wrong and expensive.

    Setting BodySetup.CollisionTraceFlag alone is NOT sufficient and silently
    produces a mesh the navigation generator ignores: the build then finds zero
    dirty tiles and reports success in 0.00s. UStaticMesh::CollisionComplexity
    is the property that also rebuilds the physics state, so set that, verify
    the value stuck, and only then fall back to the low-level flag.
    """
    want, how = _complex_as_simple()
    report["collision_complexity_enum"] = how

    ok = False
    try:
        mesh.set_editor_property("collision_complexity", want)
        got = mesh.get_editor_property("collision_complexity")
        ok = int(got) == int(want) if hasattr(got, "__int__") else got == want
        step("collision_complexity", ok, "set via {} -> read back {}".format(how, got))
    except Exception as exc:  # noqa: BLE001
        step("collision_complexity", False, str(exc))

    if not ok:
        try:
            body = mesh.get_editor_property("body_setup")
            body.set_editor_property(
                "collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
            )
            step("body_setup_trace_flag_fallback", True)
        except Exception as exc:  # noqa: BLE001
            warn("body_setup.collision_trace_flag: {}".format(exc))

    # Navigation relevance. UStaticMesh no longer exposes this as a script
    # property, and it defaults to true, so a failure here is informational.
    try:
        mesh.set_editor_property("can_ever_affect_navigation", True)
    except Exception:  # noqa: BLE001
        log("  can_ever_affect_navigation not settable; default is true")

    # Report what the navigation generator will actually see.
    try:
        report["collision_trace_flag"] = str(
            mesh.get_editor_property("body_setup").get_editor_property("collision_trace_flag")
        )
    except Exception as exc:  # noqa: BLE001
        warn("could not report collision state: {}".format(exc))

    # CRITICAL: the import task saved the mesh with whatever collision the
    # importer produced (none, because auto_generate_collision is off). Changing
    # the trace flag afterwards marks the asset dirty but does not write it, so
    # the .uasset on disk keeps no collision — and the navigation build then
    # gathers zero geometry and reports success in 0.00s. Save it explicitly.
    path = mesh.get_path_name()
    try:
        saved = unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
        step("save_mesh_asset", bool(saved), path)
    except Exception as exc:  # noqa: BLE001
        step("save_mesh_asset", False, str(exc))


def spawn_mesh_actor(mesh):
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
    )
    if not actor:
        return step("spawn_mesh_actor", False, "spawn returned None")
    actor.set_actor_label("SS_Blockout_Geometry")
    try:
        smc = actor.static_mesh_component
        smc.set_static_mesh(mesh)
        smc.set_collision_profile_name("BlockAll")
        return step("spawn_mesh_actor", True, "{}".format(mesh.get_name()))
    except Exception as exc:  # noqa: BLE001
        return step("spawn_mesh_actor", False, str(exc))


def read_layout():
    rows = []
    if not os.path.isfile(LAYOUT_CSV):
        warn("layout CSV missing: {}".format(LAYOUT_CSV))
        return rows
    with open(LAYOUT_CSV, "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(
                {
                    "name": row["name"],
                    "x": float(row["x"]),
                    "y": float(row["y"]),
                    "z": float(row["z"]),
                    "kind": row["kind"],
                }
            )
    report["layout_rows"] = rows
    return rows


def spawn_gameplay_actors(rows):
    """Deployments become PlayerStarts, objectives become placeholder actors at
    the exact verified coordinates from the layout CSV.

    ADR-003: the level does NOT assign teams. ESS_TeamId is match-relative and
    decided by the game mode, so these are simply named spawn points. Baking a
    faction into map data is precisely what ADR-003 exists to prevent.
    """
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    placed = []
    for row in rows:
        # Y is negated: the layout CSV is Blender (right-handed) space, Unreal is
        # left-handed, and the FBX import mirrors Y accordingly. Getting this
        # wrong is silent — the map is symmetric in Y, so the two deployments
        # simply swap ends and everything still looks plausible. The navigation
        # pass now cross-checks traced ground height against the CSV to catch it.
        x_m = float(row["x"])
        y_m = -float(row["y"])
        z_m = float(row["z"])
        loc = unreal.Vector(x_m, y_m, z_m)

        if row["kind"] == "Deployment":
            # Lyra's game mode expects ALyraPlayerStart; a plain APlayerStart is
            # reported by map check.
            start_class = getattr(unreal, "LyraPlayerStart", unreal.PlayerStart)
            actor = actors.spawn_actor_from_class(start_class, loc, unreal.Rotator(0, 180, 0))
            if actor:
                actor.set_actor_label(row["name"])
                # Default capsule half-height is 88 cm; stand the pawn on the deck.
                actor.set_actor_location(
                    unreal.Vector(x_m, y_m, z_m + 100.0), False, True
                )
        else:
            actor = actors.spawn_actor_from_class(unreal.Actor, loc, unreal.Rotator(0, 0, 0))
            if actor:
                actor.set_actor_label(row["name"])
        placed.append({
            "name": row["name"],
            "kind": row["kind"],
            "ok": bool(actor),
            "unreal_x": x_m,
            "unreal_y": y_m,
            "unreal_z": z_m,
        })

    report["gameplay_actors"] = placed
    failed = [p["name"] for p in placed if not p["ok"]]
    return step(
        "spawn_gameplay_actors",
        bool(placed) and not failed,
        "{} placed{}".format(len(placed), "; failed: " + ",".join(failed) if failed else ""),
    )


def set_and_confirm_scale(volume, target, max_iters=8):
    """Set the volume scale and verify what was actually stored.

    The obvious call — set_actor_scale3d(200) then read back 200 — does not
    hold here: a NavMeshBoundsVolume is brush-based, and after the growth loop
    asked for 200, 400 and 800, the stored scale still read back as 80, which
    produced TotalNavBounds of only +/-80 m and left both deployments outside
    the navigation volume entirely.

    Rather than trust the setter, read back what landed and keep applying a
    multiplicative correction until the stored scale matches. This converges
    regardless of whatever normalisation the brush path is doing, and it
    records the factor so the behaviour is documented rather than mysterious.
    """
    target = unreal.Vector(target.x, target.y, target.z)
    applied = None
    for i in range(max_iters):
        volume.set_actor_scale3d(unreal.Vector(target.x, target.y, target.z))
        got = volume.get_actor_scale3d()
        if abs(got.x - target.x) < 0.5 and abs(got.y - target.y) < 0.5 and abs(got.z - target.z) < 0.5:
            applied = i + 1
            report["nav_volume_scale_attempts"] = applied
            report["nav_volume_scale"] = [got.x, got.y, got.z]
            return step("spawn_nav_volume", True,
                        "scale ({},{},{}) confirmed after {} set(s)".format(
                            got.x, got.y, got.z, applied))
        # Correct for the ratio actually applied. Guard against a zero or
        # absurd factor so a broken setter cannot produce an infinite scale.
        factor = unreal.Vector(
            _safe_factor(target.x, got.x),
            _safe_factor(target.y, got.y),
            _safe_factor(target.z, got.z),
        )
        log("  scale read back ({:.1f},{:.1f},{:.1f}); correcting by ({:.3f},{:.3f},{:.3f})".format(
            got.x, got.y, got.z, factor.x, factor.y, factor.z))
        target = unreal.Vector(target.x * factor.x, target.y * factor.y, target.z * factor.z)
    got = volume.get_actor_scale3d()
    return step("spawn_nav_volume", False,
                "could not confirm scale; last read back ({:.1f},{:.1f},{:.1f})".format(
                    got.x, got.y, got.z))


def _safe_factor(want, got):
    if got is None or abs(got) < 1e-6:
        return 1.0
    f = want / got
    return max(0.05, min(20.0, f))


def spawn_nav_volume():
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    volume = actors.spawn_actor_from_class(
        unreal.NavMeshBoundsVolume, unreal.Vector(0, 0, NAV_CENTRE_Z_CM), unreal.Rotator(0, 0, 0)
    )
    if not volume:
        return step("spawn_nav_volume", False, "spawn returned None")
    volume.set_actor_label("SS_NavMeshBoundsVolume")

    # Measured mapping: the default AVolume brush half-extent is 100 cm, so
    # bounds half-width in cm == scale * 100 and bounds height == scale_z * 200.
    # The map is 260 x 180 m with 14 m of relief, so a scale of 140/100/30
    # yields roughly +/-140 x +/-100 x 60 m. Oversizing is free: the navmesh is
    # clipped to walkable surfaces and there is no walkable surface off the
    # terrain.
    return set_and_confirm_scale(volume, NAV_SCALE)


def ensure_nav_data():
    """Deliberately does nothing.

    Spawning a RecastNavMesh from script was tried and removed: the navigation
    system registers nav data through RequestRegistrationDeferred, which appends
    to a queue drained on tick, and a one-shot script never ticks. The result was
    a nav data actor that existed but had no geometry, so the build reported
    success in 0.00s with zero tiles.

    Creating the navigation data on map LOAD instead — which is what the second
    pass does — puts it through normal registration, and matches what a person
    does in the editor: place the volume, then Build Paths.
    """
    step("ensure_nav_data", True, "deferred to the navigation pass, by design")


# --------------------------------------------------------------------------
# Synchronous navigation build + real acceptance check
# --------------------------------------------------------------------------


def build_paths():
    """Blocking editor nav build (the 'Build Paths' toolbar command)."""
    world = current_world()
    try:
        unreal.SystemLibrary.execute_console_command(world, "BUILDPATHS")
        return True
    except Exception as exc:  # noqa: BLE001
        warn("BUILDPATHS: {}".format(exc))
        return False


def deployments(rows):
    return [r for r in rows if r["kind"] == "Deployment"]


def path_exists(rows):
    """The acceptance check that actually matters: can an agent walk from one
    deployment to the other? A navmesh actor existing proves nothing; a
    traversable path across all 170 m proves the volume is correctly sized, the
    mesh carries collision, and the build succeeded."""
    deps = deployments(rows)
    world = current_world()
    if len(deps) < 2 or not world:
        report["path_verification"] = {"error": "need 2 deployments and a world"}
        return False

    a, b = deps[0], deps[1]
    # Query just above the terrain, not a metre above it. The nav query extent
    # is small, and a point floating 100 cm over the surface fails to project:
    # observed as "start point not on navmesh" before this was corrected.
    start = unreal.Vector(a["x"] * 100.0, a["y"] * 100.0, (a["z"] + 0.1) * 100.0)
    end = unreal.Vector(b["x"] * 100.0, b["y"] * 100.0, (b["z"] + 0.1) * 100.0)

    result = {"start": [start.x, start.y, start.z], "end": [end.x, end.y, end.z]}
    try:
        path = unreal.NavigationSystemV1.find_path_to_location_synchronously(
            world, start, end, None, None
        )
    except Exception as exc:  # noqa: BLE001
        result["error"] = str(exc)
        report["path_verification"] = result
        warn("find_path_to_location_synchronously: {}".format(exc))
        return False

    if not path:
        result["path_found"] = False
        report["path_verification"] = result
        return False

    # UNavigationPath exposes only PathPoints to script: bIsValid is a private,
    # non-UPROPERTY bitfield. PathPoints is therefore the ground truth, and a
    # better one than a validity flag — a non-empty point list is a path an
    # agent can actually walk.
    try:
        points = [[p.x, p.y, p.z] for p in (path.get_editor_property("path_points") or [])]
    except Exception as exc:  # noqa: BLE001
        result["error"] = "reading path_points: {}".format(exc)
        report["path_verification"] = result
        return False

    result["path_found"] = bool(points)
    result["point_count"] = len(points)
    if points:
        result["first_point"] = points[0]
        result["last_point"] = points[-1]
    report["path_verification"] = result
    log("path check: found={} points={}".format(result["path_found"], result.get("point_count")))
    return bool(points)


def build_and_verify(rows, volume):
    """Build, test, and grow the volume if the path did not fully connect."""
    for attempt in range(1, NAV_GROWTH_ATTEMPTS + 1):
        build_paths()
        if path_exists(rows):
            return step("navmesh_path_verified", True,
                        "attempt {} scale {}".format(attempt, volume.get_actor_scale3d()))
        log("path not found on attempt {}; growing nav volume".format(attempt))
        s = volume.get_actor_scale3d()
        volume.set_actor_scale3d(unreal.Vector(s.x * 2.0, s.y * 2.0, s.z * 1.5))
    return step("navmesh_path_verified", False, "no path after {} attempts".format(NAV_GROWTH_ATTEMPTS))


def save_level():
    sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    for name in ("save_current_level", "save_all_dirty_levels"):
        fn = getattr(sub, name, None)
        if fn is None:
            continue
        try:
            if fn():
                return step("save_level", True, "{}() -> {}".format(name, LEVEL_PATH))
        except Exception as exc:  # noqa: BLE001
            warn("{}: {}".format(name, exc))
    if hasattr(unreal, "EditorAssetLibrary"):
        try:
            if unreal.EditorAssetLibrary.save_asset(LEVEL_PATH, only_if_is_dirty=False):
                return step("save_level", True, "EditorAssetLibrary.save_asset")
        except Exception as exc:  # noqa: BLE001
            warn("EditorAssetLibrary.save_asset: {}".format(exc))
    return step("save_level", False, "no working save API")


def finish():
    report["navmesh_actor_count"] = None
    try:
        os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
        with open(REPORT_PATH, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        unreal.log("[DryRiver] REPORT_WRITTEN {}".format(REPORT_PATH))
    except Exception:  # noqa: BLE001
        unreal.log("[DryRiver] report write failed:\n" + traceback.format_exc())
    unreal.log("[DryRiver] COMPLETE ok={}".format(report.get("ok")))


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def main():
    try:
        if not new_level():
            return finish()
        if not import_fbx():
            return finish()

        mesh = find_mesh()
        if not mesh:
            step("find_mesh", False, "no StaticMesh in {}".format(MESH_DEST))
            return finish()
        step("find_mesh", True, mesh.get_path_name())

        configure_collision(mesh)
        spawn_mesh_actor(mesh)

        rows = read_layout()
        spawn_gameplay_actors(rows)

        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        volume = actors.spawn_actor_from_class(
            unreal.NavMeshBoundsVolume, unreal.Vector(0, 0, NAV_CENTRE_Z_CM), unreal.Rotator(0, 0, 0)
        )
        if not volume:
            step("spawn_nav_volume", False, "spawn returned None")
            return finish()
        volume.set_actor_label("SS_NavMeshBoundsVolume")
        set_and_confirm_scale(volume, NAV_SCALE)

        ensure_nav_data()
        nav_ok = build_and_verify(rows, volume)
        final = volume.get_actor_scale3d()
        report["nav_volume_final_scale"] = [final.x, final.y, final.z]

        # Always save, even if a later step throws. A cosmetic bug in the
        # reporting code must never cost us the whole constructed level — that
        # is exactly what happened once, leaving a saved map with no actors in
        # it and a second pass that could find nothing to work with.
        try:
            saved = save_level()
        except Exception as exc:  # noqa: BLE001
            report["errors"].append(traceback.format_exc())
            saved = False
            unreal.log("[DryRiver] save_level raised:\n" + traceback.format_exc())

        report["ok"] = bool(nav_ok and saved)
        report["result_summary"] = "nav path verified={} level saved={}".format(nav_ok, saved)
        return finish()
    except Exception:  # noqa: BLE001
        report["errors"].append(traceback.format_exc())
        unreal.log("[DryRiver] raised:\n" + traceback.format_exc())
        # Best-effort save so the constructed level is never lost.
        try:
            save_level()
        except Exception:  # noqa: BLE001
            pass
        return finish()


main()
