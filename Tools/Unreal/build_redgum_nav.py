# Southern Spear - Red Gum Station pass 2: build navigation on a fresh load
# (the bounds volume must register on load, see build_dryriver_nav.py).
import json, os, unreal
PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
MAP = "/Game/Maps/L_RedGum_01"
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not unreal.GameplayStatics.get_all_actors_of_class(world, unreal.RecastNavMesh):
    unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
        unreal.RecastNavMesh, unreal.Vector(0, 0, 0), unreal.Rotator(roll=0, pitch=0, yaw=0))
for _ in range(2):
    unreal.SystemLibrary.execute_console_command(world, "BUILDPATHS")
nav = unreal.NavigationSystemV1.get_navigation_system(world)
labels = lambda cls: {x.get_actor_label(): x.get_actor_location() for x in
                      unreal.GameplayStatics.get_all_actors_of_class(world, cls)}
pts = labels(unreal.PlayerStart)
objs = labels(unreal.SSObjectiveActor)

def reachable(p0, p1):
    p = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, p0, p1)
    return p is not None and p.is_valid() and not p.is_partial()

# Everything must connect to the centre objective (ObjB). The example map has
# fenced paddocks and outcrops, so trace-placed points can land in an enclosed
# pocket: move each objective, or each deployment group as a whole, to the
# nearest nav point on 10 m rings that reaches ObjB both ways.
moves = {}
centre = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SSObjectiveActor)
              if "ObjB" in a.get_actor_label()).get_actor_location()


def ok_to(q):
    return reachable(q, centre) and reachable(centre, q)


def relocate(c):
    if ok_to(c):
        return c
    for r in range(10, 160, 10):
        for k in range(16):
            ang = k * 3.14159 / 8
            q = unreal.NavigationSystemV1.project_point_to_navigation(
                world, unreal.Vector(c.x + r * 100 * unreal.MathLibrary.cos(ang), c.y + r * 100 * unreal.MathLibrary.sin(ang), c.z),
                None, None, unreal.Vector(300, 300, 3000))
            if q and ok_to(q):
                return q
    return None


for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SSObjectiveActor):
    c = actor.get_actor_location()
    q = relocate(c)
    if q is not None and q != c:
        actor.set_actor_location(q, False, False)
    moves[actor.get_actor_label()] = None if q is None else round((q - c).length() / 100, 1)
all_starts = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart)
for side in ("A", "B"):
    label = "SS_MAP_RedGum_Deploy" + side
    c = pts[label]
    q = relocate(c)
    moves[label] = None if q is None else round((q - c).length() / 100, 1)
    if q is None or q == c:
        continue
    delta = q - c
    for st in all_starts:
        if st.get_actor_label().startswith(label):
            n = st.get_actor_location() + delta
            g = unreal.NavigationSystemV1.project_point_to_navigation(world, n, None, None, unreal.Vector(300, 300, 3000))
            st.set_actor_location((g if g else n) + unreal.Vector(0, 0, 100), False, False)
pts = labels(unreal.PlayerStart)
objs = labels(unreal.SSObjectiveActor)
route = [pts.get("SS_MAP_RedGum_DeployA")] + [objs[k] for k in sorted(objs)] + [pts.get("SS_MAP_RedGum_DeployB")]
legs = []
for s0, s1 in zip(route, route[1:]):
    p = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, s0, s1)
    ok = p is not None and p.is_valid() and not p.is_partial()
    end = p.path_points[-1] if p is not None and p.path_points else None
    legs.append({"ok": ok, "points": len(p.path_points) if p else 0,
                 "end_gap_cm": round((end - s1).length()) if end else None})
path = all(l["ok"] for l in legs)
saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
r = {"ok": bool(path) and saved, "deploy_to_deploy_path": path, "saved": saved, "legs": legs, "objective_moves_m": moves}
json.dump(r, open(os.path.join(PROJECT_DIR, "Build", "redgum_nav.json"), "w"), indent=1)
unreal.log("[RedGumNav] {}".format(r))
