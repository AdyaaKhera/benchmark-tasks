"""On the station table, between the arms: a white lab tray, fixed to the table. On its left half stands a dark grey
rack of four square pockets, two by two. On its right half are two printed outlines: a light blue circle the size of
a Petri dish and, nearer the middle, a light blue strip the size of a syringe running away from the arms. In front
of the left arm, five 50 mL culture tubes stand in a row of white holders, nearest to farthest: a clear one, one
full of cloudy yellow broth, then three clear ones. In front of the right arm lie a clear Petri dish, a syringe full
of red liquid (nearer the tray) and an empty white syringe (nearer the right edge), both syringes pointing away from
the arms. The tray, rack and holders are fixed; the tubes, dish and syringes are loose.
"""

import math

from yam_arena.constants import FINGER_OPEN, PAD_TIP_PAST_TCP
from yam_arena.demo import Waypoint
from yam_arena.task_file import TABLE_TOP, Box, Cylinder

SCENE = "station"
TOP = TABLE_TOP[SCENE]

# World frame: x forward from the arms, y to the left, z up (m); the arm bases stand at x 0, y +-0.305.
SAMPLES = 3  # the instruction asks for three samples: one tube each, one plate, one syringe

# The tray: a 4 mm slab with a 12 mm rim, 20 x 26 cm outside.
TRAY_X, TRAY_Y = (0.20, 0.40), (-0.13, 0.13)
TRAY_FLOOR_H, RIM_H, RIM_W = 0.004, 0.012, 0.004
FLOOR_Z = TOP + TRAY_FLOOR_H

# The rack: four 40 mm square pockets, 40 mm deep, two by two on the tray's left half, 50 mm apart.
POCKETS = ((0.305, 0.075), (0.305, 0.025), (0.355, 0.075), (0.355, 0.025))  # near left, near right, far left, far right
POCKET_INNER, POCKET_WALL, POCKET_DEPTH = 0.040, 0.004, 0.040

# Printed outlines: 1 mm thick, so a dish or syringe set on one rests 1 mm above the floor.
MARK_H = 0.001
DISH_SPOT = (0.255, -0.085)
SYRINGE_SPOT = (0.270, -0.030)  # the strip runs along x
SYRINGE_STRIP = (0.13, 0.03)

# Supply holders in front of the left arm, nearest to farthest.
HOLDER_XS = (0.14, 0.19, 0.24, 0.29, 0.34)
HOLDER_Y = 0.30
HOLDER_INNER, HOLDER_WALL, HOLDER_H = 0.034, 0.004, 0.030

# A 50 mL conical tube with 40 mL in it, as in the accepted centrifuge task: a 15 mL tube is too light to settle.
TUBE_R, TUBE_H, TUBE_KG = 0.015, 0.115, 0.053
TUBES = {  # name: (holder index, used)
    "tube_a": (0, False),
    "tube_used": (1, True),
    "tube_b": (2, False),
    "tube_c": (3, False),
    "tube_d": (4, False),
}
CLEAN_TUBES = [n for n, (_, used) in TUBES.items() if not used]

DISH_R, DISH_H, DISH_KG = 0.030, 0.016, 0.020  # a 60 mm plate poured with agar, lid on
DISH_XY = (0.18, -0.25)
SYRINGE_SIZE, SYRINGE_KG = (0.110, 0.020, 0.020), 0.025  # a 10 mL syringe, barrel and plunger, as a box
SYRINGES = {"syringe_used": ((0.30, -0.23), True), "syringe": ((0.30, -0.33), False)}

CLEAR, BROTH, BLOOD = (0.82, 0.86, 0.92), (0.85, 0.65, 0.15), (0.75, 0.08, 0.08)
TRAY_WHITE, RACK_GREY, MARK_BLUE = (0.95, 0.95, 0.95), (0.25, 0.25, 0.27), (0.55, 0.75, 0.95)


def _cell(prefix, centre_xy, inner, wall, height, base_z, color):
    """Four fixed walls around a square opening (inner x inner m), standing on base_z, sides along the world axes."""
    cx, cy = centre_xy
    off = inner / 2 + wall / 2
    z = base_z + height / 2
    outer = inner + 2 * wall
    return [
        Box(f"{prefix}_n", pos=(cx, cy + off, z), size=(outer, wall, height), color=color),
        Box(f"{prefix}_s", pos=(cx, cy - off, z), size=(outer, wall, height), color=color),
        Box(f"{prefix}_e", pos=(cx + off, cy, z), size=(wall, inner, height), color=color),
        Box(f"{prefix}_w", pos=(cx - off, cy, z), size=(wall, inner, height), color=color),
    ]


def _tray():
    (x0, x1), (y0, y1) = TRAY_X, TRAY_Y
    cx, cy, lx, ly = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    z = FLOOR_Z + RIM_H / 2
    return [
        Box("tray_floor", pos=(cx, cy, TOP + TRAY_FLOOR_H / 2), size=(lx, ly, TRAY_FLOOR_H), color=TRAY_WHITE),
        Box("tray_rim_far", pos=(x1 - RIM_W / 2, cy, z), size=(RIM_W, ly, RIM_H), color=TRAY_WHITE),
        Box("tray_rim_near", pos=(x0 + RIM_W / 2, cy, z), size=(RIM_W, ly, RIM_H), color=TRAY_WHITE),
        Box("tray_rim_left", pos=(cx, y1 - RIM_W / 2, z), size=(lx, RIM_W, RIM_H), color=TRAY_WHITE),
        Box("tray_rim_right", pos=(cx, y0 + RIM_W / 2, z), size=(lx, RIM_W, RIM_H), color=TRAY_WHITE),
    ]


OBJECTS = [
    *_tray(),
    *[wall for k, xy in enumerate(POCKETS)
      for wall in _cell(f"pocket{k}", xy, POCKET_INNER, POCKET_WALL, POCKET_DEPTH, FLOOR_Z, RACK_GREY)],
    Cylinder("dish_mark", pos=(*DISH_SPOT, FLOOR_Z + MARK_H / 2), radius=DISH_R + 0.004, height=MARK_H,
             color=MARK_BLUE),
    Box("syringe_mark", pos=(*SYRINGE_SPOT, FLOOR_Z + MARK_H / 2), size=(*SYRINGE_STRIP, MARK_H), color=MARK_BLUE),
    *[wall for k, x in enumerate(HOLDER_XS)
      for wall in _cell(f"holder{k}", (x, HOLDER_Y), HOLDER_INNER, HOLDER_WALL, HOLDER_H, TOP, TRAY_WHITE)],
    *[Cylinder(name, pos=(HOLDER_XS[k], HOLDER_Y, TOP + TUBE_H / 2 + 0.001), radius=TUBE_R, height=TUBE_H,
               mass=TUBE_KG, color=BROTH if used else CLEAR)
      for name, (k, used) in TUBES.items()],
    Cylinder("dish", pos=(*DISH_XY, TOP + DISH_H / 2 + 0.001), radius=DISH_R, height=DISH_H, mass=DISH_KG,
             color=CLEAR),
    *[Box(name, pos=(*xy, TOP + SYRINGE_SIZE[2] / 2 + 0.001), size=SYRINGE_SIZE, mass=SYRINGE_KG,
          color=BLOOD if used else TRAY_WHITE)
      for name, (xy, used) in SYRINGES.items()],
]

# Poses come from each object's centre and axis, never from low/high: Arena builds those from the corners of the
# object's local box, which swing out when a cylinder spins on its axis (noted in the accepted centrifuge task).
MAX_FLOOR_GAP = 0.005  # a tube's lowest point within 5 mm of the pocket floor
MAX_TUBE_TILT_DEG = 18.0  # a tube can lean about 14 degrees against a 40 mm pocket's walls
MAX_FLAT_TILT_DEG = 10.0  # the dish or a syringe lying flat
REST_GAP = 0.004  # a dish's or syringe's lowest point within 4 mm of the floor (the outline is 1 mm)
DISH_OFF = 0.015  # the dish's centre within 15 mm of the circle's centre
SYRINGE_OFF_ALONG, SYRINGE_OFF_ACROSS = 0.030, 0.015
SYRINGE_TURN_DEG = 20.0


def _rot(q):
    x, y, z, w = (float(v) for v in q)
    return (
        (1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)),
        (2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)),
        (2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)),
    )


def _axis(q, k):
    """The object's local axis k (0 x, 1 y, 2 z) in the world frame."""
    r = _rot(q)
    return r[0][k], r[1][k], r[2][k]


def _tilt_deg(q, k=2):
    """How far the object's local axis k is from vertical."""
    return math.degrees(math.acos(max(-1.0, min(1.0, abs(_axis(q, k)[2])))))


def _cyl_lowest_z(obj, radius, height):
    c = min(1.0, abs(_axis(obj.quat_xyzw, 2)[2]))
    return float(obj.pos[2]) - (height / 2 * c + radius * math.sqrt(1.0 - c * c))


def _box_lowest_z(obj, size):
    r = _rot(obj.quat_xyzw)
    return float(obj.pos[2]) - sum(abs(r[2][k]) * size[k] / 2 for k in range(3))


def _tube_bottom_xy(tube):
    a = _axis(tube.quat_xyzw, 2)
    sign = -1.0 if a[2] >= 0 else 1.0  # the end that is lower
    return float(tube.pos[0]) + sign * a[0] * TUBE_H / 2, float(tube.pos[1]) + sign * a[1] * TUBE_H / 2


def _pocket_of(tube):
    """The index of the rack pocket the tube stands in, or None: lowest point down on the pocket floor, the centre of
    its lower end inside the pocket's square opening, leaning at most 18 degrees."""
    if _tilt_deg(tube.quat_xyzw) > MAX_TUBE_TILT_DEG:
        return None
    if abs(_cyl_lowest_z(tube, TUBE_R, TUBE_H) - FLOOR_Z) > MAX_FLOOR_GAP:
        return None
    bx, by = _tube_bottom_xy(tube)
    half = POCKET_INNER / 2
    for k, (px, py) in enumerate(POCKETS):
        if abs(bx - px) <= half and abs(by - py) <= half:
            return k
    return None


def _in_tray(obj, lowest_z) -> bool:
    """Its centre over the tray, inside the rim, and down on the floor or an outline."""
    (x0, x1), (y0, y1) = TRAY_X, TRAY_Y
    x, y = float(obj.pos[0]), float(obj.pos[1])
    inside = x0 + RIM_W < x < x1 - RIM_W and y0 + RIM_W < y < y1 - RIM_W
    return inside and lowest_z - FLOOR_Z <= REST_GAP


def _dish_set(dish) -> bool:
    off = math.hypot(float(dish.pos[0]) - DISH_SPOT[0], float(dish.pos[1]) - DISH_SPOT[1])
    flat = _tilt_deg(dish.quat_xyzw) <= MAX_FLAT_TILT_DEG
    return flat and off <= DISH_OFF and _cyl_lowest_z(dish, DISH_R, DISH_H) - FLOOR_Z <= REST_GAP


def _syringe_set(syringe) -> bool:
    long_axis = _axis(syringe.quat_xyzw, 0)
    turn = math.degrees(math.acos(max(-1.0, min(1.0, abs(long_axis[0]) / max(1e-9, math.hypot(*long_axis[:2]))))))
    flat = _tilt_deg(syringe.quat_xyzw, 0) >= 90.0 - MAX_FLAT_TILT_DEG  # the long axis lies level
    along = abs(float(syringe.pos[0]) - SYRINGE_SPOT[0]) <= SYRINGE_OFF_ALONG
    across = abs(float(syringe.pos[1]) - SYRINGE_SPOT[1]) <= SYRINGE_OFF_ACROSS
    low = _box_lowest_z(syringe, SYRINGE_SIZE) - FLOOR_Z <= REST_GAP
    return flat and turn <= SYRINGE_TURN_DEG and along and across and low


_START = {n: (HOLDER_XS[k], HOLDER_Y) for n, (k, _) in TUBES.items()}
_START |= {"dish": DISH_XY} | {n: xy for n, (xy, _) in SYRINGES.items()}
_used_placed = False


def _track(objects):
    """Remember, for the whole trial, whether a used item was ever put in the rack or the tray. Cleared only when
    every loose object is back within 1 cm of its start, as at a reset, where nothing is set up and the score is 0
    anyway."""
    global _used_placed
    if all(math.hypot(objects[n].pos[0] - x, objects[n].pos[1] - y) < 0.01 for n, (x, y) in _START.items()):
        _used_placed = False
    used_tube = objects["tube_used"]
    used_syringe = objects["syringe_used"]
    _used_placed = (
        _used_placed
        or _pocket_of(used_tube) is not None
        or _in_tray(used_tube, _cyl_lowest_z(used_tube, TUBE_R, TUBE_H))
        or _in_tray(used_syringe, _box_lowest_z(used_syringe, SYRINGE_SIZE))
    )


def _parts(objects):
    """(clean tubes racked, dish set, syringe set)."""
    racked = sum(_pocket_of(objects[n]) is not None for n in CLEAN_TUBES)
    return racked, _dish_set(objects["dish"]), _syringe_set(objects["syringe"])


def score(objects):
    """0 if the used tube or the used syringe was ever put in the rack or the tray. Otherwise 0.2 for each clean tube
    standing in a rack pocket, up to three (four racked tubes earn nothing for tubes: the instruction asks for three
    samples), 0.2 for the dish set on its circle and 0.2 for the clean syringe set on its strip."""
    _track(objects)
    if _used_placed:
        return 0.0
    racked, dish, syringe = _parts(objects)
    tubes = racked if racked <= SAMPLES else 0
    return round(0.2 * (tubes + dish + syringe), 6)


def success(objects):
    """Three clean tubes racked, the dish and syringe set and still, no used item ever placed; must hold for 1 s. The
    tubes need not be still: PhysX has no rolling resistance, so a released tube can rock in its pocket for seconds
    (noted in the accepted centrifuge task)."""
    return score(objects) == 1.0 and objects["dish"].resting() and objects["syringe"].resting()


def distance(objects):
    """Items still to set out (0 to 5), plus 5 if a used item was placed."""
    racked, dish, syringe = _parts(objects)
    return (SAMPLES - min(racked, SAMPLES)) + (not dish) + (not syringe) + 5 * _used_placed


# The demo: the left arm racks three clean tubes; the right arm sets the dish and the syringe, then waits clear.
GRIP_BELOW_TOP = 0.045  # a tube is gripped 4.5 cm below its top
_TUBE_TCP_TO_BOTTOM = TUBE_H - GRIP_BELOW_TOP
_TUBE_GRIP_Z = TOP + 0.001 + _TUBE_TCP_TO_BOTTOM
_TUBE_CARRY_Z = FLOOR_Z + POCKET_DEPTH + 0.015 + _TUBE_TCP_TO_BOTTOM  # bottom 1.5 cm over the pocket rims
_TUBE_SET_Z = FLOOR_Z + _TUBE_TCP_TO_BOTTOM
_TUBE_CLEAR_Z = max(TOP + TUBE_H + PAD_TIP_PAST_TCP + 0.015, _TUBE_CARRY_Z)  # pads 1.5 cm over a standing tube
# Pads 44 mm apart (0 is closed, FINGER_OPEN 94 mm): 7 mm each side of a 30 mm tube, and 13 mm short of a tube in
# the next pocket, 50 mm along.
FINGER_PART_OPEN = FINGER_OPEN * 44 / 94


def _grip(width):
    """The finger target that closes the pads to 8 mm narrower than a part ``width`` m across: each finger then pushes
    without saturating, and the pair centres the part. Fully shut, the fingers saturate and a part can slide onto one
    (noted in the accepted fragile-stow task)."""
    return FINGER_OPEN * max(0.0, width - 0.008) / 0.094


TUBE_GRIP, DISH_GRIP, SYRINGE_GRIP = _grip(2 * TUBE_R), _grip(2 * DISH_R), _grip(SYRINGE_SIZE[1])


def _rack_tube(holder_x, pocket):
    """Grip the tube in a holder (fingers across world y), lift it out, carry it over a pocket, lower it onto the
    pocket floor, let go and go back up. Over the rack the fingers open only part way: fully open, one would come
    down on the tube in the next pocket."""
    hx, hy, (px, py) = holder_x, HOLDER_Y, POCKETS[pocket]
    return [
        Waypoint(1.5, (hx, hy, _TUBE_CLEAR_Z), FINGER_OPEN, "over the tube"),
        Waypoint(1.5, (hx, hy, _TUBE_GRIP_Z), FINGER_OPEN, "down"),
        Waypoint(0.8, (hx, hy, _TUBE_GRIP_Z), TUBE_GRIP, "grip"),
        Waypoint(1.5, (hx, hy, _TUBE_CARRY_Z), TUBE_GRIP, "lift out of the holder"),
        Waypoint(2.0, (px, py, _TUBE_CARRY_Z), TUBE_GRIP, "carry over the pocket"),
        Waypoint(0.5, (px, py, _TUBE_CARRY_Z), TUBE_GRIP, "settle"),
        Waypoint(2.0, (px, py, _TUBE_SET_Z), TUBE_GRIP, "lower into the pocket"),
        Waypoint(0.5, (px, py, _TUBE_SET_Z), TUBE_GRIP, "hold on the floor"),
        Waypoint(1.0, (px, py, _TUBE_SET_Z), FINGER_PART_OPEN, "let go"),
        Waypoint(0.8, (px, py, _TUBE_SET_Z), FINGER_PART_OPEN, "wait, fingers open"),
        Waypoint(1.0, (px, py, _TUBE_CLEAR_Z), FINGER_PART_OPEN, "up"),
    ]


FLAT_GRIP_ABOVE_TABLE = 0.016  # the TCP this far above the surface: pad tips 3 mm above it
_FLAT_TRAVEL_Z = TOP + 0.12


def _set_flat(start_xy, spot_xy, grip):
    """Pick a flat-lying dish or syringe (fingers across world y) and set it down on its outline."""
    (sx, sy), (px, py) = start_xy, spot_xy
    grip_z = TOP + FLAT_GRIP_ABOVE_TABLE
    set_z = FLOOR_Z + MARK_H + FLAT_GRIP_ABOVE_TABLE + 0.002
    return [
        Waypoint(1.5, (sx, sy, _FLAT_TRAVEL_Z), FINGER_OPEN, "over it"),
        Waypoint(1.5, (sx, sy, grip_z), FINGER_OPEN, "down"),
        Waypoint(0.8, (sx, sy, grip_z), grip, "grip"),
        Waypoint(1.2, (sx, sy, _FLAT_TRAVEL_Z), grip, "lift"),
        Waypoint(2.0, (px, py, _FLAT_TRAVEL_Z), grip, "carry over the tray"),
        Waypoint(1.5, (px, py, set_z + 0.01), grip, "lower to just over the outline"),
        Waypoint(1.0, (px, py, set_z), grip, "set down slowly"),
        Waypoint(0.8, (px, py, set_z), FINGER_OPEN, "let go"),
        Waypoint(1.0, (px, py, _FLAT_TRAVEL_Z), FINGER_OPEN, "up"),
    ]


RIGHT_PARK = (0.20, -0.30, _FLAT_TRAVEL_Z)  # over the right arm's side, clear of the tray
TUBE_PLAN = (("tube_a", 2), ("tube_b", 0), ("tube_c", 1))  # far left, near left, near right


def demo():
    """The right arm sets the dish on its circle and the empty syringe on its strip, then parks over its own side.
    Meanwhile the left arm racks the nearest clean tube in the far left pocket, then the next two in the near pockets,
    skipping the used tube. It leaves the far right pocket empty: at its corner of the tray the left arm is near the
    edge of its reach."""
    right = [*_set_flat(DISH_XY, DISH_SPOT, DISH_GRIP), *_set_flat(SYRINGES["syringe"][0], SYRINGE_SPOT, SYRINGE_GRIP)]
    right.append(Waypoint(1.5, RIGHT_PARK, FINGER_OPEN, "park clear of the tray"))
    left = [w for name, k in TUBE_PLAN for w in _rack_tube(HOLDER_XS[TUBES[name][0]], k)]
    return {"left": left, "right": right}
