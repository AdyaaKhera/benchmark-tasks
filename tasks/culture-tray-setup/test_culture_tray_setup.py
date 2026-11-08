"""Checks of culture_tray_setup.py's scoring and demo, without the simulator. Needs yam_arena (the official stack):

    python -m pytest -q test_culture_tray_setup.py
"""

import math
from pathlib import Path

import numpy as np
import pytest

from yam_arena import station
from yam_arena.demo import ArmPlan
from yam_arena.task_file import ObjectState, load

TASK = load(Path(__file__).with_name("culture_tray_setup.py"))
M = TASK.module


def _state(pos, quat=(0.0, 0.0, 0.0, 1.0), moving=False):
    pos = np.array(pos, dtype=float)
    return ObjectState(pos=pos, quat_xyzw=np.array(quat, dtype=float),
                       lin_vel=np.array([0.05, 0.0, 0.0]) if moving else np.zeros(3), ang_vel=np.zeros(3),
                       low=pos - 0.01, high=pos + 0.01)  # low/high are never read by the scorer


def _tilt_x(deg):
    """A quaternion tilting an object ``deg`` about world x."""
    h = math.radians(deg) / 2
    return (math.sin(h), 0.0, 0.0, math.cos(h))


def _yaw(deg):
    h = math.radians(deg) / 2
    return (0.0, 0.0, math.sin(h), math.cos(h))


def tube_at(x, y, bottom_z, tilt_deg=0.0):
    return _state((x, y, bottom_z + M.TUBE_H / 2), _tilt_x(tilt_deg))


def in_holder(name):
    return tube_at(M.HOLDER_XS[M.TUBES[name][0]], M.HOLDER_Y, M.TOP + 0.001)


def in_pocket(k, dx=0.0, dy=0.0, lift=0.0, tilt_deg=0.0):
    return tube_at(M.POCKETS[k][0] + dx, M.POCKETS[k][1] + dy, M.FLOOR_Z + lift, tilt_deg)


def dish_on_spot(dx=0.0, lift=0.0, tilt_deg=0.0):
    return _state((M.DISH_SPOT[0] + dx, M.DISH_SPOT[1], M.FLOOR_Z + M.MARK_H + M.DISH_H / 2 + lift), _tilt_x(tilt_deg))


def syringe_on_spot(dy=0.0, yaw_deg=0.0):
    return _state((M.SYRINGE_SPOT[0], M.SYRINGE_SPOT[1] + dy, M.FLOOR_Z + M.MARK_H + M.SYRINGE_SIZE[2] / 2),
                  _yaw(yaw_deg))


def start():
    s = {n: in_holder(n) for n in M.TUBES}
    s["dish"] = _state((*M.DISH_XY, M.TOP + M.DISH_H / 2))
    for n, (xy, _) in M.SYRINGES.items():
        s[n] = _state((*xy, M.TOP + M.SYRINGE_SIZE[2] / 2))
    return s


def done():
    s = start()
    s.update(tube_a=in_pocket(0), tube_b=in_pocket(1), tube_c=in_pocket(2), dish=dish_on_spot(),
             syringe=syringe_on_spot())
    return s


@pytest.fixture(autouse=True)
def fresh_trial():
    M.score(start())  # every loose object at its start clears the memory of a used item, as at a reset


def test_the_start_scores_zero():
    assert M.score(start()) == 0.0 and not M.success(start())


def test_the_full_setup_is_success():
    assert M.score(done()) == 1.0 and M.success(done())


@pytest.mark.parametrize("racked", [0, 1, 2, 3])
def test_each_racked_tube_earns_a_fifth(racked):
    s = start()
    for k, name in enumerate(["tube_a", "tube_b", "tube_c"][:racked]):
        s[name] = in_pocket(k)
    assert M.score(s) == pytest.approx(0.2 * racked)


def test_any_pocket_counts():
    s = done()
    s["tube_a"] = in_pocket(3)
    assert M.score(s) == 1.0


def test_four_tubes_earn_nothing_for_tubes():
    s = done()
    s["tube_d"] = in_pocket(3)
    assert M.score(s) == pytest.approx(0.4)  # the dish and the syringe only


def test_the_used_tube_racked_scores_zero():
    s = done()
    s["tube_used"] = in_pocket(3)
    assert M.score(s) == 0.0


def test_the_used_syringe_in_the_tray_scores_zero():
    s = done()
    s["syringe_used"] = syringe_on_spot(dy=0.05)
    assert M.score(s) == 0.0


def test_the_used_syringe_carried_over_the_tray_is_no_violation():
    s = done()
    s["syringe_used"] = _state((*M.SYRINGE_SPOT, M.FLOOR_Z + 0.10))
    assert M.score(s) == 1.0


def test_a_used_item_placed_and_taken_back_out_still_scores_zero():
    s = done()
    s["syringe_used"] = syringe_on_spot(dy=0.05)
    M.score(s)
    s["syringe_used"] = _state((*M.SYRINGES["syringe_used"][0], M.TOP + 0.01 + 0.03))  # lifted out, not at start
    assert M.score(s) == 0.0
    s["syringe_used"] = _state((*M.SYRINGES["syringe_used"][0], M.TOP + M.SYRINGE_SIZE[2] / 2))  # back at start
    assert M.score(s) == 0.0  # the rest is still set out, so this is no reset


def test_a_reset_clears_the_memory():
    s = done()
    s["tube_used"] = in_pocket(3)
    M.score(s)
    assert M.score(start()) == 0.0
    assert M.score(done()) == 1.0


def test_a_tube_held_above_the_floor_is_not_racked():
    s = done()
    s["tube_a"] = in_pocket(0, lift=0.01)
    assert M.score(s) == pytest.approx(0.8)


def test_a_tube_leaning_in_its_pocket_counts_up_to_18_degrees():
    s = done()
    s["tube_a"] = in_pocket(0, tilt_deg=14)
    s["tube_a"] = _state(s["tube_a"].pos - np.array([0, 0, M.TUBE_H / 2 * (1 - math.cos(math.radians(14)))
                                                     - M.TUBE_R * math.sin(math.radians(14))]),
                         s["tube_a"].quat_xyzw)  # lowered so its lowest point is on the floor
    assert M._pocket_of(s["tube_a"]) == 0


def test_a_tube_beside_the_rack_is_not_racked():
    s = done()
    s["tube_a"] = in_pocket(0, dx=-0.045)
    assert M.score(s) == pytest.approx(0.8)


@pytest.mark.parametrize(("dx", "ok"), [(0.010, True), (0.020, False)])
def test_the_dish_must_be_on_its_circle(dx, ok):
    s = done()
    s["dish"] = dish_on_spot(dx=dx)
    assert M.score(s) == pytest.approx(1.0 if ok else 0.8)


def test_a_tipped_dish_does_not_count():
    s = done()
    s["dish"] = dish_on_spot(tilt_deg=30)
    assert M.score(s) == pytest.approx(0.8)


@pytest.mark.parametrize(("yaw_deg", "ok"), [(10, True), (180, True), (45, False), (90, False)])
def test_the_syringe_must_lie_along_its_strip(yaw_deg, ok):
    s = done()
    s["syringe"] = syringe_on_spot(yaw_deg=yaw_deg)
    assert M.score(s) == pytest.approx(1.0 if ok else 0.8)


def test_the_syringe_off_its_strip_does_not_count():
    s = done()
    s["syringe"] = syringe_on_spot(dy=0.03)
    assert M.score(s) == pytest.approx(0.8)


def test_the_used_tube_left_in_its_holder_is_fine():
    assert M.score(done()) == 1.0 and M._pocket_of(done()["tube_used"]) is None


@pytest.mark.parametrize("arm", ["left", "right"])
def test_the_demo_is_within_reach(arm):
    plan = ArmPlan(M.demo()[arm], station.BASES[arm])
    for t in np.arange(0.0, plan.duration, 0.05):
        plan.action7(t)
    assert plan.worst_ik_mm < 0.5 and plan.worst_ik_deg < 0.1, (plan.worst_ik_mm, plan.worst_ik_deg)


def test_the_demo_fits_the_run_limit():
    longest = max(sum(w.duration for w in wps) for wps in M.demo().values())
    assert longest * 20 < 2400
