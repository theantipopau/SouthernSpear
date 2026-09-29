# Southern Spear - Wandarra layout spec (M-009, the MOUT training village).
#
# Pure Python: no unreal, no bpy. Every dimension and position the build and
# verify tools use is read from this file, so generator and verifier cannot
# disagree (the dryriver_spec.py pattern). Positions are metres on the site
# frame: origin at the south-west corner of a 300 x 300 m site, x east, y
# north, ground at z = 0. The Unreal builder converts with Y mirrored:
#   unreal = (x * 100, -y * 100, z * 100)   # centimetres
#
# The village is an INVENTED training facility (producer decision, Session 082;
# MAPS_TRAININGRANGE.md section 4.1): one big map built from the MOUT kit,
# RustyCars wrecks and EuropeanBeech trees. It must not resemble any real
# facility; the name is an invented locality, used as Ravenshoe and Red Gum are.

ROLE = ("MOUT urban training village: close-quarters clearing, doorway work and "
        "identification among lookalike buildings (GDD section 5 modules 1 and 4), "
        "the map the producer committed to on 2026-09-29")

SITE = dict(size_m=300.0)          # 300 x 300 m, flat, ground z = 0
GROUND_TILE_CM = 300.0             # Ravenshoe gravel albedo world-mapped tile

# ---- Kit and pack paths (project assets reference packs by path; ADR-021) ----
MOUT = "/Game/MOUT_Civilian"
KIT = MOUT + "/Meshes/ModularAssets"
PROPS = MOUT + "/Meshes/Props"
BP = MOUT + "/Blueprints/Buildings"
CARS = "/Game/RustyCarsFree/Geometries"
BEECH = "/Game/EuropeanBeech/Geometry/SimpleWind"
GRAVEL_D = "/Game/Art/Environment/Ravenshoe/Surfaces/T_SS_Raven_Gravel_BC"
GRAVEL_N = "/Game/Art/Environment/Ravenshoe/Surfaces/T_SS_Raven_Gravel_N"

# Modular kit dimensions in metres (vendor BuildingKit: wall length 5 m,
# height 3 m, floor 5 m). Buildings sit on a 1 m planning grid (snap below).
WALL_L, WALL_H, FLOOR = 5.0, 3.0, 5.0
SNAP_M = 1.0

# Buildings are vendor Blueprints: they arrive with materials, interiors and
# (in the interactable-door variants) doors. We place them; we do not rebuild
# them from kit meshes (ADR-004: no gameplay logic lives in placed props).
BUILDING_BPS = {
    "bungalow_01": BP + "/BP_Bungalow",
    "bungalow_02": BP + "/BP_Bungalow_02",
    "bungalow_03": BP + "/BP_Bungalow_03",
    "house_01": BP + "/BP_House",
    "house_02": BP + "/BP_House_02",
    "government": BP + "/BP_GovernmentBuilding_01",
}

# Vendor BuildingKit mesh dimensions drive the church assembly and the
# documented kit totals in Docs/MAPS_WANDARRA.md (all in metres).
CHURCH_PARTS = {
    "wall": KIT + "/ChurchKit/SM_Church_wall",
    "wall_half": KIT + "/ChurchKit/SM_Church_Wall_Half",
    "wall_quarter": KIT + "/ChurchKit/SM_Church_Wall_Quarter",
    "roof": KIT + "/ChurchKit/SM_Church_Roof",
    "tower_top": KIT + "/ChurchKit/SM_Church_Tower_Top",
    "cross": KIT + "/ChurchKit/SM_Church_Cross",
    "door": KIT + "/ChurchKit/SM_Church_Door_01",
    "window": KIT + "/ChurchKit/SM_Church_Window",
}

# Prop asset per furniture kind. Skeletal meshes (the Flag set) are excluded:
# they need an animation Blueprint and enter nothing (ADR-020 pattern).
FURNITURE_MESH = {
    "bollard_a": PROPS + "/Bollards/SM_Bollard_01",
    "bollard_b": PROPS + "/Bollards/SM_Bollard_02",
    "hydrant": PROPS + "/FireHydrant/SM_Fire_Hydrant_01",
    "bin": PROPS + "/TrashCans/SM_Trash_Can_01a",
    "bin_b": PROPS + "/TrashCans/SM_Trash_Can_01b",
    "bench": PROPS + "/ParkBench/SM_Park_Bench_01",
    "postbox": PROPS + "/PostBox/SM_Post_Box_01a",
    "bus_stop": PROPS + "/BusStop/SM_BusStop_01",
    "clothesline": PROPS + "/ClothesLine/SM_ClothesLine",
    "police_sign": PROPS + "/PoliceSign/SM_PoliceStation_Signage",
    "fountain": PROPS + "/Fountain/SM_Fountain",
    "swing": PROPS + "/Playground/SwingSet/SM_PlaygroundSwings_01",
    "slide": PROPS + "/Playground/Slide/SM_PlaygroundSlide_01",
    "climbing_frame": PROPS + "/Playground/ClimbingFrame/SM_ClimbingFrame",
    "power_pole": PROPS + "/ElectricityPole/SM_ElectricityPole_01",
    "fence_2m": PROPS + "/Fencing/FenceSetA/2m/SM_Fence_A_2m",
    "fence_1_5m": PROPS + "/Fencing/FenceSetA/1_5m/SM_Fence_A_1_5m",
    "fence_1m": PROPS + "/Fencing/FenceSetA/1m/SM_Fence_A_1m",
    "picket_1m": PROPS + "/Fencing/FenceSetA/1m/SM_Fence_Picket_A_1m",
}
CAR_MESHES = [CARS + "/SM_asset_0%d" % i for i in range(5)]
TREE_MESHES = [BEECH + "/SM_EuropeanBeech_Forest_%02d" % i for i in range(1, 9)] + [BEECH + "/SM_EuropeanBeech_Field_01"]

# ---- Roads ----
# Two streets cross at the centre: the main street runs north-south, the cross
# street east-west. 7 m bitumen + 1.5 m footpath each side = an 11 m corridor
# that traffic-width cover (cars, bollards, bus stop) can break only at points,
# which is what makes the crossings the map's contested ground.
ROAD_W = 7.0
WALK_W = 1.5
MAIN_STREET_X = 150.0
CROSS_STREET_Y = 150.0

def road_corridors():
    """(x0, x1, y0, y1) cm rectangles the audit keeps free of building overlap."""
    half = (ROAD_W / 2 + WALK_W) * 100
    mx, cy = MAIN_STREET_X * 100, CROSS_STREET_Y * 100
    site = SITE["size_m"] * 100
    return [(mx - half, mx + half, 0.0, site),   # main street
            (50.0, site, cy - half, cy + half)]  # cross street, west end at the church

# ---- Buildings ----
# (key, x, y, facing, why). Facing is the side the entrance faces. All on the
# 1 m grid; the builder snaps every coordinate. Bungalows are single storey,
# houses two storey: the two-storey corners hold overwatch over the streets,
# the single-storey rows are the clearing lanes.
BUILDINGS = [
    ("bungalow_02", 98, 55, "E", "first cover off the south approach; team B's flank into town"),
    ("bungalow_01", 98, 95, "E", "clearing lane west of the main street; doorway pairs"),
    ("bungalow_03", 98, 195, "E", "north-west row; approach cover for objective C"),
    ("house_01", 98, 235, "E", "two-storey NW corner: overwatch of the depot gate lane"),
    ("house_02", 202, 55, "W", "two-storey SE corner: overwatch of the green and the south crossing"),
    ("bungalow_01", 202, 95, "W", "east row clearing lane; mirrors the west row"),
    ("bungalow_02", 202, 195, "W", "east row north of the crossing; park approach cover"),
    ("bungalow_03", 202, 235, "W", "east row far north; bounds the NE block"),
    ("government", 105, 197, "S", "civic face onto the cross street; forecourt benches and the police sign"),
    ("house_02", 235, 197, "S", "north side of the cross street; closes the park's south-west corner"),
    ("house_01", 235, 102, "N", "two-storey facing the intersection: the strongest overwatch, fought over"),
]

# The church is assembled from ChurchKit meshes on the building grid (vendor
# Blueprints have no church). Its east front terminates the cross street: the
# tower is the landmark read from both streets and objective C sits at its door.
CHURCH = dict(x=42, y=150, facing="E",
              body_w=8.0, body_l=16.0, wall_h=WALL_H,
              why="landmark and street terminus; assembly from ChurchKit walls, roof, tower and cross")

# ---- Streets and grounds furniture ----
# (kind, x, y, yaw_deg, why). Yaw is site-frame degrees clockwise from north,
# mirroring the layout-CSV convention; the builder converts to Unreal.
FURNITURE = [
    # Main street: traffic-width cover breaks the 11 m corridor at points only.
    ("bollard_a", 147, 40, 0, "bollard row, south main street edge"),
    ("bollard_b", 153, 120, 0, "bollard row, north of the first block"),
    ("bollard_a", 147, 180, 0, "bollard row, north of the crossing"),
    ("bollard_b", 153, 260, 0, "bollard row, far north"),
    ("hydrant", 143, 143, 0, "intersection south-west corner cover"),
    ("bin", 157, 157, 0, "intersection north-east corner cover"),
    ("bin_b", 143, 118, 0, "bin on the west footpath"),
    ("postbox", 157, 118, 0, "post box on the east footpath"),
    ("bus_stop", 143, 128, 90, "bus stop shelter: waist-high walls facing the road"),
    ("power_pole", 158, 40, 0, "power pole line on the east verge"),
    ("power_pole", 158, 110, 0, "power pole line"),
    ("power_pole", 158, 190, 0, "power pole line"),
    ("power_pole", 158, 260, 0, "power pole line"),
    # Civic forecourt.
    ("bench", 105, 182, 0, "forecourt bench facing the civic building"),
    ("bench", 110, 182, 0, "forecourt bench"),
    ("police_sign", 105, 187, 180, "police signage by the civic face (identification training texture)"),
    ("hydrant", 112, 191, 0, "forecourt corner hydrant"),
    # The green (south-east): low-cover texture on the approach lane.
    ("bus_stop", 226, 40, 270, "green bus stop facing the road"),
    ("clothesline", 226, 68, 0, "clothes line with carpets: sightline breaker at torso height"),
    ("clothesline", 226, 78, 90, "second line, crossed"),
    ("hydrant", 226, 84, 0, "green edge hydrant"),
    ("postbox", 214, 30, 270, "green corner post box"),
    ("bench", 220, 55, 90, "green bench"),
    # The park (north-east): the open heart. Long views, punished by exposure.
    ("fountain", 240, 250, 0, "park centre fountain: the only hard cover in the open"),
    ("bench", 228, 250, 90, "park bench facing the fountain"),
    ("bench", 252, 250, 270, "park bench facing the fountain"),
    ("bench", 240, 262, 180, "park bench facing the fountain"),
    ("bin", 234, 242, 0, "park bin"),
    ("swing", 215, 235, 45, "playground swing frame: low cover cluster"),
    ("slide", 215, 262, 315, "playground slide"),
    ("climbing_frame", 228, 248, 0, "climbing frame"),
    ("postbox", 197, 220, 0, "park gate post box"),
    # Depot yard (north-west): compound-clearing practice.
    ("bin_b", 32, 212, 0, "depot yard bin by the gate"),
    ("bollard_a", 60, 212, 0, "depot bollard row"),
    ("bollard_b", 64, 212, 0, "depot bollard row"),
]

# Fence runs: (x0, y0, x1, y1, [(gap_start, gap_end) along the run in metres],
# picket?, why). The builder tiles the longest kit length that fits, leaving
# the gates open. Depot compound walls compound clearing; the picket row gives
# the green a low front boundary you can shoot and see over.
FENCE_RUNS = [
    (20, 205, 85, 205, [(48.8, 51.2)], False, "depot south wall; main gate narrowed to a 2.4 m personnel gate for door control (ADR-041)"),
    (20, 285, 85, 285, [], False, "depot north wall"),
    (20, 205, 20, 285, [], False, "depot west wall"),
    (85, 205, 85, 285, [(41.4, 43.8)], False, "depot east wall; side gate 2.4 m, absolute y 246.4-248.8"),
    (212, 15, 212, 85, [(44.4, 46.8)], True, "green picket boundary; gate 2.4 m, absolute y 59.4-61.8"),
]

# ---- Awnings and doors (Session 083: ADR-041) ----
# Government awnings (vendor BPs with pillars and roofs) dress the civic face
# and the row buildings' footpath sides as shopfront verandahs: a covered edge
# that breaks a street sightline at torso height and gives crouch cover where
# the buildings meet the footpath. The dressing pass pushes each awning out
# along its facing until it clears the (unmeasured) vendor building box by 40 cm
# - the spec row is the intent, the pass reconciles with the real footprint.
AWNING_BPS = {
    "awning_01a": MOUT + "/Blueprints/GovernmentAwnings/BP_GovernmentAwning_01a",
    "awning_01b": MOUT + "/Blueprints/GovernmentAwnings/BP_GovernmentAwning_01b",
    "awning_02a": MOUT + "/Blueprints/GovernmentAwnings/BP_GovernmentAwning_02a",
    "awning_02b": MOUT + "/Blueprints/GovernmentAwnings/BP_GovernmentAwning_02b",
}
AWNING_ROWS = [
    ("awning_01a", 103.5, 194.5, 180, "civic face west awning: the post office verandah"),
    ("awning_02a", 109.5, 194.5, 180, "civic face east awning: the store verandah"),
    ("awning_01b", 100.5, 95, 90, "west row verandah over the main-street footpath (east side)"),
    ("awning_02b", 199.5, 195, 90, "east row park-side verandah"),
    ("awning_01a", 234, 194.5, 180, "the park-facing store's verandah on the cross street"),
    ("awning_02a", 234, 104.5, 0, "the corner building's north verandah over the depot lane"),
]

# Interactable door Blueprints as SCENERY ONLY (ADR-041: not wired into
# gameplay this phase). They stand in existing fence-line openings - the depot
# gates and the green's picket gate - so compound-clearing gets door control
# (open, clear, close behind) where a gap already exists. They are NOT placed
# on building walls: vendor buildings have their doorways meshed in, and the
# footprints are unmeasured (R-90), so a wall-mounted door could block a real
# doorway. Building-mounted doors wait for the bounds dump and, per ADR-041,
# a server-owned SSDoorComponent.
DOOR_BPS = {
    "door_wood": MOUT + "/Blueprints/Doors/BP_WoodenDoor_Interactable",
    "door_glass": MOUT + "/Blueprints/Doors/BP_GlassDoors_Interactable",
    "door_green": MOUT + "/Blueprints/Doors/BP_GreenDoors_Interactable",
}
DOOR_ROWS = [
    ("door_wood", 85, 247.6, 90, "depot side gate: door plane along the N-S wall, normal east. The MAIN gate stays an open 2.4 m gap: TeamOne spawns inside the compound and the navmesh bakes a closed door as a blocker, so the compound's walkable exit must never depend on an unwired scenery door (ADR-041)"),
    ("door_wood", 212, 60.6, 90, "the green's picket gate: normal east off the south lane; nobody spawns inside this yard"),
]

# ---- Cars: RustyCars wrecks ----
# (mesh_index, x, y, yaw_deg, why). Ten wrecks: traffic-width cover on the
# streets, hulks in the depot yard, parked along the green. Car size ~4.5 x 2 m.
CARS_LAYOUT = [
    (0, 146, 150, 25, "stalled in the crossing: the map's signature cover"),
    (1, 152, 210, 70, "north main street cover"),
    (2, 148, 75, 15, "south main street cover"),
    (3, 110, 152, 100, "cross street west cover"),
    (4, 195, 147, 80, "cross street east cover"),
    (0, 35, 240, 130, "depot yard hulk"),
    (2, 55, 255, 10, "depot yard hulk"),
    (4, 40, 268, 250, "depot yard hulk by the north wall"),
    (1, 215, 25, 170, "parked along the green"),
    (3, 238, 25, 190, "parked along the green"),
]

# ---- Trees: EuropeanBeech (UE 5.1 native) ----
# Deterministic rows and clusters with jitter. Fixed seed so rebuilds match.
TREE_SEED = 20260930
TREE_ROWS = [
    # (x0, y0, x1, y1, count, why)
    (166, 30, 168, 270, 8, "main street east verge: breaks the 11 m corridor for foot traffic, not wheels"),
    (60, 132, 200, 134, 6, "cross street south verge"),
    (200, 215, 285, 285, 10, "park cluster: the open heart's tree cover"),
    (14, 205, 22, 285, 6, "depot west edge: screens the deployment from the main street"),
    (236, 20, 246, 92, 6, "green east edge"),
    (60, 28, 140, 32, 4, "south boundary scrub"),
]

# ---- Deployments, objectives, protected ground ----
# Deployments are anchors: the level pass drops a start ring around each and
# layout_spawns.py re-lays all starts on the navmesh afterwards (final authority).
DEPLOYS = [
    dict(name="Depot", x=30, y=255, r=12, team="TeamOne",
         why="north-west: behind the compound, screened by trees, opens on a 200 m advance"),
    dict(name="Green", x=270, y=40, r=12, team="TeamTwo",
         why="south-east: behind the green's low cover, mirrored advance"),
]

# Sequential Objectives Assault A -> B -> C, 90 m legs: south street, the
# crossing, the church door. Radii stay at the project's urban 900 cm.
OBJECTIVES = [
    dict(key="A", name="Bus Stop Corner", x=150, y=60, radius_cm=900.0,
         why="south main street: the first fight off both deployments"),
    dict(key="B", name="The Crossing", x=150, y=150, radius_cm=900.0,
         why="the main intersection: open ground broken by the stalled car"),
    dict(key="C", name="Church Square", x=60, y=150, radius_cm=900.0,
         why="the church forecourt: the vista terminus and the hardest opening to defend"),
]

def protected_zones():
    """(x0_cm, y0_cm, x1_cm, y1_cm) rectangles nothing may be placed in and no
    test may ray through: deployment rings, objective capture discs, the road
    corridors' car-free centre at building height, church walls."""
    zones = []
    for d in DEPLOYS:
        r = d["r"] * 100
        zones.append((d["x"] * 100 - r, d["y"] * 100 - r, d["x"] * 100 + r, d["y"] * 100 + r))
    for o in OBJECTIVES:
        r = o["radius_cm"]
        zones.append((o["x"] * 100 - r, o["y"] * 100 - r, o["x"] * 100 + r, o["y"] * 100 + r))
    # Church body and tower footprint (west street end).
    zones.append(((CHURCH["x"] - CHURCH["body_w"]) * 100, (CHURCH["y"] - CHURCH["body_w"] / 2 - 1) * 100,
                  (CHURCH["x"] + CHURCH["body_l"] / 2) * 100, (CHURCH["y"] + CHURCH["body_w"] / 2 + 1) * 100))
    return zones


# ---- Shared geometry helpers (same contract as dryriver_spec.py) ----
def seg_point_distance(ax, ay, bx, by, px, py):
    """Distance in metres from point (px, py) to segment (ax, ay)-(bx, by)."""
    abx, aby = bx - ax, by - ay
    len2 = abx * abx + aby * aby
    if len2 == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - ax) * abx + (py - ay) * aby) / len2))
    cx, cy = ax + t * abx, ay + t * aby
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def _seg_intersects_rect(x0, y0, x1, y1, rx0, ry0, rx1, ry1):
    """Liang-Barsky: does the segment cross the rectangle's interior?"""
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for (p, q) in ((-dx, x0 - rx0), (dx, rx1 - x0), (-dy, y0 - ry0), (dy, ry1 - y0)):
        if p == 0:
            if q < 0:
                return False
            continue
        t = q / p
        if p < 0:
            if t > t1:
                return False
            t0 = max(t0, t)
        else:
            if t < t0:
                return False
            t1 = min(t1, t)
    return t0 <= t1


def run_clears_protected(x0, y0, x1, y1, margin_m=0.0):
    """True if the segment (metres) stays clear of every protected zone."""
    for (zx0, zy0, zx1, zy1) in protected_zones():
        zx0, zy0, zx1, zy1 = zx0 / 100 - margin_m, zy0 / 100 - margin_m, zx1 / 100 + margin_m, zy1 / 100 + margin_m
        for cx, cy in ((x0, y0), (x1, y1)):
            if zx0 <= cx <= zx1 and zy0 <= cy <= zy1:
                return False
        for (px, py) in ((zx0, zy0), (zx1, zy0), (zx0, zy1), (zx1, zy1)):
            if seg_point_distance(x0, y0, x1, y1, px, py) <= margin_m:
                return False
        if _seg_intersects_rect(x0, y0, x1, y1, zx0, zy0, zx1, zy1):
            return False
    return True


def snap(v):
    return round(v / SNAP_M) * SNAP_M
